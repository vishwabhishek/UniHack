"""
Catalog Exploration, Search, Detail, and Statistics Endpoints.
"""

import math
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends

from ..auth import User, get_current_user
from ..state import catalog_state
from ..schemas import (
    ProductListResponse,
    ProductListItem,
    ProductDetailResponse,
    CatalogStatsResponse,
    FilterOptionsResponse,
    AttributeTripleSchema,
    PhysicalDimensionsSchema,
    EvidenceRecordSchema,
    ProductProvenanceSummarySchema,
    TaxonomyCandidateSchema,
    TaxonomyExplanationSchema
)

router = APIRouter(prefix="/api", tags=["Catalog"])


@router.get("/products", response_model=ProductListResponse)
def get_products(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=1000, description="Items per page"),
    search: Optional[str] = Query(None, description="Search across MPN, descriptions, brand, category"),
    status: Optional[str] = Query(None, description="Filter by status (Validated, Enriched, Flagged, Draft)"),
    category: Optional[str] = Query(None, description="Filter by department / category"),
    brand: Optional[str] = Query(None, description="Filter by canonical brand name"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    max_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Maximum confidence threshold"),
    sort_by: str = Query("row_id", description="Sort field (row_id, confidence, mfg_part_num, brand, status)"),
    sort_dir: str = Query("asc", description="Sort direction (asc, desc)"),
    current_user: User = Depends(get_current_user)
):
    """Retrieve paginated and filtered catalog records."""
    products, total = catalog_state.list_products(
        search=search,
        status=status,
        category=category,
        brand=brand,
        min_confidence=min_confidence,
        max_confidence=max_confidence,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_dir=sort_dir
    )

    items: List[ProductListItem] = []
    for p in products:
        row_id_val = p.raw.row_id or 1
        items.append(
            ProductListItem(
                id=str(row_id_val),
                row_id=row_id_val,
                part_number=p.part_number,
                sku=p.sku,
                mfg_part_number=p.mfg_part_number,
                brand_name=p.brand_name,
                manufacturer_name=p.manufacturer_name,
                classpath=p.classpath,
                product_name=p.product_name,
                dept=p.dept or "General",
                invoice_desc=p.invoice_desc,
                invoice_desc_len=len(p.invoice_desc),
                mobile_desc=p.mobile_desc,
                mobile_desc_len=len(p.mobile_desc),
                short_desc=p.short_desc,
                confidence_score=p.confidence_score,
                status=p.status,
                validation_flags=p.validation_flags
            )
        )

    total_pages = math.ceil(total / limit) if limit > 0 else 1

    return ProductListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )


