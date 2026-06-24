#!/usr/bin/env python3
"""
ingest.py — Chunk and embed the LastPass-2022 post-mortem knowledge base into ChromaDB.

Usage:
    python3 scripts/ingest.py [--data-dir data/knowledge-base] [--chroma-host http://chromadb:8000]
"""

import argparse
import os
import sys

CHUNK_SIZE = 500       # characters per chunk
CHUNK_OVERLAP = 80     # character overlap between consecutive chunks
COLLECTION_NAME = "soc-kb"


def install_deps():
    import subprocess
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q",
         "chromadb==0.5.23", "requests"],
        check=True,
    )


try:
    import chromadb
    import requests
except ImportError:
    install_deps()
    import chromadb
    import requests


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into overlapping character-based chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end].strip())
        if end == len(text):
            break
        start += chunk_size - overlap
    return [c for c in chunks if c]  # remove empties


def embed_text(texts: list[str], ollama_host: str, model: str = "nomic-embed-text") -> list[list[float]]:
    """Embed a list of texts using Ollama's embedding API."""
    embeddings = []
    for text in texts:
        resp = requests.post(
            f"{ollama_host}/api/embeddings",
            json={"model": model, "prompt": text},
            timeout=60,
        )
        resp.raise_for_status()
        embeddings.append(resp.json()["embedding"])
    return embeddings


def main():
    parser = argparse.ArgumentParser(description="Ingest knowledge base into ChromaDB")
    parser.add_argument("--data-dir", default="data/knowledge-base")
    parser.add_argument("--chroma-host", default=os.environ.get("CHROMA_HOST", "http://chromadb:8000"))
    parser.add_argument("--ollama-host", default=os.environ.get("OLLAMA_HOST", "http://ollama:11434"))
    parser.add_argument("--embed-model", default="nomic-embed-text")
    args = parser.parse_args()

    chroma = chromadb.HttpClient(
        host=args.chroma_host.replace("http://", "").split(":")[0],
        port=int(args.chroma_host.split(":")[-1]),
    )
    collection = chroma.get_or_create_collection(COLLECTION_NAME)

    # Get existing document IDs to support incremental ingestion
    existing = set()
    existing_ids = collection.get(include=[])["ids"]
    for doc_id in existing_ids:
        # IDs are formatted as "<filename>_chunk_<n>" — extract filename
        filename = "_chunk_".join(doc_id.split("_chunk_")[:-1])
        existing.add(filename)

    md_files = sorted(
        f for f in os.listdir(args.data_dir) if f.endswith(".md")
    )
    if not md_files:
        print(f"No .md files found in {args.data_dir}")
        sys.exit(1)

    total_chunks = 0
    for filename in md_files:
        filepath = os.path.join(args.data_dir, filename)
        base = os.path.splitext(filename)[0]

        if base in existing:
            print(f"  SKIP {filename} (already in collection)")
            continue

        with open(filepath, encoding="utf-8") as f:
            text = f.read()

        chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
        print(f"  Embedding {filename}: {len(chunks)} chunks...", flush=True)

        embeddings = embed_text(chunks, args.ollama_host, args.embed_model)

        ids = [f"{base}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"source": filename, "chunk": i} for i in range(len(chunks))]

        collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
        total_chunks += len(chunks)
        print(f"    Added {len(chunks)} chunks.")

    print(f"\nIngestion complete. Total new chunks: {total_chunks}")
    print(f"Collection '{COLLECTION_NAME}' now has {collection.count()} chunks.")


if __name__ == "__main__":
    main()
