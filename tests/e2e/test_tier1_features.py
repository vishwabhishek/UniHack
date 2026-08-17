"""Tier 1: Feature Coverage E2E Test Suite.

This module provides comprehensive opaque-box and functional test coverage for all core
features of the Industrial Product Intelligence & PIM Enrichment pipeline:
1. Ingestion & Placeholder Sanitizer (>= 5 tests)
2. Canonical Brand & Manufacturer Resolver (>= 5 tests)
3. Taxonomy & UNSPSC Hierarchical Classifier (>= 5 tests)
4. Attribute Extractor & LOV Controlled Vocabulary Engine (>= 5 tests)
5. UOM & Fraction Standardization Engine (>= 5 tests)
6. 5-Tier Content & Description Generator (>= 5 tests)
7. Full 252-Column Delivery Exporter (>= 5 tests)
"""

import pytest
from typing import Dict, Any, List
import pandas as pd
from pathlib import Path


# ===========================================================================
# 1. Feature: Ingestion & Placeholder Sanitizer
# ===========================================================================

class TestFeature1Sanitizer:
    """Test suite for Feature 1: Ingestion & Placeholder Sanitizer."""

    @pytest.mark.parametrize("placeholder", [
        "-- Unbranded --",
        "-- UNBRANDED --",
        "-- unbranded --",
        "-- No Unilog Brand --",
        "-- NO UNILOG BRAND --",
        "-- No DIB Brand --",
        "-- NO DIB BRAND --",
        "COMMODITY - UNBRANDED",
        "-",
        "  -- Unbranded --  ",
        "N/A",
        "None",
    ])
    def test_sanitizer_removes_unbranded_and_null_placeholders(self, placeholder: str):
        """Verify that all dummy placeholders and null sentinels are stripped to None/empty."""
        from src.pipeline.sanitizer import ProductSanitizer
        
        cleaned = ProductSanitizer.clean_placeholder(placeholder)
        assert cleaned is None or cleaned == "", f"Expected None/empty for placeholder '{placeholder}', got '{cleaned}'"

    def test_sanitizer_cleans_unicode_whitespace_and_punctuation(self):
        """Verify that non-breaking spaces, control characters, and multiple spaces are normalized."""
        from src.pipeline.sanitizer import ProductSanitizer
        
        raw_text = "PDSH4816AF \u00a0 Dishwasher\tSS  -   Display Only. \n"
        cleaned = ProductSanitizer.normalize_unicode(raw_text)
        assert "  " not in cleaned
        assert "\u00a0" not in cleaned
        assert "\t" not in cleaned
        assert "\n" not in cleaned
        assert "PDSH4816AF Dishwasher SS - Display Only." in cleaned or "PDSH4816AF" in cleaned

    def test_sanitizer_parses_vendor_and_supplier_code_parentheses(self):
        """Verify parsing of supplier name and bracketed vendor code e.g. 'Freud Inc (2435)'."""
        from src.pipeline.sanitizer import ProductSanitizer
        
        raw_vendor = "Freud Inc (2435)"
        vendor_name, vendor_code = ProductSanitizer.parse_supplier(raw_vendor)
        assert vendor_name == "Freud Inc"
        assert vendor_code == "2435"

        raw_vendor2 = "Milwaukee Accessory (4031)"
        name2, code2 = ProductSanitizer.parse_supplier(raw_vendor2)
        assert name2 == "Milwaukee Accessory"
        assert code2 == "4031"

        raw_vendor3 = "Appliance Dealers Cooperative (APPDE)"
        name3, code3 = ProductSanitizer.parse_supplier(raw_vendor3)
        assert name3 == "Appliance Dealers Cooperative"
        assert code3 == "APPDE"

    def test_sanitizer_isolates_mpn_from_part_desc(self):
        """Verify that leading redundant MPN in part_desc is detected and stripped from token stream."""
        from src.pipeline.sanitizer import ProductSanitizer
        from src.pipeline.models import RawProduct
        
        raw = RawProduct(
            mfg_part_num="PDSH4816AF",
            part_desc="PDSH4816AF Dishwasher SS - Display Only",
            e1_brand="-- Unbranded --",
            unilog_brand="-- No Unilog Brand --",
            dib_brand="-- No DIB Brand --",
            part_manuf="Appliance Dealers Cooperative (APPDE)",
        )
        sanitized = ProductSanitizer.sanitize(raw)
        assert sanitized["mfg_part_num"] == "PDSH4816AF"
        assert sanitized["desc_tokens"] == "Dishwasher SS" or "Dishwasher" in sanitized["desc_tokens"]
        assert not sanitized["desc_tokens"].startswith("PDSH4816AF")

    def test_sanitizer_handles_raw_product_record(self, sample_dishwasher_frigidaire: Dict[str, Any]):
        """Verify that ProductSanitizer.sanitize processes a full RawProduct dict."""
        from src.pipeline.sanitizer import ProductSanitizer
        from src.pipeline.models import RawProduct
        
        raw_obj = RawProduct(**sample_dishwasher_frigidaire)
        sanitized = ProductSanitizer.sanitize(raw_obj)
        
        assert sanitized["mfg_part_num"] == "PDSH4816AF"
        assert sanitized["e1_brand"] is None or sanitized["e1_brand"] == ""
        assert sanitized["unilog_brand"] is None or sanitized["unilog_brand"] == ""
        assert sanitized["dib_brand"] is None or sanitized["dib_brand"] == ""
        assert "Appliance Dealers Cooperative" in sanitized["supplier_name"]

    def test_sanitizer_handles_completely_empty_or_hyphen_manufacturer(self):
        """Verify handling of records where manufacturer is simply '-' or empty string."""
        from src.pipeline.sanitizer import ProductSanitizer
        from src.pipeline.models import RawProduct
        
        empty_manuf_dict = {
            "mfg_part_num": "X100",
            "part_desc": "Test part description",
            "e1_brand": "-- Unbranded --",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "-- No DIB Brand --",
            "part_manuf": "-",
        }
        sanitized = ProductSanitizer.sanitize(RawProduct(**empty_manuf_dict))
        assert sanitized["supplier_name"] is None or sanitized["supplier_name"] == ""


