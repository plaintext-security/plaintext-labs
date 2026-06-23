#!/usr/bin/env python3
"""
SOC Copilot — combines RAG (ChromaDB) and MCP tools (threat intel, alerts, incidents)
to answer analyst questions with full evidence traceability.

Usage:
    python3 copilot/copilot.py "Is 185.220.101.42 malicious?"
    python3 copilot/copilot.py "What containment steps should I follow for a ransomware event?"
"""

import json
import os
import re
import sys

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://ollama:11434")
CHROMA_HOST = os.environ.get("CHROMA_HOST", "http://chromadb:8000")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "tinyllama")
EMBED_MODEL = "nomic-embed-text"
COLLECTION_NAME = "soc-kb"
N_RETRIEVE = 3
DATA_DIR = os.environ.get("DATA_DIR", "/lab/data")


def install_deps():
    import subprocess
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "requests", "chromadb==0.5.23"],
        check=True,
    )


try:
    import requests
    import chromadb
except ImportError:
    install_deps()
    import requests
    import chromadb


# ── Tool implementations (inlined from module 05 for self-contained copilot) ──

import re as _re
import json as _json
from pathlib import Path

_DATA = Path(DATA_DIR)
_IOC_PATTERN = _re.compile(r'^[a-zA-Z0-9./:\-_@]{1,255}$')


def _load_json(filename):
    with open(_DATA / filename) as f:
        return _json.load(f)


def tool_get_threat_intel(ioc: str) -> dict:
    if not _IOC_PATTERN.match(ioc):
        return {"error": f"Invalid IOC: {ioc[:40]}"}
    intel = _load_json("threat-intel.json")
    for bucket in ("ips", "domains", "hashes"):
        if ioc in intel.get(bucket, {}):
            r = intel[bucket][ioc]
            return {"found": True, "ioc": ioc, "classification": r["classification"],
                    "category": r["category"], "confidence": r["confidence"]}
    return {"found": False, "ioc": ioc}


def tool_search_alerts(query: str) -> dict:
    if not query.strip():
        return {"error": "Empty query"}
    alerts = _load_json("alerts.json")
    q = query.lower()
    matches = [a for a in alerts if q in json.dumps(a).lower()][:5]
    return {"count": len(matches), "alerts": [
        {"id": a["id"], "severity": a["severity"], "title": a["title"],
         "host": a["host"], "status": a["status"]} for a in matches
    ]}


def tool_summarize_incident(id: str) -> dict:
    if not _re.match(r'^INC-\d{4}-\d{4}$', id):
        return {"error": f"Invalid ID: {id}"}
    incidents = _load_json("incidents.json")
    for inc in incidents:
        if inc["id"] == id:
            return {"found": True, **inc}
    return {"found": False, "id": id}


# ── RAG retrieval ──

def embed(text: str) -> list:
    r = requests.post(f"{OLLAMA_HOST}/api/embeddings",
                      json={"model": EMBED_MODEL, "prompt": text}, timeout=60)
    r.raise_for_status()
    return r.json()["embedding"]


def retrieve_context(question: str) -> list[dict]:
    try:
        chroma = chromadb.HttpClient(
            host=CHROMA_HOST.replace("http://", "").split(":")[0],
            port=int(CHROMA_HOST.split(":")[-1]),
        )
        col = chroma.get_collection(COLLECTION_NAME)
        q_emb = embed(question)
        results = col.query(query_embeddings=[q_emb], n_results=N_RETRIEVE,
                            include=["documents", "metadatas", "distances"])
        return [{"text": doc, "source": meta["source"], "distance": dist}
                for doc, meta, dist in zip(results["documents"][0],
                                           results["metadatas"][0],
                                           results["distances"][0])]
    except Exception as e:
        return [{"text": f"(RAG unavailable: {e})", "source": "error", "distance": 0}]


# ── Tool dispatch heuristics ──

IP_RE = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
DOMAIN_RE = re.compile(r'\b[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z]{2,})+\b')
HASH_RE = re.compile(r'\b[a-fA-F0-9]{32,64}\b')
INC_RE = re.compile(r'\bINC-\d{4}-\d{4}\b')


