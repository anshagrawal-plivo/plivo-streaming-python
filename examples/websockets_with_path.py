"""Example WebSocket server with path routing (like /stream endpoint)"""

import asyncio
import websockets
from websockets.server import ServerConnection
from plivo_streaming import (
    WebSocketStreamingHandler,
    StartEvent,
    MediaEvent,
    DtmfEvent,
    PlayedStreamEvent,
    ClearedAudioEvent,
    StreamEvent,
)


async def handle_stream(websocket: ServerConnection):
    """Handle /stream endpoint"""

    handler = WebSocketStreamingHandler()

    @handler.on_connected
    async def on_connect():
        print(f"🟢 Stream connected: {websocket.remote_address}")

    @handler.on_disconnected
    async def on_disconnect():
        print(f"🔴 Stream disconnected: {websocket.remote_address}")

    @handler.on_start
    async def on_start(data: StartEvent):
        """Handle stream start event"""
        print(f"▶️  Stream started!")
        print(f"   Stream ID: {handler.get_stream_id()}")
        print(f"   Call ID: {handler.get_call_id()}")
        print(f"   Account ID: {handler.get_account_id()}")

    @handler.on_media
    async def on_media(data: MediaEvent):
        """Handle incoming media (audio) data"""
        # Clean Pydantic attribute access with full autocomplete!
        payload = data.media.payload
        print(f"📡 Received media chunk: {len(payload)} bytes")

        # Echo the media back
        if payload:
            await handler.send_media(payload)

    @handler.on_dtmf
    async def on_dtmf(data: DtmfEvent):
        """Handle DTMF tone detection"""
        digit = data.dtmf.digit
        print(f"📞 DTMF detected: {digit}")

    @handler.on_played_stream
    async def on_played_stream(data: PlayedStreamEvent):
        """Handle playedStream event (audio finished playing)"""
        print(f"✅ Audio finished playing: {data.name}")

    @handler.on_cleared_audio
    async def on_cleared_audio(data: ClearedAudioEvent):
        """Handle clearedAudio event (audio buffer cleared)"""
        print(f"🧹 Audio buffer cleared for stream: {data.streamId}")

    @handler.on_error
    async def on_error(error):
        """Handle errors"""
        print(f"❌ Error: {error}")

    await handler.handle(websocket)


async def router(websocket: ServerConnection):
    """Route requests based on path"""
    path = websocket.request.path if hasattr(websocket, 'request') else websocket.path

    print(f"📥 Connection to {path} from {websocket.remote_address}")

    if path == "/stream":
        await handle_stream(websocket)
    else:
        # Return 404-like message
        await websocket.send('{"error": "Not found"}')
        await websocket.close()


async def main():
    """Start the WebSocket server with routing"""
    host = "0.0.0.0"
    port = 8000

    print(f"🚀 Starting WebSocket server on ws://{host}:{port}")
    print(f"📍 Available endpoints:")
    print(f"   - ws://{host}:{port}/stream")

    async with websockets.serve(router, host, port):
        print("✅ Server running! Press Ctrl+C to stop.")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