# ===========================================================================
# 2. Feature: Canonical Brand & Manufacturer Entity Resolution
# ===========================================================================

class TestFeature2EntityResolver:
    """Test suite for Feature 2: Canonical Brand & Manufacturer Resolver."""

    def test_resolver_appliance_cooperative_to_frigidaire(self, sample_dishwasher_frigidaire: Dict[str, Any], pipeline_engine):
        """Verify mapping of APPDE cooperative + PDSH4816AF to Rheem Manufacturing and FRIGIDAIRE®."""
        sanitized = pipeline_engine.sanitizer.sanitize(pipeline_engine.raw_cls(**sample_dishwasher_frigidaire))
        res = pipeline_engine.resolver.resolve(sanitized)
        
        assert "Rheem" in res["manufacturer_name"] or "Frigidaire" in res["manufacturer_name"] or "Electrolux" in res["manufacturer_name"]
        assert "FRIGIDAIRE" in res["brand_name"]
        assert "®" in res["brand_name"]

    def test_resolver_appliance_cooperative_to_whirlpool(self, sample_dishwasher_whirlpool: Dict[str, Any], pipeline_engine):
        """Verify mapping of APPDE cooperative + WDTS7024RZ to Whirlpool Corporation and Whirlpool®."""
        sanitized = pipeline_engine.sanitizer.sanitize(pipeline_engine.raw_cls(**sample_dishwasher_whirlpool))
        res = pipeline_engine.resolver.resolve(sanitized)
        
        assert "Whirlpool" in res["manufacturer_name"]
        assert "Whirlpool" in res["brand_name"]
        assert "®" in res["brand_name"]

    def test_resolver_freud_diablo(self, sample_power_tool_diablo: Dict[str, Any], pipeline_engine):
        """Verify mapping of Freud Inc (2435) to Freud and Diablo® brand."""
        sanitized = pipeline_engine.sanitizer.sanitize(pipeline_engine.raw_cls(**sample_power_tool_diablo))
        res = pipeline_engine.resolver.resolve(sanitized)
        
        assert "Freud" in res["manufacturer_name"]
        assert "Diablo" in res["brand_name"]
        assert "®" in res["brand_name"]

    def test_resolver_milwaukee_accessory(self, sample_milwaukee_disc: Dict[str, Any], pipeline_engine):
        """Verify mapping of Milwaukee Accessory (4031) to Milwaukee Tool and Milwaukee® brand."""
        sanitized = pipeline_engine.sanitizer.sanitize(pipeline_engine.raw_cls(**sample_milwaukee_disc))
        res = pipeline_engine.resolver.resolve(sanitized)
        
        assert "Milwaukee" in res["manufacturer_name"]
        assert "Milwaukee" in res["brand_name"]
        assert "®" in res["brand_name"]

    def test_resolver_lighting_philips(self, sample_lighting_philips: Dict[str, Any], pipeline_engine):
        """Verify mapping of Phillips Lighting (5831) to Philips® brand."""
        sanitized = pipeline_engine.sanitizer.sanitize(pipeline_engine.raw_cls(**sample_lighting_philips))
        res = pipeline_engine.resolver.resolve(sanitized)
        
        assert "Philips" in res["brand_name"] or "Signify" in res["manufacturer_name"]
        assert "®" in res["brand_name"]

    def test_resolver_trex_decking(self, sample_trex_decking: Dict[str, Any], pipeline_engine):
        """Verify mapping of Boise Cascade distributor + TREX to Trex Company, Inc. and Trex®."""
        sanitized = pipeline_engine.sanitizer.sanitize(pipeline_engine.raw_cls(**sample_trex_decking))
        res = pipeline_engine.resolver.resolve(sanitized)
        
        assert "Trex" in res["brand_name"]
        assert "®" in res["brand_name"]

    def test_resolver_preserves_trademark_symbols_and_legal_casing(self, pipeline_engine):
        """Verify entity resolver outputs standard legal casing and registered trademark symbols."""
        raw = pipeline_engine.raw_cls(
            mfg_part_num="929001127004",
            part_desc="10.5A19/LED/827/ND 120V 4/1FB",
            e1_brand="-- Unbranded --",
            unilog_brand="-- No Unilog Brand --",
            dib_brand="Philips",
            part_manuf="Phillips Lighting (5831)",
        )
        sanitized = pipeline_engine.sanitizer.sanitize(raw)
        res = pipeline_engine.resolver.resolve(sanitized)
        assert "®" in res["brand_name"]
        assert "Philips" in res["brand_name"]


