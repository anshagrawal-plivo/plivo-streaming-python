import asyncio
import base64
import os

from deepgram import AsyncDeepgramClient
from deepgram.core.events import EventType
from deepgram.listen.v2.socket_client import AsyncV2SocketClient
from elevenlabs.client import AsyncElevenLabs
from fastapi import FastAPI, Request, Response, WebSocket
from openai import AsyncOpenAI
from plivo import plivoxml
from plivo.xml import StreamElement
from plivo_streaming import ClearedAudioEvent, DtmfEvent, PlayedStreamEvent, PlivoFastAPIStreamingHandler, MediaEvent, StartEvent
import logging
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,  # This is the key line
    format="%(asctime)s - %(levelname)s - %(message)s",
)
load_dotenv()
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration & API Keys
# ============================================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

# Audio configuration
AUDIO_SAMPLE_RATE = int(os.getenv("AUDIO_SAMPLE_RATE"))
AUDIO_CONTENT_TYPE = os.getenv("AUDIO_CONTENT_TYPE")
RECORDING_CALLBACK_URL = os.getenv("RECORDING_CALLBACK_URL")

# Model configuration
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
DEEPGRAM_MODEL = os.getenv("DEEPGRAM_MODEL")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID")

# System prompt
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT")

# ============================================================================
# Client Initialization
# ============================================================================

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
elevenlabs_client = AsyncElevenLabs(api_key=ELEVENLABS_API_KEY)
deepgram_client = AsyncDeepgramClient(api_key=DEEPGRAM_API_KEY)

# Conversation history storage
conversation_history = []

# ============================================================================
# Helper Functions
# ============================================================================


async def get_openai_response() -> str:
    """Get a response from OpenAI based on conversation history."""
    response = await openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            *conversation_history,
        ],
    )
    return response.choices[0].message.content


async def add_message_and_get_response(user_message: str) -> str:
    """Add user message to history and get AI response."""
    conversation_history.append({"role": "user", "content": user_message})
    assistant_response = await get_openai_response()
    conversation_history.append({"role": "assistant", "content": assistant_response})
    
    # Keep only the last 10 pairs (20 messages)
    if len(conversation_history) > 20:
        conversation_history[:] = conversation_history[-20:]
    
    return assistant_response


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI()


# ============================================================================
# HTTP Routes
# ============================================================================


@app.get("/")
def read_root():
    """Health check endpoint."""
    return {"message": "Hello World"}


@app.get("/stream")
def initiate_stream(request: Request):
    """Initialize a Plivo streaming session with bidirectional audio."""
    host = request.headers.get("Host")

    # Build Plivo XML response
    plivo_response = plivoxml.ResponseElement()
    # Record the call session and send the recording metadata to the callback URL
    plivo_response.add_record(
        # maximum number of seconds to record
        max_length=86400,
        record_session=True,
        callback_url=RECORDING_CALLBACK_URL,
    )
    plivo_response.add(
        StreamElement(
            bidirectional=True,
            keepCallAlive=True,
            contentType=f"{AUDIO_CONTENT_TYPE};rate={AUDIO_SAMPLE_RATE}",
            content=f"ws://{host}/stream",
        )
    )

    return Response(content=plivo_response.to_string(), media_type="application/xml")


# ============================================================================
# WebSocket Routes
# ============================================================================