@router.get("/products/{product_id}", response_model=ProductDetailResponse)
def get_product_detail(product_id: str, current_user: User = Depends(get_current_user)):
    """Retrieve full 252-column product detail and metadata for a single item."""
    res = catalog_state.get_product(product_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Product with ID '{product_id}' not found.")

    prod, deliv_dict = res
    row_id_val = prod.raw.row_id or 1

    # Convert attribute triples with evidence records
    attr_schemas = [
        AttributeTripleSchema(
            label=a.label,
            value=a.value,
            uom=a.uom or "",
            evidence_records=[
                EvidenceRecordSchema(
                    field_name=ev.field_name,
                    candidate_value=ev.candidate_value,
                    normalized_value=ev.normalized_value,
                    source_url=ev.source_url,
                    source_type=ev.source_type,
                    source_title=ev.source_title,
                    source_page_or_section=ev.source_page_or_section,
                    evidence_excerpt=ev.evidence_excerpt,
                    extraction_method=ev.extraction_method,
                    retrieved_at=ev.retrieved_at,
                    confidence=ev.confidence,
                    verification_status=ev.verification_status,
                    dictionary_identity=ev.dictionary_identity
                )
                for ev in getattr(a, "evidence_records", [])
            ]
        )
        for a in prod.attributes
    ]

    # Convert dimensions
    dim_schema = PhysicalDimensionsSchema(
        length=prod.dimensions.length,
        length_uom=prod.dimensions.length_uom,
        height=prod.dimensions.height,
        height_uom=prod.dimensions.height_uom,
        width=prod.dimensions.width,
        width_uom=prod.dimensions.width_uom,
        weight=prod.dimensions.weight,
        weight_uom=prod.dimensions.weight_uom,
        volume=prod.dimensions.volume,
        volume_uom=prod.dimensions.volume_uom
    )

    # Convert field_evidence dictionary
    ev_dict = {}
    if hasattr(prod, "field_evidence") and prod.field_evidence:
        for fname, records in prod.field_evidence.items():
            ev_dict[fname] = [
                EvidenceRecordSchema(
                    field_name=r.field_name,
                    candidate_value=r.candidate_value,
                    normalized_value=r.normalized_value,
                    source_url=r.source_url,
                    source_type=r.source_type,
                    source_title=r.source_title,
                    source_page_or_section=r.source_page_or_section,
                    evidence_excerpt=r.evidence_excerpt,
                    extraction_method=r.extraction_method,
                    retrieved_at=r.retrieved_at,
                    confidence=r.confidence,
                    verification_status=r.verification_status,
                    dictionary_identity=r.dictionary_identity
                )
                for r in records
            ]

    prov_sum_schema = None
    if hasattr(prod, "provenance_summary") and prod.provenance_summary:
        ps = prod.provenance_summary
        prov_sum_schema = ProductProvenanceSummarySchema(
            total_fields_tracked=ps.total_fields_tracked,
            verified_fields_count=ps.verified_fields_count,
            candidate_fields_count=ps.candidate_fields_count,
            missing_evidence_count=ps.missing_evidence_count,
            rejected_fields_count=ps.rejected_fields_count,
            verification_score=ps.verification_score,
            primary_sources_breakdown=ps.primary_sources_breakdown
        )

    # Convert taxonomy candidates and explanation
    tax_candidates = []
    if hasattr(prod, "taxonomy_candidates") and prod.taxonomy_candidates:
        for c in prod.taxonomy_candidates:
            tax_candidates.append(
                TaxonomyCandidateSchema(
                    classpath=c.classpath,
                    unspsc=c.unspsc,
                    dept=c.dept,
                    class_name=c.class_name,
                    fine=c.fine,
                    product_name=c.product_name,
                    matching_terms=c.matching_terms,
                    score=c.score,
                    source_evidence=c.source_evidence,
                    rule_confidence=c.rule_confidence,
                    evidence_confidence=c.evidence_confidence,
                    tie_break_reason=c.tie_break_reason
                )
            )

    tax_explanation_schema = None
    if hasattr(prod, "taxonomy_explanation") and prod.taxonomy_explanation:
        te = prod.taxonomy_explanation
        tax_explanation_schema = TaxonomyExplanationSchema(
            selected_classpath=te.selected_classpath,
            selected_unspsc=te.selected_unspsc,
            is_ambiguous=te.is_ambiguous,
            is_fallback=te.is_fallback,
            top_candidates=tax_candidates,
            rationale=te.rationale,
            routing_decision=te.routing_decision
        )

    return ProductDetailResponse(
        id=str(row_id_val),
        row_id=row_id_val,
        part_number=prod.part_number,
        sku=prod.sku,
        mfg_part_number=prod.mfg_part_number,
        alternate_part_number=prod.alternate_part_number or "",
        upc=prod.upc or "",
        ean=prod.ean or "",
        gtin=prod.gtin or "",
        unspsc=prod.unspsc,
        raw=prod.raw.model_dump(),
        dept=prod.dept,
        class_name=prod.class_name,
        fine=prod.fine,
        manufacturer_name=prod.manufacturer_name,
        brand_name=prod.brand_name,
        trade_name=prod.trade_name or "",
        mfr_url=prod.mfr_url or "",
        ref_urls=prod.ref_urls or [],
        classpath=prod.classpath,
        product_name=prod.product_name,
        taxonomy_candidates=tax_candidates,
        taxonomy_explanation=tax_explanation_schema,
        invoice_desc=prod.invoice_desc,
        invoice_desc_len=len(prod.invoice_desc),
        mobile_desc=prod.mobile_desc,
        mobile_desc_len=len(prod.mobile_desc),
        short_desc=prod.short_desc,
        long_desc1=prod.long_desc1,
        retail_desc=prod.retail_desc,
        marketing_description=prod.marketing_description,
        item_features=prod.item_features,
        with_spec=prod.with_spec or "",
        standard_approvals=prod.standard_approvals or "",
        prop_65=prod.prop_65 or "",
        application=prod.application or "",
        includes=prod.includes or "",
        attributes=attr_schemas,
        dimensions=dim_schema,
        warranty=prod.warranty or "",
        list_price=prod.list_price or "",
        selling_qty=prod.selling_qty or "1",
        selling_uom=prod.selling_uom or "EA",
        country_of_origin=prod.country_of_origin or "",
        product_image=prod.product_image or "",
        alternate_images=prod.alternate_images or [],
        actual_image=prod.actual_image or "No",
        documents=prod.documents or {},
        confidence_score=prod.confidence_score,
        confidence_breakdown=prod.confidence_breakdown,
        validation_flags=prod.validation_flags,
        field_evidence=ev_dict,
        provenance_summary=prov_sum_schema,
        field_provenance={k: (v.model_dump() if hasattr(v, "model_dump") else v) for k, v in prod.field_provenance.items()},
        status=prod.status,
        delivery_columns=deliv_dict
    )


@router.get("/stats", response_model=CatalogStatsResponse)
def get_catalog_stats(current_user: User = Depends(get_current_user)):
    """Retrieve catalog KPI counters, compliance pass rates, and category/brand distributions."""
    return catalog_state.get_stats()


@router.get("/filters", response_model=FilterOptionsResponse)
def get_filter_facets(current_user: User = Depends(get_current_user)):
    """Retrieve distinct status, category, and brand options with item counts."""
    return catalog_state.get_filter_options()


@router.get("/products/{product_id}/graph")
def get_product_knowledge_graph(product_id: str, current_user: User = Depends(get_current_user)):
    """Generate relational knowledge graph nodes and edges for a catalog product."""
    res = catalog_state.get_product(product_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Product with ID '{product_id}' not found.")

    prod, _ = res
    row_id_val = prod.raw.row_id or 1

    nodes = [
        {"id": f"raw_{row_id_val}", "label": prod.raw.part_desc[:30] + "...", "type": "raw_input", "group": "Source Feed", "color": "#EF5A5A"},
        {"id": f"prod_{row_id_val}", "label": prod.mfg_part_number, "type": "product", "group": "Master SKU", "color": "#45E0D6"},
        {"id": f"mfr_{prod.manufacturer_name}", "label": prod.manufacturer_name, "type": "manufacturer", "group": "Manufacturer", "color": "#8B93A3"},
        {"id": f"brand_{prod.brand_name}", "label": prod.brand_name, "type": "brand", "group": "Brand Entity", "color": "#45E0D6"},
        {"id": f"unspsc_{prod.unspsc}", "label": f"UNSPSC {prod.unspsc}", "type": "unspsc", "group": "Standard Taxonomy", "color": "#3DDC84"},
        {"id": f"dept_{prod.dept}", "label": prod.dept, "type": "department", "group": "Taxonomy Level 1", "color": "#E8A33D"},
        {"id": f"class_{prod.class_name}", "label": prod.class_name, "type": "class", "group": "Taxonomy Level 2", "color": "#E8A33D"},
        {"id": f"fine_{prod.fine}", "label": prod.fine, "type": "fine", "group": "Taxonomy Level 3", "color": "#E8A33D"},
    ]

    edges = [
        {"source": f"raw_{row_id_val}", "target": f"prod_{row_id_val}", "label": "RESOLVED_INTO"},
        {"source": f"prod_{row_id_val}", "target": f"mfr_{prod.manufacturer_name}", "label": "MANUFACTURED_BY"},
        {"source": f"mfr_{prod.manufacturer_name}", "target": f"brand_{prod.brand_name}", "label": "OWNS_BRAND"},
        {"source": f"prod_{row_id_val}", "target": f"brand_{prod.brand_name}", "label": "BRANDED_AS"},
        {"source": f"prod_{row_id_val}", "target": f"unspsc_{prod.unspsc}", "label": "STANDARDIZED_AS"},
        {"source": f"unspsc_{prod.unspsc}", "target": f"dept_{prod.dept}", "label": "MAPS_TO_DEPT"},
        {"source": f"dept_{prod.dept}", "target": f"class_{prod.class_name}", "label": "CONTAINS_CLASS"},
        {"source": f"class_{prod.class_name}", "target": f"fine_{prod.fine}", "label": "CONTAINS_FINE"},
        {"source": f"prod_{row_id_val}", "target": f"fine_{prod.fine}", "label": "CLASSIFIED_AS"},
    ]

    # Add Attribute LOV specification nodes
    for idx, attr in enumerate(prod.attributes[:8]):
        attr_node_id = f"attr_{row_id_val}_{idx}"
        nodes.append({
            "id": attr_node_id,
            "label": f"{attr.label}: {attr.value} {attr.uom or ''}".strip(),
            "type": "attribute_lov",
            "group": "LOV Specification",
            "color": "#3DDC84"
        })
        edges.append({
            "source": f"prod_{row_id_val}",
            "target": attr_node_id,
            "label": "HAS_SPECIFICATION"
        })

    return {
        "product_id": str(row_id_val),
        "mfg_part_number": prod.mfg_part_number,
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "ontology_depth": 4,
            "lov_conformance": "100%"
        }
    }
