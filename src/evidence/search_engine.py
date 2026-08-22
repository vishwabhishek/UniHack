"""
Manufacturer Evidence Search Engine.

Enables lexical and key-value querying over discrete evidence chunks.
"""

from typing import List, Dict, Optional
import re
from .models import EvidenceChunk, EvidenceQueryResponse, ExtractedCandidate
from .registry import EvidenceRegistryManager


class EvidenceSearchEngine:
    """Fast search index across ingested manufacturer specification chunks."""

    def __init__(self, registry_manager: Optional[EvidenceRegistryManager] = None):
        self.registry = registry_manager or EvidenceRegistryManager()

    def search_by_mpn(self, mpn: str, brand: Optional[str] = None) -> List[EvidenceChunk]:
        """Retrieve all active chunks matching an MPN."""
        clean_mpn = mpn.strip().upper()
        entries = self.registry.get_entries_by_mpn(clean_mpn)
        chunks: List[EvidenceChunk] = []
        for entry in entries:
            chunks.extend(self.registry.load_chunks_for_entry(entry))
        return chunks

    def search_by_keyword(self, query: str, mpn: Optional[str] = None, limit: int = 10) -> List[EvidenceChunk]:
        """Perform search across chunk text and specification keys."""
        all_chunks = self.registry.get_all_active_chunks()
        tokens = [t.lower() for t in re.findall(r"\w+", query) if len(t) > 1]
        if not tokens:
            return all_chunks[:limit]

        scored: List[tuple[float, EvidenceChunk]] = []
        for chk in all_chunks:
            if mpn and chk.mpn.upper() != mpn.strip().upper():
                continue

            score = 0.0
            content_lower = chk.text_content.lower()
            section_lower = chk.section_title.lower()
            mpn_lower = chk.mpn.lower()

            for tok in tokens:
                if tok == mpn_lower:
                    score += 5.0
                if tok in section_lower:
                    score += 3.0
                if tok in content_lower:
                    score += 1.0
                for k, v in chk.key_value_specs.items():
                    if tok in k.lower() or tok in v.lower():
                        score += 2.0

            if score > 0:
                scored.append((score, chk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:limit]]
