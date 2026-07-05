#!/usr/bin/env python3

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


async def test_setup():
    print("🧪 Testing RAG Backend Setup...")
    print("=" * 50)

    try:
        print("1️⃣  Testing imports...")
        from app.core.config import get_settings
        from app.core.database import db
        from app.services.rag import rag_service

        print("   ✅ All modules imported successfully")

        print("\n2️⃣  Testing configuration...")
        settings = get_settings()

        required_vars = [
            "SUPABASE_URL",
            "SUPABASE_ANON_KEY",
            "SUPABASE_SERVICE_ROLE_KEY",
            "OPENAI_API_KEY",
        ]

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var) or os.getenv(var) == f"your_{var.lower()}_here":
                missing_vars.append(var)

        if missing_vars:
            print(f"   ❌ Missing environment variables: {', '.join(missing_vars)}")
            print("   💡 Please update your .env file with real API keys")
            return False

        print("   ✅ Environment variables configured")
        print(f"   📊 Using embedding model: {settings.openai_embed_model}")
        print(f"   🤖 Using chat model: {settings.openai_chat_model}")
        print(f"   🔗 Using AI provider: {settings.ai_provider}")

        print("\n3️⃣  Testing database connection...")
        await db.connect()
        health = await db.health_check()

        if not health:
            print("   ❌ Database connection failed")
            print("   💡 Check your Supabase credentials and ensure the project is active")
            return False

        print("   ✅ Database connection successful")

        print("\n4️⃣  Testing database schema...")
        await db.initialize_schema()
        print("   ✅ Database schema validated")

        print("\n5️⃣  Testing document seeding...")
        inserted_count = await rag_service.seed_documents()

        if inserted_count == 0:
            print("   ⚠️  No new documents inserted (may already exist)")
        else:
            print(f"   ✅ Successfully seeded {inserted_count} document chunks")

        print("\n6️⃣  Testing RAG query...")
        test_query = "Can I return shoes after 30 days?"
        result = await rag_service.answer_query(test_query)

        if not result["text"] or "error" in result["text"].lower():
            print("   ❌ RAG query failed")
            print(f"   🔍 Response: {result['text'][:100]}...")
            return False

        print("   ✅ RAG query successful!")
        print(f"   📝 Answer: {result['text'][:100]}...")
        print(f"   📚 Citations: {result['citations']}")
        print(f"   ⏱️  Latency: {result['debug']['latency_ms']}ms")

        await db.disconnect()

        print("\n🎉 ALL TESTS PASSED!")
        print("=" * 50)
        print("✅ Your RAG backend is fully functional!")
        print("🚀 You can now start the server with: uvicorn main:app --reload --port 8000")
        print("📚 Visit http://localhost:8000/docs for interactive API documentation")

        return True

    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        print("   💡 Make sure you've installed dependencies: pip install -r requirements.txt")
        return False

    except Exception as e:
        print(f"   ❌ Setup test failed: {e}")
        print("   💡 Check the error message above and refer to README.md")
        return False


async def main():
    print("🔧 RAG Backend Setup Verification")
    print("This will test your complete setup without starting the server.\n")

    from dotenv import load_dotenv

    load_dotenv()

    success = await test_setup()

    if success:
        print("\n🎯 Next Steps:")
        print("1. Start the server: uvicorn main:app --reload --port 8000")
        print("2. Test the health endpoint: curl http://localhost:8000/healthz")
        print(
            '3. Ask a question: curl -X POST http://localhost:8000/answer -H \'Content-Type: application/json\' -d \'{"query":"What is your return policy?"}\''
        )
        print("4. Visit the interactive docs: http://localhost:8000/docs")
        sys.exit(0)
    else:
        print("\n❌ Setup incomplete. Please fix the issues above and try again.")
        print("📖 Refer to README.md for detailed setup instructions.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