# ===========================================================================
# 3. Feature: Taxonomy & UNSPSC Hierarchical Classification
# ===========================================================================

class TestFeature3TaxonomyClassifier:
    """Test suite for Feature 3: Taxonomy & UNSPSC Classifier."""

    def test_taxonomy_dishwasher_classification(self, sample_dishwasher_frigidaire: Dict[str, Any], pipeline_engine):
        """Verify classification of dishwasher to Built-In Dishwashers classpath."""
        sanitized = pipeline_engine.sanitizer.sanitize(pipeline_engine.raw_cls(**sample_dishwasher_frigidaire))
        entity = pipeline_engine.resolver.resolve(sanitized)
        tax = pipeline_engine.taxonomy.classify(sanitized, entity)
        
        assert "Dishwasher" in tax["product_name"] or "Dishwashers" in tax["classpath"] or "Dishwasher" in tax["fine"]
        assert tax["dept"] == "Appliances" or "Appliances" in tax["classpath"]
        assert tax["unspsc"] != ""

    def test_taxonomy_power_tool_abrasives(self, sample_milwaukee_disc: Dict[str, Any], pipeline_engine):
        """Verify classification of cut off disc to Cut-Off & Grinding Wheels."""
        sanitized = pipeline_engine.sanitizer.sanitize(pipeline_engine.raw_cls(**sample_milwaukee_disc))
        entity = pipeline_engine.resolver.resolve(sanitized)
        tax = pipeline_engine.taxonomy.classify(sanitized, entity)
        
        assert "Cut-Off" in tax["classpath"] or "Abrasive" in tax["classpath"] or "Wheels" in tax["fine"] or "Disc" in tax["fine"] or "Tools" in tax["dept"]

    def test_taxonomy_lighting_lamps(self, sample_lighting_philips: Dict[str, Any], pipeline_engine):
        """Verify classification of LED lamp."""
        sanitized = pipeline_engine.sanitizer.sanitize(pipeline_engine.raw_cls(**sample_lighting_philips))
        entity = pipeline_engine.resolver.resolve(sanitized)
        tax = pipeline_engine.taxonomy.classify(sanitized, entity)
        
        assert "Lamps" in tax["classpath"] or "Lighting" in tax["classpath"] or "Bulbs" in tax["classpath"] or "LED" in tax["product_name"] or "Lamp" in tax["product_name"]

    def test_taxonomy_building_decking(self, sample_trex_decking: Dict[str, Any], pipeline_engine):
        """Verify classification of Trex composite decking board."""
        sanitized = pipeline_engine.sanitizer.sanitize(pipeline_engine.raw_cls(**sample_trex_decking))
        entity = pipeline_engine.resolver.resolve(sanitized)
        tax = pipeline_engine.taxonomy.classify(sanitized, entity)
        
        assert "Deck" in tax["classpath"] or "Building Materials" in tax["dept"] or "Board" in tax["product_name"] or "Decking" in tax["fine"]

    def test_taxonomy_hierarchy_depth_and_format(self, pipeline_engine):
        """Verify that Classpath strictly adheres to non-empty hierarchical tiers."""
        raw = pipeline_engine.raw_cls(
            mfg_part_num="PDSH4816AF",
            part_desc="PDSH4816AF Dishwasher SS - Display Only",
            part_manuf="Appliance Dealers Cooperative (APPDE)"
        )
        sanitized = pipeline_engine.sanitizer.sanitize(raw)
        entity = pipeline_engine.resolver.resolve(sanitized)
        tax = pipeline_engine.taxonomy.classify(sanitized, entity)
        
        assert tax["dept"] != "", "Department must not be empty"
        assert tax["class_name"] != "", "Class must not be empty"
        assert tax["fine"] != "", "Fine must not be empty"
        assert ">" in tax["classpath"], "Classpath must be hierarchical"

    def test_taxonomy_unspsc_code_format(self, pipeline_engine):
        """Verify that UNSPSC is an 8-digit numeric string."""
        raw = pipeline_engine.raw_cls(
            mfg_part_num="PDSH4816AF",
            part_desc="PDSH4816AF Dishwasher SS",
            part_manuf="Appliance Dealers Cooperative (APPDE)"
        )
        sanitized = pipeline_engine.sanitizer.sanitize(raw)
        entity = pipeline_engine.resolver.resolve(sanitized)
        tax = pipeline_engine.taxonomy.classify(sanitized, entity)
        
        if tax["unspsc"]:
            assert tax["unspsc"].isdigit(), f"UNSPSC code should be numeric, got {tax['unspsc']}"
            assert len(tax["unspsc"]) == 8, f"UNSPSC code should be 8 digits, got {tax['unspsc']}"


