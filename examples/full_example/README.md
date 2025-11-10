# Full Voice AI Pipeline Example

Complete real-time voice AI implementation using Plivo streaming with Deepgram, OpenAI, and ElevenLabs.

## Flow

```
Plivo Audio Stream (incoming)
    ↓
Deepgram STT (speech → text)
    ↓
OpenAI API (text completion)
    ↓
ElevenLabs TTS (text → speech)
    ↓
Plivo Audio Stream (outgoing)
```

## Setup

1. Navigate to the example directory:
```bash
cd examples/full_example
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
uv pip install -e .
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. Run the server:
```bash
python main.py
```

Server starts on `http://0.0.0.0:8000` with WebSocket endpoint at `ws://0.0.0.0:8000/stream`

## Run with Docker

1. Create a `.env` file with your API keys and configuration (see `.env.example` for required variables)

2. Build and run with docker-compose from the repo root:
```bash
cd /path/to/plivo-streaming-python
docker-compose -f examples/full_example/docker-compose.yml up --build
```

The server will be available on `http://localhost:8000`

## Usage

Configure your Plivo phone number to stream audio to your server's WebSocket endpoint. When a call comes in:

1. Audio chunks arrive via Plivo streaming
2. Deepgram transcribes in real-time
3. OpenAI generates conversational responses
4. ElevenLabs synthesizes natural-sounding speech
5. Audio plays back to the caller through Plivo

## Requirements

- Python ≥ 3.9
- Active API keys for Deepgram, OpenAI, and ElevenLabs
- Plivo account with streaming enabled
- Public endpoint (use ngrok for local development)

