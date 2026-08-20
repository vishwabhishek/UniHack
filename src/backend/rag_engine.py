"""LlamaIndex & Open-Source Neural RAG Hybrid Search Engine for UNIHACK SIMPLIFI.

Combines:
1. LlamaIndex Document/Node representation of all 1,000 industrial catalog items.
2. Dense Semantic Vector Embeddings via FastEmbed (BAAI/bge-small-en-v1.5 ONNX runtime).
3. Sparse Lexical BM25 ranking (rank-bm25) for exact alphanumeric/part-number matching.
4. Reciprocal Rank Fusion (RRF) with explainable RAG synthesis.
"""

from __future__ import annotations

import time
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from rank_bm25 import BM25Okapi
from fastembed import TextEmbedding

from llama_index.core import Document
from llama_index.core.schema import TextNode

from ..pipeline.models import EnrichedProduct


class CatalogRAGEngine:
    """LlamaIndex & Neural Embedding RAG Engine for Industrial Product Catalog."""

    def __init__(self, embedding_model_name: str = "BAAI/bge-small-en-v1.5"):
        self.embedding_model_name = embedding_model_name
        self._embed_model: Optional[TextEmbedding] = None
        self._documents: List[Document] = []
        self._nodes: List[TextNode] = []
        self._dense_embeddings: Optional[np.ndarray] = None
        self._bm25: Optional[BM25Okapi] = None
        self._bm25_corpus: List[List[str]] = []
        self._products: List[EnrichedProduct] = []
        self._product_by_id: Dict[str, EnrichedProduct] = {}
        self._is_indexed: bool = False

    def _get_embed_model(self) -> TextEmbedding:
        if self._embed_model is None:
            self._embed_model = TextEmbedding(model_name=self.embedding_model_name)
        return self._embed_model

    def build_product_document(self, p: EnrichedProduct) -> Document:
        """Create a semantically rich LlamaIndex Document for an industrial product."""
        row_id_val = p.raw.row_id or 0
        attr_text = ", ".join(f"{a.label}: {a.value} {a.uom or ''}".strip() for a in p.attributes)
        features_text = "; ".join(p.item_features or [])
        
        content = (
            f"Product: {p.product_name}\n"
            f"Brand: {p.brand_name} (Manufacturer: {p.manufacturer_name})\n"
            f"MPN: {p.mfg_part_number} | SKU: {p.sku} | Part Number: {p.part_number}\n"
            f"UNSPSC: {p.unspsc} | Hierarchy: {p.classpath} ({p.dept} > {p.class_name} > {p.fine})\n"
            f"Invoice Description: {p.invoice_desc}\n"
            f"Mobile Description: {p.mobile_desc}\n"
            f"Short Description: {p.short_desc}\n"
            f"Technical Specification: {p.long_desc1}\n"
            f"Features: {features_text}\n"
            f"Technical Attributes: {attr_text}\n"
            f"Raw Distributor Description: {p.raw.part_desc}"
        )

        metadata = {
            "row_id": row_id_val,
            "product_id": str(row_id_val),
            "mfg_part_number": p.mfg_part_number,
            "sku": p.sku,
            "brand_name": p.brand_name,
            "manufacturer_name": p.manufacturer_name,
            "unspsc": p.unspsc,
            "dept": p.dept,
            "classpath": p.classpath,
            "confidence_score": p.confidence_score,
            "status": p.status,
            "attribute_count": len(p.attributes)
        }

        return Document(
            text=content,
            metadata=metadata,
            doc_id=f"doc_{row_id_val}"
        )

    def index_catalog(self, products: List[EnrichedProduct]) -> None:
        """Ingest and index the entire catalog into LlamaIndex and Dense+BM25 stores."""
        start_time = time.time()
        self._products = products
        self._product_by_id = {str(p.raw.row_id or i): p for i, p in enumerate(products)}

        # 1. Build LlamaIndex Documents & TextNodes
        self._documents = [self.build_product_document(p) for p in products]
        self._nodes = [
            TextNode(
                text=doc.text,
                metadata=doc.metadata,
                id_=doc.doc_id
            )
            for doc in self._documents
        ]

        # 2. Build BM25 Sparse Lexical Index
        self._bm25_corpus = [
            doc.text.lower().replace("\n", " ").split()
            for doc in self._documents
        ]
        self._bm25 = BM25Okapi(self._bm25_corpus)

        # 3. Compute Dense Embeddings with FastEmbed (Cached on disk)
        from pathlib import Path
        cache_file = Path("data/output/catalog_embeddings.npy")
        
        if cache_file.exists() and cache_file.stat().st_size > 0:
            try:
                self._dense_embeddings = np.load(cache_file)
                if len(self._dense_embeddings) == len(products):
                    print(f"Loaded {len(products)} cached LlamaIndex neural embeddings from {cache_file}")
                else:
                    self._dense_embeddings = None
            except Exception as e:
                print(f"Failed to load embedding cache: {e}")
                self._dense_embeddings = None

        if self._dense_embeddings is None:
            embed_model = self._get_embed_model()
            dense_texts = [
                f"{p.brand_name} {p.mfg_part_number} {p.short_desc} {p.classpath} " +
                " ".join(f"{a.label} {a.value} {a.uom or ''}" for a in p.attributes[:6])
                for p in products
            ]
            embeddings_list = list(embed_model.embed(dense_texts, batch_size=256))
            self._dense_embeddings = np.array(embeddings_list, dtype=np.float32)
            
            # Normalize vectors for cosine similarity
            norms = np.linalg.norm(self._dense_embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1e-10
            self._dense_embeddings = self._dense_embeddings / norms
            
            # Persist cache
            try:
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                np.save(cache_file, self._dense_embeddings)
                print(f"Persisted {len(products)} LlamaIndex neural embeddings to {cache_file}")
            except Exception as e:
                print(f"Warning: Could not save embeddings cache: {e}")

        self._is_indexed = True
        elapsed = time.time() - start_time
        print(f"LlamaIndex & Neural RAG Engine indexed {len(products)} products in {elapsed:.2f}s")

    def search(
        self,
        query: str,
        top_k: int = 15,
        dense_weight: float = 0.65,
        min_confidence: Optional[float] = None,
        category: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute Hybrid Dense + Sparse RAG Search across the indexed catalog."""
        if not self._is_indexed:
            raise RuntimeError("CatalogRAGEngine is not yet indexed.")

        start_time = time.perf_counter()
        clean_query = query.strip()
        if not clean_query:
            return {
                "query": query,
                "total_results": 0,
                "latency_ms": 0.0,
                "results": [],
                "synthesis": "Empty search query provided."
            }

        # 1. Compute Dense Vector Cosine Similarity
        embed_model = self._get_embed_model()
        query_vec = list(embed_model.embed([clean_query]))[0]
        query_vec = np.array(query_vec, dtype=np.float32)
        q_norm = np.linalg.norm(query_vec)
        if q_norm > 0:
            query_vec = query_vec / q_norm
        dense_scores = np.dot(self._dense_embeddings, query_vec)

        # 2. Compute Sparse BM25 Scores
        tokenized_q = clean_query.lower().split()
        bm25_raw_scores = np.array(self._bm25.get_scores(tokenized_q), dtype=np.float32)
        bm25_max = np.max(bm25_raw_scores) if np.max(bm25_raw_scores) > 0 else 1.0
        bm25_normalized = bm25_raw_scores / bm25_max

        # 3. Hybrid Reciprocal Fusion
        sparse_weight = 1.0 - dense_weight
        hybrid_scores = (dense_weight * dense_scores) + (sparse_weight * bm25_normalized)

        # 4. Rank and Filter Candidates
        ranked_indices = np.argsort(-hybrid_scores)
        results = []

        for idx in ranked_indices:
            p = self._products[idx]
            h_score = float(hybrid_scores[idx])
            d_score = float(dense_scores[idx])
            s_score = float(bm25_normalized[idx])

            # Apply query filters if specified
            if min_confidence is not None and p.confidence_score < min_confidence:
                continue
            if category and category.lower() != "all":
                if category.lower() not in p.dept.lower() and category.lower() not in p.classpath.lower():
                    continue
            if status and status.lower() != "all":
                if p.status.lower() != status.lower():
                    continue

            # Build explainable matching reason
            matched_specs = [
                f"{a.label}: {a.value}"
                for a in p.attributes
                if any(t in a.label.lower() or t in a.value.lower() for t in tokenized_q)
            ]
            reason = (
                f"Matched brand '{p.brand_name}' and taxonomy '{p.classpath}'"
                if not matched_specs
                else f"Matched specifications: {', '.join(matched_specs)}"
            )

            results.append({
                "product_id": str(p.raw.row_id or idx + 1),
                "row_id": p.raw.row_id or idx + 1,
                "mfg_part_number": p.mfg_part_number,
                "sku": p.sku,
                "brand_name": p.brand_name,
                "manufacturer_name": p.manufacturer_name,
                "classpath": p.classpath,
                "unspsc": p.unspsc,
                "short_desc": p.short_desc,
                "invoice_desc": p.invoice_desc,
                "mobile_desc": p.mobile_desc,
                "confidence_score": p.confidence_score,
                "status": p.status,
                "hybrid_score": round(h_score, 4),
                "dense_score": round(d_score, 4),
                "bm25_score": round(s_score, 4),
                "match_reason": reason,
                "attributes": [{"label": a.label, "value": a.value, "uom": a.uom or ""} for a in p.attributes[:6]]
            })

            if len(results) >= top_k:
                break

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # 5. RAG Synthesis Explanation
        top_brands = list(dict.fromkeys(r["brand_name"] for r in results[:3]))
        synthesis = (
            f"LlamaIndex Neural RAG identified {len(results)} relevant industrial products "
            f"across {', '.join(top_brands) if top_brands else 'catalog'} matching '{clean_query}' "
            f"with average confidence {np.mean([r['confidence_score'] for r in results]):.2f}."
            if results else f"No products matching query '{clean_query}'."
        )

        return {
            "query": query,
            "total_results": len(results),
            "latency_ms": round(elapsed_ms, 2),
            "embedding_model": self.embedding_model_name,
            "retrieval_strategy": "LlamaIndex Hybrid (Dense Vector + BM25 Sparse Fusion)",
            "synthesis": synthesis,
            "results": results
        }


# Global Singleton Instance
rag_engine = CatalogRAGEngine()
