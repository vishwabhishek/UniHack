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
    PhysicalDimensionsSchema,
    ProductFieldReviewResponse,
    FieldActionPayload,
    PromoteValidatedResponse,
    AuditRecordSchema
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

        prov_sum_schema = None
        if hasattr(p, "provenance_summary") and p.provenance_summary:
            ps = p.provenance_summary
            from ..schemas import ProductProvenanceSummarySchema
            prov_sum_schema = ProductProvenanceSummarySchema(
                total_fields_tracked=ps.total_fields_tracked,
                verified_fields_count=ps.verified_fields_count,
                candidate_fields_count=ps.candidate_fields_count,
                missing_evidence_count=ps.missing_evidence_count,
                rejected_fields_count=ps.rejected_fields_count,
                verification_score=ps.verification_score,
                primary_sources_breakdown=ps.primary_sources_breakdown
            )

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
                raw_manufacturer=p.raw.part_manuf or "",
                provenance_summary=prov_sum_schema
            )
        )

    return ReviewQueueResponse(
        items=review_items,
        total=len(review_items),
        flagged_count=flagged_cnt,
        low_confidence_count=low_conf_cnt
    )


@router.get("/{product_id}/fields", response_model=ProductFieldReviewResponse)
def get_product_field_review(product_id: str, current_user: User = Depends(get_current_user)):
    """Retrieve structured field-level evidence review items and audit trail for a product."""
    data = catalog_state.get_product_field_review(product_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Product with ID '{product_id}' not found.")
    return data


@router.post("/{product_id}/field-action", response_model=ProductFieldReviewResponse)
def submit_field_action(
    product_id: str,
    payload: FieldActionPayload,
    current_user: User = Depends(require_roles(["admin", "specialist", "reviewer"]))
):
    """
    Apply a granular field curation action (approve, edit, reject, mark_unknown).
    Role enforcement:
    - 'edit': specialist, reviewer, admin
    - 'approve', 'reject', 'mark_unknown': reviewer, admin
    """
    if payload.action in ("approve", "reject", "mark_unknown") and current_user.role not in ("reviewer", "admin"):
        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: Action '{payload.action}' requires 'reviewer' or 'admin' role. Your role is '{current_user.role}'."
        )

    updated_review = catalog_state.apply_field_action(
        key=product_id,
        field_name=payload.field_name,
        action=payload.action,
        new_value=payload.new_value,
        reason=payload.reason,
        reviewer=current_user.email or current_user.name
    )
    if not updated_review:
        raise HTTPException(status_code=404, detail=f"Product with ID '{product_id}' not found.")
    return updated_review


@router.post("/{product_id}/promote-to-validated", response_model=PromoteValidatedResponse)
@router.post("/{product_id}/promote-validated", response_model=PromoteValidatedResponse)
def promote_to_validated(
    product_id: str,
    payload: Optional[ApprovalPayload] = None,
    current_user: User = Depends(require_roles(["admin", "reviewer"]))
):
    """
    Promote a product to 'Validated' status.
    Rejects promotion if any high-risk field is unresolved, missing evidence, or conflicting.
    """
    notes = payload.notes if payload else ""
    success, msg, unresolved = catalog_state.promote_to_validated(
        key=product_id,
        reviewer=current_user.email or current_user.name,
        notes=notes
    )
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Promotion blocked: {msg}. Unresolved high-risk fields: {', '.join(unresolved)}"
        )

    return PromoteValidatedResponse(
        success=True,
        product_id=product_id,
        status="Validated",
        message=msg,
        unresolved_high_risk_fields=unresolved
    )


@router.get("/{product_id}/audit-trail", response_model=List[AuditRecordSchema])
def get_product_audit_trail(product_id: str, current_user: User = Depends(get_current_user)):
    """Retrieve complete immutable audit history for a product."""
    data = catalog_state.get_product_field_review(product_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Product with ID '{product_id}' not found.")
    return data.audit_trail


@router.post("/{product_id}/approve", response_model=ApprovalResponse)
def approve_product(
    product_id: str,
    payload: Optional[ApprovalPayload] = None,
    current_user: User = Depends(require_roles(["admin", "reviewer"]))
):
    """
    Approve a product record for production delivery.
    Strictly passes through the guarded promote_to_validated workflow to ensure
    that all high-risk fields have verified evidence or explicit human resolution.
    """
    notes = payload.notes if payload else ""
    success, msg, unresolved = catalog_state.promote_to_validated(
        key=product_id,
        reviewer=current_user.email or current_user.name,
        notes=notes
    )
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Promotion blocked: {msg}. Unresolved high-risk fields: {', '.join(unresolved)}"
        )

    return ApprovalResponse(
        success=True,
        status="Validated",
        id=product_id,
        message=f"Product {product_id} successfully approved and promoted to Validated."
    )


@router.post("/{product_id}/reject", response_model=ApprovalResponse)
def reject_product(
    product_id: str,
    payload: Optional[ApprovalPayload] = None,
    current_user: User = Depends(require_roles(["admin", "reviewer"]))
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


@router.get("/{product_id}/timeline")
def get_product_timeline(
    product_id: str,
    current_user: User = Depends(get_current_user)
):
    """Retrieve the unified chronological activity timeline for a product."""
    from ..db.repositories.audit import audit_repo
    res = catalog_state.get_product(product_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Product with ID '{product_id}' not found.")
    prod, _ = res
    mpn = prod.mfg_part_number or prod.part_number
    timeline = audit_repo.get_product_activity_timeline(product_id=product_id, mpn=mpn)
    return {
        "product_id": product_id,
        "mpn": mpn,
        "total_events": len(timeline),
        "timeline": timeline,
    }

