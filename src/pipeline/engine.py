"""
Master Pipeline Orchestrator & Batch Processing Engine.
"""

import time
from typing import Dict, Any, List, Optional, Callable, Tuple
from .models import RawProduct, EnrichedProduct, AttributeTriple, PhysicalDimensions
from .sanitizer import ProductSanitizer
from .entity_resolver import EntityResolver
from .taxonomy import TaxonomyClassifier
from .attribute_extractor import AttributeExtractor
from .uom_standardizer import UOMStandardizer
from .description_generator import DescriptionGenerator
from .delivery_mapper import DeliveryMapper, to_delivery_dict


class EnrichmentEngine:
    """Master orchestrator executing the 7-stage PIM enrichment pipeline."""

    def __init__(self, dictionaries_dir: Optional[str] = None):
        self.sanitizer = ProductSanitizer()
        self.resolver = EntityResolver()
        self.taxonomy = TaxonomyClassifier()
        self.extractor = AttributeExtractor()
        self.uom_std = UOMStandardizer()
        self.desc_gen = DescriptionGenerator()
        self.mapper = DeliveryMapper()

    def process_item(self, raw: RawProduct) -> EnrichedProduct:
        """Execute full multi-stage enrichment on a single raw product."""
        # Stage 1: Ingestion & Sanitization
        sanitized = self.sanitizer.sanitize(raw)
        
        # Stage 2: Canonical Brand & Manufacturer Resolution
        entity = self.resolver.resolve(sanitized)
        
        # Check if official registered manufacturer evidence exists
        if not hasattr(self, "evidence_service") or self.evidence_service is None:
            from ..evidence.enrichment_service import EvidenceEnrichmentService
            self.evidence_service = EvidenceEnrichmentService()

        mpn_key = sanitized.get("mfg_part_num", "")
        has_evidence = bool(mpn_key and self.evidence_service.registry.get_entries_by_mpn(mpn_key))

        # Stage 3: Explainable Taxonomy & UNSPSC Classification
        tax = self.taxonomy.classify(sanitized, entity, has_official_evidence=has_evidence)
        
        # Stage 4 & 5: Attribute Extraction & LOV / UOM Standardization
        attr_data = self.extractor.extract(sanitized, entity, tax)
        
        # Stage 6: 5-Tier Description Generation
        descriptions = self.desc_gen.generate_all(sanitized, entity, tax, attr_data)
        
        # Quality & Transparent Confidence Scoring
        confidence, breakdown, flags = self._compute_confidence(
            sanitized, entity, tax, attr_data, descriptions, has_official_evidence=has_evidence
        )
        
        from .confidence_config import REVIEW_CONFIDENCE_THRESHOLD
        status = "Flagged" if (
            confidence < REVIEW_CONFIDENCE_THRESHOLD
            or "AMBIGUOUS_TAXONOMY" in flags
            or "FALLBACK_TAXONOMY" in flags
            or "UNRESOLVED_IDENTITY" in flags
        ) else "Enriched"

        # Field-level traceable evidence and provenance mapping
        from .models import EvidenceRecord, FieldProvenance, ProductProvenanceSummary, SourceType, ExtractionMethod, VerificationStatus
        from datetime import datetime, timezone
        now_ts = datetime.now(timezone.utc).isoformat()

        field_evidence: Dict[str, List[EvidenceRecord]] = {}
        field_provenance: Dict[str, FieldProvenance] = {}

        def add_evidence(
            field_name: str,
            candidate_val: str,
            normalized_val: str,
            source_type: str,
            source_title: str,
            extraction_method: str,
            confidence: float,
            verification_status: str,
            dictionary_identity: Optional[str] = None,
            source_url: Optional[str] = None,
            section: Optional[str] = None,
            excerpt: Optional[str] = None
        ):
            rec = EvidenceRecord(
                field_name=field_name,
                candidate_value=candidate_val or "",
                normalized_value=normalized_val or "",
                source_url=source_url,
                source_type=source_type,
                source_title=source_title,
                source_page_or_section=section,
                evidence_excerpt=excerpt or f"Extracted from {source_title}",
                extraction_method=extraction_method,
                retrieved_at=now_ts,
                confidence=confidence,
                verification_status=verification_status,
                dictionary_identity=dictionary_identity
            )
            if field_name not in field_evidence:
                field_evidence[field_name] = []
            field_evidence[field_name].append(rec)

            # Backward compatibility field_provenance
            field_provenance[field_name] = FieldProvenance(
                field_name=field_name,
                source_url=source_url,
                source_type=source_type,
                extraction_method=extraction_method,
                section_or_rule=section or dictionary_identity,
                timestamp=now_ts,
                confidence=confidence,
                verified=(verification_status == VerificationStatus.VERIFIED.value)
            )

        # 1. MPN
        raw_mpn = sanitized.get("mfg_part_num", "")
        add_evidence(
            field_name="mfg_part_number",
            candidate_val=raw.mfg_part_num or raw_mpn,
            normalized_val=raw_mpn,
            source_type=SourceType.SUPPLIER_INPUT.value,
            source_title="Distributor Input Feed",
            extraction_method=ExtractionMethod.DETERMINISTIC_RULE.value,
            confidence=1.0 if raw_mpn else 0.4,
            verification_status=VerificationStatus.VERIFIED.value if raw_mpn else VerificationStatus.MISSING_EVIDENCE.value,
            section="Mfg_Part_Num column"
        )

        # 2. Brand Name (Multi-record: supplier string -> canonical dictionary)
        raw_b = raw.part_manuf or raw.e1_brand or ""
        norm_b = entity.get("brand_name", "")
        is_b_verified = bool(norm_b and "®" in norm_b or "™" in norm_b)
        add_evidence(
            field_name="brand_name",
            candidate_val=raw_b,
            normalized_val=raw_b,
            source_type=SourceType.SUPPLIER_INPUT.value,
            source_title="Distributor Input Feed",
            extraction_method=ExtractionMethod.DETERMINISTIC_RULE.value,
            confidence=0.80,
            verification_status=VerificationStatus.CANDIDATE.value,
            section="Part_Manuf / Brand feed"
        )
        add_evidence(
            field_name="brand_name",
            candidate_val=raw_b,
            normalized_val=norm_b,
            source_type=SourceType.REFERENCE_DICTIONARY.value,
            source_title="UniCat Brand Master Index",
            extraction_method=ExtractionMethod.DETERMINISTIC_RULE.value,
            confidence=breakdown.get("brand_confidence", 0.9),
            verification_status=VerificationStatus.VERIFIED.value if is_b_verified else VerificationStatus.CANDIDATE.value,
            dictionary_identity="UniCat_Manufacturer_and_Brand_List.json",
            section="Master Brand Registry"
        )

        # 3. Manufacturer Name
        raw_m = raw.part_manuf or ""
        norm_m = entity.get("manufacturer_name", "")
        is_m_verified = bool(norm_m and norm_m != "Industrial Supplies")
        add_evidence(
            field_name="manufacturer_name",
            candidate_val=raw_m,
            normalized_val=norm_m,
            source_type=SourceType.REFERENCE_DICTIONARY.value,
            source_title="UniCat Manufacturer Master Index",
            extraction_method=ExtractionMethod.DETERMINISTIC_RULE.value,
            confidence=breakdown.get("brand_confidence", 0.9),
            verification_status=VerificationStatus.VERIFIED.value if is_m_verified else VerificationStatus.CANDIDATE.value,
            dictionary_identity="UniCat_Manufacturer_and_Brand_List.json"
        )

        # 4. Classpath & UNSPSC
        norm_cp = tax.get("classpath", "")
        norm_unspsc = tax.get("unspsc", "")
        is_tax_verified = bool(norm_unspsc and norm_unspsc != "27110000")
        add_evidence(
            field_name="classpath",
            candidate_val=raw.part_desc,
            normalized_val=norm_cp,
            source_type=SourceType.REFERENCE_DICTIONARY.value,
            source_title="Unicat Taxonomy Classification Hierarchy",
            extraction_method=ExtractionMethod.DETERMINISTIC_RULE.value,
            confidence=breakdown.get("taxonomy_confidence", 0.9),
            verification_status=VerificationStatus.VERIFIED.value if is_tax_verified else VerificationStatus.CANDIDATE.value,
            dictionary_identity="Unicat_Lov_v1_0_Updated_With_Remarks.json",
            section="Dept > Class > Fine Classification"
        )
        add_evidence(
            field_name="unspsc",
            candidate_val=raw.part_desc,
            normalized_val=norm_unspsc,
            source_type=SourceType.REFERENCE_DICTIONARY.value,
            source_title="UNSPSC Master Codebook v24.0",
            extraction_method=ExtractionMethod.DETERMINISTIC_RULE.value,
            confidence=breakdown.get("taxonomy_confidence", 0.9),
            verification_status=VerificationStatus.VERIFIED.value if is_tax_verified else VerificationStatus.CANDIDATE.value,
            dictionary_identity="UNSPSC_Codebook_v24.json"
        )

        # 5. Descriptions (Rule generated = candidate status per Rule 6)
        for desc_key, desc_label in [
            ("invoice_desc", "INVOICE_DESC (<=40 ALL CAPS)"),
            ("mobile_desc", "MOBILE_DESC (60-80 chars)"),
            ("short_desc", "SHORT_DESC (Product Title)"),
            ("long_desc1", "LONG_DESC1 (Technical Spec Sentence)"),
        ]:
            val = descriptions.get(desc_key, "")
            add_evidence(
                field_name=desc_key,
                candidate_val=raw.part_desc,
                normalized_val=val,
                source_type=SourceType.SUPPLIER_INPUT.value,
                source_title="Unilog Content Synthesis Engine",
                extraction_method=ExtractionMethod.DETERMINISTIC_RULE.value,
                confidence=breakdown.get("description_compliance", 0.95),
                verification_status=VerificationStatus.CANDIDATE.value,  # Formatting rules do NOT confer verified status
                section=desc_label
            )

        # 6. Extracted Attributes & LOV Normalization
        normalized_attributes = []
        for attr in attr_data.get("attributes", []):
            if attr.value:
                ev_rec = EvidenceRecord(
                    field_name=f"attr_{attr.label}",
                    candidate_value=attr.value,
                    normalized_value=attr.value,
                    source_type=SourceType.REFERENCE_DICTIONARY.value,
                    source_title="UniCat Controlled Vocabulary (LOV)",
                    extraction_method=ExtractionMethod.DETERMINISTIC_RULE.value,
                    retrieved_at=now_ts,
                    confidence=0.95,
                    verification_status=VerificationStatus.VERIFIED.value,
                    dictionary_identity="lov_dictionaries.json",
                    source_page_or_section=f"LOV Category: {attr.label}"
                )
                attr.evidence_records = [ev_rec]
                if f"attr_{attr.label}" not in field_evidence:
                    field_evidence[f"attr_{attr.label}"] = []
                field_evidence[f"attr_{attr.label}"].append(ev_rec)
                
                attr_prov = FieldProvenance(
                    field_name=attr.label,
                    source_type="reference_dictionary",
                    extraction_method="deterministic_rule",
                    section_or_rule="lov_dictionaries.json",
                    timestamp=now_ts,
                    confidence=0.95,
                    verified=True
                )
                attr.provenance = attr_prov
                field_provenance[f"attr_{attr.label}"] = attr_prov
            else:
                if attr.label:
                    ev_rec = EvidenceRecord(
                        field_name=f"attr_{attr.label}",
                        candidate_value="",
                        normalized_value="",
                        source_type=SourceType.SUPPLIER_INPUT.value,
                        source_title="Distributor Input Feed",
                        extraction_method=ExtractionMethod.DETERMINISTIC_RULE.value,
                        retrieved_at=now_ts,
                        confidence=0.5,
                        verification_status=VerificationStatus.MISSING_EVIDENCE.value,
                        source_page_or_section="Attribute Slot Unpopulated"
                    )
                    attr.evidence_records = [ev_rec]
            normalized_attributes.append(attr)

        # 7. Unverified commercial & digital asset fields
        add_evidence(
            field_name="country_of_origin",
            candidate_val="",
            normalized_val="",
            source_type=SourceType.SUPPLIER_INPUT.value,
            source_title="Distributor Feed",
            extraction_method=ExtractionMethod.DETERMINISTIC_RULE.value,
            confidence=0.0,
            verification_status=VerificationStatus.MISSING_EVIDENCE.value,
            section="Country Of Origin"
        )
        add_evidence(
            field_name="product_image",
            candidate_val="",
            normalized_val="",
            source_type=SourceType.SUPPLIER_INPUT.value,
            source_title="Digital Asset Registry",
            extraction_method=ExtractionMethod.DETERMINISTIC_RULE.value,
            confidence=0.0,
            verification_status=VerificationStatus.MISSING_EVIDENCE.value,
            section="Product Image"
        )

        # 8. Check and integrate registered official manufacturer evidence
        if hasattr(self, "evidence_service") and self.evidence_service is None:
            from ..evidence.enrichment_service import EvidenceEnrichmentService
            self.evidence_service = EvidenceEnrichmentService()
        elif not hasattr(self, "evidence_service"):
            from ..evidence.enrichment_service import EvidenceEnrichmentService
            self.evidence_service = EvidenceEnrichmentService()

        mpn_key = sanitized.get("mfg_part_num", "")
        if mpn_key and self.evidence_service.registry.get_entries_by_mpn(mpn_key):
            ev_res = self.evidence_service.enrich_product_attributes(mpn_key)
            if ev_res.get("status") == "SUCCESS":
                # Add manufacturer evidence records
                for f_name, ev_list in ev_res.get("field_evidence", {}).items():
                    field_evidence[f_name] = ev_list

        # Compute ProductProvenanceSummary
        v_count = 0
        c_count = 0
        m_count = 0
        r_count = 0
        src_breakdown: Dict[str, int] = {}

        for fname, records in field_evidence.items():
            primary = records[-1] if records else None
            if primary:
                src_breakdown[primary.source_type] = src_breakdown.get(primary.source_type, 0) + 1
                if primary.verification_status == VerificationStatus.VERIFIED.value:
                    v_count += 1
                elif primary.verification_status == VerificationStatus.CANDIDATE.value:
                    c_count += 1
                elif primary.verification_status == VerificationStatus.MISSING_EVIDENCE.value:
                    m_count += 1
                elif primary.verification_status == VerificationStatus.REJECTED.value:
                    r_count += 1

        total_tracked = len(field_evidence)
        v_score = round(v_count / max(1, (v_count + c_count)), 3)

        provenance_summary = ProductProvenanceSummary(
            total_fields_tracked=total_tracked,
            verified_fields_count=v_count,
            candidate_fields_count=c_count,
            missing_evidence_count=m_count,
            rejected_fields_count=r_count,
            verification_score=v_score,
            primary_sources_breakdown=src_breakdown
        )

        # IDs & Codes
        part_num = f"{20000000 + (raw.row_id or 1000)}"
        sku = f"{1500000 + (raw.row_id or 1000)}"

        # Digital Assets & Commercial Facts: strictly empty unless verified from evidence
        product_image = ""
        alt_images: List[str] = []
        documents: Dict[str, str] = {}
        actual_image = "No"
        country_of_origin = ""  # Never invent country of origin without evidence

        # Assemble Enriched Product
        enriched = EnrichedProduct(
            field_evidence=field_evidence,
            provenance_summary=provenance_summary,
            field_provenance=field_provenance,
            part_number=part_num,
            sku=sku,
            mfg_part_number=sanitized.get("mfg_part_num", ""),
            alternate_part_number="",
            upc="",
            ean="",
            gtin="",
            unspsc=tax.get("unspsc", ""),
            raw=raw,
            dept=tax.get("dept", ""),
            class_name=tax.get("class_name", ""),
            fine=tax.get("fine", ""),
            manufacturer_name=entity.get("manufacturer_name", ""),
            brand_name=entity.get("brand_name", ""),
            trade_name=entity.get("trade_name", ""),
            mfr_url=entity.get("mfr_url", ""),
            ref_urls=[],
            classpath=tax.get("classpath", ""),
            product_name=tax.get("product_name", ""),
            taxonomy_candidates=tax.get("taxonomy_candidates", []),
            taxonomy_explanation=tax.get("taxonomy_explanation"),
            invoice_desc=descriptions.get("invoice_desc", ""),
            mobile_desc=descriptions.get("mobile_desc", ""),
            short_desc=descriptions.get("short_desc", ""),
            long_desc1=descriptions.get("long_desc1", ""),
            retail_desc=descriptions.get("retail_desc", ""),
            marketing_description=descriptions.get("marketing_description", ""),
            item_features=attr_data.get("item_features", []),
            with_spec=attr_data.get("with_spec", ""),
            standard_approvals=attr_data.get("standard_approvals", ""),
            prop_65=attr_data.get("prop_65", ""),
            application=attr_data.get("application", ""),
            includes=attr_data.get("includes", ""),
            attributes=normalized_attributes,
            dimensions=attr_data.get("dimensions", PhysicalDimensions()),
            warranty=attr_data.get("warranty", ""),
            list_price="",
            selling_qty=attr_data.get("selling_qty", "1"),
            selling_uom=attr_data.get("selling_uom", "EA"),
            standard_packaging="",
            country_of_origin=country_of_origin,
            discontinued="No",
            product_image=product_image,
            alternate_images=alt_images,
            actual_image=actual_image,
            documents=documents,
            confidence_score=confidence,
            confidence_breakdown=breakdown,
            validation_flags=flags,
            status=status
        )

        return enriched

    def process_batch(
        self,
        raw_items: List[RawProduct],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[EnrichedProduct]:
        """Batch process a list of raw product items."""
        enriched_list = []
        total = len(raw_items)
        for idx, item in enumerate(raw_items):
            enriched = self.process_item(item)
            enriched_list.append(enriched)
            if progress_callback and (idx + 1) % 50 == 0:
                progress_callback(idx + 1, total)
        if progress_callback:
            progress_callback(total, total)
        return enriched_list

    def _compute_confidence(
        self,
        sanitized: Dict[str, Any],
        entity: Dict[str, str],
        tax: Dict[str, Any],
        attr_data: Dict[str, Any],
        desc: Dict[str, str],
        has_official_evidence: bool = False
    ) -> Tuple[float, Dict[str, float], List[str]]:
        """
        Compute transparent, field-level composite confidence score using documented weights and penalties.
        Weights: Identity (0.25), Taxonomy (0.25), Attributes (0.25), Evidence (0.15), Description (0.10).
        """
        from .confidence_config import (
            WEIGHT_IDENTITY,
            WEIGHT_TAXONOMY,
            WEIGHT_ATTRIBUTES,
            WEIGHT_EVIDENCE,
            WEIGHT_DESCRIPTION,
            PENALTY_MISSING_OFFICIAL_EVIDENCE,
            PENALTY_FALLBACK_TAXONOMY,
            PENALTY_AMBIGUOUS_TAXONOMY,
            PENALTY_UNRESOLVED_IDENTITY,
            PENALTY_LOV_REJECTION,
            REVIEW_CONFIDENCE_THRESHOLD
        )
        
        flags: List[str] = []
        penalties: Dict[str, float] = {}

        # 1. Identity Dimension (Weight: 0.25)
        # Verify master manufacturer/brand resolution (trademark symbol is styling, not factual proof)
        brand_name = entity.get("brand_name", "")
        if not brand_name or "Generic" in brand_name or brand_name == "Industrial Supplies":
            c_identity = 0.40
            flags.append("UNRESOLVED_IDENTITY")
            penalties["UNRESOLVED_IDENTITY"] = PENALTY_UNRESOLVED_IDENTITY
        else:
            c_identity = 1.0

        # 2. Taxonomy Dimension (Weight: 0.25)
        if tax.get("is_fallback") or not tax.get("unspsc") or tax.get("unspsc") == "27110000":
            c_tax = 0.50
            flags.append("FALLBACK_TAXONOMY")
            penalties["FALLBACK_TAXONOMY"] = PENALTY_FALLBACK_TAXONOMY
        elif tax.get("is_ambiguous"):
            c_tax = 0.70
            flags.append("AMBIGUOUS_TAXONOMY")
            penalties["AMBIGUOUS_TAXONOMY"] = PENALTY_AMBIGUOUS_TAXONOMY
        else:
            c_tax = tax.get("rule_confidence", 1.0)

        # 3. Attribute & LOV Dimension (Weight: 0.25)
        extracted_dict = attr_data.get("extracted_dict", {})
        attr_count = len([v for v in extracted_dict.values() if v and v[0]])
        
        if attr_count >= 4:
            c_attr = 1.0
        elif attr_count >= 2:
            c_attr = 0.90
        elif attr_count == 1:
            c_attr = 0.80
            flags.append("LOW_ATTRIBUTE_DENSITY")
        else:
            c_attr = 0.50
            flags.append("MISSING_EVIDENCE")

        # 4. Evidence Dimension (Weight: 0.15)
        if has_official_evidence:
            c_evidence = 1.0
        else:
            c_evidence = 0.70
            flags.append("MISSING_OFFICIAL_EVIDENCE")
            penalties["MISSING_OFFICIAL_EVIDENCE"] = PENALTY_MISSING_OFFICIAL_EVIDENCE

        # 5. Description Schema Compliance (Weight: 0.10)
        c_desc = 1.0
        inv = desc.get("invoice_desc", "")
        mob = desc.get("mobile_desc", "")
        if len(inv) > 40:
            c_desc -= 0.30
            flags.append("INVOICE_DESC_LENGTH_OVERFLOW")
        if not inv.isupper():
            c_desc -= 0.10
            flags.append("INVOICE_DESC_CASING_ERROR")
        if len(mob) < 60 or len(mob) > 80:
            c_desc -= 0.20
            flags.append("MOBILE_DESC_LENGTH_OUT_OF_BOUNDS")
        # 6. Completeness & Digital Asset Verification Flag
        if not sanitized.get("mfg_part_num"):
            flags.append("MISSING_MPN")
        flags.append("UNVERIFIED_ASSET")

        # Composite Calculation: Weighted sum minus active penalties
        raw_weighted_score = (
            WEIGHT_IDENTITY * c_identity +
            WEIGHT_TAXONOMY * c_tax +
            WEIGHT_ATTRIBUTES * c_attr +
            WEIGHT_EVIDENCE * c_evidence +
            WEIGHT_DESCRIPTION * c_desc
        )
        total_penalties = sum(penalties.values())
        composite = round(max(0.0, min(1.0, raw_weighted_score - total_penalties)), 3)

        breakdown = {
            "brand_confidence": round(c_identity, 2),
            "taxonomy_confidence": round(c_tax, 2),
            "attribute_confidence": round(c_attr, 2),
            "evidence_confidence": round(c_evidence, 2),
            "description_compliance": round(c_desc, 2),
            "raw_weighted_score": round(raw_weighted_score, 3),
            "total_penalties": round(total_penalties, 3),
            "composite": composite
        }

        return composite, breakdown, flags
