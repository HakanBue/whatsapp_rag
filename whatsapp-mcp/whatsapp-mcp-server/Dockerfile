FROM python:3.11-slim

# install via uv
RUN pip install uvicorn

WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r <(uv pip compile pyproject.toml)

# Expose port
EXPOSE 8000

# Start the MCP server
CMD ["python", "main.py"]

