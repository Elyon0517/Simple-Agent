import logging

import openai

from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmbeddingService:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        self.embed_model = settings.openai_embed_model

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        try:
            response = self.openai_client.embeddings.create(
                model=self.embed_model,
                input=texts,
            )

            embeddings = [item.embedding for item in response.data]
            logger.info(f"Generated embeddings for {len(texts)} texts")
            return embeddings

        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise

    async def embed_query(self, query: str) -> list[float]:
        embeddings = await self.embed_texts([query])
        return embeddings[0]


embedding_service = EmbeddingService()
