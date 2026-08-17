"""
Interactive Playground & Real-Time Transformation Sandbox Endpoints.
Provides live, sub-second execution of arbitrary supplier strings with
step-by-step stage visualization.
"""

import time
from typing import List, Dict, Any
from fastapi import APIRouter

from ..state import catalog_state
from ..schemas import (
    TransformRequest,
    TransformResponse,
    PipelineStageOutput,
    PlaygroundPreset,
    AttributeTripleSchema,
    PhysicalDimensionsSchema
)
from src.pipeline.models import RawProduct, AttributeTriple
from src.pipeline.delivery_mapper import to_delivery_dict

router = APIRouter(prefix="/api/playground", tags=["Playground"])

# Predefined playground presets for 1-click testing
PRESET_SAMPLES: List[Dict[str, Any]] = [
    {
        "id": "preset-1",
        "name": "Frigidaire Built-In Dishwasher",
        "category": "Appliances",
        "mfg_part_num": "PDSH4816AF",
        "part_desc": "PDSH4816AF Dishwasher SS - Display Only",
        "part_manuf": "Appliance Dealers Cooperative (APPDE)",
        "e1_brand": "-- Unbranded --",
        "unilog_brand": "-- No Unilog Brand --",
        "dib_brand": "-- No DIB Brand --"
    },
    {
        "id": "preset-2",
        "name": "Whirlpool Built-In Dishwasher",
        "category": "Appliances",
        "mfg_part_num": "WDTS7024RZ",
        "part_desc": "WDTS7024RZ Dishwasher SS - Display Only",
        "part_manuf": "Appliance Dealers Cooperative (APPDE)",
        "e1_brand": "-- Unbranded --",
        "unilog_brand": "-- No Unilog Brand --",
        "dib_brand": "-- No DIB Brand --"
    },
    {
        "id": "preset-3",
        "name": "Diablo Sanding Belt 6-Pack",
        "category": "Abrasives & Cutting",
        "mfg_part_num": "DCB518ASTS06G",
        "part_desc": 'DCB518ASTS06G Diablo 1/2"x18" - Sanding Belt 6pc',
        "part_manuf": "Freud Inc (2435)",
        "e1_brand": "-- Unbranded --",
        "unilog_brand": "-- No Unilog Brand --",
        "dib_brand": "-- No DIB Brand --"
    },
    {
        "id": "preset-4",
        "name": "Milwaukee Metal Cut-Off Disc",
        "category": "Abrasives & Cutting",
        "mfg_part_num": "49-94-0013",
        "part_desc": '49-94-0013 Milw 5"x.045"x7/8" Metal Cut Off Disc',
        "part_manuf": "Milwaukee Accessory (4031)",
        "e1_brand": "-- Unbranded --",
        "unilog_brand": "-- No Unilog Brand --",
        "dib_brand": "-- No DIB Brand --"
    },
    {
        "id": "preset-5",
        "name": "Trex Transcend Composite Decking",
        "category": "Building Materials",
        "mfg_part_num": "PG010616TS01",
        "part_desc": "1x6-16' Transcend Island Mist Square Edge Deck Board",
        "part_manuf": "Boise Cascade Building Materials (BOICA)",
        "e1_brand": "TREX",
        "unilog_brand": "-- No Unilog Brand --",
        "dib_brand": "-- No DIB Brand --"
    },
    {
        "id": "preset-6",
        "name": "Philips LED A19 Light Bulb",
        "category": "Lighting & Electrical",
        "mfg_part_num": "929001127004",
        "part_desc": "10.5A19/LED/827/ND 120V 4/1FB Non-Dimmable Soft White",
        "part_manuf": "Phillips Lighting (5831)",
        "e1_brand": "-- Unbranded --",
        "unilog_brand": "-- No Unilog Brand --",
        "dib_brand": "Philips"
    }
]


@router.get("/presets", response_model=List[PlaygroundPreset])
def get_presets():
    """Retrieve preloaded test records for instantaneous 1-click evaluation."""
    return [PlaygroundPreset(**p) for p in PRESET_SAMPLES]


