CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE rag_chunks (
    id BIGSERIAL PRIMARY KEY,
    chunk_id TEXT NOT NULL UNIQUE,
    source TEXT NOT NULL,
    text TEXT NOT NULL,
    embedding VECTOR(1536),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX rag_chunks_vec_idx
    ON rag_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX rag_chunks_src_idx ON rag_chunks (source);
CREATE INDEX rag_chunks_chunk_id_idx ON rag_chunks (chunk_id);
CREATE INDEX rag_chunks_created_at_idx ON rag_chunks (created_at DESC);

CREATE OR REPLACE FUNCTION match_chunks (
  query_embedding vector(1536),
  match_count int DEFAULT 6,
  min_similarity float DEFAULT 0.0
)
RETURNS TABLE (
  chunk_id text,
  source text,
  text text,
  similarity float,
  created_at timestamptz
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    rag_chunks.chunk_id,
    rag_chunks.source,
    rag_chunks.text,
    1 - (rag_chunks.embedding <=> query_embedding) as similarity,
    rag_chunks.created_at
  FROM rag_chunks
  WHERE 1 - (rag_chunks.embedding <=> query_embedding) >= min_similarity
  ORDER BY rag_chunks.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

CREATE OR REPLACE FUNCTION get_chunk_stats()
RETURNS TABLE (
  total_chunks bigint,
  unique_sources bigint,
  latest_chunk timestamptz
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    COUNT(*) as total_chunks,
    COUNT(DISTINCT source) as unique_sources,
    MAX(created_at) as latest_chunk
  FROM rag_chunks;
END;
$$;

ALTER TABLE rag_chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow service role full access" ON rag_chunks
  FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Allow authenticated read access" ON rag_chunks
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Allow anonymous read access" ON rag_chunks
  FOR SELECT USING (true);

SELECT 'pgvector extension installed' as test_result
WHERE EXISTS (
  SELECT 1 FROM pg_extension WHERE extname = 'vector'
);

SELECT 'rag_chunks table created' as test_result
WHERE EXISTS (
  SELECT 1 FROM information_schema.tables
  WHERE table_schema = 'public' AND table_name = 'rag_chunks'
);

SELECT
  'Vector column configured for text-embedding-3-small' as test_result,
  'VECTOR(1536) dimensions' as details
WHERE EXISTS (
  SELECT 1 FROM information_schema.columns
  WHERE table_name = 'rag_chunks'
  AND column_name = 'embedding'
);

SELECT 'match_chunks function created' as test_result
WHERE EXISTS (
  SELECT 1 FROM information_schema.routines
  WHERE routine_schema = 'public' AND routine_name = 'match_chunks'
);

SELECT 'get_chunk_stats function created' as test_result
WHERE EXISTS (
  SELECT 1 FROM information_schema.routines
  WHERE routine_schema = 'public' AND routine_name = 'get_chunk_stats'
);

SELECT 'Vector index created' as test_result
WHERE EXISTS (
  SELECT 1 FROM pg_indexes
  WHERE tablename = 'rag_chunks' AND indexname = 'rag_chunks_vec_idx'
);

SELECT
  'Database ready - ' || total_chunks::text || ' chunks' as test_result
FROM get_chunk_stats();

SELECT '🎉 SUCCESS! Your Supabase database is ready for RAG!' as final_result;
