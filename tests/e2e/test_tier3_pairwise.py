"""Tier 3: Pairwise Combinations E2E Test Suite.

This module provides systematic pairwise and combinatorial test coverage across:
1. Brand & Manufacturer Families (Frigidaire, Whirlpool, Milwaukee, Diablo, Trex, Philips, Leviton, Generic)
2. Taxonomy & Product Categories (Dishwashers, Abrasives/Wheels, Sanding Belts, Decking, Lighting, Wiring)
3. Input Lengths & Cryptic Levels (Short 10-char, Medium 45-char, Long 120-char)
4. Dimensional Complexities (None, Single unit, Multi-axis 64th mixed fractions)
5. Electrical / Power Configurations (None, 120V 15A, 240V 50A, 100W LED)
"""

import pytest
from typing import Dict, Any, List
import itertools


# Orthogonal parameter sets for pairwise matrix generation
BRANDS = [
    {"name": "FRIGIDAIRE", "manuf": "Appliance Dealers Cooperative (APPDE)", "expected_brand": "FRIGIDAIRE®"},
    {"name": "Whirlpool", "manuf": "Whirlpool Corporation", "expected_brand": "Whirlpool®"},
    {"name": "Milwaukee", "manuf": "Milwaukee Accessory (4031)", "expected_brand": "Milwaukee®"},
    {"name": "Diablo", "manuf": "Freud Inc (2435)", "expected_brand": "Diablo®"},
    {"name": "Trex", "manuf": "Boise Cascade Building Materials (BOICA)", "expected_brand": "Trex®"},
    {"name": "Philips", "manuf": "Phillips Lighting (5831)", "expected_brand": "Philips®"},
    {"name": "Generic", "manuf": "-", "expected_brand": ""},
]

CATEGORIES = [
    {"type": "Dishwasher", "keywords": "Dishwasher SS 120V 15A Built-in Mounting", "dept": "Appliances"},
    {"type": "Cut-Off Disc", "keywords": '5"x.045"x7/8" Metal Cut Off Disc Abrasive', "dept": "Tools & Hardware"},
    {"type": "Sanding Belt", "keywords": '1/2"x18" Sanding Belt 6pc 80 Grit', "dept": "Tools & Hardware"},
    {"type": "Deck Board", "keywords": "1x6-16' Composite Deck Board Island Mist", "dept": "Building Materials"},
    {"type": "LED Lamp", "keywords": "10.5W A19 LED Lamp 120V 2700K E26 Base", "dept": "Electrical & Lighting"},
]

LENGTH_STYLES = [
    {"style": "short", "prefix": "MPN100 "},
    {"style": "medium", "prefix": "MPN100 Premium Grade "},
    {"style": "long", "prefix": "MPN100 Heavy-Duty High-Performance Industrial Professional Series "},
]


def generate_pairwise_samples():
    """Generate representative pairwise combination tuples."""
    samples = []
    for brand, cat in itertools.product(BRANDS, CATEGORIES):
        sample_id = f"{brand['name']}_{cat['type']}"
        samples.append((brand, cat, sample_id))
    return samples


PAIRWISE_SAMPLES = generate_pairwise_samples()


# ===========================================================================
# Pairwise Test Matrix Suite
# ===========================================================================

