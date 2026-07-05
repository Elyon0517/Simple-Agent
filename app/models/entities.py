from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class RagChunk(BaseModel):
    id: Optional[int] = Field(None, description="Database primary key")
    chunk_id: str = Field(..., description="Unique chunk identifier")
    source: str = Field(..., description="Source URL or identifier")
    text: str = Field(..., description="Text content")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    similarity: Optional[float] = Field(None, description="Similarity score (0-1)")
    distance: Optional[float] = Field(None, description="Cosine distance")


class SearchResult(BaseModel):
    chunk: RagChunk = Field(..., description="The retrieved chunk")
    similarity: float = Field(..., description="Similarity score")
    rank: int = Field(..., description="Result rank (1-based)")
