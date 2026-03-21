"""Embedding module using sentence-transformers for semantic search."""

import numpy as np

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_CACHE_DIR = "/tmp/models"
BATCH_SIZE = 64


class Embedder:
    """Lazy-loading sentence-transformer embedder for compliance documents."""

    def __init__(self):
        self._model = None

    def _load_model(self):
        if self._model is not None:
            return
        print(f"[Embedder] Loading model {MODEL_NAME} ...")
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(
            MODEL_NAME,
            cache_folder=MODEL_CACHE_DIR,
            device="cpu",
        )
        print(f"[Embedder] Model loaded. Dimension: {self._model.get_sentence_embedding_dimension()}")

    def embed(self, texts: list[str]) -> np.ndarray:
        """Embed a list of texts, returning normalized vectors.

        Processes in batches of BATCH_SIZE to avoid OOM on free-tier.
        Returns shape (len(texts), dim).
        """
        self._load_model()

        all_embeddings = []
        for start in range(0, len(texts), BATCH_SIZE):
            batch = texts[start : start + BATCH_SIZE]
            emb = self._model.encode(
                batch,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            all_embeddings.append(emb)

        return np.vstack(all_embeddings).astype(np.float32)

    def embed_single(self, text: str) -> np.ndarray:
        """Embed a single text string. Returns shape (dim,)."""
        self._load_model()
        emb = self._model.encode(
            [text],
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return emb[0].astype(np.float32)

    @property
    def dimension(self) -> int:
        self._load_model()
        return self._model.get_sentence_embedding_dimension()
