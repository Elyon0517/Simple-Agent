#!/usr/bin/env python3

import os

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()


def check_embedding_dimensions():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials in .env file")
        return

    supabase = create_client(supabase_url, supabase_key)

    try:
        print("🔍 Checking embedding dimensions...")

        result = supabase.rpc(
            "match_chunks",
            {
                "query_embedding": "[0]" * 1536,
                "match_threshold": 0.1,
                "match_count": 1,
            },
        ).execute()

        if result.data:
            print(f"✅ Found {len(result.data)} chunks in database")
        else:
            print("⚠️  No chunks found in database. Run /seed first.")
            return

        schema_result = supabase.table("rag_chunks").select("*").limit(1).execute()

        if schema_result.data:
            chunk = schema_result.data[0]
            if "embedding" in chunk and chunk["embedding"]:
                dimensions = len(chunk["embedding"])
                print(f"📐 Embedding dimensions: {dimensions}")
                print(f"📊 Vector type: {type(chunk['embedding'])}")
                print(f"🎯 First few values: {chunk['embedding'][:5]}...")
            else:
                print("❌ No embedding data found")

        print("\n📋 Table Schema Info:")
        print("Run this SQL in Supabase SQL Editor:")
        print("SELECT column_name, data_type FROM information_schema.columns")
        print("WHERE table_name = 'rag_chunks' AND column_name = 'embedding';")

        print("\n🔧 Or use pgvector function:")
        print("SELECT vector_dims(embedding) FROM rag_chunks LIMIT 1;")

    except Exception as e:
        print(f"❌ Error checking dimensions: {e}")
        print("💡 Make sure you've run the /seed endpoint first to populate data")


if __name__ == "__main__":
    check_embedding_dimensions()