def decide_tools(question: str) -> list[tuple[str, dict]]:
    """Heuristically decide which tools to call based on the question content."""
    calls = []

    # Threat intel for IPs, domains, and hashes
    for ip in IP_RE.findall(question):
        if not ip.startswith("10.") and not ip.startswith("192.168."):
            calls.append(("get_threat_intel", {"ioc": ip}))
    for domain in DOMAIN_RE.findall(question):
        if "." in domain and not domain.endswith(".example"):
            calls.append(("get_threat_intel", {"ioc": domain}))
    for h in HASH_RE.findall(question):
        calls.append(("get_threat_intel", {"ioc": h}))

    # Incident lookup
    for inc_id in INC_RE.findall(question):
        calls.append(("summarize_incident", {"id": inc_id}))

    # Alert search for hostnames or keywords
    alert_keywords = ["alert", "host", "HOST-", "incident", "open"]
    if any(kw.lower() in question.lower() for kw in alert_keywords):
        # Extract a search term
        match = re.search(r'HOST-\w+-\d+', question)
        if match:
            calls.append(("search_alerts", {"query": match.group()}))

    return calls[:3]  # cap at 3 tool calls


def run_tools(calls: list[tuple[str, dict]]) -> list[dict]:
    results = []
    for name, args in calls:
        if name == "get_threat_intel":
            result = tool_get_threat_intel(**args)
        elif name == "search_alerts":
            result = tool_search_alerts(**args)
        elif name == "summarize_incident":
            result = tool_summarize_incident(**args)
        else:
            result = {"error": f"Unknown tool: {name}"}
        results.append({"tool": name, "args": args, "result": result})
    return results


# ── Generation ──

SYSTEM_PROMPT = """You are a security operations assistant for the corporate SOC.
Answer questions using ONLY the evidence provided in the CONTEXT and TOOL RESULTS sections below.
- For every factual claim, cite its source: [RAG: filename] or [TOOL: tool_name].
- If the evidence does not support a claim, say "The available data does not cover this."
- Do not fabricate CVE IDs, IP addresses, hash values, or policy details.
- Be concise: 3–5 sentences unless a longer structured answer is clearly needed."""


def generate(question: str, context: list[dict], tool_results: list[dict]) -> str:
    context_text = "\n\n".join(
        f"[RAG: {c['source']}]\n{c['text'][:400]}" for c in context
    ) or "(No RAG context retrieved)"

    tool_text = "\n\n".join(
        f"[TOOL: {t['tool']}({json.dumps(t['args'])})]\n{json.dumps(t['result'], indent=2)[:400]}"
        for t in tool_results
    ) or "(No tool calls made)"

    prompt = f"""{SYSTEM_PROMPT}

CONTEXT (from the SOC knowledge base):
{context_text}

TOOL RESULTS:
{tool_text}

QUESTION:
{question}

ANSWER:"""

    r = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=180,
    )
    r.raise_for_status()
    return r.json().get("response", "").strip()


# ── Main ──

def answer(question: str, verbose: bool = True) -> dict:
    if verbose:
        print(f"QUESTION: {question}\n")
        print("1. Retrieving context from knowledge base...")

    context = retrieve_context(question)

    if verbose:
        for c in context:
            print(f"  [RAG: {c['source']} | distance: {c['distance']:.4f}]")
            print(f"  {c['text'][:120]}...")
        print()

    tool_calls = decide_tools(question)
    if verbose:
        print(f"2. Calling {len(tool_calls)} tool(s)...")

    tool_results = run_tools(tool_calls)

    if verbose:
        for t in tool_results:
            print(f"  [TOOL: {t['tool']}({t['args']})]")
            print(f"  {json.dumps(t['result'])[:120]}...")
        print()
        print("3. Generating answer...")

    answer_text = generate(question, context, tool_results)

    if verbose:
        print("\n--- ANSWER ---")
        print(answer_text)
        print()
        print("Review: every factual claim should cite [RAG: source] or [TOOL: name].")

    return {
        "question": question,
        "context_sources": [c["source"] for c in context],
        "tools_called": [t["tool"] for t in tool_results],
        "answer": answer_text,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 copilot/copilot.py 'your question here'")
        sys.exit(1)
    question = " ".join(sys.argv[1:])
    answer(question, verbose=True)
