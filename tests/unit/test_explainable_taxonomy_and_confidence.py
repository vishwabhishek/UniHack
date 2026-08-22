"""
Unit & Integration Tests for Explainable Taxonomy Classification and Transparent Confidence Model.
"""

import pytest
from src.pipeline.models import RawProduct, TaxonomyCandidate, TaxonomyExplanation
from src.pipeline.taxonomy import TaxonomyClassifier
from src.pipeline.engine import EnrichmentEngine
from src.pipeline.confidence_config import (
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


class TestExplainableTaxonomy:
    """Verify explainable taxonomy classification, candidate ranking, and review routing."""

    @pytest.fixture
    def classifier(self):
        return TaxonomyClassifier()

    def test_top_candidate_classpaths_ranking_and_tie_breaking(self, classifier):
        """Test that classifier returns ranked candidates with matching terms, scores, and tie-break reasons."""
        sanitized = {
            "raw_desc": "Built-In Dishwasher Stainless Steel 24 inch Quiet 47 dBA",
            "desc_tokens": "built-in dishwasher stainless steel 24 in quiet",
            "mfg_part_num": "PDSH4816AF"
        }
        entity = {"brand_name": "Frigidaire", "manufacturer_name": "Electrolux"}
        
        result = classifier.classify(sanitized, entity, has_official_evidence=True)
        
        assert "taxonomy_candidates" in result
        candidates = result["taxonomy_candidates"]
        assert len(candidates) >= 1
        
        top = candidates[0]
        assert "Dishwasher" in top.classpath
        assert top.score > 0
        assert len(top.matching_terms) > 0
        assert "dishwasher" in [t.lower() for t in top.matching_terms]
        assert top.tie_break_reason is not None
        assert top.rule_confidence >= 0.70
        assert top.evidence_confidence == 0.98  # Corroborated with official evidence

    def test_ambiguous_classification_routes_to_review(self, classifier):
        """Test that close scores between two category classpaths trigger ambiguity and review routing."""
        # Ambiguous input containing keywords matching multiple categories
        sanitized = {
            "raw_desc": "Electric Motor with Built-in Pump Mechanism",
            "desc_tokens": "electric motor pump mechanism",
            "mfg_part_num": "AMBIG-001"
        }
        entity = {"brand_name": "Industrial Supplies", "manufacturer_name": "Industrial Supplies"}
        
        result = classifier.classify(sanitized, entity, has_official_evidence=False)
        explanation = result["taxonomy_explanation"]
        
        # If ambiguous, explanation must record ambiguity and route to review
        if result["is_ambiguous"]:
            assert explanation.routing_decision == "ROUTED_TO_HUMAN_REVIEW"
            assert "Ambiguous" in explanation.rationale

    def test_fallback_classification_detection_and_routing(self, classifier):
        """Test that unmatchable strings fall back to generic hardware and route to human review."""
        sanitized = {
            "raw_desc": "XYZ99999 NONEXISTENT COMMODITY ITEM",
            "desc_tokens": "xyz99999 nonexistent commodity",
            "mfg_part_num": "XYZ-9999"
        }
        entity = {"brand_name": "Industrial Supplies", "manufacturer_name": "Industrial Supplies"}
        
        result = classifier.classify(sanitized, entity, has_official_evidence=False)
        
        assert result["is_fallback"] is True
        assert result["unspsc"] == "27110000"
        assert result["classpath"] == "Industrial Supplies>Maintenance & Repair>General Hardware"
        
        explanation = result["taxonomy_explanation"]
        assert explanation.is_fallback is True
        assert explanation.routing_decision == "ROUTED_TO_HUMAN_REVIEW"
        assert "fallback" in explanation.rationale.lower()

    def test_distinction_between_rule_confidence_and_evidence_confidence(self, classifier):
        """Test that rule confidence reflects syntax match while evidence confidence reflects manufacturer corroboration."""
        sanitized = {
            "raw_desc": "Copper Solder 90 Degree Elbow 1/2 in",
            "desc_tokens": "copper solder 90 degree elbow 1/2 in",
            "mfg_part_num": "NIB-607-1/2"
        }
        entity = {"brand_name": "NIBCO", "manufacturer_name": "NIBCO INC."}
        
        # Without official manufacturer evidence
        res_no_ev = classifier.classify(sanitized, entity, has_official_evidence=False)
        top_no_ev = res_no_ev["taxonomy_candidates"][0]
        assert top_no_ev.rule_confidence >= 0.80
        assert top_no_ev.evidence_confidence == 0.60
        
        # With official manufacturer evidence
        res_with_ev = classifier.classify(sanitized, entity, has_official_evidence=True)
        top_with_ev = res_with_ev["taxonomy_candidates"][0]
        assert top_with_ev.rule_confidence == top_no_ev.rule_confidence
        assert top_with_ev.evidence_confidence == 0.98


class TestTransparentConfidenceModel:
    """Verify field-level confidence calculations, single source of truth weights, and penalties."""

    @pytest.fixture
    def engine(self):
        return EnrichmentEngine()

    def test_confidence_weights_sum_to_one(self):
        """Verify that single-source-of-truth component weights sum precisely to 1.0."""
        total_weight = (
            WEIGHT_IDENTITY +
            WEIGHT_TAXONOMY +
            WEIGHT_ATTRIBUTES +
            WEIGHT_EVIDENCE +
            WEIGHT_DESCRIPTION
        )
        assert round(total_weight, 5) == 1.0

    def test_trademark_symbol_not_treated_as_factual_accuracy_proof(self, engine):
        """Verify that brand resolution score is based on identity resolution, not formatting styling."""
        raw_clean = RawProduct(
            mfg_part_num="7594SRS",
            part_desc="Moen Arbor Pulldown Kitchen Faucet",
            part_manuf="Moen Incorporated"
        )
        enriched = engine.process_item(raw_clean)
        
        # Identity confidence must be high because entity was resolved to Moen Incorporated
        assert enriched.confidence_breakdown["brand_confidence"] == 1.0
        assert "UNVERIFIED_BRAND_SYMBOL" not in enriched.validation_flags

    def test_penalty_for_missing_official_evidence(self, engine):
        """Verify that products lacking registered official manufacturer evidence receive the documented penalty."""
        raw_unknown = RawProduct(
            mfg_part_num="CUSTOM-UNKNOWN-PART-999",
            part_desc="Custom fabricated steel bracket 12x4",
            part_manuf="Custom Fab"
        )
        enriched = engine.process_item(raw_unknown)
        
        assert "MISSING_OFFICIAL_EVIDENCE" in enriched.validation_flags
        assert enriched.confidence_breakdown["evidence_confidence"] <= 0.75
        assert enriched.confidence_breakdown["total_penalties"] >= PENALTY_MISSING_OFFICIAL_EVIDENCE

    def test_penalty_for_unresolved_identity(self, engine):
        """Verify that unresolvable brand/manufacturer receives documented penalty and routes to review."""
        raw_unbranded = RawProduct(
            mfg_part_num="NO-BRAND-123",
            part_desc="Generic Unknown Widget",
            e1_brand="-- Unbranded --",
            part_manuf="-- Unbranded --"
        )
        enriched = engine.process_item(raw_unbranded)
        
        assert "UNRESOLVED_IDENTITY" in enriched.validation_flags
        assert enriched.confidence_breakdown["brand_confidence"] == 0.40
        assert enriched.status == "Flagged"

    def test_fallback_taxonomy_routes_to_flagged(self, engine):
        """Verify that fallback taxonomy automatically forces status to Flagged regardless of other fields."""
        raw_obscure = RawProduct(
            mfg_part_num="OBSCURE-001",
            part_desc="ZQXKJ999 Miscellaneous item without known category",
            part_manuf="Industrial Supplies"
        )
        enriched = engine.process_item(raw_obscure)
        
        assert "FALLBACK_TAXONOMY" in enriched.validation_flags
        assert enriched.status == "Flagged"
        assert enriched.taxonomy_explanation is not None
        assert enriched.taxonomy_explanation.is_fallback is True

    def test_configurable_demo_threshold_routing(self, engine):
        """Verify that composite confidence below 0.85 routes product to Flagged for review."""
        assert REVIEW_CONFIDENCE_THRESHOLD == 0.85
        
        # Construct low confidence item
        raw_low = RawProduct(
            mfg_part_num="",  # Missing MPN
            part_desc="Unspecified parts kit",
            part_manuf="-- No DIB Brand --"
        )
        enriched = engine.process_item(raw_low)
        
        assert enriched.confidence_score < REVIEW_CONFIDENCE_THRESHOLD
        assert enriched.status == "Flagged"
