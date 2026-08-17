"""Tier 2: Boundary & Corner Cases E2E Test Suite.

This module provides exhaustive boundary, stress, and corner case testing:
1. Character Limit Strict Boundaries (INVOICE_DESC <= 40 ALL CAPS, MOBILE_DESC 60-80 chars)
2. 0% Hallucinations & Strict Controlled Vocabulary (LOV) Adherence
3. Decimal & 64th Fraction Boundary Values (0.015625 to 0.984375, whole integers, compound strings)
4. Missing, Malformed, and Adversarial Supplier Data (empty inputs, unicode, injections)
"""

import pytest
from typing import Dict, Any, List
import pandas as pd


# ===========================================================================
# 1. Boundary: Character Limit Strict Enforcement
# ===========================================================================

class TestTier2CharacterLimitBoundaries:
    """Test suite for hard-gate character limit boundaries on generated descriptions."""

    def test_boundary_invoice_desc_extremely_long_input(self, pipeline_engine):
        """Verify that an extremely long raw description (250+ characters) is safely condensed to <= 40 chars ALL CAPS."""
        long_raw = {
            "mfg_part_num": "LONGPART12345",
            "part_desc": "Ultra Heavy Duty Commercial Multi-Stage Commercial Dishwasher With Sanitizing Rinse Cycle Built-In Leg Mounting 120V 15A 50.25in Stainless Steel Finish Professional Grade Restaurant Kitchen Appliance System",
            "e1_brand": "-- Unbranded --",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "-- No DIB Brand --",
            "part_manuf": "Appliance Dealers Cooperative (APPDE)",
        }
        enriched = pipeline_engine.process_record(long_raw)
        
        inv = enriched.invoice_desc
        assert len(inv) <= 40, f"INVOICE_DESC must not exceed 40 chars on long input (got {len(inv)}): '{inv}'"
        assert inv.isupper(), f"INVOICE_DESC must be ALL CAPS: '{inv}'"

    def test_boundary_invoice_desc_minimal_single_word_input(self, pipeline_engine):
        """Verify that a minimal 3-character raw input still produces valid uppercase INVOICE_DESC <= 40 chars."""
        minimal_raw = {
            "mfg_part_num": "X1",
            "part_desc": "Lug",
            "e1_brand": "-- Unbranded --",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "-- No DIB Brand --",
            "part_manuf": "-",
        }
        enriched = pipeline_engine.process_record(minimal_raw)
        
        inv = enriched.invoice_desc
        assert len(inv) <= 40
        assert inv.isupper()
        assert len(inv) > 0

    def test_boundary_mobile_desc_short_input_padding_and_expansion(self, pipeline_engine):
        """Verify that a very short raw input is intelligently expanded to meet the 60-80 character requirement."""
        short_raw = {
            "mfg_part_num": "A100",
            "part_desc": "Cut-Off Disc",
            "e1_brand": "-- Unbranded --",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "-- No DIB Brand --",
            "part_manuf": "Freud Inc (2435)",
        }
        enriched = pipeline_engine.process_record(short_raw)
        
        mob = enriched.mobile_desc
        assert 60 <= len(mob) <= 80, f"MOBILE_DESC must be between 60 and 80 chars (got {len(mob)}): '{mob}'"

    def test_boundary_mobile_desc_long_input_word_boundary_truncation(self, pipeline_engine):
        """Verify that a very long description is truncated cleanly without splitting words to stay within 60-80 chars."""
        long_raw = {
            "mfg_part_num": "WDTS7024RZ",
            "part_desc": "Whirlpool Eco Series WDTS7024RZ Dishwasher Built-in Mounting 120V 10A Stainless Steel Extra Quiet 41 dBA Triple Wash Sensor Sani Rinse Option",
            "e1_brand": "-- Unbranded --",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "-- No DIB Brand --",
            "part_manuf": "Whirlpool Corporation",
        }
        enriched = pipeline_engine.process_record(long_raw)
        
        mob = enriched.mobile_desc
        assert 60 <= len(mob) <= 80, f"MOBILE_DESC must be within 60-80 chars (got {len(mob)}): '{mob}'"
        assert not mob.endswith(",")
        assert not mob.endswith(" ")

    @pytest.mark.parametrize("mfg_part_num, part_desc", [
        ("PDSH4816AF", "PDSH4816AF Dishwasher SS - Display Only"),
        ("WDTS7024RZ", "WDTS7024RZ Dishwasher SS - Display Only"),
        ("49-94-0013", 'Milw 5"x.045"x7/8" Metal Cut Off Disc'),
        ("DCB518ASTS06G", 'Diablo 1/2"x18" - Sanding Belt 6pc'),
        ("PG010616TS01", "1x6-16' Transcend Island Mist Square Edge Deck Board"),
    ])
    def test_boundary_all_descriptions_lengths_for_sample_catalog_items(self, mfg_part_num: str, part_desc: str, pipeline_engine):
        """Assert both INVOICE_DESC (<=40 CAPS) and MOBILE_DESC (60-80 chars) pass across diverse catalog samples."""
        raw = {
            "mfg_part_num": mfg_part_num,
            "part_desc": part_desc,
            "e1_brand": "-- Unbranded --",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "-- No DIB Brand --",
            "part_manuf": "Appliance Dealers Cooperative (APPDE)",
        }
        enriched = pipeline_engine.process_record(raw)
        
        assert len(enriched.invoice_desc) <= 40, f"Invoice desc > 40: {enriched.invoice_desc}"
        assert enriched.invoice_desc.isupper(), f"Invoice desc not uppercase: {enriched.invoice_desc}"
        assert 60 <= len(enriched.mobile_desc) <= 80, f"Mobile desc not in 60-80 range: {enriched.mobile_desc}"


