import logging
from typing import Any

from ..core.database import db
from .embedding import embedding_service

logger = logging.getLogger(__name__)


async def retrieve_context(query: str, top_k: int = 6) -> list[dict[str, Any]]:
    """Return up to four relevant chunks, one per source document."""
    query_embedding = await embedding_service.embed_query(query)
    search_results = await db.vector_search(query_embedding, top_k)

    seen_document_ids: set[str] = set()
    context_blocks: list[dict[str, Any]] = []

    for result in search_results:
        document_id = result.get("chunk_id", "").split("#", 1)[0]
        if document_id in seen_document_ids:
            continue

        context_blocks.append(result)
        seen_document_ids.add(document_id)

        if len(context_blocks) >= 4:
            break

    logger.info("Prepared %s unique context blocks", len(context_blocks))
    return context_blocks
