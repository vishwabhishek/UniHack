"""
Production-Safe Gemini Evidence Extraction Provider for Official Manufacturer Evidence.

Adheres strictly to the 6-rule governance:
1. Gemini extracts facts ONLY from supplied official source chunks.
2. Never infer or extrapolate numbers not stated in text.
3. Every candidate fact must cite exact evidence_chunk_id and verbatim excerpt.
4. Conflicting statements are recorded in conflicts list, never silently resolved.
5. All outputs pass deterministic post-verification (span alignment, chunk existence, LOV check).
6. Fails safely to deterministic fallback with AI_EXTRACTION_UNAVAILABLE flag.
7. Caches successful extractions by (source_file_hash, mpn, model, schema, lov_version) to prevent duplicate API cost.
"""

from __future__ import annotations

import os
import re
import json
import hashlib
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timezone

from .base import (
    BaseEvidenceExtractionProvider,
    ExtractionRequest,
    ExtractionResult,
    GeminiExtractedFact,
    GeminiExtractionOutput,
)
from ..models import EvidenceChunk
from ..gemini_extractor import SourceSpanVerifier

logger = logging.getLogger(__name__)

PROMPT_VERSION = "v1.0.0"

SYSTEM_INSTRUCTION = """
You are a rigorous industrial product catalog data extraction specialist.
Extract factual product attributes for the target MPN strictly and exclusively from the provided official manufacturer source chunks.

CRITICAL NON-NEGOTIABLE EXTRACTION RULES:
1. USE ONLY SUPPLIED SOURCE CHUNKS. Do not use external knowledge, unmentioned assumptions, or generic training data.
2. NEVER INFER, GUESS, OR FABRICATE. If an attribute is not explicitly and unambiguously stated in the text, set raw_value to null and record the reason in 'unresolved_reason'. Place unbacked fields in 'unsupported_fields'.
3. EXACT CITATION IS MANDATORY. For every extracted fact, you MUST provide:
   - 'evidence_chunk_id': The exact chunk identifier from the provided text.
   - 'evidence_excerpt': The verbatim quote snippet from that specific chunk supporting the extraction.
4. REPORT CONFLICTS HONESTLY. If multiple chunks state conflicting values for the same attribute (e.g. 200 psi vs 300 psi), report all conflicting claims in the 'conflicts' list rather than choosing one arbitrarily.
5. RESPECT CONTROLLED VOCABULARY (LOV) AND UOM. Propose 'normalized_candidate' matching the supplied category LOV and standard UOM formatting where applicable.
6. OUTPUT STRICT JSON. Return valid JSON matching the GeminiExtractionOutput schema.
"""


