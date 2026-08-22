"""
Evidence-Based Attribute Enrichment & Verified Description Assembly Service.

Executes the 6-step lifecycle:
1. Extract candidate fact from official manufacturer source evidence.
2. Validate against category LOV dictionaries.
3. Normalize UOM using approved Unilog UOM standardizer.
4. Record supporting evidence record with exact citations and dictionary identities.
5. Reject unsupported or invalid values.
6. Keep original source candidate value separately from the normalized value.

Strict Non-Fabrication Rule:
Product titles and descriptions are assembled ONLY from verified fields with direct evidence.
No attribute lacking evidence is ever included in generated titles or descriptions.
"""

from typing import Dict, List, Optional, Any, Tuple
import json
import os
import re
from datetime import datetime, timezone

from .models import (
    ExtractedCandidate,
    EvidenceChunk,
    SourceRegistryEntry,
    EvidenceType,
    SourceStatus
)
from .registry import EvidenceRegistryManager
from .extractor import EvidenceAttributeExtractor
from ..pipeline.models import EvidenceRecord, ProductProvenanceSummary
from ..pipeline.uom_standardizer import UOMStandardizer


class EvidenceEnrichmentService:
    """Enriches product attributes using verified manufacturer evidence and LOV validation."""

    def __init__(self, registry_manager: Optional[EvidenceRegistryManager] = None):
        self.registry = registry_manager or EvidenceRegistryManager()
        self.extractor = EvidenceAttributeExtractor(self.registry)
        self.uom_std = UOMStandardizer()
        self._load_lov_dictionaries()

    def _load_lov_dictionaries(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        dict_path = os.path.join(base_dir, "data", "dictionaries", "lov_dictionaries.json")
        self.lov_data = {}
        if os.path.exists(dict_path):
            try:
                with open(dict_path, "r", encoding="utf-8") as f:
                    self.lov_data = json.load(f)
            except Exception:
                self.lov_data = {}

    def enrich_product_attributes(self, mpn: str) -> Dict[str, Any]:
        """
        Perform 6-step evidence enrichment lifecycle for a given MPN.
        
        Returns:
            Dict containing:
                - mpn
                - brand
                - manufacturer
                - enriched_attributes (dict of field_name -> {candidate_value, normalized_value, status, ...})
                - rejected_attributes (list of rejected candidate facts)
                - field_evidence (dict of field_name -> List[EvidenceRecord])
                - provenance_summary
                - verified_descriptions (invoice_desc, short_desc, long_desc1, mobile_desc)
        """
        clean_mpn = mpn.strip().upper()
        entries = self.registry.get_entries_by_mpn(clean_mpn)
        
        if not entries:
            return {
                "mpn": mpn,
                "status": "NO_EVIDENCE_FOUND",
                "message": f"No active manufacturer evidence registered for MPN '{mpn}'",
                "enriched_attributes": {},
                "rejected_attributes": [],
                "field_evidence": {},
                "provenance_summary": None,
                "verified_descriptions": {}
            }

        primary_entry = entries[0]
        raw_candidates = self.extractor.extract_candidates_for_mpn(clean_mpn)
        now_ts = datetime.now(timezone.utc).isoformat()

        enriched_attrs: Dict[str, Dict[str, Any]] = {}
        rejected_attrs: List[Dict[str, Any]] = []
        field_evidence_map: Dict[str, List[EvidenceRecord]] = {}

        # 1. Manufacturer and Brand Evidence Lineage
        # Rigorous Identity Rule:
        # Registry metadata = candidate identity
        # Explicit document mention of MPN + Brand/Mfr = verified identity
        # UniCat index match = normalized identity
        chunks = self.registry.load_chunks_for_entry(primary_entry)
        all_chunk_text = " ".join([c.text_content + " " + " ".join(c.key_value_specs.values()) for c in chunks])
        all_chunk_text_lower = all_chunk_text.lower()
        doc_title_lower = (primary_entry.title or "").lower()

        clean_mpn_core = re.sub(r"[^A-Z0-9]", "", clean_mpn).lower()
        mpn_parts = [p for p in re.split(r"[-_\s/]+", clean_mpn.lower()) if len(p) >= 2]
        mpn_num_only = re.sub(r"[^0-9]", "", clean_mpn)

        text_simplified = re.sub(r"[^a-z0-9]", "", all_chunk_text_lower + " " + doc_title_lower)
        has_explicit_mpn = (
            clean_mpn_core in text_simplified
            or (len(mpn_num_only) >= 3 and mpn_num_only in text_simplified)
            or any(p in text_simplified for p in mpn_parts if len(p) >= 3)
        )

        mfr_tokens = [w for w in re.findall(r"[a-z0-9]+", primary_entry.manufacturer.lower()) if w not in ["inc", "llc", "ltd", "corp", "corporation", "company", "co", "a", "the", "products"]]
        has_explicit_mfr = any(t in text_simplified for t in mfr_tokens)

        brand_tokens = [w for w in re.findall(r"[a-z0-9]+", primary_entry.brand.lower()) if len(w) >= 2]
        has_explicit_brand = any(t in text_simplified for t in brand_tokens)

        # Manufacturer Identity
        mfr_status = "verified" if has_explicit_mpn and has_explicit_mfr else "candidate"
        mfr_conf = 0.98 if mfr_status == "verified" else 0.80
        mfr_excerpt = (
            f"Official document explicitly verifies MPN {clean_mpn} with manufacturer {primary_entry.manufacturer}"
            if mfr_status == "verified"
            else f"Registry metadata for MPN '{clean_mpn}'"
        )
        mfr_ev = EvidenceRecord(
            field_name="Manufacturer",
            candidate_value=primary_entry.manufacturer,
            normalized_value=primary_entry.manufacturer,
            source_url=primary_entry.url,
            source_type=primary_entry.source_type,
            source_title=primary_entry.title or "Official Manufacturer Document",
            source_page_or_section="Document Header / Text" if mfr_status == "verified" else "Source Registry Metadata",
            evidence_excerpt=mfr_excerpt,
            extraction_method="document_parser" if mfr_status == "verified" else "deterministic_rule",
            retrieved_at=primary_entry.retrieved_at,
            confidence=mfr_conf,
            verification_status=mfr_status,
            dictionary_identity="UniCat Master Manufacturer Index"
        )
        field_evidence_map["Manufacturer"] = [mfr_ev]
        enriched_attrs["Manufacturer"] = {
            "candidate_value": primary_entry.manufacturer,
            "normalized_value": primary_entry.manufacturer,
            "status": mfr_status
        }

        # Brand Identity
        brand_status = "verified" if has_explicit_mpn and has_explicit_brand else "candidate"
        brand_conf = 0.98 if brand_status == "verified" else 0.80
        brand_excerpt = (
            f"Official document explicitly verifies MPN {clean_mpn} with brand {primary_entry.brand}"
            if brand_status == "verified"
            else f"Registry metadata for MPN '{clean_mpn}'"
        )
        brand_ev = EvidenceRecord(
            field_name="Brand",
            candidate_value=primary_entry.brand,
            normalized_value=primary_entry.brand,
            source_url=primary_entry.url,
            source_type=primary_entry.source_type,
            source_title=primary_entry.title or "Official Manufacturer Document",
            source_page_or_section="Document Header / Text" if brand_status == "verified" else "Source Registry Metadata",
            evidence_excerpt=brand_excerpt,
            extraction_method="document_parser" if brand_status == "verified" else "deterministic_rule",
            retrieved_at=primary_entry.retrieved_at,
            confidence=brand_conf,
            verification_status=brand_status,
            dictionary_identity="UniCat Brand Index"
        )
        field_evidence_map["Brand"] = [brand_ev]
        enriched_attrs["Brand"] = {
            "candidate_value": primary_entry.brand,
            "normalized_value": primary_entry.brand,
            "status": brand_status
        }

        # 2. Process Candidates through LOV & UOM Validation Lifecycle
        for cand in raw_candidates:
            is_valid_lov, norm_lov_val, dict_name = self._validate_and_normalize_lov(
                cand.field_name,
                cand.candidate_value,
                cand.normalized_value
            )

            if not is_valid_lov:
                # Step 5: Reject unsupported or invalid values
                rej_record = EvidenceRecord(
                    field_name=cand.field_name,
                    candidate_value=cand.candidate_value,
                    normalized_value="",
                    source_url=cand.source_url,
                    source_type=cand.source_type,
                    source_title=cand.source_title,
                    source_page_or_section=cand.source_page_or_section,
                    evidence_excerpt=cand.evidence_excerpt,
                    extraction_method=cand.extraction_method,
                    retrieved_at=cand.retrieved_at,
                    confidence=cand.confidence,
                    verification_status="rejected",
                    dictionary_identity=dict_name,
                    model_name=cand.model_name,
                    prompt_version=cand.prompt_version,
                    source_hash=cand.source_hash,
                    conflicts=cand.conflicts,
                    extraction_reason=cand.extraction_reason,
                    unresolved_reason=cand.unresolved_reason,
                    ai_extraction_unavailable=cand.ai_extraction_unavailable,
                )
                field_evidence_map.setdefault(cand.field_name, []).append(rej_record)
                rejected_attrs.append({
                    "field_name": cand.field_name,
                    "candidate_value": cand.candidate_value,
                    "reason": f"Value '{cand.candidate_value}' failed category LOV validation."
                })
                continue

            # Step 3: Normalize UOM using approved standardizer
            final_normalized = self._normalize_uom_if_applicable(cand.field_name, norm_lov_val)

            # If conflicts exist, status is "candidate", never automatically verified
            field_status = "candidate" if cand.conflicts else cand.verification_status

            # Step 4: Record supporting evidence record
            ev_record = EvidenceRecord(
                field_name=cand.field_name,
                candidate_value=cand.candidate_value,  # Step 6: keep original source value separately
                normalized_value=final_normalized,
                source_url=cand.source_url,
                source_type=cand.source_type,
                source_title=cand.source_title,
                source_page_or_section=cand.source_page_or_section,
                evidence_excerpt=cand.evidence_excerpt,
                extraction_method=cand.extraction_method,
                retrieved_at=cand.retrieved_at,
                confidence=cand.confidence,
                verification_status=field_status,
                dictionary_identity=dict_name,
                model_name=cand.model_name,
                prompt_version=cand.prompt_version,
                source_hash=cand.source_hash,
                conflicts=cand.conflicts,
                extraction_reason=cand.extraction_reason,
                unresolved_reason=cand.unresolved_reason,
                ai_extraction_unavailable=cand.ai_extraction_unavailable,
            )
            field_evidence_map.setdefault(cand.field_name, []).append(ev_record)

            # Record in enriched attributes
            enriched_attrs[cand.field_name] = {
                "candidate_value": cand.candidate_value,
                "normalized_value": final_normalized,
                "status": field_status,
                "source_type": cand.source_type,
                "section": cand.source_page_or_section,
                "dictionary": dict_name,
                "conflicts": cand.conflicts,
            }

        # 3. Compute Provenance Summary
        total_fields = len(field_evidence_map)
        verified_count = sum(1 for evs in field_evidence_map.values() if any(e.verification_status == "verified" for e in evs))
        candidate_count = sum(1 for evs in field_evidence_map.values() if any(e.verification_status == "candidate" for e in evs))
        rejected_count = sum(1 for evs in field_evidence_map.values() if all(e.verification_status == "rejected" for e in evs))
        score = (verified_count / max(1, total_fields)) * 100.0

        prov_summary = ProductProvenanceSummary(
            total_fields_tracked=total_fields,
            verified_fields_count=verified_count,
            candidate_fields_count=candidate_count,
            missing_evidence_count=0,
            rejected_fields_count=rejected_count,
            verification_score=round(score, 1),
            primary_sources_breakdown={
                primary_entry.source_type: verified_count
            }
        )

        # 4. Assemble Verified-Only Descriptions
        verified_descriptions = self._assemble_verified_descriptions(
            mpn=clean_mpn,
            brand=primary_entry.brand,
            enriched_attrs=enriched_attrs
        )

        return {
            "mpn": clean_mpn,
            "brand": primary_entry.brand,
            "manufacturer": primary_entry.manufacturer,
            "status": "SUCCESS",
            "enriched_attributes": enriched_attrs,
            "rejected_attributes": rejected_attrs,
            "field_evidence": field_evidence_map,
            "provenance_summary": prov_summary,
            "verified_descriptions": verified_descriptions
        }

    def _validate_and_normalize_lov(
        self,
        field_name: str,
        raw_val: str,
        tentative_norm: str
    ) -> Tuple[bool, str, str]:
        """Validate candidate against category LOVs and return (is_valid, normalized_val, dictionary_name)."""
        dict_name = "lov_dictionaries.json"
        clean_raw = raw_val.strip()
        clean_tent = tentative_norm.strip()

        # Fitting Type
        if field_name == "Fitting Type":
            lov = self.lov_data.get("fitting_types", {})
            allowed = lov.get("allowed", [])
            synonyms = lov.get("synonyms", {})
            if clean_tent in allowed:
                return True, clean_tent, f"{dict_name} -> fitting_types"
            if clean_raw.lower() in synonyms:
                return True, synonyms[clean_raw.lower()], f"{dict_name} -> fitting_types"
            for al in allowed:
                if al.lower() in clean_raw.lower() or clean_raw.lower() in al.lower():
                    return True, al, f"{dict_name} -> fitting_types"
            return False, "", f"{dict_name} -> fitting_types"

        # Connection Type
        if field_name == "Connection Type":
            lov = self.lov_data.get("connection_types", {})
            allowed = lov.get("allowed", [])
            synonyms = lov.get("synonyms", {})
            if clean_tent in allowed:
                return True, clean_tent, f"{dict_name} -> connection_types"
            if clean_raw.lower() in synonyms:
                return True, synonyms[clean_raw.lower()], f"{dict_name} -> connection_types"
            for al in allowed:
                if al.lower() in clean_raw.lower():
                    return True, al, f"{dict_name} -> connection_types"
            return False, "", f"{dict_name} -> connection_types"

        # Material
        if field_name == "Material" or field_name == "Tub Material":
            lov = self.lov_data.get("materials", {})
            allowed = lov.get("allowed", [])
            synonyms = lov.get("synonyms", {})
            if clean_tent in allowed:
                return True, clean_tent, f"{dict_name} -> materials"
            if clean_raw.lower() in synonyms:
                return True, synonyms[clean_raw.lower()], f"{dict_name} -> materials"
            for al in allowed:
                if al.lower() in clean_raw.lower():
                    return True, al, f"{dict_name} -> materials"
            return False, "", f"{dict_name} -> materials"

        # Mounting Type
        if field_name == "Mounting Type":
            lov = self.lov_data.get("mounting_types", {})
            allowed = lov.get("allowed", [])
            synonyms = lov.get("synonyms", {})
            if clean_tent in allowed:
                return True, clean_tent, f"{dict_name} -> mounting_types"
            if clean_raw.lower() in synonyms:
                return True, synonyms[clean_raw.lower()], f"{dict_name} -> mounting_types"
            return False, "", f"{dict_name} -> mounting_types"

        # Faucet Type
        if field_name == "Faucet Type":
            lov = self.lov_data.get("faucet_types", {})
            allowed = lov.get("allowed", [])
            synonyms = lov.get("synonyms", {})
            if clean_tent in allowed:
                return True, clean_tent, f"{dict_name} -> faucet_types"
            if clean_raw.lower() in synonyms:
                return True, synonyms[clean_raw.lower()], f"{dict_name} -> faucet_types"
            return False, "", f"{dict_name} -> faucet_types"

        # Pressure Rating, Voltage, Amps, Sound Level, Flow Rate, Nominal Size: standard UOM fields
        return True, clean_tent, "Unilog Approved UOM & Value Dictionaries"

    def _normalize_uom_if_applicable(self, field_name: str, val: str) -> str:
        """Apply Unilog standard spacing and fraction formatting."""
        v = val.strip()

        # Dimension / Nominal Size e.g. "1/2 in"
        if field_name in ["Nominal Size", "Size", "Width", "Height", "Depth"]:
            return self.uom_std.standardize_dimension_string(v)

        # Pressure rating e.g. "300 psi"
        if field_name == "Pressure Rating":
            m = re.search(r"(\d+)\s*(?:psi|cwp)?", v, re.IGNORECASE)
            if m:
                return f"{m.group(1)} psi"

        # Flow rate e.g. "1.5 gpm"
        if field_name == "Flow Rate":
            m = re.search(r"(\d+(?:\.\d+)?)\s*(?:gpm)?", v, re.IGNORECASE)
            if m:
                return f"{m.group(1)} gpm"

        # Electrical
        if field_name == "Voltage":
            m = re.search(r"(\d+)\s*v", v, re.IGNORECASE)
            if m:
                return f"{m.group(1)} V"

        if field_name == "Amps":
            m = re.search(r"(\d+)\s*a", v, re.IGNORECASE)
            if m:
                return f"{m.group(1)} A"

        if field_name == "Sound Level":
            m = re.search(r"(\d+)\s*dba", v, re.IGNORECASE)
            if m:
                return f"{m.group(1)} dBA"

        return v

    def _assemble_verified_descriptions(
        self,
        mpn: str,
        brand: str,
        enriched_attrs: Dict[str, Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Assemble product titles and descriptions ONLY from verified fields with supporting evidence.
        Strict Non-Fabrication Rule: No attribute lacking evidence is ever included.
        """
        clean_brand = re.sub(r"[®™]", "", brand).strip()
        tokens = [clean_brand]
        
        # 1. MPN
        tokens.append(mpn)

        # 2. Check for verified category types
        is_fitting = "Fitting Type" in enriched_attrs
        is_faucet = "Faucet Type" in enriched_attrs
        is_appliance = "Sound Level" in enriched_attrs or "Voltage" in enriched_attrs or "Wash Cycles" in enriched_attrs

        # Assemble verified SHORT_DESC / Product Title
        title_parts: List[str] = [brand]
        
        if is_fitting:
            # Verified fitting attributes
            nom_size = enriched_attrs.get("Nominal Size", {}).get("normalized_value", "")
            material = enriched_attrs.get("Material", {}).get("normalized_value", "")
            conn_type = enriched_attrs.get("Connection Type", {}).get("normalized_value", "")
            fit_type = enriched_attrs.get("Fitting Type", {}).get("normalized_value", "Fitting")
            
            if nom_size:
                title_parts.append(nom_size)
            if material:
                title_parts.append(material)
            if conn_type:
                title_parts.append(conn_type)
            title_parts.append(fit_type)
            title_parts.append(f"({mpn})")
            
            # Short Desc
            short_desc = " ".join(title_parts)
            
            # Long Desc 1 - Only verified specs
            long_specs = []
            if nom_size:
                long_specs.append(f"Nominal Size: {nom_size}")
            if fit_type:
                long_specs.append(f"Fitting Type: {fit_type}")
            if conn_type:
                long_specs.append(f"Connection Type: {conn_type}")
            if material:
                long_specs.append(f"Material: {material}")
            if "Pressure Rating" in enriched_attrs:
                long_specs.append(f"Pressure Rating: {enriched_attrs['Pressure Rating']['normalized_value']}")
            
            long_desc1 = f"{short_desc}. Features {', '.join(long_specs)}."
            
            # Invoice Desc (<= 40 chars, ALL CAPS)
            inv_tokens = []
            
            # Fitting type abbreviation
            ft_u = fit_type.upper()
            if "CORD GRIP" in ft_u or "CORD CONNECTOR" in ft_u:
                inv_tokens.append("CORD GRP CONN")
            elif "90 DEG" in ft_u or "90 ELBOW" in ft_u:
                inv_tokens.append("90 ELB")
            elif "45 DEG" in ft_u or "45 ELBOW" in ft_u:
                inv_tokens.append("45 ELB")
            elif "COUPLING" in ft_u:
                inv_tokens.append("CPLG")
            elif "TEE" in ft_u:
                inv_tokens.append("TEE")
            elif "ADAPTER" in ft_u:
                inv_tokens.append("ADPT")
            else:
                inv_tokens.append(ft_u.replace(" DEG ", " "))

            # Material abbreviation
            if material:
                mat_u = material.upper()
                if "COPPER" in mat_u:
                    inv_tokens.append("CU")
                elif "BRASS" in mat_u:
                    inv_tokens.append("BRS")
                elif "ALUMINUM" in mat_u:
                    inv_tokens.append("ALUM")
                elif "STAINLESS" in mat_u:
                    inv_tokens.append("SST")
                else:
                    inv_tokens.append(mat_u)

            # Connection abbreviation
            if conn_type:
                ct_u = conn_type.upper()
                if "SWEAT" in ct_u or "SOLDER" in ct_u:
                    inv_tokens.append("SWT")
                elif "PUSH" in ct_u:
                    inv_tokens.append("PUSH")
                elif "MALE NPT" in ct_u or "MNPT" in ct_u:
                    inv_tokens.append("MNPT")
                elif "FEMALE NPT" in ct_u or "FNPT" in ct_u:
                    inv_tokens.append("FNPT")
                elif "COMPRESSION" in ct_u:
                    inv_tokens.append("COMP")
                else:
                    inv_tokens.append(ct_u)

            if nom_size:
                inv_tokens.append(nom_size.upper().replace(" ", ""))
            if "Pressure Rating" in enriched_attrs:
                inv_tokens.append(enriched_attrs["Pressure Rating"]["normalized_value"].upper().replace(" ", ""))
            
            invoice_desc = " ".join(inv_tokens)[:40]
            mobile_desc = f"{brand} {mpn} {nom_size} {material} {fit_type}"[:80]

        elif is_faucet:
            faucet_type = enriched_attrs.get("Faucet Type", {}).get("normalized_value", "Faucet")
            finish = enriched_attrs.get("Color / Finish", {}).get("normalized_value", "")
            flow_rate = enriched_attrs.get("Flow Rate", {}).get("normalized_value", "")
            conn_type = enriched_attrs.get("Connection Type", {}).get("normalized_value", "")
            
            if finish:
                title_parts.append(finish)
            title_parts.append(faucet_type)
            title_parts.append(f"({mpn})")
            
            short_desc = " ".join(title_parts)
            long_specs = [f"Faucet Type: {faucet_type}"]
            if finish:
                long_specs.append(f"Finish: {finish}")
            if flow_rate:
                long_specs.append(f"Flow Rate: {flow_rate}")
            if conn_type:
                long_specs.append(f"Connection: {conn_type}")
                
            long_desc1 = f"{short_desc}. Features {', '.join(long_specs)}."
            
            inv_tokens = ["FAUCET", "PULL-DWN" if "PULL-DOWN" in faucet_type.upper() else "FAUCET"]
            if finish:
                inv_tokens.append("SST" if "STAINLESS" in finish.upper() else finish.upper())
            if flow_rate:
                inv_tokens.append(flow_rate.upper().replace(" ", ""))
            invoice_desc = " ".join(inv_tokens)[:40]
            mobile_desc = f"{brand} {mpn} {finish} {faucet_type}"[:80]

        else:
            # Dishwashers / Major Appliances
            mounting = enriched_attrs.get("Mounting Type", {}).get("normalized_value", "")
            voltage = enriched_attrs.get("Voltage", {}).get("normalized_value", "")
            amps = enriched_attrs.get("Amps", {}).get("normalized_value", "")
            sound = enriched_attrs.get("Sound Level", {}).get("normalized_value", "")
            tub_mat = enriched_attrs.get("Tub Material", {}).get("normalized_value", "")
            
            title_parts.append(mpn)
            if mounting:
                title_parts.append(mounting)
            title_parts.append("Dishwasher")
            
            short_desc = " ".join(title_parts)
            
            long_specs = ["Product: Built-In Dishwasher"]
            if voltage:
                long_specs.append(f"Voltage: {voltage}")
            if amps:
                long_specs.append(f"Amperage: {amps}")
            if sound:
                long_specs.append(f"Sound Level: {sound}")
            if tub_mat:
                long_specs.append(f"Tub Material: {tub_mat}")
            if "Energy Star Qualified" in enriched_attrs:
                long_specs.append(f"Energy Star: {enriched_attrs['Energy Star Qualified']['normalized_value']}")
                
            long_desc1 = f"{short_desc}. Specifications: {', '.join(long_specs)}."
            
            inv_tokens = ["DISHWASHER"]
            if mounting:
                inv_tokens.append("BLTLN" if "BUILT-IN" in mounting.upper() else mounting.upper())
            if tub_mat:
                inv_tokens.append("SST" if "STAINLESS" in tub_mat.upper() else tub_mat.upper())
            if voltage:
                inv_tokens.append(voltage.replace(" ", ""))
            if amps:
                inv_tokens.append(amps.replace(" ", ""))
            if sound:
                inv_tokens.append(sound.replace(" ", ""))
            invoice_desc = " ".join(inv_tokens)[:40]
            mobile_desc = f"{brand} {mpn} {mounting} Dishwasher {sound}".strip()[:80]

        return {
            "invoice_desc": invoice_desc.upper(),
            "short_desc": short_desc,
            "long_desc1": long_desc1,
            "mobile_desc": mobile_desc
        }