@app.websocket("/stream")
async def stream_websocket_handler(websocket: WebSocket):
    """
    Handle bidirectional audio streaming between Plivo, Deepgram, and ElevenLabs.

    Flow:
    1. Receive audio from Plivo call
    2. Send to Deepgram for transcription
    3. Process transcription with OpenAI
    4. Convert response to speech with ElevenLabs
    5. Stream audio back to Plivo call
    """
    try:
        deepgram_connection: AsyncV2SocketClient = None
        plivo_handler = PlivoFastAPIStreamingHandler(websocket)
        playing = False

        async def stream_elevenlabs_audio(text: str):
            nonlocal playing
            """Convert text to speech using ElevenLabs and stream to Plivo."""
            audio_stream = elevenlabs_client.text_to_speech.stream(
                text=text,
                voice_id=ELEVENLABS_VOICE_ID,
                model_id=ELEVENLABS_MODEL_ID,
                output_format="pcm_16000",
            )
            playing = True
            async for audio_chunk in audio_stream:
                await plivo_handler.send_media(
                    media_data=audio_chunk,
                    content_type=AUDIO_CONTENT_TYPE,
                    sample_rate=AUDIO_SAMPLE_RATE,
                )
            # Send checkpoint to indicate that all audio has been played
            await plivo_handler.send_checkpoint("all_audio_played")

        @plivo_handler.on_played_stream
        async def on_played_stream(event: PlayedStreamEvent):
            nonlocal playing
            """Handle the played stream event."""
            # All audio has been played to the user, so we can stop playing
            playing = False

        async def connect_and_listen_deepgram():
            """Connect to Deepgram and handle transcription events."""
            nonlocal deepgram_connection

            async with deepgram_client.listen.v2.connect(
                model=DEEPGRAM_MODEL,
                encoding="linear16",
                sample_rate=str(AUDIO_SAMPLE_RATE),
            ) as connection:

                async def on_deepgram_message(message):
                    nonlocal playing
                    """Handle incoming Deepgram transcription messages."""
                    if message.type == "TurnInfo" and message.event == "EndOfTurn":
                        logger.info(message.transcript)

                        # Get AI response for the transcribed text
                        ai_response = await add_message_and_get_response(
                            message.transcript
                        )
                        logger.info(f"{ai_response}")

                        # Convert AI response to speech and stream back
                        if playing:
                            # If the audio is still being played to the user, we need to clear the audio buffer
                            await plivo_handler.send_clear_audio()
                            # The audio has been stopped playing to the user, so we can start playing the new audio
                            playing = False
                        await stream_elevenlabs_audio(ai_response)

                deepgram_connection = connection
                logger.info("Connected to Deepgram")
                connection.on(EventType.MESSAGE, on_deepgram_message)
                await connection.start_listening()

        @plivo_handler.on_media
        async def on_plivo_media(event: MediaEvent):
            """Forward incoming audio from Plivo to Deepgram for transcription."""
            if deepgram_connection is not None:
                await deepgram_connection.send_media(
                    event.get_raw_media()
                )
            else:
                logger.error("No Deepgram connection established")

        @plivo_handler.on_start
        async def on_start(event: StartEvent):
            """Handle the start event."""
            logger.info(f"Stream started: {event.start.stream_id}")

        @plivo_handler.on_disconnected
        async def on_disconnected():
            """Handle the disconnected event."""
            logger.info("Disconnected from Plivo")

        @plivo_handler.on_dtmf
        async def on_dtmf(event: DtmfEvent):
            """Handle the DTMF event."""
            logger.info(f"DTMF detected: {event.dtmf.digit}")

        @plivo_handler.on_cleared_audio
        async def on_cleared_audio(event: ClearedAudioEvent):
            """Handle the cleared audio event."""
            logger.info(f"Cleared audio: {event.stream_id}")

        @plivo_handler.on_disconnected
        async def on_disconnected():
            """Handle the disconnected event."""
            logger.info("Disconnected from Plivo")

        @plivo_handler.on_error
        async def on_error(error: Exception):
            """Handle the error event."""
            logger.error(f"Error: {error}")

        # Run both Deepgram listener and Plivo handler concurrently
        deepgram_task = asyncio.create_task(connect_and_listen_deepgram())
        plivo_task = asyncio.create_task(plivo_handler.start())
        await asyncio.gather(deepgram_task, plivo_task)

    except Exception as e:
        logger.error(f"Error: {e}")
        return {"message": "Error occurred"}


# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