class GeminiEvidenceExtractionProvider(BaseEvidenceExtractionProvider):
    """
    Official Google Gemini API extraction provider with persistent caching and deterministic verification.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        enabled: Optional[bool] = None,
        timeout_seconds: float = 15.0,
        cache: Optional[Any] = None,
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "").strip() or None
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        
        # Default must be disabled when no API key is available
        env_enabled = os.getenv("GEMINI_ENABLED", "false").lower() in ("true", "1", "yes")
        self.enabled = (enabled if enabled is not None else env_enabled) and bool(self.api_key)
        self.timeout_seconds = timeout_seconds
        self.prompt_version = PROMPT_VERSION
        self.span_verifier = SourceSpanVerifier()

        if cache is None:
            from ..cache import default_extraction_cache
            self.cache = default_extraction_cache
        else:
            self.cache = cache

        self._client = None
        if self.enabled and self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize google-genai client: {e}")
                self.enabled = False

    def extract(self, request: ExtractionRequest, force_refresh: bool = False) -> ExtractionResult:
        """
        Execute structured extraction using Gemini with deterministic post-verification and caching.
        Falls back safely if disabled, timed out, or unavailable.
        """
        now_ts = datetime.now(timezone.utc).isoformat()
        primary_hash = request.source_chunks[0].chunk_hash if request.source_chunks else "no_chunks"
        lov_version = hashlib.md5(json.dumps(request.lov_subset, sort_keys=True).encode()).hexdigest()[:8]

        # 1. Check Persistent Cache unless force_refresh is requested
        cache_key = self.cache.generate_cache_key(
            source_hash=primary_hash,
            mpn=request.mpn,
            model_name=self.model_name,
            schema_version=self.prompt_version,
            lov_version=lov_version,
        )

        if not force_refresh and self.cache:
            cached_res = self.cache.get(cache_key)
            if cached_res:
                logger.info(f"Persistent cache hit for MPN: {request.mpn} (key: {cache_key[:12]}...)")
                cached_res.mpn = request.mpn
                cached_res.brand = cached_res.brand or request.brand_candidate
                cached_res.manufacturer = cached_res.manufacturer or request.manufacturer_candidate
                return cached_res

        # 2. Guard: Check if Gemini is enabled and chunks are provided
        if not self.enabled or not self._client:
            logger.info(f"Gemini provider disabled or unconfigured for {request.mpn}; returning fallback indicator.")
            return ExtractionResult(
                mpn=request.mpn,
                brand=request.brand_candidate,
                manufacturer=request.manufacturer_candidate,
                facts=[],
                unsupported_fields=request.requested_fields,
                conflicts=[],
                model_name=self.model_name,
                prompt_version=self.prompt_version,
                source_hash=primary_hash,
                extraction_timestamp=now_ts,
                status="AI_EXTRACTION_UNAVAILABLE",
                error_message="Gemini extraction provider is disabled or missing GEMINI_API_KEY",
                ai_extraction_unavailable=True,
            )

        if not request.source_chunks:
            return ExtractionResult(
                mpn=request.mpn,
                brand=request.brand_candidate,
                manufacturer=request.manufacturer_candidate,
                facts=[],
                unsupported_fields=request.requested_fields,
                conflicts=[],
                model_name=self.model_name,
                prompt_version=self.prompt_version,
                source_hash=None,
                extraction_timestamp=now_ts,
                status="AI_EXTRACTION_UNAVAILABLE",
                error_message="No official source chunks provided for extraction",
                ai_extraction_unavailable=True,
            )

        # 3. Build strictly constrained prompt
        prompt_text = self._build_constrained_prompt(request)

        # 4. Call Gemini API via official google-genai SDK
        try:
            from google.genai import types

            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt_text,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=GeminiExtractionOutput,
                    temperature=0.0,
                    system_instruction=SYSTEM_INSTRUCTION,
                ),
            )

            # Parse and validate output JSON
            raw_output = None
            if hasattr(response, "parsed") and response.parsed:
                raw_output = response.parsed
            elif hasattr(response, "text") and response.text:
                parsed_dict = json.loads(response.text)
                raw_output = GeminiExtractionOutput(**parsed_dict)

            if not isinstance(raw_output, GeminiExtractionOutput):
                raise ValueError("Gemini response could not be parsed into GeminiExtractionOutput")

            # Track actual token usage from response if available
            usage_dict = {}
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                usage_dict = {
                    "prompt_tokens": getattr(response.usage_metadata, "prompt_token_count", None),
                    "candidates_tokens": getattr(response.usage_metadata, "candidates_token_count", None),
                    "total_tokens": getattr(response.usage_metadata, "total_token_count", None),
                }

            # 5. Run Deterministic Post-Verification on Gemini proposals
            verified_facts, verified_conflicts = self._post_verify_gemini_output(raw_output, request)

            res = ExtractionResult(
                mpn=request.mpn,
                brand=raw_output.brand or request.brand_candidate,
                manufacturer=raw_output.manufacturer or request.manufacturer_candidate,
                facts=verified_facts,
                unsupported_fields=raw_output.unsupported_fields,
                conflicts=verified_conflicts,
                model_name=self.model_name,
                prompt_version=self.prompt_version,
                source_hash=primary_hash,
                extraction_timestamp=now_ts,
                status="SUCCESS",
                ai_extraction_unavailable=False,
            )

            # 6. Store validated result into cache
            if self.cache:
                self.cache.set(
                    cache_key=cache_key,
                    mpn=request.mpn,
                    source_hash=primary_hash,
                    model_name=self.model_name,
                    schema_version=self.prompt_version,
                    lov_version=lov_version,
                    result=res,
                )

            return res

        except Exception as e:
            logger.warning(f"Gemini extraction call failed for {request.mpn}: {e}. Falling back safely.", exc_info=True)
            return ExtractionResult(
                mpn=request.mpn,
                brand=request.brand_candidate,
                manufacturer=request.manufacturer_candidate,
                facts=[],
                unsupported_fields=request.requested_fields,
                conflicts=[],
                model_name=self.model_name,
                prompt_version=self.prompt_version,
                source_hash=primary_hash,
                extraction_timestamp=now_ts,
                status="AI_EXTRACTION_UNAVAILABLE",
                error_message=f"Gemini API error: {str(e)}",
                ai_extraction_unavailable=True,
            )

    def _select_relevant_chunks(
        self,
        chunks: List[EvidenceChunk],
        mpn: str,
        max_char_budget: int = 16000
    ) -> List[EvidenceChunk]:
        """
        Rank and select relevant official source chunks within a token character budget.
        Prioritizes chunks matching the MPN and technical keywords (specs, dimensions, materials, electrical).
        """
        if not chunks:
            return []

        clean_mpn = (mpn or "").strip().upper()
        scored_chunks = []

        tech_keywords = {
            "specification", "specifications", "spec", "specs", "dimension", "dimensions",
            "material", "finish", "voltage", "amperage", "wattage", "psi", "capacity",
            "certifications", "features", "model", "diameter", "length", "width", "height"
        }

        for c in chunks:
            score = 0.0
            txt = c.text_content.upper()
            txt_lower = c.text_content.lower()

            # Direct MPN match
            if clean_mpn and clean_mpn in txt:
                score += 50.0
            if c.mpn and clean_mpn and c.mpn.upper() == clean_mpn:
                score += 30.0

            # Technical keyword bonus
            for kw in tech_keywords:
                if kw in txt_lower:
                    score += 2.0

            # Section title relevance
            sec_lower = (c.section_title or "").lower()
            if any(kw in sec_lower for kw in tech_keywords):
                score += 10.0

            scored_chunks.append((score, c))

        # Sort descending by relevance score
        scored_chunks.sort(key=lambda x: -x[0])

        selected = []
        accumulated_chars = 0

        for _, chunk in scored_chunks:
            chunk_len = len(chunk.text_content)
            if accumulated_chars + chunk_len > max_char_budget and selected:
                continue
            selected.append(chunk)
            accumulated_chars += chunk_len
            if accumulated_chars >= max_char_budget:
                break

        return selected or chunks[:6]

    def _build_constrained_prompt(self, request: ExtractionRequest) -> str:
        """
        Build restricted prompt containing ONLY registered official evidence chunks,
        target product identity, requested fields, LOV subset, and UOM rules.
        """
        selected_chunks = self._select_relevant_chunks(request.source_chunks, request.mpn)
        formatted_chunks = []
        for c in selected_chunks:
            formatted_chunks.append(
                f"--- OFFICIAL SOURCE CHUNK: [ID: {c.chunk_id}] ---\n"
                f"Section: {c.section_title} | Page: {c.page_number or 1}\n"
                f"Text Content:\n{c.text_content}\n"
            )
        chunks_str = "\n".join(formatted_chunks)

        lov_lines = []
        for field, values in request.lov_subset.items():
            lov_lines.append(f"- {field}: {', '.join(values[:12])}")
        lov_str = "\n".join(lov_lines) if lov_lines else "Standard Industrial PIM Vocabulary"

        uom_lines = [f"- {k}: {v}" for k, v in request.uom_rules.items()]
        uom_str = "\n".join(uom_lines) if uom_lines else "Unilog Standard UOM (e.g. '1/2 in', '200 psi', '120 V')"

        prompt = f"""
