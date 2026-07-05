from typing import List, Optional

from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    chunk_id: str = Field(..., description="Unique identifier for the chunk")
    source: str = Field(..., description="Source URL or identifier")
    text: str = Field(..., description="Text content of the chunk")


class SeedRequest(BaseModel):
    docs: Optional[List[DocumentChunk]] = Field(
        None,
        description="Optional list of documents to seed. If omitted, uses default documents.",
    )


class AnswerRequest(BaseModel):
    query: str = Field(..., description="User question to answer")
    top_k: Optional[int] = Field(
        6,
        ge=1,
        le=20,
        description="Number of chunks to retrieve for context",
    )