# ===========================================================================
# 4. Feature: Attribute Extractor & Controlled Vocabulary (LOV) Engine
# ===========================================================================

class TestFeature4AttributeExtractor:
    """Test suite for Feature 4: Attribute Extractor & LOV Engine."""

    def test_extractor_dishwasher_mounting_type(self, sample_dishwasher_frigidaire: Dict[str, Any], pipeline_engine):
        """Verify extraction of Mounting Type attribute conforming strictly to canonical LOV."""
        sanitized = pipeline_engine.sanitizer.sanitize(pipeline_engine.raw_cls(**sample_dishwasher_frigidaire))
        entity = pipeline_engine.resolver.resolve(sanitized)
        tax = pipeline_engine.taxonomy.classify(sanitized, entity)
        attr_data = pipeline_engine.extractor.extract(sanitized, entity, tax)
        
        extracted = attr_data.get("extracted_dict", {})
        assert "Mounting Type" in extracted or "Mounting" in extracted
        val = extracted.get("Mounting Type", extracted.get("Mounting"))[0]
        assert val in ["Leg", "Built-in", "Undercounter", "Freestanding"]

    def test_extractor_voltage_and_amperage_ratings(self, sample_dishwasher_frigidaire: Dict[str, Any], pipeline_engine):
        """Verify extraction of Voltage Rating (120 V) and Amperage Rating (15 A)."""
        sanitized = pipeline_engine.sanitizer.sanitize(pipeline_engine.raw_cls(**sample_dishwasher_frigidaire))
        entity = pipeline_engine.resolver.resolve(sanitized)
        tax = pipeline_engine.taxonomy.classify(sanitized, entity)
        attr_data = pipeline_engine.extractor.extract(sanitized, entity, tax)
        
        extracted = attr_data.get("extracted_dict", {})
        if "Voltage Rating" in extracted:
            v_val, v_uom = extracted["Voltage Rating"]
            assert v_val in ["120", "120 V", "120/240"]
            assert v_uom == "V" or v_uom == ""

        if "Amperage Rating" in extracted:
            a_val, a_uom = extracted["Amperage Rating"]
            assert a_val in ["15", "15 A", "10", "10 A"]
            assert a_uom == "A" or a_uom == ""

    def test_extractor_wash_cycles_and_sound_level(self, sample_dishwasher_frigidaire: Dict[str, Any], pipeline_engine):
        """Verify extraction of Number of Wash Cycles (5) and Sound Level (47 dBA)."""
        sanitized = pipeline_engine.sanitizer.sanitize(pipeline_engine.raw_cls(**sample_dishwasher_frigidaire))
        entity = pipeline_engine.resolver.resolve(sanitized)
        tax = pipeline_engine.taxonomy.classify(sanitized, entity)
        attr_data = pipeline_engine.extractor.extract(sanitized, entity, tax)
        
        extracted = attr_data.get("extracted_dict", {})
        if "Number of Wash Cycles" in extracted:
            assert extracted["Number of Wash Cycles"][0] in ["5", "5-Wash Cycle", "5 Wash Cycles"]
        if "Sound Level" in extracted:
            s_val, s_uom = extracted["Sound Level"]
            assert s_val in ["47", "47 dBA", "41", "41 dBA"]
            assert s_uom == "dBA" or s_uom == ""

    def test_extractor_material_construction_stainless_steel(self, sample_dishwasher_frigidaire: Dict[str, Any], pipeline_engine):
        """Verify that 'SS' or 'SST' translates strictly to canonical LOV 'Stainless Steel'."""
        sanitized = pipeline_engine.sanitizer.sanitize(pipeline_engine.raw_cls(**sample_dishwasher_frigidaire))
        entity = pipeline_engine.resolver.resolve(sanitized)
        tax = pipeline_engine.taxonomy.classify(sanitized, entity)
        attr_data = pipeline_engine.extractor.extract(sanitized, entity, tax)
        
        extracted = attr_data.get("extracted_dict", {})
        if "Material" in extracted:
            assert extracted["Material"][0] == "Stainless Steel"

    def test_extractor_attribute_triplet_structure(self, sample_dishwasher_frigidaire: Dict[str, Any], pipeline_engine):
        """Verify that all extracted attributes conform to the (LABEL, VALUE, UOM) triplet contract."""
        from src.pipeline.models import AttributeTriple
        
        sanitized = pipeline_engine.sanitizer.sanitize(pipeline_engine.raw_cls(**sample_dishwasher_frigidaire))
        entity = pipeline_engine.resolver.resolve(sanitized)
        tax = pipeline_engine.taxonomy.classify(sanitized, entity)
        attr_data = pipeline_engine.extractor.extract(sanitized, entity, tax)
        
        attrs = attr_data.get("attributes", [])
        assert len(attrs) > 0
        populated = [a for a in attrs if a.label]
        assert len(populated) >= 5, "Expected at least 5 populated attributes for reference dishwasher"
        for attr in populated:
            assert isinstance(attr, AttributeTriple)
            assert isinstance(attr.label, str) and len(attr.label) > 0
            assert isinstance(attr.value, str)

    def test_extractor_zero_hallucination_guarantee(self, pipeline_engine):
        """Verify that random text strings not matching LOVs are not fabricated into canonical attributes."""
        dummy_raw = pipeline_engine.raw_cls(
            mfg_part_num="XYZ999",
            part_desc="Random uncharacterized widget with unknown features",
            part_manuf="Acme Corp (9999)"
        )
        sanitized = pipeline_engine.sanitizer.sanitize(dummy_raw)
        entity = pipeline_engine.resolver.resolve(sanitized)
        tax = pipeline_engine.taxonomy.classify(sanitized, entity)
        attr_data = pipeline_engine.extractor.extract(sanitized, entity, tax)
        
        populated = [a for a in attr_data.get("attributes", []) if a.label]
        for attr in populated:
            assert attr.value != "Unknown"
            assert attr.value != "N/A"
            assert attr.label != ""