@router.post("/transform", response_model=TransformResponse)
def transform_product(payload: TransformRequest):
    """Execute live multi-stage pipeline transformation with step-by-step latency tracking."""
    engine = catalog_state.engine
    t_start = time.perf_counter()

    raw_obj = RawProduct(
        mfg_part_num=payload.mfg_part_num or "",
        part_desc=payload.part_desc,
        e1_brand=payload.e1_brand,
        unilog_brand=payload.unilog_brand,
        dib_brand=payload.dib_brand,
        part_manuf=payload.part_manuf,
        row_id=payload.row_id or 1001
    )

    stages: List[PipelineStageOutput] = []

    # Stage 1: Ingestion & Sanitization
    s1_t0 = time.perf_counter()
    sanitized = engine.sanitizer.sanitize(raw_obj)
    s1_t1 = time.perf_counter()
    stages.append(
        PipelineStageOutput(
            stage_id=1,
            stage_name="Ingestion & Placeholder Sanitizer",
            description="Strips null flags, normalizes Unicode, isolates vendor tokens & MPN",
            duration_ms=round((s1_t1 - s1_t0) * 1000, 3),
            output=sanitized
        )
    )

    # Stage 2: Canonical Entity Resolution
    s2_t0 = time.perf_counter()
    entity = engine.resolver.resolve(sanitized)
    s2_t1 = time.perf_counter()
    stages.append(
        PipelineStageOutput(
            stage_id=2,
            stage_name="Canonical Entity Resolver",
            description="Resolves distributor codes to manufacturer names & trademarked brands with symbols (®, ™)",
            duration_ms=round((s2_t1 - s2_t0) * 1000, 3),
            output=entity
        )
    )

    # Stage 3: Taxonomy & UNSPSC Classification
    s3_t0 = time.perf_counter()
    tax = engine.taxonomy.classify(sanitized, entity)
    s3_t1 = time.perf_counter()
    stages.append(
        PipelineStageOutput(
            stage_id=3,
            stage_name="Taxonomy & UNSPSC Classifier",
            description="Assigns 3-level hierarchical Classpath and 8-digit UNSPSC code",
            duration_ms=round((s3_t1 - s3_t0) * 1000, 3),
            output=tax
        )
    )

    # Stage 4 & 5: Attribute Extraction & LOV / UOM Standardization
    s4_t0 = time.perf_counter()
    attr_data = engine.extractor.extract(sanitized, entity, tax)
    s4_t1 = time.perf_counter()
    stages.append(
        PipelineStageOutput(
            stage_id=4,
            stage_name="Attribute Extractor & LOV Engine",
            description="Extracts 50-slot triplet specs, validates LOV vocabulary, formats 64th fractions & UOMs",
            duration_ms=round((s4_t1 - s4_t0) * 1000, 3),
            output={
                "attributes_count": len(attr_data.get("attributes", [])),
                "features_count": len(attr_data.get("item_features", [])),
                "attributes": [
                    {"label": a.label, "value": a.value, "uom": a.uom}
                    for a in attr_data.get("attributes", [])
                ],
                "item_features": attr_data.get("item_features", []),
                "dimensions": attr_data.get("dimensions", {}).model_dump() if hasattr(attr_data.get("dimensions", {}), "model_dump") else {}
            }
        )
    )

    # Stage 6: 5-Tier Description Generation
    s5_t0 = time.perf_counter()
    descs = engine.desc_gen.generate_all(sanitized, entity, tax, attr_data)
    s5_t1 = time.perf_counter()
    stages.append(
        PipelineStageOutput(
            stage_id=5,
            stage_name="5-Tier Description Generator",
            description="Synthesizes Invoice (<=40 CAPS), Mobile (60-80), Short, Long, and Marketing copy",
            duration_ms=round((s5_t1 - s5_t0) * 1000, 3),
            output=descs
        )
    )

    # Final Stage: Assembly into Enriched Product & Delivery Map
    s6_t0 = time.perf_counter()
    enriched = engine.process_item(raw_obj)
    delivery_map = to_delivery_dict(enriched)
    s6_t1 = time.perf_counter()
    stages.append(
        PipelineStageOutput(
            stage_id=6,
            stage_name="252-Column Delivery Mapper",
            description="Compiles all attributes, taxonomy, and digital assets into exact 252-column delivery schema",
            duration_ms=round((s6_t1 - s6_t0) * 1000, 3),
            output={"column_count": len(delivery_map), "status": enriched.status}
        )
    )

    t_total = (time.perf_counter() - t_start) * 1000

    attr_schemas = [
        AttributeTripleSchema(label=a.label, value=a.value, uom=a.uom or "")
        for a in enriched.attributes
    ]

    dim_schema = PhysicalDimensionsSchema(
        length=enriched.dimensions.length,
        length_uom=enriched.dimensions.length_uom,
        height=enriched.dimensions.height,
        height_uom=enriched.dimensions.height_uom,
        width=enriched.dimensions.width,
        width_uom=enriched.dimensions.width_uom,
        weight=enriched.dimensions.weight,
        weight_uom=enriched.dimensions.weight_uom,
        volume=enriched.dimensions.volume,
        volume_uom=enriched.dimensions.volume_uom
    )

    return TransformResponse(
        invoice_desc=enriched.invoice_desc,
        invoice_desc_len=len(enriched.invoice_desc),
        mobile_desc=enriched.mobile_desc,
        mobile_desc_len=len(enriched.mobile_desc),
        short_desc=enriched.short_desc,
        long_desc1=enriched.long_desc1,
        retail_desc=enriched.retail_desc,
        marketing_description=enriched.marketing_description,
        brand_name=enriched.brand_name,
        manufacturer_name=enriched.manufacturer_name,
        classpath=enriched.classpath,
        product_name=enriched.product_name,
        unspsc=enriched.unspsc,
        item_features=enriched.item_features,
        attributes=attr_schemas,
        dimensions=dim_schema,
        confidence_score=enriched.confidence_score,
        confidence_breakdown=enriched.confidence_breakdown,
        validation_flags=enriched.validation_flags,
        status=enriched.status,
        stages=stages,
        total_latency_ms=round(t_total, 2),
        delivery_columns=delivery_map
    )
