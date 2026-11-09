"""
Wraps a local, on-disk Chroma collection per repository so the docs of
whichever repo the user connects get embedded and searched dynamically.

Uses Chroma's bundled default embedding function (a small local
sentence-transformer, downloaded once and cached) so no paid embedding API
is required.
"""
import re
from typing import List

import chromadb

from config import get_settings

settings = get_settings()

_client = chromadb.PersistentClient(path=settings.chroma_dir)


def _collection_name(full_name: str) -> str:
    # Chroma collection names must be simple; sanitize "owner/repo" -> "owner__repo"
    return re.sub(r"[^a-zA-Z0-9_-]", "_", full_name)[:63]


def _chunk(text: str, max_chars: int = 1200) -> List[str]:
    """Splits a doc into rough paragraph-based chunks for embedding."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, current = [], ""
    for p in paragraphs:
        if len(current) + len(p) < max_chars:
            current += ("\n\n" if current else "") + p
        else:
            if current:
                chunks.append(current)
            current = p
    if current:
        chunks.append(current)
    return chunks or [text]


def index_repo_docs(full_name: str, docs: dict) -> None:
    """docs: {path: content}. Fully replaces the collection for this repo."""
    name = _collection_name(full_name)
    try:
        _client.delete_collection(name)
    except Exception:
        pass
    collection = _client.create_collection(name)

    ids, texts, metadatas = [], [], []
    for path, content in docs.items():
        for i, chunk in enumerate(_chunk(content)):
            ids.append(f"{path}::{i}")
            texts.append(chunk)
            metadatas.append({"path": path, "chunk_index": i})

    if texts:
        collection.add(ids=ids, documents=texts, metadatas=metadatas)


def search_docs(full_name: str, query: str, top_k: int = 5) -> List[dict]:
    name = _collection_name(full_name)
    try:
        collection = _client.get_collection(name)
    except Exception:
        return []

    results = collection.query(query_texts=[query], n_results=top_k)
    hits = []
    for doc, meta, dist in zip(
        results.get("documents", [[]])[0],
        results.get("metadatas", [[]])[0],
        results.get("distances", [[]])[0],
    ):
        hits.append({"path": meta["path"], "text": doc, "distance": dist})
    return hits
