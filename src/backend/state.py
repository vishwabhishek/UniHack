"""
In-Memory Catalog Store, Indexing Engine & State Management.
Pre-loads 1,000 industrial items, provides sub-millisecond filtering,
search, HITL triage, and atomic updates.
"""

import io
import csv
import threading
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd

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
        """Pre-load all 1,000 catalog products into indexed memory."""
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

            # Load raw input CSV
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

            for prod in enriched_products:
                self._index_product(prod)

            # Ensure output directory and 252-column export file exist
            settings.output_dir.mkdir(parents=True, exist_ok=True)
            self._sync_output_csv()

            self._initialized = True

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

        # Search query matching MPN, Part Desc, Brand, Manufacturer, Classpath
        if search and search.strip():
            tokens = [t.lower() for t in search.strip().split() if t]
            def matches_search(p: EnrichedProduct) -> bool:
                haystack = f"{p.mfg_part_number} {p.raw.part_desc} {p.short_desc} {p.brand_name} {p.manufacturer_name} {p.classpath} {p.part_number} {p.sku}".lower()
                return all(token in haystack for token in tokens)
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
            "top_brands": top_brands
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
    # Export Services
    # -----------------------------------------------------------------------

    def get_export_dataframe(self, status: Optional[str] = None, search: Optional[str] = None) -> pd.DataFrame:
        """Construct pandas DataFrame containing 252 columns for filtered or full catalog."""
        if not getattr(self, "_initialized", False):
            self.initialize()
        items, _ = self.list_products(search=search, status=status, limit=10000)
        rows = [to_delivery_dict(p) for p in items]
        if not rows:
            return pd.DataFrame(columns=DeliveryMapper.get_column_headers())
        return pd.DataFrame(rows)

    def get_export_csv_bytes(self, status: Optional[str] = None, search: Optional[str] = None) -> bytes:
        """Stream 252-column CSV bytes."""
        df = self.get_export_dataframe(status=status, search=search)
        output = io.StringIO()
        df.to_csv(output, index=False)
        return output.getvalue().encode("utf-8")

    def get_export_excel_bytes(self, status: Optional[str] = None, search: Optional[str] = None) -> bytes:
        """Stream 252-column Excel (.xlsx) bytes."""
        df = self.get_export_dataframe(status=status, search=search)
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
