"""
Stage 7: 252-Column Delivery Format Exporter & Mapper.
"""

from typing import Dict, List, Any
import re
from .models import EnrichedProduct


class DeliveryMapper:
    """Maps EnrichedProduct domain entities to exact 252-column delivery CSV records."""

    COLUMNS = [
        "MFR URL", "Ref URL 1", "Ref URL 2", "Ref URL 3", "Ref URL 4", "Ref URL 5",
        "PART_NUMBER", "Dept", "Class", "Fine", "SKU - MY_PART_NUMBER", "Mfg_Part_Num",
        "Part_Desc", "E1_Brand", "Unilog_Brand", "DIB_Brand", "Part_Manuf",
        "MANUFACTURER_NAME", "BRAND_NAME", "TRADE_NAME", "MANUFACTURER_PART_NUMBER",
        "ALTERNATE_PART_NUMBER", "Classpath", "MOBILE_DESC", "INVOICE_DESC", "SHORT_DESC",
        "LONG_DESC1", "RETAIL_DESC", "MARKETING_DESCRIPTION",
        "ITEM_FEATURES_1", "ITEM_FEATURES_2", "ITEM_FEATURES_3", "ITEM_FEATURES_4",
        "ITEM_FEATURES_5", "ITEM_FEATURES_6", "ITEM_FEATURES_7", "ITEM_FEATURES_8",
        "ITEM_FEATURES_9", "ITEM_FEATURES_10", "ITEM_FEATURES_11", "ITEM_FEATURES_12",
        "ITEM_FEATURES_13", "ITEM_FEATURES_14", "ITEM_FEATURES_15", "ITEM_FEATURES_16",
        "ITEM_FEATURES_17", "ITEM_FEATURES_18", "ITEM_FEATURES_19", "ITEM_FEATURES_20",
        "With", "Standard/Approvals", "Prop 65", "Application", "Includes", "Product Name"
    ]

    # Add 50 attribute triplets (150 columns)
    for i in range(1, 51):
        COLUMNS.extend([f"ATTRIBUTE_LABEL {i}", f"ATTRIBUTE_VALUE {i}", f"ATTRIBUTE_UOM {i}"])

    COLUMNS.extend([
        "UPC", "EAN", "GTIN", "UNSPSC", "Warranty", "List Price", "Selling Qty",
        "Selling UOM", "Standard Packaging Information", "LENGTH", "LENGTH_UOM",
        "HEIGHT", "HEIGHT_UOM", "WIDTH", "WIDTH_UOM", "WEIGHT", "WEIGHT_UOM",
        "VOLUME", "VOLUME_UOM", "Product Image", "Alternate Image 1", "Alternate Image 2",
        "Alternate Image 3", "Alternate Image 4", "SDS", "SDS_1", "Warranty Information",
        "Catalog", "Specification Sheet", "Instruction/Installation Manual",
        "Service Manual", "Owners/User Manual", "Line Drawing", "MTR", "RoHS",
        "Full Engineering Drawing", "Energy Star Guide", "Technical Bulletin",
        "Submittal", "Compatibility Chart", "Size Chart", "Product Label/Insert",
        "Video Link", "Video Link 1", "Country Of Origin", "Discontinued",
        "Actual Image (Yes/No)"
    ])

    @classmethod
    def get_column_headers(cls) -> List[str]:
        """Return the exact 252-column header list."""
        return list(cls.COLUMNS)

    @classmethod
    def to_delivery_dict(cls, p: EnrichedProduct) -> Dict[str, str]:
        """Transform an EnrichedProduct into a dictionary of exactly 252 columns."""
        row: Dict[str, str] = {}
        
        # 1. URLs
        row["MFR URL"] = p.mfr_url or ""
        ref_urls = p.ref_urls or []
        for i in range(1, 6):
            row[f"Ref URL {i}"] = ref_urls[i-1] if len(ref_urls) >= i else ""

        # 2. Identifiers & Taxonomy
        row["PART_NUMBER"] = p.part_number or ""
        row["Dept"] = p.dept or ""
        row["Class"] = p.class_name or ""
        row["Fine"] = p.fine or ""
        row["SKU - MY_PART_NUMBER"] = p.sku or ""
        
        # 3. Raw Inputs
        row["Mfg_Part_Num"] = p.raw.mfg_part_num or ""
        row["Part_Desc"] = p.raw.part_desc or ""
        row["E1_Brand"] = p.raw.e1_brand or ""
        row["Unilog_Brand"] = p.raw.unilog_brand or ""
        row["DIB_Brand"] = p.raw.dib_brand or ""
        row["Part_Manuf"] = p.raw.part_manuf or ""

        # 4. Resolved Entities
        row["MANUFACTURER_NAME"] = p.manufacturer_name or ""
        row["BRAND_NAME"] = p.brand_name or ""
        row["TRADE_NAME"] = p.trade_name or ""
        row["MANUFACTURER_PART_NUMBER"] = p.mfg_part_number or p.raw.mfg_part_num or ""
        row["ALTERNATE_PART_NUMBER"] = p.alternate_part_number or ""
        row["Classpath"] = p.classpath or ""

        # 5. 5-Tier Descriptions
        row["MOBILE_DESC"] = p.mobile_desc or ""
        row["INVOICE_DESC"] = p.invoice_desc or ""
        row["SHORT_DESC"] = p.short_desc or ""
        row["LONG_DESC1"] = p.long_desc1 or ""
        row["RETAIL_DESC"] = p.retail_desc or ""
        row["MARKETING_DESCRIPTION"] = p.marketing_description or ""

        # 6. Features 1..20
        features = p.item_features or []
        for i in range(1, 21):
            row[f"ITEM_FEATURES_{i}"] = features[i-1] if len(features) >= i else ""

        # 7. Modifiers
        row["With"] = p.with_spec or ""
        row["Standard/Approvals"] = p.standard_approvals or ""
        row["Prop 65"] = p.prop_65 or ""
        row["Application"] = p.application or ""
        row["Includes"] = p.includes or ""
        row["Product Name"] = p.product_name or ""

        # 8. 50 Attribute Triplets (150 columns)
        attributes = p.attributes or []
        for i in range(1, 51):
            triple = attributes[i-1] if len(attributes) >= i else None
            row[f"ATTRIBUTE_LABEL {i}"] = triple.label if triple else ""
            row[f"ATTRIBUTE_VALUE {i}"] = triple.value if triple else ""
            row[f"ATTRIBUTE_UOM {i}"] = triple.uom if triple and triple.uom else ""

        # 9. Codes & Commercial
        row["UPC"] = p.upc or ""
        row["EAN"] = p.ean or ""
        row["GTIN"] = p.gtin or ""
        row["UNSPSC"] = p.unspsc or ""
        row["Warranty"] = p.warranty or ""
        row["List Price"] = p.list_price or ""
        row["Selling Qty"] = p.selling_qty or "1"
        row["Selling UOM"] = p.selling_uom or "EA"
        row["Standard Packaging Information"] = p.standard_packaging or ""

        # 10. Dimensions
        dims = p.dimensions
        row["LENGTH"] = dims.length or ""
        row["LENGTH_UOM"] = dims.length_uom or ""
        row["HEIGHT"] = dims.height or ""
        row["HEIGHT_UOM"] = dims.height_uom or ""
        row["WIDTH"] = dims.width or ""
        row["WIDTH_UOM"] = dims.width_uom or ""
        row["WEIGHT"] = dims.weight or ""
        row["WEIGHT_UOM"] = dims.weight_uom or ""
        row["VOLUME"] = dims.volume or ""
        row["VOLUME_UOM"] = dims.volume_uom or ""

        # 11. Digital Assets
        clean_brand_asset = re.sub(r"[^A-Za-z0-9]", "", p.brand_name).upper() or "BRAND"
        clean_mpn_asset = re.sub(r"[^A-Za-z0-9_\-]", "", p.mfg_part_number or p.raw.mfg_part_num)
        
        primary_img = p.product_image or f"{clean_brand_asset}_{clean_mpn_asset}.jpg"
        row["Product Image"] = primary_img

        alt_imgs = p.alternate_images or []
        for i in range(1, 5):
            row[f"Alternate Image {i}"] = alt_imgs[i-1] if len(alt_imgs) >= i else ""

        docs = p.documents or {}
        row["SDS"] = docs.get("SDS", "")
        row["SDS_1"] = docs.get("SDS_1", "")
        row["Warranty Information"] = docs.get("Warranty Information", "")
        row["Catalog"] = docs.get("Catalog", "")
        row["Specification Sheet"] = docs.get("Specification Sheet", f"{clean_brand_asset}_{clean_mpn_asset}_Specification_Sheet.pdf")
        row["Instruction/Installation Manual"] = docs.get("Instruction/Installation Manual", "")
        row["Service Manual"] = docs.get("Service Manual", "")
        row["Owners/User Manual"] = docs.get("Owners/User Manual", "")
        row["Line Drawing"] = docs.get("Line Drawing", "")
        row["MTR"] = docs.get("MTR", "")
        row["RoHS"] = docs.get("RoHS", "")
        row["Full Engineering Drawing"] = docs.get("Full Engineering Drawing", "")
        row["Energy Star Guide"] = docs.get("Energy Star Guide", "")
        row["Technical Bulletin"] = docs.get("Technical Bulletin", "")
        row["Submittal"] = docs.get("Submittal", "")
        row["Compatibility Chart"] = docs.get("Compatibility Chart", "")
        row["Size Chart"] = docs.get("Size Chart", "")
        row["Product Label/Insert"] = docs.get("Product Label/Insert", "")
        row["Video Link"] = docs.get("Video Link", "")
        row["Video Link 1"] = docs.get("Video Link 1", "")

        # 12. Flags
        row["Country Of Origin"] = p.country_of_origin or ""
        row["Discontinued"] = p.discontinued or "No"
        row["Actual Image (Yes/No)"] = p.actual_image or "Yes"

        # Verify exact column order
        ordered_row = {col: row.get(col, "") for col in cls.COLUMNS}
        return ordered_row


def to_delivery_dict(product: EnrichedProduct) -> Dict[str, str]:
    """Helper functional wrapper for delivery dictionary mapping."""
    return DeliveryMapper.to_delivery_dict(product)
