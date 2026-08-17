"""
Master Pipeline Orchestrator & Batch Processing Engine.
"""

import time
from typing import Dict, Any, List, Optional, Callable
from .models import RawProduct, EnrichedProduct, AttributeTriple, PhysicalDimensions
from .sanitizer import ProductSanitizer
from .entity_resolver import EntityResolver
from .taxonomy import TaxonomyClassifier
from .attribute_extractor import AttributeExtractor
from .uom_standardizer import UOMStandardizer
from .description_generator import DescriptionGenerator
from .delivery_mapper import DeliveryMapper, to_delivery_dict


class EnrichmentEngine:
    """Master orchestrator executing the 7-stage PIM enrichment pipeline."""

    def __init__(self, dictionaries_dir: Optional[str] = None):
        self.sanitizer = ProductSanitizer()
        self.resolver = EntityResolver()
        self.taxonomy = TaxonomyClassifier()
        self.extractor = AttributeExtractor()
        self.uom_std = UOMStandardizer()
        self.desc_gen = DescriptionGenerator()
        self.mapper = DeliveryMapper()

    def process_item(self, raw: RawProduct) -> EnrichedProduct:
        """Execute full multi-stage enrichment on a single raw product."""
        # Stage 1: Ingestion & Sanitization
        sanitized = self.sanitizer.sanitize(raw)
        
        # Stage 2: Canonical Brand & Manufacturer Resolution
        entity = self.resolver.resolve(sanitized)
        
        # Stage 3: Taxonomy & UNSPSC Classification
        tax = self.taxonomy.classify(sanitized, entity)
        
        # Stage 4 & 5: Attribute Extraction & LOV / UOM Standardization
        attr_data = self.extractor.extract(sanitized, entity, tax)
        
        # Stage 6: 5-Tier Description Generation
        descriptions = self.desc_gen.generate_all(sanitized, entity, tax, attr_data)
        
        # Quality & Confidence Scoring
        confidence, breakdown, flags = self._compute_confidence(sanitized, entity, tax, attr_data, descriptions)
        status = "Flagged" if confidence < 0.85 else "Enriched"

        # IDs & Codes
        part_num = f"{20000000 + (raw.row_id or 1000)}"
        sku = f"{1500000 + (raw.row_id or 1000)}"
        
        # Digital Assets
        clean_brand_asset = entity.get("brand_name", "").replace("®", "").replace("™", "").replace(" ", "").upper() or "BRAND"
        clean_mpn_asset = sanitized.get("mfg_part_num", "ITEM").replace("/", "_").replace(" ", "_")
        product_image = f"{clean_brand_asset}_{clean_mpn_asset}.jpg"
        alt_images = [
            f"{clean_brand_asset}_{clean_mpn_asset}_1.jpg",
            f"{clean_brand_asset}_{clean_mpn_asset}_2.jpg",
            f"{clean_brand_asset}_{clean_mpn_asset}_3.jpg",
            f"{clean_brand_asset}_{clean_mpn_asset}_4.jpg"
        ]
        documents = {
            "Specification Sheet": f"{clean_brand_asset}_{clean_mpn_asset}_Specification_Sheet.pdf"
        }

        # Assemble Enriched Product
        enriched = EnrichedProduct(
            part_number=part_num,
            sku=sku,
            mfg_part_number=sanitized.get("mfg_part_num", ""),
            alternate_part_number="",
            upc="",
            ean="",
            gtin="",
            unspsc=tax.get("unspsc", ""),
            raw=raw,
            dept=tax.get("dept", ""),
            class_name=tax.get("class_name", ""),
            fine=tax.get("fine", ""),
            manufacturer_name=entity.get("manufacturer_name", ""),
            brand_name=entity.get("brand_name", ""),
            trade_name=entity.get("trade_name", ""),
            mfr_url=entity.get("mfr_url", ""),
            ref_urls=[],
            classpath=tax.get("classpath", ""),
            product_name=tax.get("product_name", ""),
            invoice_desc=descriptions.get("invoice_desc", ""),
            mobile_desc=descriptions.get("mobile_desc", ""),
            short_desc=descriptions.get("short_desc", ""),
            long_desc1=descriptions.get("long_desc1", ""),
            retail_desc=descriptions.get("retail_desc", ""),
            marketing_description=descriptions.get("marketing_description", ""),
            item_features=attr_data.get("item_features", []),
            with_spec=attr_data.get("with_spec", ""),
            standard_approvals=attr_data.get("standard_approvals", ""),
            prop_65=attr_data.get("prop_65", ""),
            application=attr_data.get("application", ""),
            includes=attr_data.get("includes", ""),
            attributes=attr_data.get("attributes", []),
            dimensions=attr_data.get("dimensions", PhysicalDimensions()),
            warranty=attr_data.get("warranty", ""),
            list_price="",
            selling_qty=attr_data.get("selling_qty", "1"),
            selling_uom=attr_data.get("selling_uom", "EA"),
            standard_packaging="",
            country_of_origin="US",
            discontinued="No",
            product_image=product_image,
            alternate_images=alt_images,
            actual_image="Yes",
            documents=documents,
            confidence_score=confidence,
            confidence_breakdown=breakdown,
            validation_flags=flags,
            status=status
        )

        return enriched

    def process_batch(
        self,
        raw_items: List[RawProduct],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[EnrichedProduct]:
        """Batch process a list of raw product items."""
        enriched_list = []
        total = len(raw_items)
        for idx, item in enumerate(raw_items):
            enriched = self.process_item(item)
            enriched_list.append(enriched)
            if progress_callback and (idx + 1) % 50 == 0:
                progress_callback(idx + 1, total)
        if progress_callback:
            progress_callback(total, total)
        return enriched_list

    def _compute_confidence(
        self,
        sanitized: Dict[str, Any],
        entity: Dict[str, str],
        tax: Dict[str, Any],
        attr_data: Dict[str, Any],
        desc: Dict[str, str]
    ) -> (float, Dict[str, float], List[str]):
        """Compute composite confidence score across 5 quality factors."""
        flags = []
        
        # 1. Brand Confidence
        c_brand = 1.0
        if not entity.get("brand_name") or "Generic" in entity.get("brand_name", ""):
            c_brand = 0.5
            flags.append("Unresolved Brand")
        elif "®" not in entity.get("brand_name", "") and "™" not in entity.get("brand_name", ""):
            c_brand = 0.85
        
        # 2. Taxonomy Confidence
        c_tax = 1.0
        if not tax.get("unspsc") or tax.get("unspsc") == "27110000":
            c_tax = 0.70
            flags.append("Fallback Taxonomy")
            
        # 3. Attribute Confidence
        extracted_dict = attr_data.get("extracted_dict", {})
        attr_count = len([v for v in extracted_dict.values() if v[0]])
        if attr_count >= 5:
            c_attr = 1.0
        elif attr_count >= 2:
            c_attr = 0.90
        elif attr_count >= 1:
            c_attr = 0.80
        else:
            c_attr = 0.65
            flags.append("Low Attribute Density")

        # 4. Description Limits Compliance
        c_desc = 1.0
        inv = desc.get("invoice_desc", "")
        mob = desc.get("mobile_desc", "")
        if len(inv) > 40:
            c_desc -= 0.3
            flags.append(f"Invoice Desc Exceeds Limit ({len(inv)} > 40)")
        if not inv.isupper():
            c_desc -= 0.1
            flags.append("Invoice Desc Not All Caps")
        if len(mob) < 60 or len(mob) > 80:
            c_desc -= 0.2
            flags.append(f"Mobile Desc Out of Bounds ({len(mob)} chars)")

        # 5. Completeness
        c_comp = 0.95
        if not sanitized.get("mfg_part_num"):
            c_comp -= 0.3
            flags.append("Missing MPN")

        composite = round(0.25 * c_brand + 0.20 * c_tax + 0.25 * c_attr + 0.20 * c_desc + 0.10 * c_comp, 3)
        breakdown = {
            "brand_confidence": round(c_brand, 2),
            "taxonomy_confidence": round(c_tax, 2),
            "attribute_confidence": round(c_attr, 2),
            "description_compliance": round(c_desc, 2),
            "completeness": round(c_comp, 2)
        }

        return composite, breakdown, flags
