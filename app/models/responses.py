from typing import Any, Dict, List

from pydantic import BaseModel, Field


class SeedResponse(BaseModel):
    inserted: int = Field(..., description="Number of chunks successfully inserted")


class DebugInfo(BaseModel):
    top_doc_ids: List[str] = Field(..., description="IDs of retrieved chunks")
    latency_ms: int = Field(..., description="Total processing time in milliseconds")


class AnswerResponse(BaseModel):
    text: str = Field(..., description="Generated answer with inline citations")
    citations: List[str] = Field(..., description="List of chunk IDs used as sources")
    debug: DebugInfo = Field(..., description="Debug information")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Health status")
    database_connected: bool = Field(..., description="Database connection status")


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    detail: str = Field(..., description="Detailed error information")
