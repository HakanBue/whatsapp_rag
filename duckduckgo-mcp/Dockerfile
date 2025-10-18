FROM python:3.11-slim

WORKDIR /app

# Copy requirements (from repo root) so we can install the duckduckgo-mcp-server package
COPY ../requirements.txt /app/requirements.txt

# Install
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

# Start the DuckDuckGo MCP server
CMD ["duckduckgo-mcp-server"]

