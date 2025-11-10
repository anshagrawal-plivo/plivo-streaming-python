FROM python:3.11-slim

WORKDIR /app

# Install uv for faster package management
RUN pip install uv

# Copy the root plivo-streaming-python package first (workspace dependency)
COPY plivo_streaming /app/plivo_streaming
COPY pyproject.toml /app/pyproject.toml
COPY README.md /app/README.md

# Copy the example application
COPY examples/full_example /app/examples/full_example

WORKDIR /app/examples/full_example

# Install dependencies
RUN uv pip install --system -r pyproject.toml

# Expose the FastAPI port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "main.py"]