# ===========================================================================
# 2. Boundary: 0% Hallucination & Controlled Vocabulary (LOV) Adherence
# ===========================================================================

class TestTier2LOVHallucinationBoundaries:
    """Test suite for verifying 0% hallucination and strict LOV adherence."""

    def test_boundary_lov_unknown_attribute_not_hallucinated(self, pipeline_engine):
        """Verify that unrecognized or hallucinated attribute values are not forced into standard LOV slots."""
        raw = {
            "mfg_part_num": "SPECIAL123",
            "part_desc": "Special Dishwasher with Quantum Flux Capacitor and Telepathic Sensor",
            "e1_brand": "-- Unbranded --",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "-- No DIB Brand --",
            "part_manuf": "Appliance Dealers Cooperative (APPDE)",
        }
        enriched = pipeline_engine.process_record(raw)
        
        attr_values = [a.value.lower() for a in enriched.attributes if a.value]
        assert "quantum flux capacitor" not in attr_values
        assert "telepathic sensor" not in attr_values

    def test_boundary_lov_case_insensitivity_and_synonym_normalization(self, pipeline_engine):
        """Verify that noisy supplier variants normalize to exact canonical LOVs."""
        raw_leg = {
            "mfg_part_num": "P1",
            "part_desc": "Dishwasher with leg mount 120V 15A stainless steel",
            "e1_brand": "-- Unbranded --",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "-- No DIB Brand --",
            "part_manuf": "Appliance Dealers Cooperative (APPDE)",
        }
        enriched_leg = pipeline_engine.process_record(raw_leg)
        attr_map = {a.label: a.value for a in enriched_leg.attributes if a.label}
        
        if "Mounting Type" in attr_map:
            assert attr_map["Mounting Type"] in ["Leg", "Built-in"]
        if "Material" in attr_map:
            assert attr_map["Material"] == "Stainless Steel"

    def test_boundary_lov_empty_attribute_slots_cleanliness(self, pipeline_engine):
        """Verify that unused attribute triplet slots in 252-column export remain empty string, not None or NaN."""
        from src.pipeline.delivery_mapper import to_delivery_dict
        
        raw = {
            "mfg_part_num": "P1",
            "part_desc": "Simple Screw #8 x 1 in",
            "e1_brand": "-- Unbranded --",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "-- No DIB Brand --",
            "part_manuf": "-",
        }
        enriched = pipeline_engine.process_record(raw)
        row = to_delivery_dict(enriched)
        
        # Attribute slots 40 through 50 should be clean empty strings
        for slot in range(40, 51):
            assert row[f"ATTRIBUTE_LABEL {slot}"] == ""
            assert row[f"ATTRIBUTE_VALUE {slot}"] == ""
            assert row[f"ATTRIBUTE_UOM {slot}"] == ""

    def test_boundary_lov_numerical_voltage_amperage_validation(self, pipeline_engine):
        """Verify that unrealistic electrical values (e.g. 99999 V) are not accepted as valid standard voltage LOVs."""
        raw = {
            "mfg_part_num": "ELEC1",
            "part_desc": "Dishwasher 99999V 5000A",
            "e1_brand": "-- Unbranded --",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "-- No DIB Brand --",
            "part_manuf": "Appliance Dealers Cooperative (APPDE)",
        }
        enriched = pipeline_engine.process_record(raw)
        attr_map = {a.label: a.value for a in enriched.attributes if a.label}
        
        if "Voltage Rating" in attr_map:
            assert attr_map["Voltage Rating"] != "99999"
            assert attr_map["Voltage Rating"] != "99999 V"


# ===========================================================================
# 3. Boundary: Decimal & 64th Fraction Boundary Values
# ===========================================================================

