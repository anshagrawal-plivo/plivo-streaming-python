"""Plivo Streaming SDK for Python"""

__version__ = "0.1.0"

from plivo_streaming.base import BaseStreamingHandler
from plivo_streaming.fastapi import FastAPIStreamingHandler
from plivo_streaming.websockets import WebSocketStreamingHandler
from plivo_streaming.types import (
    EventType,
    StreamEvent,
    # Callback types
    EventCallback,
    StartCallback,
    MediaCallback,
    DtmfCallback,
    PlayedStreamCallback,
    ClearedAudioCallback,
    ErrorCallback,
    ConnectionCallback,
    # Incoming event types
    StartEvent,
    StartData,
    MediaEvent,
    MediaData,
    DtmfEvent,
    DtmfData,
    PlayedStreamEvent,
    ClearedAudioEvent,
    EndEvent,
    MediaFormat,
    # Outgoing event types
    PlayAudioEvent,
    PlayAudioMedia,
    CheckpointEvent,
    ClearAudioEvent,
)

__all__ = [
    # Handlers
    "BaseStreamingHandler",
    "FastAPIStreamingHandler",
    "WebSocketStreamingHandler",
    # Enums
    "EventType",
    # Base types
    "StreamEvent",
    # Callback types
    "EventCallback",
    "StartCallback",
    "MediaCallback",
    "DtmfCallback",
    "PlayedStreamCallback",
    "ClearedAudioCallback",
    "ErrorCallback",
    "ConnectionCallback",
    # Incoming event types
    "StartEvent",
    "StartData",
    "MediaEvent",
    "MediaData",
    "DtmfEvent",
    "DtmfData",
    "PlayedStreamEvent",
    "ClearedAudioEvent",
    "EndEvent",
    "MediaFormat",
    # Outgoing event types
    "PlayAudioEvent",
    "PlayAudioMedia",
    "CheckpointEvent",
    "ClearAudioEvent",
]

