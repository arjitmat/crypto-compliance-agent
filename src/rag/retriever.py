"""Retriever for semantic search over the compliance knowledge base."""

import os

import faiss
import numpy as np

from src.rag.embedder import Embedder
from src.rag.index_builder import INDEX_DIR, INDEX_FILE, META_FILE, Document

# Jurisdiction name mappings for query expansion
JURISDICTION_KEYWORDS = {
    "EU": ["europe", "european", "mica", "eu", "eea", "euro"],
    "US": ["united states", "american", "sec", "us", "usa", "cftc", "fincen"],
    "UK": ["united kingdom", "british", "fca", "uk", "england", "britain"],
    "SG": ["singapore", "mas", "singaporean"],
    "AE": ["uae", "dubai", "vara", "abu dhabi", "adgm", "emirates", "emirati"],
}


class Retriever:
    """Semantic retrieval over the FAISS compliance index."""

    def __init__(self):
        self._index: faiss.IndexFlatIP | None = None
        self._documents: list[Document] | None = None
        self._embedder: Embedder | None = None

    def _load(self):
        """Load the FAISS index, metadata, and embedder."""
        if self._index is not None:
            return

        import pickle

        if not os.path.exists(INDEX_FILE) or not os.path.exists(META_FILE):
            raise FileNotFoundError(
                f"Index not found at {INDEX_DIR}. Run IndexBuilder.load_or_build() first."
            )

        print(f"[Retriever] Loading FAISS index from {INDEX_DIR} ...")
        self._index = faiss.read_index(INDEX_FILE)

        with open(META_FILE, "rb") as f:
            self._documents = pickle.load(f)

        self._embedder = Embedder()
        print(f"[Retriever] Ready. {self._index.ntotal} vectors, {len(self._documents)} documents.")

    def _expand_query(self, query: str) -> str:
        """Simple query expansion: append jurisdiction name if detected."""
        query_lower = query.lower()
        expansions = []

        for jurisdiction, keywords in JURISDICTION_KEYWORDS.items():
            for kw in keywords:
                if kw in query_lower:
                    # Add the full jurisdiction context
                    jurisdiction_names = {
                        "EU": "European Union MiCA regulation",
                        "US": "United States SEC federal securities",
                        "UK": "United Kingdom FCA financial conduct",
                        "SG": "Singapore MAS payment services",
                        "AE": "UAE Dubai VARA virtual assets",
                    }
                    expansion = jurisdiction_names.get(jurisdiction, "")
                    if expansion and expansion.lower() not in query_lower:
                        expansions.append(expansion)
                    break

        if expansions:
            return f"{query} {' '.join(expansions)}"
        return query

    def _detect_jurisdictions(self, query: str) -> list[str]:
        """Detect jurisdiction codes mentioned in the query."""
        query_lower = query.lower()
        detected = []
        for jurisdiction, keywords in JURISDICTION_KEYWORDS.items():
            for kw in keywords:
                if kw in query_lower:
                    detected.append(jurisdiction)
                    break
        return detected

    def retrieve(
        self,
        query: str,
        k: int = 8,
        jurisdiction_filter: list[str] | None = None,
    ) -> list[Document]:
        """Retrieve the top-k most relevant documents for a query.

        Args:
            query: Natural language query.
            k: Number of documents to return.
            jurisdiction_filter: If provided, only return documents matching
                these jurisdiction codes (e.g. ["US", "EU"]). Filters from
                top-20 candidates, returns best k that match.

        Returns:
            List of Document objects with .score populated.
        """
        self._load()

        expanded_query = self._expand_query(query)
        query_vec = self._embedder.embed_single(expanded_query)
        query_vec = query_vec.reshape(1, -1)

        # Retrieve more candidates if filtering
        search_k = max(k * 3, 20) if jurisdiction_filter else k

        scores, indices = self._index.search(query_vec, search_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue

            doc = self._documents[idx]

            # Apply jurisdiction filter
            if jurisdiction_filter:
                if doc.jurisdiction and doc.jurisdiction not in jurisdiction_filter:
                    continue

            # Create a copy with score
            result = Document(
                id=doc.id,
                text=doc.text,
                metadata=doc.metadata,
                source_file=doc.source_file,
                category=doc.category,
                jurisdiction=doc.jurisdiction,
                score=float(score),
                tags=doc.tags,
            )
            results.append(result)

            if len(results) >= k:
                break

        return results

    def retrieve_cases(self, query: str, k: int = 5) -> list[Document]:
        """Retrieve enforcement cases and precedents relevant to the query."""
        self._load()

        expanded_query = self._expand_query(query)
        query_vec = self._embedder.embed_single(expanded_query)
        query_vec = query_vec.reshape(1, -1)

        # Search a wider pool then filter to cases/precedents
        search_k = max(k * 5, 30)
        scores, indices = self._index.search(query_vec, search_k)

        results = []
        case_categories = {"enforcement", "precedent"}

        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue

            doc = self._documents[idx]
            if doc.category not in case_categories:
                continue

            result = Document(
                id=doc.id,
                text=doc.text,
                metadata=doc.metadata,
                source_file=doc.source_file,
                category=doc.category,
                jurisdiction=doc.jurisdiction,
                score=float(score),
                tags=doc.tags,
            )
            results.append(result)

            if len(results) >= k:
                break

        return results

    def retrieve_sop(self, activity: str, k: int = 6) -> list[Document]:
        """Retrieve SOP steps relevant to a given activity or process."""
        self._load()

        expanded = self._expand_query(activity)
        query_vec = self._embedder.embed_single(expanded)
        query_vec = query_vec.reshape(1, -1)

        search_k = max(k * 5, 30)
        scores, indices = self._index.search(query_vec, search_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue

            doc = self._documents[idx]
            if doc.category != "sop":
                continue

            result = Document(
                id=doc.id,
                text=doc.text,
                metadata=doc.metadata,
                source_file=doc.source_file,
                category=doc.category,
                jurisdiction=doc.jurisdiction,
                score=float(score),
                tags=doc.tags,
            )
            results.append(result)

            if len(results) >= k:
                break

        return results

    def get_stats(self) -> dict:
        """Return index statistics."""
        self._load()

        jurisdiction_counts = {}
        category_counts = {}
        for doc in self._documents:
            j = doc.jurisdiction or "unknown"
            jurisdiction_counts[j] = jurisdiction_counts.get(j, 0) + 1
            c = doc.category or "unknown"
            category_counts[c] = category_counts.get(c, 0) + 1

        return {
            "total_documents": len(self._documents),
            "index_vectors": self._index.ntotal,
            "by_jurisdiction": jurisdiction_counts,
            "by_category": category_counts,
        }
