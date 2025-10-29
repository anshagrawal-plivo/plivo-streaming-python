"""Example FastAPI application using Plivo Streaming SDK"""

import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from plivo_streaming import (
    FastAPIStreamingHandler,
    StartEvent,
    MediaEvent,
    DtmfEvent,
    PlayedStreamEvent,
    ClearedAudioEvent,
    StreamEvent,
)

app = FastAPI()

# Add CORS middleware for ngrok
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for Plivo streaming"""
    
    # print(f"🔌 WebSocket connection attempt from: {websocket.client}")
    # print(f"📋 Headers: {dict(websocket.headers)}")
    
    # Create handler instance
    handler = FastAPIStreamingHandler(websocket)
    
    # Register event handlers
    @handler.on_connected
    async def on_connect():
        print("🟢 Client connected!")
    
    @handler.on_disconnected
    async def on_disconnect():
        print("🔴 Client disconnected!")
    
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
    
    # Start the handler (this will block until connection closes)
    await handler.start()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