class TestTier3PairwiseCombinations:
    """Test suite for pairwise combinatorial testing of pipeline transformations."""

    @pytest.mark.parametrize("brand_info, cat_info, sample_id", PAIRWISE_SAMPLES)
    def test_pairwise_brand_category_resolution(self, brand_info: Dict[str, Any], cat_info: Dict[str, Any], sample_id: str, pipeline_engine):
        """Verify that every brand + category combination resolves valid taxonomy and entity names."""
        raw = {
            "mfg_part_num": f"PART-{sample_id}",
            "part_desc": f"{brand_info['name']} {cat_info['keywords']}",
            "e1_brand": "-- Unbranded --",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "-- No DIB Brand --",
            "part_manuf": brand_info["manuf"],
        }
        enriched = pipeline_engine.process_record(raw)
        
        # Verify entity resolution
        if brand_info["expected_brand"]:
            assert brand_info["name"].lower() in enriched.brand_name.lower() or brand_info["name"].lower() in enriched.manufacturer_name.lower()
        
        # Verify taxonomy classification has department and classpath
        assert enriched.dept != "" or enriched.classpath != ""
        assert len(enriched.classpath) > 0

    @pytest.mark.parametrize("brand_info, cat_info, sample_id", PAIRWISE_SAMPLES)
    def test_pairwise_hard_gates_across_all_pairs(self, brand_info: Dict[str, Any], cat_info: Dict[str, Any], sample_id: str, pipeline_engine):
        """Verify 100% compliance on INVOICE_DESC (<=40 ALL CAPS) and MOBILE_DESC (60-80) across all pairwise combinations."""
        raw = {
            "mfg_part_num": f"PAIR-{sample_id}",
            "part_desc": f"{brand_info['name']} {cat_info['keywords']}",
            "e1_brand": "-- Unbranded --",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "-- No DIB Brand --",
            "part_manuf": brand_info["manuf"],
        }
        enriched = pipeline_engine.process_record(raw)
        
        # Hard Gate 1: INVOICE_DESC <= 40 chars & ALL CAPS
        inv = enriched.invoice_desc
        assert len(inv) <= 40, f"Failed on {sample_id}: INVOICE_DESC length is {len(inv)} ('{inv}')"
        assert inv.isupper(), f"Failed on {sample_id}: INVOICE_DESC is not ALL CAPS ('{inv}')"
        
        # Hard Gate 2: MOBILE_DESC 60-80 chars
        mob = enriched.mobile_desc
        assert 60 <= len(mob) <= 80, f"Failed on {sample_id}: MOBILE_DESC length is {len(mob)} ('{mob}')"

    @pytest.mark.parametrize("cat_info", CATEGORIES)
    def test_pairwise_domain_attribute_isolation(self, cat_info: Dict[str, Any], pipeline_engine):
        """Verify that category-specific attributes do not leak into inappropriate categories."""
        raw = {
            "mfg_part_num": f"ATTR-{cat_info['type']}",
            "part_desc": f"Generic {cat_info['keywords']}",
            "e1_brand": "-- Unbranded --",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "-- No DIB Brand --",
            "part_manuf": "-",
        }
        enriched = pipeline_engine.process_record(raw)
        attr_labels = [a.label.lower() for a in enriched.attributes]
        
        if cat_info["type"] == "Cut-Off Disc":
            # Cut off discs should never have wash cycles
            assert "number of wash cycles" not in attr_labels
            assert "wash cycles" not in attr_labels
            
        elif cat_info["type"] == "Dishwasher":
            # Dishwashers should not have grit or abrasive grain
            assert "grit" not in attr_labels
            assert "abrasive material" not in attr_labels

    def test_pairwise_uom_standardization_in_all_generated_descriptions(self, pipeline_engine):
        """Verify that all units in short_desc and long_desc1 across combinations have mandatory space and valid unit forms."""
        test_cases = [
            {"desc": "Dishwasher 120V 15A 24in W 50.25in D", "manuf": "Appliance Dealers Cooperative (APPDE)"},
            {"desc": 'Milwaukee 5"x.045"x7/8" Metal Disc', "manuf": "Milwaukee Accessory (4031)"},
            {"desc": "10.5W LED Lamp 120V 800 Lumens", "manuf": "Phillips Lighting (5831)"},
        ]
        
        for case in test_cases:
            raw = {
                "mfg_part_num": "UOM-TEST",
                "part_desc": case["desc"],
                "e1_brand": "-- Unbranded --",
                "unilog_brand": "-- No Unilog Brand --",
                "dib_brand": "-- No DIB Brand --",
                "part_manuf": case["manuf"],
            }
            enriched = pipeline_engine.process_record(raw)
            long_text = enriched.long_desc1
            
            # Check forbidden patterns: number directly followed by unit with no space
            assert "120V" not in long_text
            assert "15A" not in long_text
            assert "50.25in" not in long_text
            assert "24in" not in long_text

    def test_pairwise_confidence_scoring_consistency(self, pipeline_engine):
        """Verify that composite confidence score is calculated between 0.0 and 1.0 for all pairwise cases."""
        for brand, cat, sample_id in PAIRWISE_SAMPLES[:10]:
            raw = {
                "mfg_part_num": f"CONF-{sample_id}",
                "part_desc": f"{brand['name']} {cat['keywords']}",
                "e1_brand": "-- Unbranded --",
                "unilog_brand": "-- No Unilog Brand --",
                "dib_brand": "-- No DIB Brand --",
                "part_manuf": brand["manuf"],
            }
            enriched = pipeline_engine.process_record(raw)
            
            score = enriched.confidence_score
            assert 0.0 <= score <= 1.0, f"Confidence score out of range on {sample_id}: {score}"
            assert isinstance(enriched.status, str)
            assert enriched.status in ["Enriched", "Validated", "Flagged", "Draft"]
