"""Example plain WebSocket application using Plivo Streaming SDK"""

import asyncio
import websockets
from plivo_streaming import (
    PlivoWebsocketStreamingHandler,
    StartEvent,
    MediaEvent,
    DtmfEvent,
    PlayedStreamEvent,
    ClearedAudioEvent,
    StreamEvent,
)
import logging

logging.basicConfig(
    level=logging.INFO,  # This is the key line
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def create_handler(websocket):
    """Create and configure handler for each connection"""

    handler = PlivoWebsocketStreamingHandler()

    # Register event handlers
    @handler.on_connected
    async def on_connect():
        logger.info(f"🟢 Client connected: {websocket.remote_address}")

    @handler.on_disconnected
    async def on_disconnect():
        logger.info(f"🔴 Client disconnected: {websocket.remote_address}")

    @handler.on_start
    async def on_start(data: StartEvent):
        """Handle stream start event"""
        logger.info(f"▶️  Stream started!")
        logger.info(f"   Stream ID: {handler.get_stream_id()}")
        logger.info(f"   Call ID: {handler.get_call_id()}")
        logger.info(f"   Account ID: {handler.get_account_id()}")

    @handler.on_media
    async def on_media(data: MediaEvent):
        """Handle incoming media (audio) data"""
        # Clean Pydantic attribute access with full autocomplete!
        payload = data.media.payload
        logger.info(f"📡 Received media chunk: {len(payload)} bytes")

        # Echo the media back
        if payload:
            await handler.send_media(payload)

    @handler.on_dtmf
    async def on_dtmf(data: DtmfEvent):
        """Handle DTMF tone detection"""
        digit = data.dtmf.digit
        logger.info(f"📞 DTMF detected: {digit}")

    @handler.on_played_stream
    async def on_played_stream(data: PlayedStreamEvent):
        """Handle playedStream event (audio finished playing)"""
        logger.info(f"✅ Audio finished playing: {data.name}")

    @handler.on_cleared_audio
    async def on_cleared_audio(data: ClearedAudioEvent):
        """Handle clearedAudio event (audio buffer cleared)"""
        logger.info(f"🧹 Audio buffer cleared for stream: {data.stream_id}")

    @handler.on_error
    async def on_error(error):
        """Handle errors"""
        logger.error(f"❌ Error: {error}")

    # Handle the connection
    await handler.handle(websocket)


async def main():
    """Start the WebSocket server"""
    logger.info("🚀 Starting WebSocket server on ws://0.0.0.0:8000")

    async with websockets.serve(create_handler, "0.0.0.0", 8000):
        logger.info("✅ Server running! Press Ctrl+C to stop.")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Server stopped")