"""
Unit Test Suite for Industrial Product Intelligence & PIM Enrichment Pipeline.
"""

import pytest
from src.pipeline.models import RawProduct, EnrichedProduct, AttributeTriple, PhysicalDimensions
from src.pipeline.sanitizer import ProductSanitizer
from src.pipeline.entity_resolver import EntityResolver
from src.pipeline.taxonomy import TaxonomyClassifier
from src.pipeline.attribute_extractor import AttributeExtractor
from src.pipeline.uom_standardizer import UOMStandardizer
from src.pipeline.description_generator import DescriptionGenerator
from src.pipeline.delivery_mapper import DeliveryMapper, to_delivery_dict
from src.pipeline.engine import EnrichmentEngine


def test_sanitizer_placeholders():
    """Test that all sentinel placeholders are stripped to None."""
    sanitizer = ProductSanitizer()
    assert sanitizer.clean_placeholder("-- Unbranded --") is None
    assert sanitizer.clean_placeholder("-- No Unilog Brand --") is None
    assert sanitizer.clean_placeholder("-- No DIB Brand --") is None
    assert sanitizer.clean_placeholder("COMMODITY - UNBRANDED") is None
    assert sanitizer.clean_placeholder("-") is None
    assert sanitizer.clean_placeholder("TREX") == "TREX"


def test_sanitizer_supplier_code_parsing():
    """Test vendor name and supplier code isolation."""
    name, code = ProductSanitizer.parse_supplier("Freud Inc (2435)")
    assert name == "Freud Inc"
    assert code == "2435"

    name, code = ProductSanitizer.parse_supplier("Appliance Dealers Cooperative (APPDE)")
    assert name == "Appliance Dealers Cooperative"
    assert code == "APPDE"


def test_sanitizer_leading_mpn_stripping():
    """Test that duplicate leading MPN in description is stripped."""
    raw = RawProduct(
        mfg_part_num="DCB518ASTS06G",
        part_desc="DCB518ASTS06G Diablo 1/2\"x18\" - Sanding Belt 6pc",
        e1_brand="-- Unbranded --",
        unilog_brand="-- No Unilog Brand --",
        dib_brand="-- No DIB Brand --",
        part_manuf="Freud Inc (2435)"
    )
    res = ProductSanitizer.sanitize(raw)
    assert res["mfg_part_num"] == "DCB518ASTS06G"
    assert res["desc_tokens"] == "Diablo 1/2\"x18\" - Sanding Belt 6pc"
    assert res["e1_brand"] is None
    assert res["supplier_code"] == "2435"


def test_entity_resolver_appliance():
    """Test appliance brand and manufacturer resolution."""
    resolver = EntityResolver()
    
    # Frigidaire row
    san = {
        "mfg_part_num": "PDSH4816AF",
        "raw_desc": "PDSH4816AF Dishwasher SS - Display Only",
        "supplier_code": "APPDE",
        "supplier_name": "Appliance Dealers Cooperative"
    }
    ent = resolver.resolve(san)
    assert "FRIGIDAIRE" in ent["brand_name"]
    assert ent["manufacturer_name"] == "Rheem Manufacturing"
    assert "®" in ent["brand_name"]


def test_entity_resolver_brands():
    """Test tooling and building materials brand resolution."""
    resolver = EntityResolver()
    
    # Diablo
    san = {
        "mfg_part_num": "DCB518ASTS06G",
        "raw_desc": "Diablo Sanding Belt",
        "supplier_name": "Freud Inc",
        "supplier_code": "2435"
    }
    ent = resolver.resolve(san)
    assert ent["brand_name"] == "Diablo®"
    assert ent["manufacturer_name"] == "Freud America, Inc."

    # Trex
    san_trex = {
        "mfg_part_num": "1513724",
        "raw_desc": "1nx6-16' Tide Pool Sq Edge - Trex Enhance Basics Decking",
        "e1_brand": "TREX",
        "supplier_name": "Boise Cascade Building Materials",
        "supplier_code": "BOICA"
    }
    ent_trex = resolver.resolve(san_trex)
    assert ent_trex["brand_name"] == "Trex®"
    assert ent_trex["manufacturer_name"] == "Trex Company, Inc."


def test_taxonomy_classifier():
    """Test taxonomy classpath and UNSPSC assignment."""
    classifier = TaxonomyClassifier()
    
    # Dishwasher
    tax_dish = classifier.classify({"raw_desc": "PDSH4816AF Dishwasher SS"}, {"brand_name": "FRIGIDAIRE®"})
    assert tax_dish["unspsc"] == "52141505"
    assert tax_dish["product_name"] == "Dishwasher"
    assert "Built-In Dishwashers" in tax_dish["classpath"]

    # Decking
    tax_deck = classifier.classify({"raw_desc": "Trex Enhance Basics Decking Board Sq Edge"}, {"brand_name": "Trex®"})
    assert tax_deck["unspsc"] == "30103603"
    assert tax_deck["product_name"] == "Decking Board"