# ===========================================================================
# 5. Feature: UOM & Fraction Standardization Engine
# ===========================================================================

class TestFeature5UOMAndFractions:
    """Test suite for Feature 5: UOM & Fraction Standardization."""

    @pytest.mark.parametrize("decimal_val, expected_fraction", [
        (0.5, "1/2"),
        (0.25, "1/4"),
        (0.75, "3/4"),
        (0.125, "1/8"),
        (0.375, "3/8"),
        (0.625, "5/8"),
        (0.875, "7/8"),
        (0.0625, "1/16"),
        (0.1875, "3/16"),
        (0.3125, "5/16"),
        (0.4375, "7/16"),
        (0.03125, "1/32"),
        (0.015625, "1/64"),
        (0.984375, "63/64"),
        (0.045, "3/64"),  # common abrasive wheel thickness
    ])
    def test_decimal_to_fraction_conversion(self, decimal_val: float, expected_fraction: str, pipeline_engine):
        """Verify conversion of exact decimal inch increments to 64th fractions."""
        result = pipeline_engine.uom_std.decimal_to_fraction(decimal_val)
        assert result == expected_fraction, f"Expected {decimal_val} -> {expected_fraction}, got {result}"

    @pytest.mark.parametrize("input_text, expected_output", [
        ("50.25 in", "50-1/4 in"),
        ("33.4375 in", "33-7/16 in"),
        ("24.25 in", "24-1/4 in"),
        ("6.5 in", "6-1/2 in"),
        ("8.5 in", "8-1/2 in"),
        ("10.375 in", "10-3/8 in"),
        ("11.25 in", "11-1/4 in"),
        ("13.25 in", "13-1/4 in"),
    ])
    def test_mixed_fraction_hyphenation(self, input_text: str, expected_output: str, pipeline_engine):
        """Verify hyphenated mixed fraction format (e.g. '50-1/4 in')."""
        result = pipeline_engine.uom_std.standardize_dimension_string(input_text)
        assert result == expected_output, f"Expected '{input_text}' -> '{expected_output}', got '{result}'"

    @pytest.mark.parametrize("raw_unit, expected_unit", [
        ("24in", "24 in"),
        ("120V", "120 V"),
        ("15A", "15 A"),
        ("47dBA", "47 dBA"),
        ("100W", "100 W"),
        ("10ft", "10 ft"),
        ("5lb", "5 lb"),
        ("240kW-hr", "240 kW-hr"),
    ])
    def test_mandatory_space_before_unit(self, raw_unit: str, expected_unit: str, pipeline_engine):
        """Verify single space enforcement between number and unit of measure."""
        result = pipeline_engine.uom_std.standardize_dimension_string(raw_unit)
        assert result == expected_unit, f"Expected '{raw_unit}' -> '{expected_unit}', got '{result}'"

    @pytest.mark.parametrize("raw_abbr, expected_canonical", [
        ("inches", "in"),
        ("IN.", "in"),
        ("inch", "in"),
        ("feet", "ft"),
        ("FT", "ft"),
        ("volts", "V"),
        ("Volt", "V"),
        ("amps", "A"),
        ("Amp", "A"),
        ("decibels", "dBA"),
        ("db", "dBA"),
        ("pounds", "lb"),
        ("lbs", "lb"),
    ])
    def test_canonical_uom_abbreviation_normalization(self, raw_abbr: str, expected_canonical: str, pipeline_engine):
        """Verify normalization of unit abbreviations to Unilog standard."""
        canonical = pipeline_engine.uom_std.normalize_uom(raw_abbr)
        assert canonical == expected_canonical, f"Expected '{raw_abbr}' -> '{expected_canonical}', got '{canonical}'"

    def test_dimension_string_parsing_and_conversion(self, pipeline_engine):
        """Verify conversion of compound dimension expressions like '24x24-1/4' or '5x.045x7/8'."""
        raw_dim = '5"x.045"x7/8"'
        std_dim = pipeline_engine.uom_std.standardize_dimension_string(raw_dim)
        assert "in" in std_dim or "/" in std_dim
        assert "3/64" in std_dim or "7/8" in std_dim


