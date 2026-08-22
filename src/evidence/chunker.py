"""
Evidence Chunker for Manufacturer Technical Specifications.

Partitions parsed documents into discrete, searchable, and hashable EvidenceChunk units.
"""

from typing import List, Dict, Any
import hashlib
import re
from .models import EvidenceChunk


def create_evidence_chunks(
    source_id: str,
    mpn: str,
    brand: str,
    manufacturer: str,
    sections: List[Dict[str, Any]]
) -> List[EvidenceChunk]:
    """
    Transform raw parsed document sections into discrete EvidenceChunk objects.
    Computes a cryptographic hash for each chunk.
    """
    chunks: List[EvidenceChunk] = []
    
    for idx, sec in enumerate(sections):
        heading = sec.get("heading", "General Overview")
        text = sec.get("text", "")
        specs = sec.get("specs", {})
        page_num = sec.get("page_number", 1)
        
        # Build deterministic hash of chunk content
        raw_sig = f"{source_id}:{mpn}:{heading}:{page_num}:{text}"
        chunk_hash = hashlib.sha256(raw_sig.encode("utf-8")).hexdigest()[:16]
        clean_mpn_slug = re.sub(r"[^a-zA-Z0-9_\-]", "_", mpn.lower())
        chunk_id = f"chk_{clean_mpn_slug}_{idx + 1}_{chunk_hash[:8]}"
        
        chunk = EvidenceChunk(
            chunk_id=chunk_id,
            source_id=source_id,
            mpn=mpn,
            brand=brand,
            manufacturer=manufacturer,
            section_title=heading,
            page_number=page_num,
            text_content=text,
            key_value_specs=specs,
            chunk_hash=chunk_hash
        )
        chunks.append(chunk)
        
    return chunks
