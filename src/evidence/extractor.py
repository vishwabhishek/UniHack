"""
Candidate Specification Extractor with Source Citations.

Extracts candidate technical attributes from official evidence chunks with complete provenance citations,
using Gemini AI structured extraction provider with deterministic rule fallback.
"""

from typing import List, Dict, Optional, Any, Tuple
import re
from datetime import datetime, timezone
from .models import ExtractedCandidate, EvidenceChunk, EvidenceType
from .search_engine import EvidenceSearchEngine
from .registry import EvidenceRegistryManager
from .providers.base import (
    BaseEvidenceExtractionProvider,
    ExtractionRequest,
    ExtractionResult,
    GeminiExtractedFact,
)
from .providers.gemini import GeminiEvidenceExtractionProvider
from .gemini_extractor import SourceSpanVerifier


class EvidenceAttributeExtractor:
    """Extracts candidate PIM attributes from ingested manufacturer chunks using Gemini or deterministic rules."""

    def __init__(
        self,
        registry_manager: Optional[EvidenceRegistryManager] = None,
        provider: Optional[BaseEvidenceExtractionProvider] = None,
    ):
        self.registry = registry_manager or EvidenceRegistryManager()
        self.search_engine = EvidenceSearchEngine(self.registry)
        self.provider = provider or GeminiEvidenceExtractionProvider()
        self.span_verifier = SourceSpanVerifier()

    def extract_candidates_for_mpn(self, mpn: str) -> List[ExtractedCandidate]:
        """Extract all candidate attributes for an MPN with full source lineage and provider extraction."""
        clean_mpn = mpn.strip().upper()
        entries = self.registry.get_entries_by_mpn(clean_mpn)
        if not entries:
            return []

        candidates: List[ExtractedCandidate] = []
        now_ts = datetime.now(timezone.utc).isoformat()

        for entry in entries:
            chunks = self.registry.load_chunks_for_entry(entry)
            if not chunks:
                continue

            chunk_map = {c.chunk_id: c for c in chunks}

            # 1. Build restricted ExtractionRequest for the AI Provider
            req = ExtractionRequest(
                mpn=entry.mpn,
                brand_candidate=entry.brand,
                manufacturer_candidate=entry.manufacturer,
                category_candidate="Plumbing & Heating / Fittings",
                requested_fields=[
                    "Fitting Type", "Connection Type", "Material", "Nominal Size",
                    "Pressure Rating", "Voltage", "Amps", "Sound Level", "Mounting Type",
                    "Wash Cycles", "Flow Rate", "Color / Finish"
                ],
                lov_subset={
                    "Fitting Type": ["90 deg Elbow", "45 deg Elbow", "Straight Tee", "Coupling", "Cord Grip Connector", "Male Adapter", "Female Adapter", "Union"],
                    "Connection Type": ["Push-to-Connect", "Sweat", "Compression", "Male NPT", "Female NPT", "Flanged", "Threaded"],
                    "Material": ["Brass", "Copper", "Stainless Steel", "Aluminum", "PVC", "Cast Iron", "Plastic"],
                    "Mounting Type": ["Built-In", "Freestanding", "Deck", "Wall"]
                },
                uom_rules={
                    "Pressure Rating": "Format as integer + ' psi', e.g. '200 psi'",
                    "Nominal Size": "Format fractional inch + ' in', e.g. '1/2 in'",
                    "Voltage": "Format as integer + ' V', e.g. '120 V'",
                    "Amps": "Format as integer + ' A', e.g. '15 A'",
                    "Sound Level": "Format as integer + ' dBA', e.g. '44 dBA'"
                },
                source_chunks=chunks
            )

            # 2. Run Provider Extraction (Gemini if enabled, else returns AI_EXTRACTION_UNAVAILABLE)
            extraction_res = self.provider.extract(req)

            if extraction_res.status == "SUCCESS" and extraction_res.facts:
                for fact in extraction_res.facts:
                    if not fact.raw_value:
                        continue

                    matching_chunk = chunk_map.get(fact.evidence_chunk_id or "", chunks[0])
                    attr_name, norm_val = self._map_key_to_attribute(
                        fact.field_name,
                        fact.normalized_candidate or fact.raw_value
                    )

                    if attr_name and norm_val:
                        verif_status = "candidate" if fact.conflicts else "verified"
                        candidates.append(
                            ExtractedCandidate(
                                field_name=attr_name,
                                candidate_value=fact.raw_value,
                                normalized_value=norm_val,
                                source_url=entry.url,
                                source_type=entry.source_type,
                                source_title=entry.title or f"{entry.brand} Official Specifications",
                                source_page_or_section=fact.source_page_or_section or f"Section: {matching_chunk.section_title} (p. {matching_chunk.page_number or 1})",
                                evidence_excerpt=fact.evidence_excerpt or matching_chunk.text_content[:80],
                                extraction_method="gemini_structured_extraction",
                                retrieved_at=now_ts,
                                confidence=fact.confidence,
                                verification_status=verif_status,
                                dictionary_identity="UniCat Controlled Vocabulary (LOV)",
                                chunk_id=fact.evidence_chunk_id,
                                model_name=extraction_res.model_name,
                                prompt_version=extraction_res.prompt_version,
                                source_hash=matching_chunk.chunk_hash,
                                conflicts=fact.conflicts,
                                extraction_reason=fact.extraction_reason,
                                unresolved_reason=fact.unresolved_reason,
                                ai_extraction_unavailable=False
                            )
                        )

            # 3. Deterministic Fallback / Baseline Extraction from key_value_specs
            for chunk in chunks:
                for raw_key, raw_val in chunk.key_value_specs.items():
                    attr_name, norm_val = self._map_key_to_attribute(raw_key, raw_val)
                    if attr_name and norm_val:
                        candidates.append(
                            ExtractedCandidate(
                                field_name=attr_name,
                                candidate_value=raw_val,
                                normalized_value=norm_val,
                                source_url=entry.url,
                                source_type=entry.source_type,
                                source_title=entry.title or f"{entry.brand} Official Specifications",
                                source_page_or_section=f"Section: {chunk.section_title} (p. {chunk.page_number or 1})",
                                evidence_excerpt=f"{raw_key}: {raw_val}",
                                extraction_method="deterministic_rule",
                                retrieved_at=now_ts,
                                confidence=0.98,
                                verification_status="verified",
                                dictionary_identity="UniCat Controlled Vocabulary (LOV)",
                                chunk_id=chunk.chunk_id,
                                source_hash=chunk.chunk_hash,
                                ai_extraction_unavailable=extraction_res.ai_extraction_unavailable
                            )
                        )

                # 4. Text regex patterns
                text_candidates = self._extract_from_text(chunk, entry, now_ts, extraction_res.ai_extraction_unavailable)
                candidates.extend(text_candidates)

        # Deduplicate candidates by field_name keeping highest confidence while preserving conflicts and provenance
        unique_map: Dict[str, ExtractedCandidate] = {}
        for c in candidates:
            if c.field_name not in unique_map:
                unique_map[c.field_name] = c
            else:
                existing = unique_map[c.field_name]
                all_conflicts = list(set(existing.conflicts + c.conflicts))

                # Check for value mismatch between different extractions
                if existing.normalized_value.lower() != c.normalized_value.lower():
                    all_conflicts.append(
                        f"Conflict detected between '{existing.normalized_value}' and '{c.normalized_value}'"
                    )

                # Prefer gemini structured extraction or higher confidence
                if c.extraction_method == "gemini_structured_extraction" or c.confidence > existing.confidence:
                    chosen = c
                else:
                    chosen = existing

                chosen.conflicts = all_conflicts
                if all_conflicts:
                    chosen.verification_status = "candidate"
                unique_map[c.field_name] = chosen

        return list(unique_map.values())

    def _map_key_to_attribute(self, key: str, val: str) -> Tuple[Optional[str], Optional[str]]:
        """Map raw specification keys to standard LOV attributes."""
        k = key.lower().strip()
        v = val.strip()

        # 1. Fitting Type
        if any(w in k for w in ["fitting type", "product type", "item type", "fitting style"]):
            if "90" in v and "elbow" in v.lower():
                return "Fitting Type", "90 deg Elbow"
            elif "45" in v and "elbow" in v.lower():
                return "Fitting Type", "45 deg Elbow"
            elif "tee" in v.lower():
                return "Fitting Type", "Straight Tee"
            elif "coupling" in v.lower():
                return "Fitting Type", "Coupling"
            elif "cord grip" in v.lower() or "cord connector" in v.lower():
                return "Fitting Type", "Cord Grip Connector"
            elif "adapter" in v.lower():
                return "Fitting Type", "Male Adapter" if "male" in v.lower() else "Female Adapter"
            elif "union" in v.lower():
                return "Fitting Type", "Union"
            return "Fitting Type", v

        # 2. Connection Type
        if any(w in k for w in ["connection type", "end type", "inlet connection", "joint type", "connection"]):
            if "push" in v.lower():
                return "Connection Type", "Push-to-Connect"
            elif "sweat" in v.lower() or "solder" in v.lower() or "c x c" in v.lower() or "cup" in v.lower():
                return "Connection Type", "Sweat"
            elif "compression" in v.lower():
                return "Connection Type", "Compression"
            elif "male npt" in v.lower() or "mnpt" in v.lower():
                return "Connection Type", "Male NPT"
            elif "female npt" in v.lower() or "fnpt" in v.lower():
                return "Connection Type", "Female NPT"
            elif "flanged" in v.lower():
                return "Connection Type", "Flanged"
            elif "threaded" in v.lower():
                return "Connection Type", "Threaded"
            return "Connection Type", v

        # 3. Nominal Size / Pipe Size
        if any(w in k for w in ["nominal size", "pipe size", "tube size", "fitting size", "inlet size"]):
            m = re.search(r"(\d+(?:-\d+/\d+|\s+\d+/\d+|/\d+)?)\s*(?:in|\"|inch)?", v, re.IGNORECASE)
            if m:
                raw_s = m.group(1).replace(" ", "-")
                return "Nominal Size", f"{raw_s} in"
            return "Nominal Size", v

        # 4. Pressure Rating / Working Pressure
        if any(w in k for w in ["pressure rating", "max pressure", "working pressure", "rated pressure", "cwp"]):
            m = re.search(r"(\d+)\s*(?:psi|cwp)?", v, re.IGNORECASE)
            if m:
                return "Pressure Rating", f"{m.group(1)} psi"
            return "Pressure Rating", v

        # 5. Faucet Type & Flow Rate
        if any(w in k for w in ["faucet type", "spout type", "configuration"]):
            if "pulldown" in v.lower() or "pull-down" in v.lower() or "pull down" in v.lower():
                return "Faucet Type", "Pull-Down Faucet"
            elif "pullout" in v.lower() or "pull-out" in v.lower():
                return "Faucet Type", "Pull-Out Faucet"
            elif "single hole" in v.lower() or "single-hole" in v.lower():
                return "Faucet Type", "Single-Hole Faucet"
            return "Faucet Type", v

        if any(w in k for w in ["flow rate", "max flow rate", "gpm"]):
            m = re.search(r"(\d+(?:\.\d+)?)\s*(?:gpm)?", v, re.IGNORECASE)
            if m:
                return "Flow Rate", f"{m.group(1)} gpm"
            return "Flow Rate", v

        # 6. Material / Finish
        if any(w in k for w in ["material", "body material", "tub material", "interior material"]):
            vl = v.lower()
            if "copper" in vl:
                return "Material", "Copper"
            elif "brass" in vl:
                return "Material", "Brass"
            elif "stainless" in vl:
                return "Material", "Stainless Steel"
            elif "aluminum" in vl:
                return "Material", "Aluminum"
            elif "pvc" in vl:
                return "Material", "PVC"
            elif "cast iron" in vl:
                return "Material", "Cast Iron"
            elif "plastic" in vl:
                return "Material", "Plastic"
            return "Material", v

        if any(w in k for w in ["finish", "color"]):
            return "Color / Finish", v

        # 7. Electrical & Appliances
        if any(w in k for w in ["voltage", "volts", "rated voltage"]):
            m = re.search(r"(\d+)\s*v", v, re.IGNORECASE)
            return "Voltage", f"{m.group(1)} V" if m else ("120 V" if "120" in v else v)

        if any(w in k for w in ["amperage", "amps", "circuit", "amperes"]):
            m = re.search(r"(\d+)\s*a", v, re.IGNORECASE)
            return "Amps", f"{m.group(1)} A" if m else ("15 A" if "15" in v else v)

        if any(w in k for w in ["sound level", "decibel", "dba", "noise level"]):
            m = re.search(r"(\d+)\s*dba", v, re.IGNORECASE)
            return "Sound Level", f"{m.group(1)} dBA" if m else v

        if any(w in k for w in ["wash cycles", "number of cycles", "cycles"]):
            m = re.search(r"(\d+)", v)
            return "Wash Cycles", m.group(1) if m else v

        if any(w in k for w in ["mounting", "installation type"]):
            if "built-in" in v.lower() or "builtin" in v.lower():
                return "Mounting Type", "Built-In"
            elif "freestanding" in v.lower():
                return "Mounting Type", "Freestanding"
            elif "deck" in v.lower():
                return "Mounting Type", "Deck"
            elif "wall" in v.lower():
                return "Mounting Type", "Wall"
            return "Mounting Type", v

        if "warranty" in k:
            return "Warranty", v

        if any(w in k for w in ["energy star", "efficiency rating"]):
            return "Energy Star Qualified", "Yes" if any(y in v.lower() for y in ["yes", "certified", "qualified", "true"]) else "No"

        return None, None

    def _extract_from_text(
        self,
        chunk: EvidenceChunk,
        entry: Any,
        now_ts: str,
        ai_unavailable: bool = False
    ) -> List[ExtractedCandidate]:
        """Extract patterns from unstructured chunk text as deterministic baseline."""
        results: List[ExtractedCandidate] = []
        text = chunk.text_content

        # Sound level pattern e.g. 47 dBA
        snd_m = re.search(r"\b(\d{2})\s*(?:dBA|dB)\b", text, re.IGNORECASE)
        if snd_m:
            results.append(
                ExtractedCandidate(
                    field_name="Sound Level",
                    candidate_value=snd_m.group(0),
                    normalized_value=f"{snd_m.group(1)} dBA",
                    source_url=entry.url,
                    source_type=entry.source_type,
                    source_title=entry.title or "Official Specifications",
                    source_page_or_section=chunk.section_title,
                    evidence_excerpt=text[max(0, snd_m.start() - 20):min(len(text), snd_m.end() + 20)],
                    extraction_method="deterministic_rule",
                    retrieved_at=now_ts,
                    confidence=0.95,
                    verification_status="verified",
                    dictionary_identity="UniCat Controlled Vocabulary (LOV)",
                    chunk_id=chunk.chunk_id,
                    source_hash=chunk.chunk_hash,
                    ai_extraction_unavailable=ai_unavailable
                )
            )

        # Voltage pattern
        volt_m = re.search(r"\b(120|240)\s*V\b", text, re.IGNORECASE)
        if volt_m:
            results.append(
                ExtractedCandidate(
                    field_name="Voltage",
                    candidate_value=volt_m.group(0),
                    normalized_value=f"{volt_m.group(1)} V",
                    source_url=entry.url,
                    source_type=entry.source_type,
                    source_title=entry.title or "Official Specifications",
                    source_page_or_section=chunk.section_title,
                    evidence_excerpt=text[max(0, volt_m.start() - 20):min(len(text), volt_m.end() + 20)],
                    extraction_method="deterministic_rule",
                    retrieved_at=now_ts,
                    confidence=0.95,
                    verification_status="verified",
                    dictionary_identity="UniCat Controlled Vocabulary (LOV)",
                    chunk_id=chunk.chunk_id,
                    source_hash=chunk.chunk_hash,
                    ai_extraction_unavailable=ai_unavailable
                )
            )

        return results