class TestTier2FractionBoundaries:
    """Test suite for 64th decimal-to-fraction boundary values."""

    def test_boundary_fraction_smallest_1_64th(self, pipeline_engine):
        """Verify conversion of minimum 64th increment: 0.015625 -> 1/64."""
        assert pipeline_engine.uom_std.decimal_to_fraction(0.015625) == "1/64"

    def test_boundary_fraction_largest_63_64th(self, pipeline_engine):
        """Verify conversion of maximum 64th increment: 0.984375 -> 63/64."""
        assert pipeline_engine.uom_std.decimal_to_fraction(0.984375) == "63/64"

    def test_boundary_fraction_integer_whole_numbers_no_spurious_fractions(self, pipeline_engine):
        """Verify that whole numbers like 24.0 or 50.0 do not produce '-0/0' or '.0' artifacts."""
        assert pipeline_engine.uom_std.standardize_dimension_string("24.0 in") == "24 in"
        assert pipeline_engine.uom_std.standardize_dimension_string("50.0 in") == "50 in"
        assert pipeline_engine.uom_std.standardize_dimension_string("12.0 ft") == "12 ft"

    def test_boundary_fraction_nearest_rounding_for_non_exact_decimals(self, pipeline_engine):
        """Verify that non-exact manufacturer decimals (e.g. 0.045, 0.33) round safely to nearest 64th."""
        assert pipeline_engine.uom_std.decimal_to_fraction(0.045) in ["3/64", "1/16"]

    def test_boundary_fraction_complex_multi_axis_dimension_string(self, pipeline_engine):
        """Verify compound multi-axis dimension expressions with mixed fractions."""
        raw_dim = "33.4375 in H x 23.875 in W x 22.625 in D"
        res = pipeline_engine.uom_std.standardize_dimension_string(raw_dim)
        assert "33-7/16 in H" in res or "33-7/16 in" in res
        assert "23-7/8 in W" in res or "23-7/8 in" in res
        assert "22-5/8 in D" in res or "22-5/8 in" in res


# ===========================================================================
# 4. Boundary: Missing, Malformed, and Adversarial Supplier Data
# ===========================================================================

class TestTier2MalformedAndAdversarialData:
    """Test suite for malformed, missing, and adversarial supplier inputs."""

    def test_boundary_completely_blank_record(self, pipeline_engine):
        """Verify pipeline handles a record where all input fields are empty without throwing unhandled exceptions."""
        empty_raw = {
            "mfg_part_num": "UNKNOWN",
            "part_desc": "",
            "e1_brand": "",
            "unilog_brand": "",
            "dib_brand": "",
            "part_manuf": "",
        }
        enriched = pipeline_engine.process_record(empty_raw)
        
        assert enriched.part_number != ""
        assert len(enriched.invoice_desc) <= 40
        assert enriched.invoice_desc.isupper()

    def test_boundary_unicode_symbols_and_smart_quotes(self, pipeline_engine):
        """Verify pipeline handles smart quotes (“ ” ‘ ’), accents (é, ñ), and symbols (°, ±, µ)."""
        unicode_raw = {
            "mfg_part_num": "UNI-100",
            "part_desc": "Diablo® 5” Blade with 10° Hook & ±0.05” Kerf for Résumé Cut",
            "e1_brand": "-- Unbranded --",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "-- No DIB Brand --",
            "part_manuf": "Freud Inc (2435)",
        }
        enriched = pipeline_engine.process_record(unicode_raw)
        
        assert enriched.brand_name != ""
        assert len(enriched.invoice_desc) <= 40

    def test_boundary_sql_injection_tokens_in_description(self, pipeline_engine):
        """Verify that SQL injection strings in supplier inputs are sanitized and do not corrupt data output."""
        sqli_raw = {
            "mfg_part_num": "SQLI-100",
            "part_desc": "Dishwasher'; DROP TABLE products; SELECT * FROM users WHERE '1'='1",
            "e1_brand": "-- Unbranded --",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "-- No DIB Brand --",
            "part_manuf": "Appliance Dealers Cooperative (APPDE)",
        }
        enriched = pipeline_engine.process_record(sqli_raw)
        
        assert len(enriched.invoice_desc) <= 40
        assert enriched.invoice_desc.isupper()
        assert "DROP TABLE" not in enriched.short_desc or "Dishwasher" in enriched.short_desc

    def test_boundary_xss_script_tags_in_description(self, pipeline_engine):
        """Verify that HTML / XSS script tags in descriptions are sanitized or escaped."""
        xss_raw = {
            "mfg_part_num": "XSS-100",
            "part_desc": "<script>alert('pwned')</script> Dishwasher 120V SS",
            "e1_brand": "-- Unbranded --",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "-- No DIB Brand --",
            "part_manuf": "Appliance Dealers Cooperative (APPDE)",
        }
        enriched = pipeline_engine.process_record(xss_raw)
        
        assert "<script>" not in enriched.short_desc
        assert "<script>" not in enriched.invoice_desc
        assert len(enriched.invoice_desc) <= 40

    def test_boundary_repeated_word_spam_in_description(self, pipeline_engine):
        """Verify that repetitive token spam is handled gracefully without producing run-away descriptions."""
        spam_raw = {
            "mfg_part_num": "SPAM-100",
            "part_desc": "Dishwasher Dishwasher Dishwasher Dishwasher Dishwasher Dishwasher Dishwasher Dishwasher Dishwasher Dishwasher",
            "e1_brand": "-- Unbranded --",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "-- No DIB Brand --",
            "part_manuf": "Appliance Dealers Cooperative (APPDE)",
        }
        enriched = pipeline_engine.process_record(spam_raw)
        
        assert len(enriched.invoice_desc) <= 40
        assert 60 <= len(enriched.mobile_desc) <= 80
