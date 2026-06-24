#!/usr/bin/env python3
"""
query.py — Query the ChromaDB knowledge base and generate an answer via Ollama.

Usage:
    python3 scripts/query.py "How did the attacker access the cloud backup storage?"
    python3 scripts/query.py "Was customer vault data encrypted?"
"""

import os
import sys

COLLECTION_NAME = "soc-kb"
N_RESULTS = 4          # number of chunks to retrieve
EMBED_MODEL = "nomic-embed-text"
GEN_MODEL = os.environ.get("OLLAMA_MODEL", "tinyllama")


def install_deps():
    import subprocess
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "chromadb==0.5.23", "requests"],
        check=True,
    )


try:
    import chromadb
    import requests
except ImportError:
    install_deps()
    import chromadb
    import requests


def embed_query(query: str, ollama_host: str) -> list[float]:
    resp = requests.post(
        f"{ollama_host}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": query},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["embedding"]


def retrieve(query_embedding: list[float], chroma_host: str) -> list[dict]:
    chroma = chromadb.HttpClient(
        host=chroma_host.replace("http://", "").split(":")[0],
        port=int(chroma_host.split(":")[-1]),
    )
    col = chroma.get_collection(COLLECTION_NAME)
    results = col.query(
        query_embeddings=[query_embedding],
        n_results=N_RESULTS,
        include=["documents", "metadatas", "distances"],
    )
    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({"text": doc, "source": meta["source"], "distance": dist})
    return chunks


def generate(query: str, chunks: list[dict], ollama_host: str) -> str:
    context = "\n\n---\n\n".join(
        f"[Source: {c['source']}]\n{c['text']}" for c in chunks
    )
    prompt = f"""You are a security analyst assistant. Answer the following
question using ONLY the context provided below (a knowledge base of public post-mortem documents on
the LastPass 2022 breach). If the context does not contain enough information
to answer confidently, say "I don't have enough information in the knowledge base to answer this."
Do not make up facts.

CONTEXT:
{context}

QUESTION:
{query}

ANSWER:"""
    resp = requests.post(
        f"{ollama_host}/api/generate",
        json={"model": GEN_MODEL, "prompt": prompt, "stream": False},
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json().get("response", "").strip()


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/query.py 'your question here'")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    ollama_host = os.environ.get("OLLAMA_HOST", "http://ollama:11434")
    chroma_host = os.environ.get("CHROMA_HOST", "http://chromadb:8000")

    print(f"QUERY: {query}\n")
    print("1. Embedding query...")
    q_embedding = embed_query(query, ollama_host)

    print("2. Retrieving relevant chunks from ChromaDB...")
    chunks = retrieve(q_embedding, chroma_host)

    print("\n--- RETRIEVED CHUNKS ---")
    for i, c in enumerate(chunks, 1):
        print(f"\n[Chunk {i} | Source: {c['source']} | Distance: {c['distance']:.4f}]")
        print(c["text"][:300] + ("..." if len(c["text"]) > 300 else ""))

    print("\n3. Generating answer with Ollama...")
    answer = generate(query, chunks, ollama_host)

    print("\n--- GENERATED ANSWER ---")
    print(answer)
    print()
    print("Review: are all facts in the answer supported by the retrieved chunks above?")


if __name__ == "__main__":
    main()
