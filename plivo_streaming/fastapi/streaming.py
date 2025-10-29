"""FastAPI WebSocket streaming handler for Plivo"""

from fastapi import WebSocket, WebSocketDisconnect
from plivo_streaming.base import BaseStreamingHandler


class PlivoFastAPIStreamingHandler(BaseStreamingHandler):
    """
    FastAPI WebSocket handler for Plivo streaming.
    
    Usage:
        handler = PlivoFastAPIStreamingHandler(websocket)
        
        @handler.on_connected
        async def handle_connect():
            print("Client connected")
        
        @handler.on_media
        async def handle_media(data):
            print(f"Received media: {data}")
        
        await handler.start()
    """
    
    def __init__(self, websocket: WebSocket):
        super().__init__()
        self.websocket = websocket
    
    async def _send_raw(self, data: str):
        """Send raw string data through FastAPI WebSocket"""
        await self.websocket.send_text(data)
    
    async def start(self):
        """
        Start the WebSocket listener loop.
        This should be awaited in your FastAPI WebSocket endpoint.
        """
        self._running = True
        
        try:
            # Accept the WebSocket connection
            await self.websocket.accept()
            await self._trigger_connection_callbacks()
            
            # Listen for messages
            while self._running:
                try:
                    message = await self.websocket.receive_text()
                    await self._process_message(message)
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    await self._trigger_error_callbacks(e)
                    
        except Exception as e:
            await self._trigger_error_callbacks(e)
        finally:
            self._running = False
            await self._trigger_disconnection_callbacks()
    
    async def stop(self):
        """Stop the WebSocket listener"""
        self._running = False
        try:
            await self.websocket.close()
        except:
            pass

