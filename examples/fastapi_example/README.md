# FastAPI + Plivo Streaming + OpenAI Realtime Example

This example demonstrates how to run a FastAPI server that communicates with Plivo's Media Streaming API and OpenAI's Realtime API, enabling real-time voice interactions.

## Prerequisites

- Python 3.9+
- OpenAI API key

## Setup

### Option 1: Using uv (Recommended)

1. **Install uv** (if not already installed):

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Create a virtual environment** (if you want the project to be isolated):

   ```bash
   uv venv .venv
   ```

   Optionally, activate it:

   - On Linux/macOS:
     ```
     source .venv/bin/activate
     ```
   - On Windows:
     ```
     .venv\Scripts\activate
     ```

3. **Sync dependencies** (installs all required packages as specified in `pyproject.toml`):

   ```bash
   uv sync
   ```

4. **Set up your OpenAI API key:**

   Create a `.env` file in the example directory:

   ```
   OPENAI_API_KEY=sk-...
   ```

   (Replace `sk-...` with your actual OpenAI API key. This file is automatically loaded.)

---

## Running the Example

1. **Start the FastAPI server:**

   Using uv:
   ```bash
   cd examples/fastapi_example
   uv run main.py
   ```


   The server will start on `http://0.0.0.0:8000`.

2. **Configure Plivo Application:**

   - In your Plivo dashboard, create or edit an Application.
   - Set the **Answer URL** to your public server URL with `/stream` endpoint (e.g., using [ngrok](https://ngrok.com/) or deployment):

     ```
     https://<your-server>/stream
     ```

   - The `/stream` endpoint returns the necessary Plivo XML that initiates WebSocket streaming back to your server.

3. **Make a call to your Plivo number attached to this application**. When the call connects, Plivo will initiate the media WebSocket and the real-time agent will process the conversation.

## Example HTTP Endpoints

- `GET /` — Simple health check, returns a JSON message.
- `GET /stream` — Returns the Plivo XML instructing Plivo Media Streaming to establish a WebSocket to your server.
- `WS /stream` — WebSocket endpoint for Plivo Media Streaming.

## Notes

- To expose your local server for Plivo to reach, you can use [ngrok](https://ngrok.com/) or [localhost.run](https://localhost.run/):

  ```
  ngrok http 8000
  ```

- Logs are printed to the terminal for both Plivo and OpenAI session events.
- If you make changes to the code, restart the server.

## Troubleshooting

- Ensure your API keys are correct and active.
- Check that your server is reachable from the public internet (use ngrok for local dev).
- Use the Plivo and server logs to debug any connection issues.

## File Overview

- `main.py` — The FastAPI app and all streaming logic
- `README.md` — This file