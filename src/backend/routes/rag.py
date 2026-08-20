"""LlamaIndex & Neural RAG Search API Endpoints for UNIHACK SIMPLIFI."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from ..auth import User, get_current_user
from ..rag_engine import rag_engine

router = APIRouter(prefix="/rag", tags=["LlamaIndex & Neural RAG Search"])


class RAGSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language search or technical query")
    top_k: int = Field(default=15, ge=1, le=100, description="Max candidate products to retrieve")
    dense_weight: float = Field(default=0.65, ge=0.0, le=1.0, description="Dense vector weight (1.0 = pure vector, 0.0 = pure BM25)")
    min_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Minimum confidence filter")
    category: Optional[str] = Field(default=None, description="Department or category filter")
    status: Optional[str] = Field(default=None, description="Status filter: Validated, Enriched, Flagged")


class RAGSearchResultItem(BaseModel):
    product_id: str
    row_id: int
    mfg_part_number: str
    sku: str
    brand_name: str
    manufacturer_name: str
    classpath: str
    unspsc: str
    short_desc: str
    invoice_desc: str
    mobile_desc: str
    confidence_score: float
    status: str
    hybrid_score: float
    dense_score: float
    bm25_score: float
    match_reason: str
    attributes: List[Dict[str, str]]


class RAGSearchResponse(BaseModel):
    query: str
    total_results: int
    latency_ms: float
    embedding_model: str
    retrieval_strategy: str
    synthesis: str
    results: List[RAGSearchResultItem]


@router.get("/search", response_model=RAGSearchResponse)
def get_rag_search(
    q: str = Query(..., min_length=1, description="Natural language search query"),
    top_k: int = Query(15, ge=1, le=100),
    dense_weight: float = Query(0.65, ge=0.0, le=1.0),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
) -> RAGSearchResponse:
    """Execute hybrid dense vector + BM25 LlamaIndex RAG search over the industrial catalog."""
    res = rag_engine.search(
        query=q,
        top_k=top_k,
        dense_weight=dense_weight,
        min_confidence=min_confidence,
        category=category,
        status=status
    )
    return RAGSearchResponse(**res)


@router.post("/query", response_model=RAGSearchResponse)
def post_rag_query(
    payload: RAGSearchRequest,
    current_user: User = Depends(get_current_user)
) -> RAGSearchResponse:
    """POST endpoint for advanced LlamaIndex neural RAG search with custom vector weights and filters."""
    res = rag_engine.search(
        query=payload.query,
        top_k=payload.top_k,
        dense_weight=payload.dense_weight,
        min_confidence=payload.min_confidence,
        category=payload.category,
        status=payload.status
    )
    return RAGSearchResponse(**res)


@router.get("/info")
def get_rag_info(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Retrieve metadata about the active LlamaIndex neural indexing engine."""
    return {
        "status": "ready" if rag_engine._is_indexed else "indexing",
        "embedding_model": rag_engine.embedding_model_name,
        "vector_dimensions": 384,
        "total_documents_indexed": len(rag_engine._documents),
        "retrievers": ["LlamaIndex FastEmbed (Dense)", "BM25Okapi (Sparse Keyword)"],
        "hybrid_fusion": "Reciprocal Rank Fusion (RRF)"
    }
