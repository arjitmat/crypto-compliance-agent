"""Builds a FAISS index from all JSON knowledge files."""

import json
import os
import pickle
from dataclasses import dataclass, field
from pathlib import Path

import faiss
import numpy as np

from src.rag.embedder import Embedder

INDEX_DIR = "/tmp/compliance_index"
INDEX_FILE = os.path.join(INDEX_DIR, "faiss.index")
META_FILE = os.path.join(INDEX_DIR, "metadata.pkl")


@dataclass
class Document:
    """A single indexed document with metadata."""

    id: str
    text: str
    metadata: dict
    source_file: str
    category: str
    jurisdiction: str
    score: float = 0.0
    tags: list[str] = field(default_factory=list)


def _extract_document(entry: dict, source_file: str) -> Document | None:
    """Extract a Document from a JSON entry, handling different schemas."""

    # Determine the document id
    doc_id = (
        entry.get("id")
        or entry.get("case_id")
        or entry.get("precedent_id")
        or entry.get("step_id")
        or ""
    )

    # Build the text for embedding from available fields
    parts = []
    for title_field in ("title", "case_name", "citation"):
        if title_field in entry:
            parts.append(str(entry[title_field]))
            break

    for content_field in ("content", "holding", "description", "outcome", "key_lesson"):
        if content_field in entry:
            parts.append(str(entry[content_field]))

    if not parts:
        return None

    text = ". ".join(parts)

    # Determine category from source path or entry fields
    category = entry.get("category", "")
    if not category:
        lower_path = source_file.lower()
        if "enforcement" in lower_path:
            category = "enforcement"
        elif "precedent" in lower_path:
            category = "precedent"
        elif "sop" in lower_path:
            category = "sop"
        elif "regulation" in lower_path:
            category = "regulation"

    # Determine jurisdiction
    jurisdiction = entry.get("jurisdiction", "")

    # Collect tags
    tags = entry.get("tags", [])

    # Store full entry as metadata (minus the heavy text fields to save memory)
    metadata = {k: v for k, v in entry.items() if k not in ("content", "description", "holding")}

    return Document(
        id=doc_id,
        text=text,
        metadata=metadata,
        source_file=source_file,
        category=category,
        jurisdiction=jurisdiction,
        tags=tags,
    )


class IndexBuilder:
    """Loads JSON knowledge files, embeds them, and builds a FAISS index."""

    def __init__(self, knowledge_dir: str):
        self.knowledge_dir = Path(knowledge_dir)
        self.embedder = Embedder()
        self.documents: list[Document] = []

    def _load_json_files(self) -> list[Document]:
        """Recursively load all JSON files from the knowledge directory."""
        documents = []
        json_files = sorted(self.knowledge_dir.rglob("*.json"))
        print(f"[IndexBuilder] Found {len(json_files)} JSON files in {self.knowledge_dir}")

        for json_path in json_files:
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                print(f"[IndexBuilder] Skipping {json_path}: {e}")
                continue

            # Handle both array and single-object JSON
            entries = data if isinstance(data, list) else [data]
            source = str(json_path.relative_to(self.knowledge_dir))

            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                doc = _extract_document(entry, source)
                if doc is not None:
                    documents.append(doc)

        print(f"[IndexBuilder] Loaded {len(documents)} documents from JSON files")
        return documents

    def build(self) -> tuple[faiss.IndexFlatIP, list[Document]]:
        """Load documents, embed, and build the FAISS index."""
        self.documents = self._load_json_files()

        if not self.documents:
            raise ValueError("No documents found to index")

        # Embed all document texts
        texts = [doc.text for doc in self.documents]
        print(f"[IndexBuilder] Embedding {len(texts)} documents ...")
        embeddings = self.embedder.embed(texts)
        print(f"[IndexBuilder] Embeddings shape: {embeddings.shape}")

        # Build FAISS inner-product index (cosine similarity on normalized vecs)
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings)
        print(f"[IndexBuilder] FAISS index built with {index.ntotal} vectors")

        # Save to disk
        self._save(index, self.documents)

        return index, self.documents

    def _save(self, index: faiss.IndexFlatIP, documents: list[Document]):
        """Save the FAISS index and document metadata to disk."""
        os.makedirs(INDEX_DIR, exist_ok=True)
        faiss.write_index(index, INDEX_FILE)

        with open(META_FILE, "wb") as f:
            pickle.dump(documents, f)

        print(f"[IndexBuilder] Saved index ({index.ntotal} vectors) and metadata to {INDEX_DIR}")

    @classmethod
    def load_or_build(cls, knowledge_dir: str) -> tuple[faiss.IndexFlatIP, list[Document]]:
        """Load existing index from disk, or build from scratch if not found."""
        if os.path.exists(INDEX_FILE) and os.path.exists(META_FILE):
            print(f"[IndexBuilder] Loading existing index from {INDEX_DIR} ...")
            index = faiss.read_index(INDEX_FILE)

            with open(META_FILE, "rb") as f:
                documents = pickle.load(f)

            print(f"[IndexBuilder] Loaded index with {index.ntotal} vectors, {len(documents)} documents")
            return index, documents

        print("[IndexBuilder] No existing index found, building from scratch ...")
        builder = cls(knowledge_dir)
        return builder.build()