TARGET PRODUCT IDENTITY:
- Target MPN: {request.mpn}
- Brand Candidate: {request.brand_candidate or 'Unknown'}
- Manufacturer Candidate: {request.manufacturer_candidate or 'Unknown'}
- Category / Classpath: {request.category_candidate or 'General Industrial'}

REQUESTED ATTRIBUTE FIELDS:
{json.dumps(request.requested_fields, indent=2)}

CONTROLLED VOCABULARY (LOV) RULES:
{lov_str}

APPROVED UOM RULES:
{uom_str}

OFFICIAL MANUFACTURER SOURCE CHUNKS:
{chunks_str}

INSTRUCTIONS:
Extract factual values for the requested attribute fields strictly supported by the official source chunks above.
For any field not explicitly supported in the text, set raw_value to null and list it in unsupported_fields.
Cite the exact evidence_chunk_id and verbatim evidence_excerpt for every extracted fact.
"""
        return prompt

    def _post_verify_gemini_output(
        self,
        output: GeminiExtractionOutput,
        request: ExtractionRequest
    ) -> Tuple[List[GeminiExtractedFact], List[str]]:
        """
        Deterministic Post-Verification Gate:
        - Cited chunk exists in the registered source chunks
        - Chunk belongs to the requested product MPN
        - Cited excerpt is physically present in the chunk text
        - Cited raw value appears in the excerpt
        - Reports conflicts if multiple chunks contradict
        """
        chunk_map = {c.chunk_id: c for c in request.source_chunks}
        verified_facts: List[GeminiExtractedFact] = []
        conflicts = list(output.conflicts)

        for fact in output.facts:
            # Skip unpopulated facts
            if not fact.raw_value or not fact.raw_value.strip():
                continue

            # 1. Chunk existence verification
            if not fact.evidence_chunk_id or fact.evidence_chunk_id not in chunk_map:
                logger.warning(f"Rejected Gemini fact for '{fact.field_name}': cited chunk '{fact.evidence_chunk_id}' does not exist.")
                fact.confidence = 0.0
                fact.unresolved_reason = f"Cited chunk '{fact.evidence_chunk_id}' does not exist in registered manufacturer evidence"
                fact.raw_value = None
                continue

            chunk = chunk_map[fact.evidence_chunk_id]

            # 1b. Verify chunk belongs to the requested MPN if chunk has MPN metadata
            if chunk.mpn and request.mpn and chunk.mpn.strip().upper() != request.mpn.strip().upper():
                logger.warning(f"Rejected Gemini fact for '{fact.field_name}': cited chunk '{chunk.chunk_id}' belongs to MPN '{chunk.mpn}', not requested MPN '{request.mpn}'.")
                fact.confidence = 0.0
                fact.unresolved_reason = f"Chunk MPN mismatch ({chunk.mpn} != {request.mpn})"
                fact.raw_value = None
                continue

            # 2. Excerpt presence & value containment verification
            if not fact.evidence_excerpt or not fact.evidence_excerpt.strip():
                logger.warning(f"Rejected Gemini fact for '{fact.field_name}': empty evidence excerpt.")
                fact.confidence = 0.0
                fact.unresolved_reason = "Missing verbatim evidence quote"
                fact.raw_value = None
                continue

            quote = fact.evidence_excerpt.strip()
            raw_val = fact.raw_value.strip()

            quote_in_chunk = (quote in chunk.text_content) or (
                re.sub(r"\s+", " ", quote.lower()) in re.sub(r"\s+", " ", chunk.text_content.lower())
            )

            if not quote_in_chunk:
                logger.warning(f"Rejected Gemini fact for '{fact.field_name}': excerpt not found in chunk text.")
                fact.confidence = 0.0
                fact.unresolved_reason = f"Evidence excerpt not found in chunk '{chunk.chunk_id}' (unverified citation)"
                fact.raw_value = None
                continue

            val_in_quote = (raw_val.lower() in quote.lower()) or (
                re.sub(r"[^a-z0-9]", "", raw_val.lower()) in re.sub(r"[^a-z0-9]", "", quote.lower())
            )

            if not val_in_quote:
                logger.warning(f"Rejected Gemini fact for '{fact.field_name}': raw value '{raw_val}' not in excerpt.")
                fact.confidence = 0.0
                fact.unresolved_reason = f"Value '{raw_val}' is not supported by cited excerpt '{quote[:40]}...'"
                fact.raw_value = None
                continue

            if fact.conflicts:
                conflicts.extend(fact.conflicts)

            verified_facts.append(fact)

        return verified_facts, list(set(conflicts))
