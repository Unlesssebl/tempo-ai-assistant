"""
Semantic chunking по предложениям с группировкой по схожести.
"""

from typing import List

import nltk
import numpy as np

from src.core.clients import GeminiEmbedder


class SemanticChunker:
    """Chunking по семантическим границам."""

    def __init__(self, embedder: GeminiEmbedder, threshold: float = 0.75):
        self.embedder = embedder
        self.threshold = threshold
        self._ensure_nltk()

    def chunk(self, text: str, max_chunk_size: int = 1000) -> List[str]:
        """Разбивка текста на семантические чанки."""
        sentences = nltk.sent_tokenize(text, language="russian")

        if len(sentences) <= 1:
            return [text]

        embeddings = self.embedder.encode(sentences, task_type="SEMANTIC_SIMILARITY", normalize=True)

        chunks: List[str] = []
        current_chunk = [sentences[0]]
        current_embedding = embeddings[0]

        for i in range(1, len(sentences)):
            similarity = np.dot(current_embedding, embeddings[i]) / (
                np.linalg.norm(current_embedding) * np.linalg.norm(embeddings[i])
            )
            current_text = " ".join(current_chunk)

            if similarity >= self.threshold and len(current_text) + len(sentences[i]) < max_chunk_size:
                current_chunk.append(sentences[i])
                start_idx = i - len(current_chunk) + 1
                current_embedding = np.mean(embeddings[start_idx : i + 1], axis=0)
            else:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentences[i]]
                current_embedding = embeddings[i]

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    @staticmethod
    def _ensure_nltk():
        """Гарантирует доступность токенизатора."""
        try:
            nltk.data.find("tokenizers/punkt")
            nltk.data.find("tokenizers/punkt_tab")
        except LookupError:
            nltk.download("punkt", quiet=True)
            nltk.download("punkt_tab", quiet=True)
