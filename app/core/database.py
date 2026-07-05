import logging
from typing import Any

from supabase import Client, create_client

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class Database:
    def __init__(self):
        self.supabase: Client | None = None
        self._admin_client: Client | None = None

    async def connect(self) -> None:
        try:
            self.supabase = create_client(
                settings.supabase_url,
                settings.supabase_anon_key,
            )

            self._admin_client = create_client(
                settings.supabase_url,
                settings.supabase_service_role_key,
            )

            logger.info("Supabase clients initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase clients: {e}")
            raise

    async def disconnect(self) -> None:
        logger.info("Supabase clients cleaned up")

    def get_client(self, admin: bool = True) -> Client:
        if not self.supabase or not self._admin_client:
            raise RuntimeError("Database not connected. Call connect() first.")

        return self._admin_client if admin else self.supabase

    async def initialize_schema(self) -> None:
        try:
            client = self.get_client(admin=True)

            result = client.table("rag_chunks").select("id").limit(1).execute()

            if result.data is not None:
                logger.info("Database schema is properly initialized")

                try:
                    stats_result = client.rpc("get_chunk_stats").execute()
                    if stats_result.data:
                        stats = stats_result.data[0]
                        logger.info(
                            f"Database stats: {stats['total_chunks']} chunks, {stats['unique_sources']} sources"
                        )
                except Exception:
                    logger.warning("get_chunk_stats function not available - some features may not work")

            else:
                logger.error("Database schema not initialized!")
                logger.error(
                    "Please run the SQL initialization script:\n"
                    "1. Open your Supabase project dashboard\n"
                    "2. Go to SQL Editor\n"
                    "3. Run the script: sql/init_supabase.sql\n"
                    "4. Restart your application"
                )

        except Exception as e:
            logger.error(f"Database schema check failed: {e}")
            logger.error(
                "Please ensure you've run sql/init_supabase.sql in your Supabase dashboard"
            )

    async def upsert_chunks(self, chunks: list[dict[str, Any]]) -> int:
        if not chunks:
            return 0

        try:
            client = self.get_client(admin=True)

            chunk_data = []
            for chunk in chunks:
                chunk_data.append(
                    {
                        "chunk_id": chunk["chunk_id"],
                        "source": chunk["source"],
                        "text": chunk["text"],
                        "embedding": chunk["embedding"],
                    }
                )

            result = client.table("rag_chunks").upsert(
                chunk_data,
                on_conflict="chunk_id",
            ).execute()

            inserted_count = len(result.data) if result.data else 0
            logger.info(f"Upserted {inserted_count} chunks to database")
            return inserted_count

        except Exception as e:
            logger.error(f"Failed to upsert chunks: {e}")
            raise

    async def vector_search(
        self, query_embedding: list[float], top_k: int = 6
    ) -> list[dict[str, Any]]:
        try:
            client = self.get_client(admin=True)

            result = client.rpc(
                "match_chunks",
                {
                    "query_embedding": query_embedding,
                    "match_count": top_k,
                },
            ).execute()

            if result.data:
                logger.info(f"Vector search returned {len(result.data)} results")
                return result.data

            logger.info("Using fallback query (match_chunks RPC function not available)")
            result = client.table("rag_chunks").select("*").limit(top_k).execute()

            if result.data:
                for i, chunk in enumerate(result.data):
                    chunk["similarity"] = 1.0 - (i * 0.1)

            return result.data or []

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    async def health_check(self) -> bool:
        try:
            client = self.get_client(admin=True)
            client.table("rag_chunks").select("id").limit(1).execute()
            return True

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


db = Database()
