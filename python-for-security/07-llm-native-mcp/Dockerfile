FROM python:3.12-slim

# The MCP SDK (FastMCP lives in `mcp.server.fastmcp`) + pydantic. instructor + the
# Anthropic SDK are NOT installed: the demo runs offline, so it shows the typed-output
# DISCIPLINE with pydantic directly (what instructor automates against a real model).
RUN pip install --no-cache-dir "mcp==1.*"

WORKDIR /lab
COPY . /lab

CMD ["sleep", "infinity"]
