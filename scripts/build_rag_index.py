"""Precompute and verify LlamaIndex neural RAG index."""
import time
from src.backend.state import catalog_state
from src.backend.rag_engine import rag_engine

print("Initializing Catalog State & Products...")
catalog_state.initialize()

print("\nTesting LlamaIndex Semantic & Hybrid RAG queries:")
test_queries = [
    "heavy duty diablo sanding disc for wood and metal",
    "quiet dishwasher 120V stainless steel",
    "milwaukee saw blade with 18 TPI",
    "3M abrasive wheel"
]

for q in test_queries:
    t0 = time.perf_counter()
    res = rag_engine.search(q, top_k=3)
    latency = (time.perf_counter() - t0) * 1000
    print(f"\n🔍 Query: '{q}' (Latency: {latency:.2f} ms | Results: {res['total_results']})")
    print(f"   💡 RAG Synthesis: {res['synthesis']}")
    for r in res["results"]:
        print(f"   • [{r['brand_name']}] MPN: {r['mfg_part_number']} | Hybrid Score: {r['hybrid_score']:.4f} | Dense: {r['dense_score']:.4f} | BM25: {r['bm25_score']:.4f}")
        print(f"     Reason: {r['match_reason']}")
print("\n✅ LlamaIndex RAG Verification Complete!")