def test_uom_standardizer_fractions():
    """Test 64th decimal to fraction converter."""
    uom = UOMStandardizer()
    assert uom.decimal_to_fraction(50.25) == "50-1/4"
    assert uom.decimal_to_fraction(50.1875) == "50-3/16"
    assert uom.decimal_to_fraction(33.4375) == "33-7/16"
    assert uom.decimal_to_fraction(23.875) == "23-7/8"
    assert uom.decimal_to_fraction(22.625) == "22-5/8"
    assert uom.decimal_to_fraction(0.5) == "1/2"
    assert uom.decimal_to_fraction(24.0) == "24"


def test_uom_standardizer_spacing():
    """Test mandatory space rule between number and unit."""
    uom = UOMStandardizer()
    assert uom.format_value_with_uom("120", "V") == "120 V"
    assert uom.format_value_with_uom("15", "A") == "15 A"
    assert uom.format_value_with_uom("47", "dBA") == "47 dBA"
    assert uom.standardize_dimension_string("24\"x24-1/4\"") == "24 in x 24-1/4 in"


def test_description_generator_hard_gates():
    """Test that description generator strictly satisfies hard gate limits."""
    gen = DescriptionGenerator()
    
    # Test invoice desc <= 40 chars ALL CAPS
    inv = gen.generate_invoice_desc(
        product_name="DISHWASHER",
        clean_brand="FRIGIDAIRE",
        series="Professional Series",
        mpn="PDSH4816AF",
        extracted={
            "Mounting Type": ("Leg", ""),
            "Number of Wash Cycles": ("5", ""),
            "Material": ("Stainless Steel", ""),
            "Voltage Rating": ("120", "V"),
            "Amperage Rating": ("15", "A"),
            "Depth With Door Open": ("50-1/4", "in")
        }
    )
    assert len(inv) <= 40
    assert inv.isupper()
    assert inv == "DISHWASHER LEG 5 SST 120V 15A 50-1/4IN"

    # Test mobile desc within 60..80 chars
    mob = gen.generate_mobile_desc(
        mfr_name="Rheem Manufacturing",
        clean_brand="FRIGIDAIRE",
        product_name="Dishwasher",
        series="Professional Series",
        mpn="PDSH4816AF",
        extracted={}
    )
    assert 60 <= len(mob) <= 80


def test_delivery_mapper_252_columns():
    """Test that delivery mapper produces exactly 252 columns matching header specification."""
    headers = DeliveryMapper.get_column_headers()
    assert len(headers) == 252
    assert headers[0] == "MFR URL"
    assert headers[6] == "PART_NUMBER"
    assert headers[23] == "MOBILE_DESC"
    assert headers[24] == "INVOICE_DESC"
    assert headers[25] == "SHORT_DESC"
    assert headers[251] == "Actual Image (Yes/No)"


def test_engine_end_to_end_single():
    """Test full engine execution on a raw product."""
    engine = EnrichmentEngine()
    raw = RawProduct(
        mfg_part_num="PDSH4816AF",
        part_desc="PDSH4816AF Dishwasher SS - Display Only",
        e1_brand="-- Unbranded --",
        unilog_brand="-- No Unilog Brand --",
        dib_brand="-- No DIB Brand --",
        part_manuf="Appliance Dealers Cooperative (APPDE)",
        row_id=61
    )
    enriched = engine.process_item(raw)
    assert enriched.brand_name == "FRIGIDAIRE®"
    assert enriched.manufacturer_name == "Rheem Manufacturing"
    assert enriched.unspsc == "52141505"
    assert len(enriched.invoice_desc) <= 40
    assert enriched.invoice_desc.isupper()
    assert 60 <= len(enriched.mobile_desc) <= 80
    assert enriched.confidence_score >= 0.85

    delivery_dict = DeliveryMapper.to_delivery_dict(enriched)
    assert len(delivery_dict) == 252
    assert delivery_dict["INVOICE_DESC"] == enriched.invoice_desc
    assert delivery_dict["Country Of Origin"] == ""
    assert delivery_dict["Actual Image (Yes/No)"] == "No"
    assert delivery_dict["Product Image"] == ""
    assert delivery_dict["Specification Sheet"] == ""
    assert delivery_dict["MFR URL"] == ""
    assert delivery_dict["Warranty"] == ""
    assert "UNVERIFIED_ASSET" in enriched.validation_flags