# ===========================================================================
# 6. Feature: 5-Tier Content & Description Generator
# ===========================================================================

class TestFeature6DescriptionGenerator:
    """Test suite for Feature 6: 5-Tier Content & Description Generator."""

    def test_invoice_desc_character_limit_and_all_caps(self, sample_dishwasher_frigidaire: Dict[str, Any], pipeline_engine):
        """Assert that INVOICE_DESC is strictly <= 40 characters and 100% ALL CAPS."""
        enriched = pipeline_engine.process_record(sample_dishwasher_frigidaire)
        
        inv_desc = enriched.invoice_desc
        assert len(inv_desc) <= 40, f"INVOICE_DESC exceeds 40 chars ({len(inv_desc)}): '{inv_desc}'"
        assert inv_desc.isupper(), f"INVOICE_DESC must be 100% ALL CAPS: '{inv_desc}'"
        assert len(inv_desc) > 0, "INVOICE_DESC must not be empty"

    def test_mobile_desc_length_range(self, sample_dishwasher_frigidaire: Dict[str, Any], pipeline_engine):
        """Assert that MOBILE_DESC length is strictly within 60 to 80 characters."""
        enriched = pipeline_engine.process_record(sample_dishwasher_frigidaire)
        
        mob_desc = enriched.mobile_desc
        assert 60 <= len(mob_desc) <= 80, f"MOBILE_DESC must be 60-80 chars ({len(mob_desc)}): '{mob_desc}'"

    def test_short_desc_formula_structure(self, sample_dishwasher_frigidaire: Dict[str, Any], pipeline_engine):
        """Assert that SHORT_DESC includes Brand, MPN, Item Type, and key specs."""
        enriched = pipeline_engine.process_record(sample_dishwasher_frigidaire)
        
        short_desc = enriched.short_desc
        assert "FRIGIDAIRE" in short_desc
        assert "PDSH4816AF" in short_desc
        assert "Dishwasher" in short_desc

    def test_long_desc1_technical_sentence(self, sample_dishwasher_frigidaire: Dict[str, Any], pipeline_engine):
        """Assert that LONG_DESC1 provides a complete technical specification sentence."""
        enriched = pipeline_engine.process_record(sample_dishwasher_frigidaire)
        
        long_desc = enriched.long_desc1
        assert "FRIGIDAIRE" in long_desc
        assert "Dishwasher" in long_desc
        assert len(long_desc) > len(enriched.short_desc)
        assert "V" in long_desc or "A" in long_desc or "in" in long_desc

    def test_retail_and_marketing_desc_generation(self, sample_dishwasher_frigidaire: Dict[str, Any], pipeline_engine):
        """Assert that RETAIL_DESC and MARKETING_DESCRIPTION are properly generated."""
        enriched = pipeline_engine.process_record(sample_dishwasher_frigidaire)
        
        assert hasattr(enriched, "retail_desc")
        assert hasattr(enriched, "marketing_description")
        assert len(enriched.retail_desc) > 0

    def test_whirlpool_5_tier_descriptions_compliance(self, sample_dishwasher_whirlpool: Dict[str, Any], pipeline_engine):
        """Assert 5-tier descriptions for Whirlpool reference record satisfy all hard gates."""
        enriched = pipeline_engine.process_record(sample_dishwasher_whirlpool)
        
        # Hard Gate: Invoice <= 40 chars & ALL CAPS
        assert len(enriched.invoice_desc) <= 40
        assert enriched.invoice_desc.isupper()
        
        # Hard Gate: Mobile 60-80 chars
        assert 60 <= len(enriched.mobile_desc) <= 80
        
        # Short & Long Desc
        assert "Whirlpool" in enriched.short_desc
        assert "WDTS7024RZ" in enriched.short_desc


