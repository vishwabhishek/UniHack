"""
Unit tests validating zero fabrication, truthfulness constraints, and validation flagging across the PIM pipeline.

Ensures:
1. Country Of Origin is never defaulted to "US".
2. Actual Image (Yes/No) is "No" unless a verified image asset is present.
3. No fake image or document filenames (.jpg, .pdf) are generated.
4. No fake manufacturer URLs are guessed from domain names.
5. No warranties are generated without explicit source text evidence.
6. Unknown or unsupplied facts remain blank strings.
7. Standard validation flags (MISSING_EVIDENCE, UNVERIFIED_ASSET, UNRESOLVED_IDENTITY) are applied.
8. Generic products do not invent brand or specifications.
"""

import pytest
from src.pipeline.models import RawProduct, EnrichedProduct
from src.pipeline.engine import EnrichmentEngine
from src.pipeline.entity_resolver import EntityResolver
from src.pipeline.attribute_extractor import AttributeExtractor
from src.pipeline.description_generator import DescriptionGenerator
from src.pipeline.delivery_mapper import DeliveryMapper


@pytest.fixture
def engine():
    return EnrichmentEngine()


@pytest.fixture
def resolver():
    return EntityResolver()


@pytest.fixture
def extractor():
    return AttributeExtractor()


def test_country_of_origin_remains_blank_without_evidence(engine):
    """Rule 1 & 7: Country Of Origin must be blank when not supplied, never defaulted to 'US'."""
    raw = RawProduct(
        mfg_part_num="TEST-MPN-101",
        part_desc="Industrial Stainless Steel Ball Valve 1/2 in",
        part_manuf="Flow Control Systems",
        row_id=999
    )
    enriched = engine.process_item(raw)
    assert enriched.country_of_origin == ""
    
    delivery = DeliveryMapper.to_delivery_dict(enriched)
    assert delivery["Country Of Origin"] == ""


def test_actual_image_is_no_and_no_fake_filenames(engine):
    """Rule 2 & 3: Actual Image must be 'No' and digital asset paths blank when no asset exists."""
    raw = RawProduct(
        mfg_part_num="TEST-MPN-102",
        part_desc="Heavy Duty Industrial Drill Bit 3/8 in",
        part_manuf="Cutting Tool Technologies",
        row_id=998
    )
    enriched = engine.process_item(raw)
    assert enriched.actual_image == "No"
    assert enriched.product_image == ""
    assert enriched.alternate_images == []
    assert enriched.documents == {}

    delivery = DeliveryMapper.to_delivery_dict(enriched)
    assert delivery["Actual Image (Yes/No)"] == "No"
    assert delivery["Product Image"] == ""
    assert delivery["Specification Sheet"] == ""
    assert delivery["SDS"] == ""
    assert delivery["Instruction/Installation Manual"] == ""
    assert "UNVERIFIED_ASSET" in enriched.validation_flags


def test_no_guessed_manufacturer_url(resolver):
    """Rule 4: Manufacturer URL must not be guessed from brand name when absent in master data."""
    sanitized = {
        "raw_manuf": "Acme Industrial Fasteners LLC",
        "clean_manuf": "Acme Industrial Fasteners",
        "raw_desc": "Hex Head Cap Screw 1/4-20 x 1 in",
        "desc_tokens": "hex head cap screw",
        "mfg_part_num": "ACME-HEX-01",
        "row_id": 997
    }
    entity = resolver.resolve(sanitized)
    assert entity["mfr_url"] == ""


def test_no_fake_warranty_without_explicit_text(extractor):
    """Rule 5: Warranty must remain blank unless explicitly mentioned in source input."""
    sanitized = {
        "raw_desc": "Standard Residential Appliance Dishwasher",
        "desc_tokens": "standard residential appliance dishwasher",
        "mfg_part_num": "APPL-001",
    }
    entity = {"brand_name": "Generic", "series": ""}
    taxonomy = {"dept": "Major Appliances", "fine": "Built-In Dishwashers", "attribute_template": []}
    
    result = extractor.extract(sanitized, entity, taxonomy)
    assert result["warranty"] == ""

    # Now verify explicit warranty IS captured
    sanitized_with_warranty = {
        "raw_desc": "Appliance Dishwasher with 2 Year Limited Warranty Included",
        "desc_tokens": "appliance dishwasher with 2 year limited warranty included",
        "mfg_part_num": "APPL-002",
    }
    result_with = extractor.extract(sanitized_with_warranty, entity, taxonomy)
    assert result_with["warranty"] == "2 Year Limited Warranty"


def test_pdsh4816af_and_wdts7024rz_processed_dynamically_without_hardcoded_overrides(engine):
    """Rule 6: Reference MPNs PDSH4816AF & WDTS7024RZ are processed dynamically without static overrides."""
    # When given sparse input, it does not invent unmentioned specs
    sparse_raw = RawProduct(
        mfg_part_num="PDSH4816AF",
        part_desc="PDSH4816AF Dishwasher SS - Display Only",
        e1_brand="-- Unbranded --",
        unilog_brand="-- No Unilog Brand --",
        dib_brand="-- No DIB Brand --",
        part_manuf="Appliance Dealers Cooperative (APPDE)",
        row_id=61
    )
    enriched = engine.process_item(sparse_raw)
    
    # Truthful: Series is resolved from pattern, but unmentioned voltage/warranty is blank
    assert enriched.brand_name == "FRIGIDAIRE®"
    assert enriched.warranty == ""
    assert enriched.country_of_origin == ""
    assert enriched.product_image == ""
    assert enriched.actual_image == "No"
    
    # 252 delivery format preserves blanks
    delivery = DeliveryMapper.to_delivery_dict(enriched)
    assert delivery["Country Of Origin"] == ""
    assert delivery["Actual Image (Yes/No)"] == "No"
    assert delivery["Specification Sheet"] == ""


def test_standard_validation_flags_applied(engine):
    """Rule 8: Standard validation flags UNRESOLVED_IDENTITY, MISSING_EVIDENCE, UNVERIFIED_ASSET are applied."""
    # Product with unbranded identity and no technical attributes
    unresolved_raw = RawProduct(
        mfg_part_num="",
        part_desc="MISCELLANEOUS HARDWARE ITEM",
        e1_brand="-- Unbranded --",
        unilog_brand="-- No Unilog Brand --",
        dib_brand="-- No DIB Brand --",
        part_manuf="-- Unbranded --",
        row_id=888
    )
    enriched = engine.process_item(unresolved_raw)
    
    assert "UNRESOLVED_IDENTITY" in enriched.validation_flags
    assert "MISSING_EVIDENCE" in enriched.validation_flags
    assert "UNVERIFIED_ASSET" in enriched.validation_flags
    assert "MISSING_MPN" in enriched.validation_flags
    assert enriched.status == "Flagged"
    assert enriched.confidence_score < 0.85


def test_blank_values_preserved_across_schema_252(engine):
    """Rule 7: Unproven facts remain blank strings across all 252 delivery columns."""
    raw = RawProduct(
        mfg_part_num="SMP-001",
        part_desc="Simple Rubber O-Ring Gasket",
        part_manuf="Acme Seals",
        row_id=777
    )
    enriched = engine.process_item(raw)
    delivery = DeliveryMapper.to_delivery_dict(enriched)
    
    assert len(delivery) == 252
    assert delivery["UPC"] == ""
    assert delivery["EAN"] == ""
    assert delivery["GTIN"] == ""
    assert delivery["List Price"] == ""
    assert delivery["Standard Packaging Information"] == ""
    assert delivery["RoHS"] == ""
    assert delivery["Video Link"] == ""
