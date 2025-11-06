import asyncio
import base64
import json
from fastapi import FastAPI, Response, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from agents.realtime import RealtimeAgent, RealtimeRunner
from plivo_streaming import (
    PlivoFastAPIStreamingHandler,
    StartEvent,
    MediaEvent,
)
import logging
from plivo.xml.streamElement import StreamElement
from dotenv import load_dotenv

load_dotenv()
from plivo import plivoxml

logging.basicConfig(
    level=logging.INFO,  # This is the key line
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def create_agent_session():
    """Create and initialize a new agent session"""
    agent = RealtimeAgent(
        name="Assistant",
        instructions="You are a helpful voice assistant. Keep your responses conversational and friendly.",
    )
    runner = RealtimeRunner(
        starting_agent=agent,
        config={
            "model_settings": {
                "model_name": "gpt-realtime",
                "voice": "ash",
                "modalities": ["audio"],
                "input_audio_format": "g711_ulaw",
                "output_audio_format": "g711_ulaw",
                "input_audio_transcription": {"model": "gpt-4o-mini-transcribe"},
                "turn_detection": {"type": "semantic_vad", "interrupt_response": True},
            }
        },
    )
    session = await runner.run()
    return session


@app.get("/")
async def root():
    return {"message": "Plivo + OpenAI Realtime API"}


@app.get("/stream")
async def stream(request: Request):
    # Try to get the original host from X-Forwarded-Host if present, else fallback to Host
    forwarded_host = request.headers.get("x-forwarded-host")
    host = forwarded_host or request.headers.get("host")
    xml = plivoxml.ResponseElement()
    xml.add_speak("Hello, world!")
    xml.add(
        StreamElement(
            bidirectional=True,
            keepCallAlive=True,
            contentType="audio/x-mulaw;rate=8000",
            content=f"ws://{host}/stream",
            # extraHeaders are comma separated key=value pairs
            extraHeaders="apikey=123456,x-plivo-signature-v3=123456",
        )
    )
    return Response(content=xml.to_string(), media_type="application/xml")


@app.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for Plivo streaming with OpenAI Realtime API"""
    try:

        # Create Plivo handler
        handler = PlivoFastAPIStreamingHandler(websocket)

        # Create agent session when connection starts (but before accepting websocket)
        logger.info("Initializing OpenAI session...")
        session = await create_agent_session()
        await session.enter()
        logger.info("OpenAI session ready")

        @handler.on_connected
        async def on_connect():
            logger.info("Plivo connected")

        @handler.on_disconnected
        async def on_disconnect():
            logger.info("Plivo disconnected")
            await session.close()
            logger.info("Cleaning up connection...")
            # Session cleanup handled by context manager

        @handler.on_start
        async def on_start(data: StartEvent):
            logger.info(f"▶️  Stream started - Call ID: {handler.get_call_id()}")

        @handler.on_media
        async def on_media(data: MediaEvent):
            """Receive audio from Plivo (mulaw) and send to OpenAI (pcm16)"""
            try:
                audio_from_plivo = base64.b64decode(data.media.payload)
                await session.send_audio(audio_from_plivo)
            except Exception as e:
                import traceback

                logger.error(f"Error processing inbound audio: {e}")
                traceback.print_exc()

        @handler.on_error
        async def on_error(error):
            logger.error(f"Plivo error: {error}")

        # Create task to handle OpenAI events
        async def handle_openai_events():
            try:
                # async with session:
                async for event in session:
                    try:
                        if event.type == "agent_start":
                            logger.info(f"Agent started: {event.agent.name}")
                            # session_ready.set()  # Mark session as ready
                        elif event.type == "audio":
                            audio_from_openai = event.audio.data
                            await handler.send_media(
                                media_data=audio_from_openai,
                                content_type="audio/x-mulaw",
                                sample_rate=8000,
                            )
                        elif event.type == "audio_interrupted":
                            logger.info("Audio interrupted")
                            await handler.send_clear_audio()
                        elif event.type == "error":
                            logger.error(f"OpenAI error: {event.error}")
                        elif event.type in ["history_updated", "history_added"]:
                            pass  # Skip frequent events
                        elif event.type == "raw_model_event":
                            pass
                        else:
                            logger.warning(f"Unknown OpenAI event: {event.type}")
                    except Exception as e:
                        logger.error(
                            f"Error processing OpenAI event: {_truncate_str(str(e), 200)}"
                        )
            except Exception as e:
                logger.error(f"OpenAI session error: {e}")

        # Run both Plivo and OpenAI handlers concurrently
        await asyncio.gather(handler.start(auth_token='YjYyMjI0YjgzNmVmZGMwOGZjNDQ2OTE0NjMwNDI0'), handle_openai_events())
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await session.close()
        logger.info("Cleaning up connection...")


def _truncate_str(s: str, max_length: int) -> str:
    if len(s) > max_length:
        return s[:max_length] + "..."
    return s


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
