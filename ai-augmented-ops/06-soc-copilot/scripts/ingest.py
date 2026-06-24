#!/usr/bin/env python3
"""Ingest the SOC knowledge base into ChromaDB for the SoC Copilot."""
import os
import sys

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://ollama:11434")
CHROMA_HOST = os.environ.get("CHROMA_HOST", "http://chromadb:8000")
COLLECTION_NAME = "soc-kb"
CHUNK_SIZE = 500
OVERLAP = 80

try:
    import requests
    import chromadb
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "requests", "chromadb==0.5.23"], check=True)
    import requests
    import chromadb

from pathlib import Path


def embed(text: str) -> list:
    r = requests.post(f"{OLLAMA_HOST}/api/embeddings",
                      json={"model": "nomic-embed-text", "prompt": text}, timeout=60)
    r.raise_for_status()
    return r.json()["embedding"]


def main():
    chroma = chromadb.HttpClient(
        host=CHROMA_HOST.replace("http://", "").split(":")[0],
        port=int(CHROMA_HOST.split(":")[-1]),
    )
    col = chroma.get_or_create_collection(COLLECTION_NAME)

    kb_dir = Path("/lab/data/knowledge-base")
    total = 0
    for f in sorted(kb_dir.glob("*.md")):
        text = f.read_text()
        chunks = [text[i:i+CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE - OVERLAP)]
        ids = [f"{f.stem}_chunk_{i}" for i in range(len(chunks))]

        # Skip if already ingested
        existing = col.get(include=[], ids=[ids[0]])["ids"]
        if existing:
            print(f"SKIP {f.name} (already ingested)")
            continue

        embeds = [embed(c) for c in chunks]
        col.add(ids=ids, embeddings=embeds, documents=chunks,
                metadatas=[{"source": f.name, "chunk": i} for i in range(len(chunks))])
        print(f"Ingested {f.name}: {len(chunks)} chunks")
        total += len(chunks)

    print(f"Done. New chunks: {total}. Collection size: {col.count()}")


if __name__ == "__main__":
    main()