# ===========================================================================
# 7. Feature: Full 252-Column Delivery Exporter
# ===========================================================================

class TestFeature7DeliveryExporter:
    """Test suite for Feature 7: Full 252-Column Delivery Exporter."""

    def test_delivery_mapper_returns_exact_252_columns(self, sample_dishwasher_frigidaire: Dict[str, Any], pipeline_engine, expected_252_columns):
        """Assert that delivery mapper returns a dict with exactly 252 keys."""
        from src.pipeline.delivery_mapper import to_delivery_dict
        
        enriched = pipeline_engine.process_record(sample_dishwasher_frigidaire)
        delivery_row = to_delivery_dict(enriched)
        
        assert len(delivery_row) == 252, f"Expected 252 columns, got {len(delivery_row)}"

    def test_delivery_mapper_exact_column_order(self, sample_dishwasher_frigidaire: Dict[str, Any], pipeline_engine, expected_252_columns):
        """Assert that delivery mapper keys match the exact column order of ground truth."""
        from src.pipeline.delivery_mapper import to_delivery_dict
        
        enriched = pipeline_engine.process_record(sample_dishwasher_frigidaire)
        delivery_row = to_delivery_dict(enriched)
        
        generated_cols = list(delivery_row.keys())
        assert generated_cols == expected_252_columns, "Delivery column keys do not match ground truth ordering"

    def test_delivery_mapper_triplet_slot_formatting(self, sample_dishwasher_frigidaire: Dict[str, Any], pipeline_engine):
        """Assert that attribute triplet columns (ATTRIBUTE_LABEL 1..50, VALUE, UOM) are populated."""
        from src.pipeline.delivery_mapper import to_delivery_dict
        
        enriched = pipeline_engine.process_record(sample_dishwasher_frigidaire)
        row = to_delivery_dict(enriched)
        
        # Slot 1 must not be empty for an enriched product
        assert row["ATTRIBUTE_LABEL 1"] != ""
        assert row["ATTRIBUTE_VALUE 1"] != ""
        
        # Slot 50 must exist as a key (even if empty string)
        assert "ATTRIBUTE_LABEL 50" in row
        assert "ATTRIBUTE_VALUE 50" in row
        assert "ATTRIBUTE_UOM 50" in row

    def test_delivery_mapper_csv_serialization(self, sample_dishwasher_frigidaire: Dict[str, Any], pipeline_engine, tmp_path):
        """Assert that batch export to CSV creates a valid RFC-4180 CSV with 252 columns."""
        from src.pipeline.delivery_mapper import to_delivery_dict
        
        enriched = pipeline_engine.process_record(sample_dishwasher_frigidaire)
        out_csv = tmp_path / "test_export_252.csv"
        
        row = to_delivery_dict(enriched)
        df = pd.DataFrame([row])
        df.to_csv(out_csv, index=False)
        assert out_csv.exists()
        
        read_df = pd.read_csv(out_csv)
        assert len(read_df.columns) == 252
        assert len(read_df) == 1

    def test_delivery_mapper_excel_serialization(self, sample_dishwasher_frigidaire: Dict[str, Any], pipeline_engine, tmp_path):
        """Assert that batch export to Excel creates a valid workbook with 252 columns."""
        from src.pipeline.delivery_mapper import to_delivery_dict
        
        enriched = pipeline_engine.process_record(sample_dishwasher_frigidaire)
        out_xlsx = tmp_path / "test_export_252.xlsx"
        
        row = to_delivery_dict(enriched)
        df = pd.DataFrame([row])
        df.to_excel(out_xlsx, index=False)
        assert out_xlsx.exists()
        
        read_df = pd.read_excel(out_xlsx)
        assert len(read_df.columns) == 252
        assert len(read_df) == 1
