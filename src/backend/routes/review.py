"""
Human-In-The-Loop (HITL) Review Queue, Product Editor, and Approval Endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Path, Depends

from ..auth import User, get_current_user, require_roles
from ..state import catalog_state
from ..schemas import (
    ReviewQueueResponse,
    ReviewItem,
    ProductUpdatePayload,
    ProductDetailResponse,
    ApprovalPayload,
    ApprovalResponse,
    AttributeTripleSchema,
    PhysicalDimensionsSchema
)

router = APIRouter(prefix="/api/review", tags=["Review Queue"])


@router.get("/queue", response_model=ReviewQueueResponse)
def get_review_queue(current_user: User = Depends(get_current_user)):
    """Fetch all products requiring human review (confidence < 0.85 or flagged status)."""
    items = catalog_state.get_review_queue()

    review_items: List[ReviewItem] = []
    flagged_cnt = 0
    low_conf_cnt = 0

    for p in items:
        row_id_val = p.raw.row_id or 1
        if p.status == "Flagged":
            flagged_cnt += 1
        if p.confidence_score < 0.85:
            low_conf_cnt += 1

        review_items.append(
            ReviewItem(
                id=str(row_id_val),
                row_id=row_id_val,
                part_number=p.part_number,
                mfg_part_num=p.mfg_part_number,
                brand_name=p.brand_name,
                manufacturer_name=p.manufacturer_name,
                classpath=p.classpath,
                invoice_desc=p.invoice_desc,
                mobile_desc=p.mobile_desc,
                short_desc=p.short_desc,
                confidence_score=p.confidence_score,
                status=p.status,
                anomaly_flags=p.validation_flags,
                raw_part_desc=p.raw.part_desc,
                raw_manufacturer=p.raw.part_manuf or ""
            )
        )

    return ReviewQueueResponse(
        items=review_items,
        total=len(review_items),
        flagged_count=flagged_cnt,
        low_confidence_count=low_conf_cnt
    )


@router.post("/{product_id}/approve", response_model=ApprovalResponse)
def approve_product(
    product_id: str,
    payload: Optional[ApprovalPayload] = None,
    current_user: User = Depends(require_roles(["admin", "specialist", "reviewer"]))
):
    """Approve a product record for production delivery, promoting status to 'Validated'."""
    notes = payload.notes if payload else ""
    prod = catalog_state.approve_product(product_id, notes=notes)
    if not prod:
        raise HTTPException(status_code=404, detail=f"Product with ID '{product_id}' not found.")

    return ApprovalResponse(
        success=True,
        status="Validated",
        id=product_id,
        message=f"Product {product_id} successfully approved and marked as Validated."
    )


@router.post("/{product_id}/reject", response_model=ApprovalResponse)
def reject_product(
    product_id: str,
    payload: Optional[ApprovalPayload] = None,
    current_user: User = Depends(require_roles(["admin", "specialist", "reviewer"]))
):
    """Flag or reject a product record with feedback for review."""
    reason = payload.notes if (payload and payload.notes) else "Rejected by human reviewer"
    prod = catalog_state.reject_product(product_id, reason=reason)
    if not prod:
        raise HTTPException(status_code=404, detail=f"Product with ID '{product_id}' not found.")

    return ApprovalResponse(
        success=True,
        status="Flagged",
        id=product_id,
        message=f"Product {product_id} marked as Flagged."
    )


@router.put("/{product_id}", response_model=ProductDetailResponse)
def update_product_detail(
    product_id: str,
    payload: ProductUpdatePayload,
    current_user: User = Depends(require_roles(["admin", "specialist"]))
):
    """Apply manual edits to descriptions, taxonomy, brand, or attributes."""
    prod = catalog_state.update_product(product_id, payload.model_dump(exclude_unset=True))
    if not prod:
        raise HTTPException(status_code=404, detail=f"Product with ID '{product_id}' not found.")

    res = catalog_state.get_product(product_id)
    _, deliv_dict = res
    row_id_val = prod.raw.row_id or 1

    attr_schemas = [
        AttributeTripleSchema(label=a.label, value=a.value, uom=a.uom or "")
        for a in prod.attributes
    ]

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
        product_image=prod.product_image or "",
        alternate_images=prod.alternate_images or [],
        actual_image=prod.actual_image or "No",
        documents=prod.documents or {},
        confidence_score=prod.confidence_score,
        confidence_breakdown=prod.confidence_breakdown,
        validation_flags=prod.validation_flags,
        status=prod.status,
        delivery_columns=deliv_dict
    )
