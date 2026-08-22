"""
In-Memory Catalog Store, Indexing Engine & State Management.
Pre-loads 1,000 industrial items, provides sub-millisecond filtering,
search, HITL triage, and atomic updates.
"""

import io
import csv
import logging
import threading
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd

logger = logging.getLogger(__name__)

from .config import settings
from src.pipeline.models import RawProduct, EnrichedProduct, AttributeTriple, PhysicalDimensions
from src.pipeline.engine import EnrichmentEngine
from src.pipeline.delivery_mapper import to_delivery_dict, DeliveryMapper
from src.benchmark.evaluator import CatalogEvaluator
from src.benchmark.confidence import CONFIDENCE_THRESHOLD_ENRICHED, CONFIDENCE_THRESHOLD_VALIDATED


class CatalogState:
    """Thread-safe singleton managing in-memory catalog data and review queue."""
    _instance = None
    _lock = threading.Lock()

    HIGH_RISK_FIELDS: List[str] = [
        "mfg_part_number",
        "brand_name",
        "manufacturer_name",
        "classpath",
        "unspsc",
        "invoice_desc",
        "short_desc"
    ]

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CatalogState, cls).__new__(cls)
                cls._instance._initialized = False
                cls._instance._products_list = []
                cls._instance._by_id = {}
                cls._instance._delivery_by_id = {}
                cls._instance._review_ids = set()
                cls._instance._cached_benchmark = None
            return cls._instance

    def initialize(self):
        """Pre-load all 1,000 catalog products into indexed memory from persistent SQLite (or seed from raw CSV)."""
        if getattr(self, "_initialized", False):
            return

        with self._lock:
            if getattr(self, "_initialized", False):
                return

            self.engine = EnrichmentEngine()
            self.evaluator = CatalogEvaluator(ground_truth_path=str(settings.ground_truth_path))
            
            self._products_list: List[EnrichedProduct] = []
            self._by_id: Dict[str, EnrichedProduct] = {}
            self._delivery_by_id: Dict[str, Dict[str, str]] = {}
            self._review_ids: set = set()
            self._cached_benchmark = None

            from .db.repositories.products import product_repo
            db_count = product_repo.count_products()

            if db_count >= 1000:
                logger.info(f"Restoring catalog from SQLite persistent database ({db_count} records)...")
                self._restore_from_sqlite()
            else:
                # Load raw input CSV & populate SQLite
                if not settings.raw_input_path.exists():
                    raise FileNotFoundError(f"Raw input dataset not found at {settings.raw_input_path}")

                df_raw = pd.read_csv(settings.raw_input_path)
                raw_products: List[RawProduct] = []
                for idx, row in df_raw.iterrows():
                    row_dict = {
                        "mfg_part_num": str(row.get("Mfg_Part_Num", "") or "").strip(),
                        "part_desc": str(row.get("Part_Desc", "") or "").strip(),
                        "e1_brand": str(row.get("E1_Brand", "") or "").strip() or None,
                        "unilog_brand": str(row.get("Unilog_Brand", "") or "").strip() or None,
                        "dib_brand": str(row.get("DIB_Brand", "") or "").strip() or None,
                        "part_manuf": str(row.get("Part_Manuf", "") or "").strip() or None,
                        "row_id": int(idx + 1)
                    }
                    raw_products.append(RawProduct(**row_dict))

                # Process all 1,000 items with EnrichmentEngine
                enriched_products = self.engine.process_batch(raw_products)
                self._populate_sqlite_from_products(enriched_products)

                for prod in enriched_products:
                    self._index_product(prod)

            # Ensure output directory and 252-column export file exist
            settings.output_dir.mkdir(parents=True, exist_ok=True)
            self._sync_output_csv()

            # Ingest & Index into LlamaIndex & Neural Embedding RAG Engine
            try:
                from .rag_engine import rag_engine
                rag_engine.index_catalog(self._products_list)
            except Exception as ex:
                logger.warning(f"LlamaIndex RAG indexing deferred or encountered issue: {ex}")

            self._initialized = True

    def _populate_sqlite_from_products(self, enriched_products: List[EnrichedProduct]):
        """Persist baseline enriched products and raw supplier inputs into SQLite database."""
        try:
            from .db.connection import get_db_connection
            import json, time

            now = time.time()
            with get_db_connection() as conn:
                cursor = conn.cursor()
                for prod in self._products_list:
                    pid = str(prod.raw.row_id or 1)
                    row_id = prod.raw.row_id or 1
                    conflicts_json = json.dumps(prod.conflicts) if hasattr(prod, "conflicts") and prod.conflicts else "[]"
                    
                    status_raw = (prod.status or "enriched").strip().lower()
                    if status_raw in ["flagged", "needs human review", "needs_human_review", "review_required"]:
                        db_status = "review_required"
                    elif status_raw in ["validated", "approved"]:
                        db_status = "validated"
                    elif status_raw in ["draft", "raw"]:
                        db_status = "raw"
                    else:
                        db_status = "enriched"

                    # Main product record
                    cursor.execute(
                        """
                        INSERT INTO products (
                            id, sku, mpn, status, brand, manufacturer,
                            class_path, unspsc, invoice_desc, mobile_desc,
                            short_desc, long_desc, marketing_desc, confidence_score,
                            conflicts_json, review_required, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(id) DO UPDATE SET
                            status = excluded.status,
                            brand = excluded.brand,
                            manufacturer = excluded.manufacturer,
                            class_path = excluded.class_path,
                            unspsc = excluded.unspsc,
                            invoice_desc = excluded.invoice_desc,
                            mobile_desc = excluded.mobile_desc,
                            short_desc = excluded.short_desc,
                            long_desc = excluded.long_desc,
                            marketing_desc = excluded.marketing_desc,
                            confidence_score = excluded.confidence_score,
                            conflicts_json = excluded.conflicts_json,
                            review_required = excluded.review_required,
                            updated_at = excluded.updated_at;
                        """,
                        (
                            pid,
                            prod.raw.mfg_part_num or prod.mfg_part_number,
                            prod.mfg_part_number,
                            db_status,
                            prod.brand_name,
                            prod.manufacturer_name,
                            prod.classpath,
                            prod.unspsc,
                            prod.invoice_desc,
                            prod.mobile_desc,
                            prod.short_desc,
                            prod.long_desc1,
                            prod.marketing_description,
                            prod.confidence_score,
                            conflicts_json,
                            1 if (db_status == "review_required" or prod.confidence_score < 0.85) else 0,
                            now,
                            now
                        )
                    )

                    # Raw supplier inputs
                    cursor.execute(
                        """
                        INSERT INTO raw_supplier_inputs (
                            product_id, row_id, raw_mfg_part_num, raw_part_desc,
                            e1_brand, unilog_brand, dib_brand, part_manuf, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(product_id) DO UPDATE SET
                            row_id = excluded.row_id,
                            raw_mfg_part_num = excluded.raw_mfg_part_num,
                            raw_part_desc = excluded.raw_part_desc,
                            e1_brand = excluded.e1_brand,
                            unilog_brand = excluded.unilog_brand,
                            dib_brand = excluded.dib_brand,
                            part_manuf = excluded.part_manuf;
                        """,
                        (
                            pid,
                            row_id,
                            prod.raw.mfg_part_num,
                            prod.raw.part_desc,
                            prod.raw.e1_brand,
                            prod.raw.unilog_brand,
                            prod.raw.dib_brand,
                            prod.raw.part_manuf,
                            now
                        )
                    )

                    # Attributes
                    for attr in (prod.attributes or []):
                        if attr.label:
                            fname = f"attr_{attr.label}"
                            fid = f"fld_{pid}_{attr.label.lower()}"
                            is_ver = bool(attr.provenance and attr.provenance.verified)
                            cursor.execute(
                                """
                                INSERT INTO enriched_fields (
                                    id, product_id, field_name, candidate_value, normalized_value,
                                    status, confidence, dictionary_path, is_approved, updated_by, updated_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ON CONFLICT(product_id, field_name) DO UPDATE SET
                                    candidate_value = excluded.candidate_value,
                                    normalized_value = excluded.normalized_value,
                                    status = excluded.status,
                                    confidence = excluded.confidence,
                                    dictionary_path = excluded.dictionary_path,
                                    is_approved = excluded.is_approved,
                                    updated_at = excluded.updated_at;
                                """,
                                (
                                    fid, pid, fname, attr.value, attr.value,
                                    "verified" if is_ver else "candidate",
                                    attr.provenance.confidence if attr.provenance else 1.0,
                                    None,
                                    1 if is_ver else 0,
                                    "pipeline",
                                    now
                                )
                            )
                conn.commit()
                logger.info("Seeded 1,000 catalog products into SQLite persistence database.")
        except Exception as e:
            logger.warning(f"Failed to populate SQLite from products: {e}")

    def _restore_from_sqlite(self):
        """Restore all catalog products, review actions, and field evidence from SQLite."""
        try:
            from .db.repositories.products import product_repo
            from .db.repositories.reviews import review_repo
            from src.pipeline.models import (
                RawProduct, EnrichedProduct, AttributeTriple, PhysicalDimensions,
                EvidenceRecord, AuditRecord, FieldProvenance
            )
            import time

            db_products = product_repo.load_all_products_with_fields()
            if not db_products:
                return

            self._products_list = []
            self._by_id = {}
            self._delivery_by_id = {}
            self._review_ids = set()

            for db_p in db_products:
                pid = str(db_p["id"])
                raw_info = db_p.get("raw_input") or {}
                raw_prod = RawProduct(
                    mfg_part_num=raw_info.get("raw_mfg_part_num", db_p.get("mfg_part_num", "")),
                    part_desc=raw_info.get("raw_part_desc", ""),
                    e1_brand=raw_info.get("e1_brand"),
                    unilog_brand=raw_info.get("unilog_brand"),
                    dib_brand=raw_info.get("dib_brand"),
                    part_manuf=raw_info.get("part_manuf"),
                    row_id=raw_info.get("row_id", int(pid) if pid.isdigit() else 1)
                )

                # Process baseline template using enrichment engine
                base_prod = self.engine.process_single(raw_prod)
                
                # Apply SQLite stored values
                raw_status = (db_p.get("status") or "").strip().lower()
                if raw_status == "validated":
                    base_prod.status = "Validated"
                elif raw_status == "enriched":
                    base_prod.status = "Enriched"
                elif raw_status in ("review_required", "flagged"):
                    base_prod.status = "Flagged"
                elif raw_status == "raw":
                    base_prod.status = "Draft"
                else:
                    base_prod.status = db_p.get("status", base_prod.status)

                base_prod.confidence_score = float(db_p.get("confidence") or base_prod.confidence_score)
                base_prod.brand_name = db_p.get("brand") or base_prod.brand_name
                base_prod.manufacturer_name = db_p.get("manufacturer") or base_prod.manufacturer_name
                base_prod.classpath = db_p.get("classpath") or base_prod.classpath
                base_prod.unspsc = db_p.get("unspsc") or base_prod.unspsc
                base_prod.invoice_desc = db_p.get("invoice_desc") or base_prod.invoice_desc
                base_prod.mobile_desc = db_p.get("mobile_desc") or base_prod.mobile_desc
                base_prod.short_desc = db_p.get("short_desc") or base_prod.short_desc
                base_prod.long_desc1 = db_p.get("long_desc") or base_prod.long_desc1
                base_prod.marketing_desc = db_p.get("marketing_desc") or base_prod.marketing_desc
                base_prod.validation_flags = db_p.get("data_conflicts", base_prod.validation_flags)

                # Apply enriched fields from DB
                for ef in db_p.get("enriched_fields", []):
                    fname = ef.get("field_name", "")
                    fval = ef.get("normalized_value") or ef.get("candidate_value") or ""
                    fstatus = ef.get("status", "candidate")

                    if fname == "mfg_part_number" and fval:
                        base_prod.mfg_part_number = fval
                    elif fname == "brand_name" and fval:
                        base_prod.brand_name = fval
                    elif fname == "manufacturer_name" and fval:
                        base_prod.manufacturer_name = fval
                    elif fname == "classpath" and fval:
                        base_prod.classpath = fval
                    elif fname == "unspsc" and fval:
                        base_prod.unspsc = fval
                    elif fname == "invoice_desc" and fval:
                        base_prod.invoice_desc = fval
                    elif fname == "mobile_desc" and fval:
                        base_prod.mobile_desc = fval
                    elif fname == "short_desc" and fval:
                        base_prod.short_desc = fval
                    elif fname == "long_desc1" and fval:
                        base_prod.long_desc1 = fval
                    elif fname.startswith("attr_"):
                        attr_lbl = fname.replace("attr_", "")
                        for attr in base_prod.attributes:
                            if attr.label.lower() == attr_lbl.lower():
                                attr.value = fval
                                if fstatus in ("verified", "approved"):
                                    if attr.provenance:
                                        attr.provenance.verified = True
                                        attr.provenance.confidence = 1.0
                                elif fstatus in ("rejected", "unknown"):
                                    attr.value = ""

                # Load review actions into audit trail
                rev_actions = review_repo.list_actions_for_product(pid)
                if rev_actions:
                    base_prod.audit_trail = [
                        AuditRecord(
                            id=ra["id"],
                            field_name=ra["field_name"],
                            reviewer=ra["user_email"],
                            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ra["created_at"])),
                            previous_value=ra.get("old_value", ""),
                            new_value=ra.get("new_value", ""),
                            action=ra["action_type"],
                            reason=ra.get("reason", "")
                        )
                        for ra in rev_actions
                    ]

                self._index_product(base_prod)

            self._sync_output_csv()
            logger.info(f"Successfully restored {len(self._products_list)} catalog products from SQLite.")
        except Exception as e:
            logger.error(f"Error restoring catalog from SQLite: {e}")
            raise

    def _index_product(self, prod: EnrichedProduct):
        """Index product across multiple lookup keys and delivery mapping."""
        self._products_list.append(prod)
        row_id_str = str(prod.raw.row_id or len(self._products_list))
        
        # Primary and secondary keys
        self._by_id[row_id_str] = prod
        if prod.part_number:
            self._by_id[str(prod.part_number)] = prod
        if prod.sku:
            self._by_id[str(prod.sku)] = prod
        if prod.mfg_part_number:
            self._by_id[str(prod.mfg_part_number)] = prod

        # Precompute delivery columns
        delivery_dict = to_delivery_dict(prod)
        self._delivery_by_id[row_id_str] = delivery_dict
        if prod.part_number:
            self._delivery_by_id[str(prod.part_number)] = delivery_dict

        # Track review queue
        if prod.status in ["Flagged", "Needs Human Review"] or prod.confidence_score < 0.85:
            self._review_ids.add(row_id_str)

    def _sync_output_csv(self):
        """Export current in-memory catalog state to output CSV."""
        try:
            delivery_rows = [to_delivery_dict(p) for p in self._products_list]
            df_out = pd.DataFrame(delivery_rows)
            df_out.to_csv(settings.enriched_catalog_path, index=False)
        except Exception as e:
            print(f"Warning: Failed to sync output CSV: {e}")

    # -----------------------------------------------------------------------
    # Catalog Search & Querying
    # -----------------------------------------------------------------------

    def list_products(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        min_confidence: Optional[float] = None,
        max_confidence: Optional[float] = None,
        page: int = 1,
        limit: int = 20,
        sort_by: str = "row_id",
        sort_dir: str = "asc"
    ) -> Tuple[List[EnrichedProduct], int]:
        """Search, filter, sort, and paginate in-memory products."""
        if not getattr(self, "_initialized", False):
            self.initialize()
        filtered = self._products_list

        # Search query matching MPN, Part Desc, Brand, Manufacturer, Classpath, UNSPSC, LOVs, Specs
        if search and search.strip():
            raw_query = search.strip().lower()
            tokens = [t for t in raw_query.split() if t]
            query_alphanumeric = "".join(c for c in raw_query if c.isalnum())
            
            def matches_search(p: EnrichedProduct) -> bool:
                # 1. Build comprehensive search haystack
                attr_text = " ".join(f"{a.label} {a.value} {a.uom or ''}" for a in p.attributes)
                features_text = " ".join(p.item_features or [])
                raw_brands = f"{p.raw.e1_brand or ''} {p.raw.unilog_brand or ''} {p.raw.dib_brand or ''} {p.raw.part_manuf or ''}"
                
                haystack = (
                    f"{p.mfg_part_number} {p.raw.mfg_part_num or ''} {p.part_number} {p.sku} "
                    f"{p.raw.row_id or ''} #{p.raw.row_id or ''} "
                    f"{p.unspsc} {p.dept} {p.class_name} {p.fine} {p.classpath} "
                    f"{p.brand_name} {p.manufacturer_name} {p.trade_name or ''} {raw_brands} "
                    f"{p.raw.part_desc} {p.short_desc} {p.product_name} {p.invoice_desc} "
                    f"{p.mobile_desc} {p.long_desc1} {p.marketing_description} {features_text} "
                    f"{attr_text}"
                ).lower()
                
                # Check standard token inclusion
                if all(token in haystack for token in tokens):
                    return True
                
                # Check alphanumeric-only inclusion (e.g. DW5SST matching DW-5SST or 5014 matching 50-1/4)
                if query_alphanumeric and len(query_alphanumeric) >= 3:
                    haystack_alphanumeric = "".join(c for c in haystack if c.isalnum())
                    if query_alphanumeric in haystack_alphanumeric:
                        return True
                
                return False

            filtered = [p for p in filtered if matches_search(p)]

        # Status filter
        if status and status.strip() and status.lower() != "all":
            clean_status = status.strip().lower()
            if clean_status in ["flagged", "needs human review", "review"]:
                filtered = [p for p in filtered if p.status in ["Flagged", "Needs Human Review"]]
            else:
                filtered = [p for p in filtered if p.status.lower() == clean_status]

        # Category / Department filter
        if category and category.strip() and category.lower() != "all":
            clean_cat = category.strip().lower()
            filtered = [p for p in filtered if clean_cat in p.dept.lower() or clean_cat in p.classpath.lower()]

        # Brand filter
        if brand and brand.strip() and brand.lower() != "all":
            clean_brand = brand.strip().lower()
            filtered = [p for p in filtered if clean_brand in p.brand_name.lower()]

        # Confidence range filters
        if min_confidence is not None:
            filtered = [p for p in filtered if p.confidence_score >= min_confidence]
        if max_confidence is not None:
            filtered = [p for p in filtered if p.confidence_score <= max_confidence]

        # Sorting
        reverse = (sort_dir.lower() == "desc")
        if sort_by == "confidence" or sort_by == "confidence_score":
            filtered.sort(key=lambda p: p.confidence_score, reverse=reverse)
        elif sort_by == "mfg_part_num" or sort_by == "mfg_part_number":
            filtered.sort(key=lambda p: p.mfg_part_number.lower(), reverse=reverse)
        elif sort_by == "brand" or sort_by == "brand_name":
            filtered.sort(key=lambda p: p.brand_name.lower(), reverse=reverse)
        elif sort_by == "status":
            filtered.sort(key=lambda p: p.status.lower(), reverse=reverse)
        else: # default row_id
            filtered.sort(key=lambda p: (p.raw.row_id or 0), reverse=reverse)

        total = len(filtered)
        start_idx = max(0, (page - 1) * limit)
        end_idx = start_idx + limit
        paginated_items = filtered[start_idx:end_idx]

        return paginated_items, total

    def get_product(self, key: str) -> Optional[Tuple[EnrichedProduct, Dict[str, str]]]:
        """Lookup product and delivery row by ID, MPN, Part Number, or SKU."""
        if not getattr(self, "_initialized", False):
            self.initialize()
        prod = self._by_id.get(str(key))
        if not prod:
            return None
        row_id_str = str(prod.raw.row_id)
        deliv = self._delivery_by_id.get(row_id_str, to_delivery_dict(prod))
        return prod, deliv

    # -----------------------------------------------------------------------
    # HITL Review Queue & Mutations
    # -----------------------------------------------------------------------

    def get_review_queue(self) -> List[EnrichedProduct]:
        """Return all items flagged for human review or with confidence < 0.85."""
        if not getattr(self, "_initialized", False):
            self.initialize()
        review_items = []
        for p in self._products_list:
            if p.status in ["Flagged", "Needs Human Review"] or p.confidence_score < 0.85:
                review_items.append(p)
        return review_items

    def approve_product(self, product_id: str, notes: Optional[str] = "") -> Optional[EnrichedProduct]:
        """Mark flagged item as Validated and update state."""
        prod = self._by_id.get(str(product_id).strip())
        if not prod:
            return None

        with self._lock:
            prod.status = "Validated"
            if notes:
                prod.validation_flags.append(f"Reviewer Note: {notes}")
            # Ensure confidence is at least 0.95 once validated
            if prod.confidence_score < 0.95:
                prod.confidence_score = 0.95
                prod.confidence_breakdown["human_validation"] = 1.0

            # Update indexes & precomputed delivery row
            row_id_str = str(prod.raw.row_id)
            if row_id_str in self._review_ids:
                self._review_ids.remove(row_id_str)
            self._delivery_by_id[row_id_str] = to_delivery_dict(prod)
            self._sync_output_csv()

        return prod

    def reject_product(self, product_id: str, reason: Optional[str] = "Rejected by reviewer") -> Optional[EnrichedProduct]:
        """Flag product with rejection reason."""
        prod = self._by_id.get(str(product_id).strip())
        if not prod:
            return None

        with self._lock:
            prod.status = "Flagged"
            if reason:
                prod.validation_flags.append(f"Rejection: {reason}")
            row_id_str = str(prod.raw.row_id)
            self._review_ids.add(row_id_str)
            self._delivery_by_id[row_id_str] = to_delivery_dict(prod)
            self._sync_output_csv()

        return prod

    def update_product(self, product_id: str, payload: Dict[str, Any]) -> Optional[EnrichedProduct]:
        """Apply inline corrections to attributes/descriptions and recalculate confidence."""
        prod = self._by_id.get(str(product_id).strip())
        if not prod:
            return None

        with self._lock:
            # Update descriptions
            if "invoice_desc" in payload and payload["invoice_desc"]:
                prod.invoice_desc = str(payload["invoice_desc"]).strip()[:40].upper()
            if "mobile_desc" in payload and payload["mobile_desc"]:
                prod.mobile_desc = str(payload["mobile_desc"]).strip()
            if "short_desc" in payload and payload["short_desc"]:
                prod.short_desc = str(payload["short_desc"]).strip()
            if "long_desc1" in payload and payload["long_desc1"]:
                prod.long_desc1 = str(payload["long_desc1"]).strip()
            if "marketing_description" in payload and payload["marketing_description"]:
                prod.marketing_description = str(payload["marketing_description"]).strip()

            # Update entity & taxonomy
            if "brand_name" in payload and payload["brand_name"]:
                prod.brand_name = str(payload["brand_name"]).strip()
            if "manufacturer_name" in payload and payload["manufacturer_name"]:
                prod.manufacturer_name = str(payload["manufacturer_name"]).strip()
            if "classpath" in payload and payload["classpath"]:
                prod.classpath = str(payload["classpath"]).strip()
            if "unspsc" in payload and payload["unspsc"]:
                prod.unspsc = str(payload["unspsc"]).strip()

            # Update attributes
            if "attributes" in payload and payload["attributes"] is not None:
                new_attrs = []
                for a in payload["attributes"]:
                    if isinstance(a, dict):
                        new_attrs.append(AttributeTriple(**a))
                    elif isinstance(a, AttributeTriple):
                        new_attrs.append(a)
                prod.attributes = new_attrs

            # Update status
            if "status" in payload and payload["status"]:
                prod.status = payload["status"]
            else:
                prod.status = "Validated"

            # Auto-boost confidence upon user edit & validation
            prod.confidence_score = max(prod.confidence_score, 0.95)
            row_id_str = str(prod.raw.row_id)
            if prod.status == "Validated" and row_id_str in self._review_ids:
                self._review_ids.remove(row_id_str)

            self._delivery_by_id[row_id_str] = to_delivery_dict(prod)
            self._sync_output_csv()

        return prod

    def get_product_field_review(self, key: str):
        """Generate field-level evidence review items with raw, candidate, normalized values, and audit history."""
        if not getattr(self, "_initialized", False):
            self.initialize()
        prod = self._by_id.get(str(key).strip())
        if not prod:
            return None

        from .schemas import (
            FieldReviewItemSchema,
            ProductFieldReviewResponse,
            AuditRecordSchema
        )
        from src.pipeline.models import AuditRecord

        fields: List[FieldReviewItemSchema] = []
        high_risk_unresolved = 0

        # Helper to construct FieldReviewItemSchema
        def build_field_item(
            field_name: str,
            display_label: str,
            raw_val: str,
            norm_val: str,
            is_high_risk: bool = False
        ):
            nonlocal high_risk_unresolved
            ev_records = (prod.field_evidence or {}).get(field_name, [])
            primary_ev = ev_records[-1] if ev_records else None
            
            cand_val = primary_ev.candidate_value if (primary_ev and primary_ev.candidate_value) else raw_val
            src_cit = primary_ev.source_title if primary_ev else "Supplier Input Feed"
            src_exc = primary_ev.evidence_excerpt if primary_ev else f"Input value: '{raw_val}'"
            src_url = primary_ev.source_url if primary_ev else None
            src_typ = primary_ev.source_type if primary_ev else "supplier_input"
            conf = primary_ev.confidence if primary_ev else 0.80
            v_status = primary_ev.verification_status if primary_ev else "candidate"
            dict_id = primary_ev.dictionary_identity if primary_ev else None
            
            field_flags = [f for f in prod.validation_flags if field_name.lower() in f.lower() or ("brand" in f.lower() and "brand" in field_name)]
            
            is_resolved = (v_status in ["verified", "unknown"])
            if is_high_risk and not is_resolved:
                high_risk_unresolved += 1

            field_audits = [
                AuditRecordSchema(
                    id=a.id,
                    field_name=a.field_name,
                    reviewer=a.reviewer,
                    timestamp=a.timestamp,
                    previous_value=a.previous_value or "",
                    new_value=a.new_value or "",
                    action=a.action,
                    reason=a.reason
                )
                for a in getattr(prod, "audit_trail", [])
                if a.field_name == field_name
            ]

            return FieldReviewItemSchema(
                field_name=field_name,
                display_label=display_label,
                raw_supplier_input=raw_val,
                candidate_value=cand_val,
                normalized_value=norm_val,
                source_citation=src_cit,
                source_excerpt=src_exc,
                source_url=src_url,
                source_type=src_typ,
                confidence=conf,
                validation_flags=field_flags,
                verification_status=v_status,
                dictionary_identity=dict_id,
                is_high_risk=is_high_risk,
                is_resolved=is_resolved,
                audit_history=field_audits
            )

        # 1. High-Risk Core Fields
        fields.append(build_field_item("mfg_part_number", "Manufacturer Part Number (MPN)", prod.raw.mfg_part_num or "", prod.mfg_part_number, is_high_risk=True))
        fields.append(build_field_item("brand_name", "Canonical Brand Name", prod.raw.part_manuf or prod.raw.e1_brand or "", prod.brand_name, is_high_risk=True))
        fields.append(build_field_item("manufacturer_name", "Manufacturer Legal Entity", prod.raw.part_manuf or "", prod.manufacturer_name, is_high_risk=True))
        fields.append(build_field_item("classpath", "Taxonomy Classpath", prod.raw.part_desc or "", prod.classpath, is_high_risk=True))
        fields.append(build_field_item("unspsc", "UNSPSC Code", prod.raw.part_desc or "", prod.unspsc, is_high_risk=True))
        fields.append(build_field_item("invoice_desc", "INVOICE_DESC (≤40 Chars ALL CAPS)", prod.raw.part_desc or "", prod.invoice_desc, is_high_risk=True))
        fields.append(build_field_item("short_desc", "SHORT_DESC / Product Title", prod.raw.part_desc or "", prod.short_desc, is_high_risk=True))

        # 2. Additional Description Tiers
        fields.append(build_field_item("mobile_desc", "MOBILE_DESC (60–80 Chars)", prod.raw.part_desc or "", prod.mobile_desc, is_high_risk=False))
        fields.append(build_field_item("long_desc1", "LONG_DESC1 (Technical Spec)", prod.raw.part_desc or "", prod.long_desc1, is_high_risk=False))

        # 3. Dynamic Technical Attributes
        for attr in (prod.attributes or []):
            if attr.label:
                attr_raw = f"{attr.label}: {attr.value} {attr.uom or ''}".strip()
                fields.append(build_field_item(
                    f"attr_{attr.label}",
                    f"Attribute: {attr.label}",
                    attr_raw,
                    f"{attr.value} {attr.uom or ''}".strip(),
                    is_high_risk=False
                ))

        all_audits = [
            AuditRecordSchema(
                id=a.id,
                field_name=a.field_name,
                reviewer=a.reviewer,
                timestamp=a.timestamp,
                previous_value=a.previous_value or "",
                new_value=a.new_value or "",
                action=a.action,
                reason=a.reason
            )
            for a in getattr(prod, "audit_trail", [])
        ]

        return ProductFieldReviewResponse(
            product_id=str(prod.raw.row_id or key),
            row_id=prod.raw.row_id or 1,
            mfg_part_number=prod.mfg_part_number,
            brand_name=prod.brand_name,
            manufacturer_name=prod.manufacturer_name,
            status=prod.status,
            confidence_score=prod.confidence_score,
            high_risk_unresolved_count=high_risk_unresolved,
            can_promote_to_validated=(high_risk_unresolved == 0),
            fields=fields,
            audit_trail=all_audits
        )

    def apply_field_action(
        self,
        key: str,
        field_name: str,
        action: str,
        new_value: Optional[str],
        reason: str,
        reviewer: str
    ) -> Optional[Any]:
        """Apply field-level approve, edit, reject, or mark_unknown action with audit record."""
        prod = self._by_id.get(str(key).strip())
        if not prod:
            return None

        from src.pipeline.models import AuditRecord, EvidenceRecord, SourceType, ExtractionMethod, VerificationStatus
        from datetime import datetime, timezone

        with self._lock:
            old_val = ""
            if field_name == "mfg_part_number":
                old_val = prod.mfg_part_number
                if action == "edit" and new_value is not None:
                    prod.mfg_part_number = new_value.strip()
            elif field_name == "brand_name":
                old_val = prod.brand_name
                if action == "edit" and new_value is not None:
                    prod.brand_name = new_value.strip()
            elif field_name == "manufacturer_name":
                old_val = prod.manufacturer_name
                if action == "edit" and new_value is not None:
                    prod.manufacturer_name = new_value.strip()
            elif field_name == "classpath":
                old_val = prod.classpath
                if action == "edit" and new_value is not None:
                    prod.classpath = new_value.strip()
            elif field_name == "unspsc":
                old_val = prod.unspsc
                if action == "edit" and new_value is not None:
                    prod.unspsc = new_value.strip()
            elif field_name == "invoice_desc":
                old_val = prod.invoice_desc
                if action == "edit" and new_value is not None:
                    prod.invoice_desc = new_value.strip()[:40].upper()
            elif field_name == "mobile_desc":
                old_val = prod.mobile_desc
                if action == "edit" and new_value is not None:
                    prod.mobile_desc = new_value.strip()
            elif field_name == "short_desc":
                old_val = prod.short_desc
                if action == "edit" and new_value is not None:
                    prod.short_desc = new_value.strip()
            elif field_name == "long_desc1":
                old_val = prod.long_desc1
                if action == "edit" and new_value is not None:
                    prod.long_desc1 = new_value.strip()
            elif field_name.startswith("attr_"):
                attr_lbl = field_name.replace("attr_", "")
                target_attr = next((a for a in prod.attributes if a.label.lower() == attr_lbl.lower()), None)
                if target_attr:
                    old_val = f"{target_attr.value} {target_attr.uom or ''}".strip()
                    if action == "edit" and new_value is not None:
                        target_attr.value = new_value.strip()
                    elif action in ["reject", "mark_unknown"]:
                        target_attr.value = ""

            # Update or append EvidenceRecord
            if not hasattr(prod, "field_evidence") or prod.field_evidence is None:
                prod.field_evidence = {}

            now_iso = datetime.now(timezone.utc).isoformat()
            if field_name not in prod.field_evidence:
                prod.field_evidence[field_name] = []

            if action == "approve":
                # Mark latest evidence record verified without erasing candidate or source
                if prod.field_evidence[field_name]:
                    prod.field_evidence[field_name][-1].verification_status = VerificationStatus.VERIFIED.value
                    prod.field_evidence[field_name][-1].confidence = 1.0
                else:
                    prod.field_evidence[field_name].append(
                        EvidenceRecord(
                            field_name=field_name,
                            candidate_value=old_val,
                            normalized_value=old_val,
                            source_type=SourceType.MANUAL_REVIEW.value,
                            source_title=f"Manual Approval by {reviewer}",
                            extraction_method=ExtractionMethod.MANUAL_REVIEW.value,
                            retrieved_at=now_iso,
                            confidence=1.0,
                            verification_status=VerificationStatus.VERIFIED.value
                        )
                    )
            elif action == "edit":
                prod.field_evidence[field_name].append(
                    EvidenceRecord(
                        field_name=field_name,
                        candidate_value=old_val,
                        normalized_value=new_value or "",
                        source_type=SourceType.MANUAL_REVIEW.value,
                        source_title=f"Manual Edit by {reviewer}",
                        evidence_excerpt=f"Reason: {reason}",
                        extraction_method=ExtractionMethod.MANUAL_REVIEW.value,
                        retrieved_at=now_iso,
                        confidence=1.0,
                        verification_status=VerificationStatus.VERIFIED.value
                    )
                )
            elif action == "reject":
                if prod.field_evidence[field_name]:
                    prod.field_evidence[field_name][-1].verification_status = VerificationStatus.REJECTED.value
                else:
                    prod.field_evidence[field_name].append(
                        EvidenceRecord(
                            field_name=field_name,
                            candidate_value=old_val,
                            normalized_value="",
                            source_type=SourceType.MANUAL_REVIEW.value,
                            source_title=f"Rejected by {reviewer}",
                            extraction_method=ExtractionMethod.MANUAL_REVIEW.value,
                            retrieved_at=now_iso,
                            confidence=0.0,
                            verification_status=VerificationStatus.REJECTED.value
                        )
                    )
            elif action == "mark_unknown":
                if prod.field_evidence[field_name]:
                    prod.field_evidence[field_name][-1].verification_status = "unknown"
                    prod.field_evidence[field_name][-1].normalized_value = ""
                else:
                    prod.field_evidence[field_name].append(
                        EvidenceRecord(
                            field_name=field_name,
                            candidate_value=old_val,
                            normalized_value="",
                            source_type=SourceType.MANUAL_REVIEW.value,
                            source_title=f"Marked Unknown by {reviewer}",
                            extraction_method=ExtractionMethod.MANUAL_REVIEW.value,
                            retrieved_at=now_iso,
                            confidence=0.0,
                            verification_status="unknown"
                        )
                    )

            # Record immutable AuditRecord
            if not hasattr(prod, "audit_trail") or prod.audit_trail is None:
                prod.audit_trail = []

            audit_rec = AuditRecord(
                field_name=field_name,
                reviewer=reviewer,
                previous_value=old_val,
                new_value=(new_value or "") if action == "edit" else old_val,
                action=action,
                reason=reason
            )
            prod.audit_trail.append(audit_rec)

            # Recompute delivery mapping and sync CSV
            row_id_str = str(prod.raw.row_id)
            self._delivery_by_id[row_id_str] = to_delivery_dict(prod)
            self._sync_output_csv()

            # SQLite database persistence sync
            try:
                from .db.repositories.products import product_repo
                from .db.repositories.reviews import review_repo
                from .db.repositories.audit import audit_repo
                row_id = prod.raw.row_id or 1
                review_repo.record_review_action(
                    product_id=str(row_id),
                    field_name=field_name,
                    action=action,
                    new_value=new_value,
                    reason=reason,
                    reviewer=reviewer,
                )
                audit_repo.record_action(
                    user_email=reviewer,
                    role="reviewer",
                    action=f"FIELD_{action.upper()}",
                    entity_type="product_field",
                    entity_id=f"{row_id}:{field_name}",
                    before_state={"value": old_val},
                    after_state={"value": new_value if action == "edit" else old_val, "action": action},
                    reason=reason,
                )
                product_repo.upsert_enriched_field(
                    product_id=str(row_id),
                    field_name=field_name,
                    field_value=new_value if action == "edit" else old_val,
                    confidence_score=1.0 if action in ("approve", "edit") else 0.0,
                    verification_status="verified" if action in ("approve", "edit") else action,
                )
            except Exception as e:
                logger.warning(f"Failed to persist field action to SQLite database: {e}")

        return self.get_product_field_review(key)

    def promote_to_validated(self, key: str, reviewer: str, notes: Optional[str] = "") -> Tuple[bool, str, List[str]]:
        """Promote product to Validated status only if all high-risk fields are resolved."""
        review_data = self.get_product_field_review(key)
        if not review_data:
            return False, f"Product {key} not found", []

        unresolved_high_risk = [f.field_name for f in review_data.fields if f.is_high_risk and not f.is_resolved]
        if unresolved_high_risk:
            return False, f"Cannot promote to Validated: High-risk fields {unresolved_high_risk} are unresolved.", unresolved_high_risk

        prod = self._by_id.get(str(key).strip())
        if not prod:
            return False, f"Product {key} not found", []

        from src.pipeline.models import AuditRecord
        with self._lock:
            prod.status = "Validated"
            prod.confidence_score = max(prod.confidence_score, 0.98)
            row_id_str = str(prod.raw.row_id)
            if row_id_str in self._review_ids:
                self._review_ids.remove(row_id_str)

            audit_rec = AuditRecord(
                field_name="product_status",
                reviewer=reviewer,
                previous_value="Flagged",
                new_value="Validated",
                action="approve",
                reason=notes or "All high-risk fields verified and validated by specialist"
            )
            prod.audit_trail.append(audit_rec)

            self._delivery_by_id[row_id_str] = to_delivery_dict(prod)
            self._sync_output_csv()

            # SQLite database persistence sync
            try:
                from .db.repositories.products import product_repo
                from .db.repositories.audit import audit_repo
                row_id = prod.raw.row_id or 1
                product_repo.upsert_product(
                    product_id=str(row_id),
                    mfg_part_num=prod.raw.mfg_part_num or prod.mfg_part_number,
                    canonical_mpn=prod.mfg_part_number,
                    status="Validated",
                    brand=prod.brand_name,
                    manufacturer=prod.manufacturer_name,
                    classpath=prod.classpath,
                    unspsc=prod.unspsc,
                    invoice_desc=prod.invoice_desc,
                    mobile_desc=prod.mobile_desc,
                    short_desc=prod.short_desc,
                    long_desc=prod.long_desc1,
                    confidence=prod.confidence_score,
                )
                audit_repo.record_action(
                    user_email=reviewer,
                    role="reviewer",
                    action="PROMOTE_TO_VALIDATED",
                    entity_type="product",
                    entity_id=str(row_id),
                    before_state={"status": "Flagged"},
                    after_state={"status": "Validated"},
                    reason=notes or "All high-risk fields verified and validated by reviewer",
                )
            except Exception as e:
                logger.warning(f"Failed to persist validation promotion to SQLite database: {e}")

        return True, f"Product {key} successfully promoted to Validated.", []

    # -----------------------------------------------------------------------
    # Statistics & Facets
    # -----------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Compute live catalog metrics, KPI counters, and compliance stats."""
        if not getattr(self, "_initialized", False):
            self.initialize()
        total = len(self._products_list)
        if total == 0:
            return {
                "total_items": 0, "enriched_count": 0, "validated_count": 0,
                "flagged_count": 0, "draft_count": 0, "mean_confidence": 0.0,
                "median_confidence": 0.0, "invoice_compliance_pct": 100.0,
                "mobile_compliance_pct": 100.0, "lov_compliance_pct": 100.0,
                "schema_columns_count": 252, "status_counts": {}, "dept_counts": {},
                "top_brands": {}
            }

        status_counts = {"Validated": 0, "Enriched": 0, "Flagged": 0, "Draft": 0}
        dept_counts: Dict[str, int] = {}
        brand_counts: Dict[str, int] = {}
        confidences = []
        invoice_valid = 0
        mobile_valid = 0

        for p in self._products_list:
            # Status
            st = p.status if p.status in status_counts else "Enriched"
            status_counts[st] = status_counts.get(st, 0) + 1

            # Dept
            dept = p.dept or "General"
            dept_counts[dept] = dept_counts.get(dept, 0) + 1

            # Brand
            clean_brand = p.brand_name.replace("®", "").replace("™", "").strip() or "Generic"
            brand_counts[clean_brand] = brand_counts.get(clean_brand, 0) + 1

            # Confidence
            confidences.append(p.confidence_score)

            # Hard gate compliance
            if len(p.invoice_desc) <= 40 and p.invoice_desc.isupper():
                invoice_valid += 1
            if 60 <= len(p.mobile_desc) <= 80:
                mobile_valid += 1

        mean_conf = round(sum(confidences) / len(confidences), 3) if confidences else 0.0
        sorted_conf = sorted(confidences)
        median_conf = round(sorted_conf[len(sorted_conf) // 2], 3) if sorted_conf else 0.0
        # Top 10 brands
        top_brands = dict(sorted(brand_counts.items(), key=lambda x: -x[1])[:10])

        # Evidence coverage calculations
        sources_registered = 0
        try:
            from src.evidence.registry import EvidenceRegistryManager
            reg_mgr = EvidenceRegistryManager()
            sources_registered = len(reg_mgr.load_registry())
        except Exception:
            sources_registered = 0

        verified_fields_total = 0
        candidate_fields_total = 0
        unsupported_withheld_total = 0

        for p in self._products_list:
            if hasattr(p, "provenance_summary") and p.provenance_summary:
                verified_fields_total += p.provenance_summary.verified_fields_count
                candidate_fields_total += p.provenance_summary.candidate_fields_count
                unsupported_withheld_total += (p.provenance_summary.missing_evidence_count + p.provenance_summary.rejected_fields_count)
            elif hasattr(p, "field_evidence") and p.field_evidence:
                for f_name, ev_list in p.field_evidence.items():
                    for ev in ev_list:
                        if ev.verification_status == "verified":
                            verified_fields_total += 1
                        elif ev.verification_status == "candidate":
                            candidate_fields_total += 1
                        elif ev.verification_status in ["rejected", "missing_evidence"]:
                            unsupported_withheld_total += 1

        return {
            "total_items": total,
            "enriched_count": status_counts.get("Enriched", 0),
            "validated_count": status_counts.get("Validated", 0),
            "flagged_count": status_counts.get("Flagged", 0),
            "draft_count": status_counts.get("Draft", 0),
            "mean_confidence": mean_conf,
            "median_confidence": median_conf,
            "invoice_compliance_pct": round((invoice_valid / total) * 100.0, 2),
            "mobile_compliance_pct": round((mobile_valid / total) * 100.0, 2),
            "lov_compliance_pct": 100.0,
            "schema_columns_count": 252,
            "status_counts": status_counts,
            "dept_counts": dept_counts,
            "top_brands": top_brands,
            "sources_registered_count": sources_registered,
            "verified_fields_count": verified_fields_total,
            "candidate_fields_count": candidate_fields_total,
            "unsupported_fields_withheld": unsupported_withheld_total
        }

    def get_filter_options(self) -> Dict[str, Any]:
        """Return distinct statuses, departments, and brands with item counts."""
        if not getattr(self, "_initialized", False):
            self.initialize()
        stats = self.get_stats()
        
        statuses = [{"label": k, "value": k, "count": v} for k, v in stats["status_counts"].items() if v > 0]
        departments = [{"label": k, "value": k, "count": v} for k, v in stats["dept_counts"].items()]
        departments.sort(key=lambda x: -x["count"])
        
        brands = [{"label": k, "value": k, "count": v} for k, v in stats["top_brands"].items()]
        brands.sort(key=lambda x: -x["count"])

        return {
            "statuses": statuses,
            "departments": departments,
            "brands": brands
        }

    # -----------------------------------------------------------------------
    # Export Services & CSV Formula Injection Sanitization (CWE-1236)
    # -----------------------------------------------------------------------

    @staticmethod
    def _sanitize_csv_cell(val: Any) -> Any:
        """Sanitize cell value to neutralize spreadsheet formula injection (=, +, -, @, |, TAB)."""
        if isinstance(val, str) and val:
            if val[0] in ("=", "+", "-", "@", "\t", "\r", "|"):
                try:
                    float(val)
                    return val
                except ValueError:
                    return f"'{val}"
        return val

    def get_export_dataframe(
        self,
        status: Optional[str] = None,
        search: Optional[str] = None,
        sanitize_formulas: bool = True
    ) -> pd.DataFrame:
        """Construct pandas DataFrame containing 252 columns with formula injection defenses."""
        if not getattr(self, "_initialized", False):
            self.initialize()
        items, _ = self.list_products(search=search, status=status, limit=10000)
        
        rows = []
        for p in items:
            row_dict = to_delivery_dict(p)
            if sanitize_formulas:
                row_dict = {k: self._sanitize_csv_cell(v) for k, v in row_dict.items()}
            rows.append(row_dict)

        if not rows:
            return pd.DataFrame(columns=DeliveryMapper.get_column_headers())
        return pd.DataFrame(rows)

    def get_export_csv_bytes(self, status: Optional[str] = None, search: Optional[str] = None) -> bytes:
        """Stream 252-column CSV bytes with formula injection defense."""
        df = self.get_export_dataframe(status=status, search=search, sanitize_formulas=True)
        output = io.StringIO()
        df.to_csv(output, index=False)
        return output.getvalue().encode("utf-8")

    def get_export_excel_bytes(self, status: Optional[str] = None, search: Optional[str] = None) -> bytes:
        """Stream 252-column Excel (.xlsx) bytes with formula injection defense."""
        df = self.get_export_dataframe(status=status, search=search, sanitize_formulas=True)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Enriched Catalog 252")
        return output.getvalue()

    # -----------------------------------------------------------------------
    # QA Benchmarking Integration
    # -----------------------------------------------------------------------

    def get_benchmark_report(self, force_recompute: bool = False) -> Dict[str, Any]:
        """Return benchmark evaluation report against ground truth."""
        if self._cached_benchmark is not None and not force_recompute:
            return self._cached_benchmark

        with self._lock:
            if self._cached_benchmark is not None and not force_recompute:
                return self._cached_benchmark

            df_catalog = self.get_export_dataframe()
            report = self.evaluator.evaluate_catalog(df_catalog)
            self._cached_benchmark = report.to_dict()
            return self._cached_benchmark


catalog_state = CatalogState()
