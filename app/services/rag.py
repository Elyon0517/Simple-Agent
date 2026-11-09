import logging
import re
import time
from typing import Any

from ..core.database import db
from ..data.default_documents import DEFAULT_DOCUMENTS
from .chat import chat_service
from .chunker import chunker
from .embedding import embedding_service
from .retrieval import retrieve_context

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self):
        self.db = db
        self.embedding_service = embedding_service
        self.chat_service = chat_service
        self.chunker = chunker

    async def seed_documents(self, documents: list[dict[str, str]] | None = None) -> int:
        start_time = time.time()

        if documents is None:
            documents = DEFAULT_DOCUMENTS
            logger.info("Using default documents for seeding")

        try:
            chunks = self.chunker.chunk_documents(documents)
            logger.info(f"Created {len(chunks)} chunks from {len(documents)} documents")

            texts = [chunk["text"] for chunk in chunks]
            embeddings = await self.embedding_service.embed_texts(texts)

            for chunk, embedding in zip(chunks, embeddings):
                chunk["embedding"] = embedding

            inserted_count = await self.db.upsert_chunks(chunks)

            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Seeding completed in {elapsed_ms}ms: {inserted_count} chunks inserted")

            return inserted_count

        except Exception as e:
            logger.error(f"Seeding failed: {e}")
            raise

    async def answer_query(self, query: str, top_k: int = 6) -> dict[str, Any]:
        start_time = time.time()

        try:
            context_blocks = await retrieve_context(query, top_k)

            if not context_blocks:
                return {
                    "text": "I don't have enough information to answer your question. Could you please rephrase or provide more context?",
                    "citations": [],
                    "debug": {
                        "top_doc_ids": [],
                        "latency_ms": int((time.time() - start_time) * 1000),
                    },
                }

            answer_text = await self.chat_service.generate_answer(query, context_blocks)
            citations = self._extract_citations(answer_text, context_blocks)

            elapsed_ms = int((time.time() - start_time) * 1000)

            result = {
                "text": answer_text,
                "citations": citations,
                "debug": {
                    "top_doc_ids": [block["chunk_id"] for block in context_blocks],
                    "latency_ms": elapsed_ms,
                },
            }

            logger.info(f"Query processed in {elapsed_ms}ms with {len(citations)} citations")
            return result

        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            return {
                "text": f"I encountered an error while processing your question: {str(e)}",
                "citations": [],
                "debug": {
                    "top_doc_ids": [],
                    "latency_ms": int((time.time() - start_time) * 1000),
                },
            }

    def _extract_citations(self, answer_text: str, context_blocks: list[dict[str, Any]]) -> list[str]:
        citation_pattern = r"\[([^\]]+)\]"
        found_citations = re.findall(citation_pattern, answer_text)

        valid_chunk_ids = {block["chunk_id"] for block in context_blocks}
        valid_citations = [cite for cite in found_citations if cite in valid_chunk_ids]

        unique_citations: list[str] = []
        for cite in valid_citations:
            if cite not in unique_citations:
                unique_citations.append(cite)

        return unique_citations


rag_service = RAGService()
