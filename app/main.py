import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from .core.config import get_settings
from .core.database import db
from .data.default_documents import DEFAULT_DOCUMENTS
from .models.requests import AnswerRequest, SeedRequest
from .models.responses import AnswerResponse, HealthResponse, SeedResponse
from .services.rag import rag_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting RAG API application")

    try:
        await db.connect()
        await db.initialize_schema()
        logger.info("Application startup completed successfully")

    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise

    yield

    logger.info("Shutting down RAG API application")
    await db.disconnect()


app = FastAPI(
    title="RAG AI Agent Backend",
    description="A minimal, production-ready FastAPI backend demonstrating Retrieval-Augmented Generation (RAG) with vector similarity search.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://yt-rag.vercel.app",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/chat", tags=["General"])
async def chat_interface():
    return FileResponse("static/chat.html")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


@app.get("/", tags=["General"])
async def root():
    return {
        "message": "Welcome to RAG AI Agent Backend",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "/healthz",
            "seed": "/seed",
            "answer": "/answer",
            "documents": "/documents",
            "greet": "/greet/{name}",
        },
    }


@app.get("/greet/{name}", tags=["General"])
async def greet(name: str):
    return {"message": f"Hello, {name}! I think you are great!"}


@app.get("/healthz", response_model=HealthResponse, tags=["Health"])
async def health_check():
    try:
        db_healthy = await db.health_check()

        return HealthResponse(
            status="ok" if db_healthy else "degraded",
            database_connected=db_healthy,
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Service unavailable: {str(e)}",
        )


@app.get("/documents", tags=["General"])
async def get_documents():
    return {"documents": DEFAULT_DOCUMENTS}


@app.post("/seed", response_model=SeedResponse, tags=["RAG"])
async def seed_documents(request: SeedRequest = SeedRequest()):
    try:
        logger.info("Starting document seeding process")

        documents = None
        if request.docs:
            documents = [
                {
                    "chunk_id": doc.chunk_id,
                    "source": doc.source,
                    "text": doc.text,
                }
                for doc in request.docs
            ]

        inserted_count = await rag_service.seed_documents(documents)

        logger.info(f"Seeding completed: {inserted_count} chunks inserted")

        return SeedResponse(inserted=inserted_count)

    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to seed documents: {str(e)}",
        )


@app.post("/answer", response_model=AnswerResponse, tags=["RAG"])
async def answer_question(request: AnswerRequest):
    try:
        logger.info(f"Processing query: '{request.query[:100]}...'")

        result = await rag_service.answer_query(
            query=request.query,
            top_k=request.top_k,
        )

        response = AnswerResponse(
            text=result["text"],
            citations=result["citations"],
            debug={
                "top_doc_ids": result["debug"]["top_doc_ids"],
                "latency_ms": result["debug"]["latency_ms"],
            },
        )

        logger.info(f"Query processed successfully in {result['debug']['latency_ms']}ms")

        return response

    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}",
        )


@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "detail": "The requested endpoint does not exist",
            "available_endpoints": ["/", "/healthz", "/seed", "/answer", "/docs"],
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred. Please check the logs.",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
