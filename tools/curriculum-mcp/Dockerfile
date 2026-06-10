FROM python:3.12-slim

WORKDIR /app

# Install only the MCP SDK; the curriculum parser is pure stdlib.
COPY server/requirements.txt ./server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt

# Copy the server, the bundled curriculum snapshot, and the tests.
COPY . .

# The bundled snapshot is the default source; override with CURRICULUM_DIR (e.g. a mounted
# full plaintext/tracks checkout) if you want to tutor over the whole, latest curriculum.
ENV CURRICULUM_DIR=/app/data/tracks

# MCP clients launch the server over stdio; this is the command they invoke.
CMD ["python3", "server/server.py"]
