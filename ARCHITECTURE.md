# Architecture

## Code Organization

The SDK uses a base class pattern to minimize code duplication and make it easy to add new WebSocket framework implementations.

### Structure

```
plivo_streaming/
├── base.py              # BaseStreamingHandler - all shared logic (~300 lines)
├── fastapi/
│   └── streaming.py     # PlivoFastAPIStreamingHandler (~68 lines)
└── websockets/
    └── streaming.py     # WebSocketStreamingHandler (~72 lines)
```

### Benefits

1. **Minimal Duplication**: ~256 lines of code eliminated (700 → 444 lines)
2. **Consistency**: All handlers share identical behavior for events, callbacks, and message processing
3. **Extensibility**: Adding new frameworks requires only ~50-100 lines

## Adding a New Framework

To add support for a new WebSocket framework (e.g., Socket.IO, Tornado, etc.), you only need to:

1. Create a new handler class that inherits from `BaseStreamingHandler`
2. Implement the `_send_raw(data: str)` method
3. Add a connection handler method that calls `_process_message()` for incoming messages

### Example: Socket.IO Handler

```python
from plivo_streaming.base import BaseStreamingHandler
import socketio

class SocketIOStreamingHandler(BaseStreamingHandler):
    def __init__(self):
        super().__init__()
        self.sio = None
        self.sid = None
    
    async def _send_raw(self, data: str):
        """Send raw string data through Socket.IO"""
        if not self.sio or not self.sid:
            raise RuntimeError("Socket.IO not connected")
        await self.sio.emit('message', data, room=self.sid)
    
    async def handle(self, sid, environ):
        """Handle a Socket.IO connection"""
        self.sid = sid
        self._running = True
        await self._trigger_connection_callbacks()
        # Socket.IO event handlers would call _process_message()
```

### Example: Tornado Handler

```python
from plivo_streaming.base import BaseStreamingHandler
from tornado.websocket import WebSocketHandler

class TornadoStreamingHandler(BaseStreamingHandler, WebSocketHandler):
    def __init__(self, *args, **kwargs):
        WebSocketHandler.__init__(self, *args, **kwargs)
        BaseStreamingHandler.__init__(self)
    
    async def _send_raw(self, data: str):
        """Send raw string data through Tornado WebSocket"""
        self.write_message(data)
    
    async def open(self):
        await self._trigger_connection_callbacks()
    
    async def on_message(self, message):
        await self._process_message(message)
    
    async def on_close(self):
        self._running = False
        await self._trigger_disconnection_callbacks()
```

## Base Handler Features

All handlers automatically get:

- Event callbacks: `on_start`, `on_media`, `on_dtmf`, `on_played_stream`, `on_cleared_audio`, `on_end`
- Connection lifecycle: `on_connected`, `on_disconnected`, `on_error`
- Send methods: `send_media()`, `send_checkpoint()`, `send_clear_audio()`, `send_json()`, `send_text()`
- Stream metadata: `get_stream_id()`, `get_call_id()`, `get_account_id()`
- Message processing: Automatic JSON parsing, event routing, and Pydantic validation

