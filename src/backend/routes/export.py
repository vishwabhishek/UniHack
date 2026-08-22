"""
252-Column Catalog Export Endpoints (CSV, Excel & Column Metadata).
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Response, Query, Depends
from fastapi.responses import Response

from ..auth import User, get_current_user
from ..state import catalog_state
from src.pipeline.delivery_mapper import DeliveryMapper

router = APIRouter(prefix="/api/export", tags=["Export"])


import hashlib
from ..db.repositories.exports import export_repo
from ..db.repositories.audit import audit_repo


@router.get("/csv")
def export_catalog_csv(
    status: Optional[str] = Query(None, description="Optional status filter (e.g. Validated, Enriched)"),
    search: Optional[str] = Query(None, description="Optional search filter"),
    current_user: User = Depends(get_current_user)
):
    """Stream full 252-column CSV file for the active or filtered catalog with audit tracking."""
    df = catalog_state.get_export_dataframe(status=status, search=search, sanitize_formulas=True)
    csv_bytes = catalog_state.get_export_csv_bytes(status=status, search=search)
    checksum = hashlib.sha256(csv_bytes).hexdigest()

    try:
        export_repo.record_export(
            user_email=current_user.email,
            user_id=current_user.id,
            schema_version="v1.0.0 (252-Column Unilog Delivery)",
            product_count=len(df),
            checksum_sha256=checksum,
            filters={"status": status, "search": search},
        )
        audit_repo.record_action(
            user_email=current_user.email,
            user_id=current_user.id,
            role=current_user.role,
            action="CATALOG_EXPORT_CSV",
            entity_type="export",
            entity_id=checksum[:12],
            after_state={"product_count": len(df), "checksum_sha256": checksum, "filters": {"status": status, "search": search}},
            reason="User downloaded 252-column CSV delivery export",
        )
    except Exception:
        pass

    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="unilog_enriched_catalog_252_columns.csv"',
            "X-Export-Checksum": checksum,
        }
    )


@router.get("/xlsx")
def export_catalog_excel(
    status: Optional[str] = Query(None, description="Optional status filter"),
    search: Optional[str] = Query(None, description="Optional search filter"),
    current_user: User = Depends(get_current_user)
):
    """Stream full 252-column Microsoft Excel (.xlsx) file with audit tracking."""
    df = catalog_state.get_export_dataframe(status=status, search=search, sanitize_formulas=True)
    xlsx_bytes = catalog_state.get_export_excel_bytes(status=status, search=search)
    checksum = hashlib.sha256(xlsx_bytes).hexdigest()

    try:
        export_repo.record_export(
            user_email=current_user.email,
            user_id=current_user.id,
            schema_version="v1.0.0 (252-Column Unilog Delivery)",
            product_count=len(df),
            checksum_sha256=checksum,
            filters={"status": status, "search": search},
        )
    except Exception:
        pass

    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="unilog_enriched_catalog_252_columns.xlsx"',
            "X-Export-Checksum": checksum,
        }
    )


@router.get("/columns")
def get_column_definitions(current_user: User = Depends(get_current_user)):
    """Retrieve metadata, groups, and column list for all 252 Unilog delivery headers."""
    headers = DeliveryMapper.get_column_headers()
    
    # Categorize into logical functional groups
    groups = {
        "Core Identifiers (1-10)": headers[0:10],
        "Audit & Raw Inputs (11-14)": headers[10:14],
        "Entity Resolution & Brands (15-20)": headers[14:20],
        "Taxonomy & Classification (21-25)": headers[20:25],
        "5-Tier Content & Descriptions (26-31)": headers[25:31],
        "Features & Bullet Points (32-51)": headers[31:51],
        "Standard Approvals & Specs (52-54)": headers[51:54],
        "Dynamic Attributes 1-10 (55-84)": headers[54:84],
        "Dynamic Attributes 11-25 (85-129)": headers[84:129],
        "Dynamic Attributes 26-50 (130-204)": headers[129:204],
        "Physical Dimensions & Packaging (205-224)": headers[204:224],
        "Commercial & Pricing (225-236)": headers[224:236],
        "Digital Media & Assets (237-252)": headers[236:252]
    }

    return {
        "total_columns": len(headers),
        "headers": headers,
        "groups": groups
    }


@router.get("/history")
def get_export_history(
    limit: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """Retrieve historical export events, cryptographic checksums, and delivery metadata."""
    exports = export_repo.list_exports(limit=limit)
    return {
        "total_exports": len(exports),
        "exports": exports,
    }

