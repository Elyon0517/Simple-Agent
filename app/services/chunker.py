import logging
import re
from typing import Any

from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TextChunker:
    def __init__(self, chunk_size: int | None = None, overlap: int | None = None):
        self.chunk_size = chunk_size or settings.chunk_size
        self.overlap = overlap or settings.chunk_overlap
        self.words_per_chunk = int(self.chunk_size * 0.75)
        self.overlap_words = int(self.overlap * 0.75)

        logger.info(
            f"Initialized chunker: ~{self.words_per_chunk} words per chunk, {self.overlap_words} overlap"
        )

    def chunk_text(self, text: str, source: str, base_chunk_id: str) -> list[dict[str, Any]]:
        if not text or not text.strip():
            return []

        cleaned_text = self._clean_text(text)
        words = cleaned_text.split()

        if len(words) <= self.words_per_chunk:
            return [
                {
                    "chunk_id": f"{base_chunk_id}#1",
                    "source": source,
                    "text": cleaned_text,
                }
            ]

        chunks: list[dict[str, Any]] = []
        start_idx = 0
        chunk_num = 1

        while start_idx < len(words):
            end_idx = min(start_idx + self.words_per_chunk, len(words))
            chunk_words = words[start_idx:end_idx]
            chunk_text = " ".join(chunk_words)

            chunk = {
                "chunk_id": f"{base_chunk_id}#{chunk_num}",
                "source": source,
                "text": chunk_text,
            }
            chunks.append(chunk)

            if end_idx >= len(words):
                break

            start_idx = end_idx - self.overlap_words
            chunk_num += 1

        logger.info(f"Chunked text into {len(chunks)} chunks (source: {source})")
        return chunks

    def _clean_text(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace("'", "'").replace("'", "'")
        return text

    def chunk_documents(self, documents: list[dict[str, str]]) -> list[dict[str, Any]]:
        all_chunks: list[dict[str, Any]] = []

        for doc in documents:
            text = doc.get("text", "")
            source = doc.get("source", "unknown")
            base_chunk_id = doc.get("chunk_id", "doc")

            chunks = self.chunk_text(text, source, base_chunk_id)
            all_chunks.extend(chunks)

        logger.info(f"Processed {len(documents)} documents into {len(all_chunks)} total chunks")
        return all_chunks


chunker = TextChunker()
