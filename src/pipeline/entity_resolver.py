"""
Stage 2: Canonical Brand & Manufacturer Entity Resolution.
"""

import json
import os
import re
from typing import Dict, Any, Optional, Tuple


class EntityResolver:
    """Resolves raw distributor supplier fields and cryptic tokens to canonical Manufacturer, Brand, and Trade Names."""

    def __init__(self, dict_path: Optional[str] = None):
        if not dict_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            dict_path = os.path.join(base_dir, "data", "dictionaries", "brand_mappings.json")
        
        self.brand_mappings = {}
        if os.path.exists(dict_path):
            with open(dict_path, "r", encoding="utf-8") as f:
                self.brand_mappings = json.load(f)
        
        self.supplier_map = self.brand_mappings.get("supplier_to_entity", {})
        self.appliance_patterns = self.brand_mappings.get("appliance_brand_patterns", {})

    def resolve(self, sanitized: Dict[str, Any]) -> Dict[str, str]:
        """Resolve canonical manufacturer, brand, trade name, and series."""
        mfg_part_num = sanitized.get("mfg_part_num", "")
        desc = sanitized.get("raw_desc", "")
        desc_tokens = sanitized.get("desc_tokens", "")
        e1_brand = sanitized.get("e1_brand")
        dib_brand = sanitized.get("dib_brand")
        supplier_name = sanitized.get("supplier_name")
        supplier_code = sanitized.get("supplier_code")
        raw_manuf = supplier_name or ""
        
        # 1. Handle missing/dash manufacturer '-'
        if not raw_manuf or raw_manuf == "-":
            resolved_dash = self._resolve_missing_manufacturer(mfg_part_num, desc)
            if resolved_dash:
                return resolved_dash

        # 2. Handle Appliance Dealers Cooperative (APPDE) or Appliance rows
        if supplier_code == "APPDE" or "appliance dealers cooperative" in raw_manuf.lower():
            resolved_app = self._resolve_appliance(mfg_part_num, desc)
            if resolved_app:
                return resolved_app

        # 3. Handle Decking / Lumber Distributors (Boise Cascade, Parksite, U S Lumber, Westwood, Palmer Donavin)
        if supplier_code in ["BOICA", "6151", "3073", "WESLU", "PALDO"] or any(
            x in raw_manuf.lower() for x in ["boise cascade", "parksite", "u s lumber", "westwood lumber", "palmer donavin"]
        ):
            resolved_deck = self._resolve_building_materials(e1_brand, dib_brand, desc, raw_manuf)
            if resolved_deck:
                return resolved_deck

        # 4. Check explicit supplier match in dictionary
        lookup_key = f"{supplier_name} ({supplier_code})" if supplier_code else supplier_name
        if lookup_key in self.supplier_map:
            ent = self.supplier_map[lookup_key]
            return self._format_entity(ent, desc, mfg_part_num)
        
        # Fuzzy match on supplier name
        for k, ent in self.supplier_map.items():
            if supplier_name and supplier_name.lower() in k.lower():
                return self._format_entity(ent, desc, mfg_part_num)

        # 5. Check DIB Brand or E1 Brand
        brand_candidate = dib_brand or e1_brand
        if brand_candidate:
            resolved_brand = self._resolve_from_brand_name(brand_candidate, desc)
            if resolved_brand:
                return resolved_brand

        # 6. Fallback from raw supplier name
        clean_name = re.sub(r"\s+inc\.?|\s+llc\.?|\s+corp\.?|\s+co\.?", "", raw_manuf, flags=re.I).strip()
        brand_name = clean_name.title() if clean_name else "Generic"
        return {
            "manufacturer_name": raw_manuf or "Industrial Supplies",
            "brand_name": f"{brand_name}®",
            "trade_name": brand_name,
            "series": "",
            "mfr_url": f"https://www.{re.sub(r'[^a-zA-Z0-9]', '', brand_name).lower()}.com"
        }

    def _resolve_missing_manufacturer(self, mpn: str, desc: str) -> Optional[Dict[str, str]]:
        """Resolve rows where Part_Manuf was '-'."""
        desc_lower = desc.lower()
        
        if "rdi" in desc_lower or "finyline" in desc_lower or "post trim" in desc_lower or "post sleeve" in desc_lower:
            return {
                "manufacturer_name": "Barrette Outdoor Living",
                "brand_name": "RDI®",
                "trade_name": "RDI Railing",
                "series": "Finyline Series" if "finyline" in desc_lower else "Elite Series",
                "mfr_url": "https://www.rdirail.com"
            }
        if "huber" in desc_lower or "zip" in desc_lower or "osb" in desc_lower:
            return {
                "manufacturer_name": "Huber Engineered Woods LLC",
                "brand_name": "ZIP System®" if "zip" in desc_lower else "AdvanTech®",
                "trade_name": "Huber",
                "series": "ZIP System R-Sheathing",
                "mfr_url": "https://www.huberwood.com"
            }
        if "lnl" in mpn.lower() or "tire pressure" in desc_lower:
            return {
                "manufacturer_name": "LockNLube, LLC",
                "brand_name": "LockNLube®",
                "trade_name": "LockNLube",
                "series": "Digital Gauges",
                "mfr_url": "https://www.locknlube.com"
            }
        if "patriot" in desc_lower or "spb-" in mpn.lower():
            return {
                "manufacturer_name": "Patriot Timber Products",
                "brand_name": "Patriot®",
                "trade_name": "Patriot",
                "series": "Adjustable Support Post",
                "mfr_url": "https://www.patriottimber.com"
            }
        if "united" in desc_lower or "slider" in desc_lower:
            return {
                "manufacturer_name": "United Window & Door Manufacturing",
                "brand_name": "United Window & Door",
                "trade_name": "3900 Series",
                "series": "3900 Series",
                "mfr_url": "https://www.unitedwindowmfg.com"
            }
        if "ice guard" in desc_lower or "weathr lk" in desc_lower:
            return {
                "manufacturer_name": "Owens Corning",
                "brand_name": "WeatherLock®",
                "trade_name": "Owens Corning",
                "series": "Ice & Water Barrier",
                "mfr_url": "https://www.owenscorning.com"
            }
        if "sl1672" in mpn.lower() or "jumpstart" in desc_lower:
            return {
                "manufacturer_name": "Schumacher Electric Corporation",
                "brand_name": "Schumacher®",
                "trade_name": "Schumacher",
                "series": "Power Supply",
                "mfr_url": "https://www.schumacherelectric.com"
            }
        if "kichler" in desc_lower:
            return {
                "manufacturer_name": "Kichler Lighting LLC",
                "brand_name": "Kichler®",
                "trade_name": "Kichler",
                "series": "Chandelier Series",
                "mfr_url": "https://www.kichler.com"
            }
        if "so cord" in desc_lower or "sjew" in desc_lower:
            return {
                "manufacturer_name": "Southwire Company, LLC",
                "brand_name": "Southwire®",
                "trade_name": "Southwire",
                "series": "Portable Power Cable",
                "mfr_url": "https://www.southwire.com"
            }
        if "hole drilling system" in desc_lower or "tp-" in mpn.lower():
            return {
                "manufacturer_name": "True Position Tools",
                "brand_name": "True Position®",
                "trade_name": "True Position",
                "series": "Cabinet Hardware Jig",
                "mfr_url": "https://www.truepositiontools.com"
            }
        if "fisch" in desc_lower:
            return {
                "manufacturer_name": "Fisch Tools",
                "brand_name": "Fisch®",
                "trade_name": "Fisch",
                "series": "Plug Cutters",
                "mfr_url": "https://www.fisch-tools.com"
            }
        if "bstd mill" in desc_lower or "file" in desc_lower:
            return {
                "manufacturer_name": "Apex Tool Group",
                "brand_name": "Crescent Nicholson®",
                "trade_name": "Nicholson",
                "series": "Bastard Mill File",
                "mfr_url": "https://www.crescenttool.com"
            }
        if "mafell" in desc_lower:
            return {
                "manufacturer_name": "Mafell AG",
                "brand_name": "Mafell®",
                "trade_name": "Mafell",
                "series": "Carpentry Machine Series",
                "mfr_url": "https://www.mafell.de"
            }
        if "leather phone holster" in desc_lower or "5328" in mpn:
            return {
                "manufacturer_name": "Custom LeatherCraft",
                "brand_name": "CLC®",
                "trade_name": "Tech Gear",
                "series": "Phone Holster",
                "mfr_url": "https://www.goclc.com"
            }
        if "andersen" in desc_lower or "tw52" in desc_lower:
            return {
                "manufacturer_name": "Andersen Corporation",
                "brand_name": "Andersen®",
                "trade_name": "Andersen Windows",
                "series": "A-Series",
                "mfr_url": "https://www.andersenwindows.com"
            }
        return None

    def _resolve_appliance(self, mpn: str, desc: str) -> Optional[Dict[str, str]]:
        """Resolve specific appliance brand & series from MPN prefix or description."""
        clean_mpn = mpn.upper().replace("-", "")
        desc_upper = desc.upper()
        
        # Match longest prefix from appliance_patterns
        for prefix in sorted(self.appliance_patterns.keys(), key=lambda x: -len(x)):
            if clean_mpn.startswith(prefix) or prefix in desc_upper:
                pattern_data = self.appliance_patterns[prefix]
                # Special series override if found in desc
                series = pattern_data.get("series", "")
                if "PROFESSIONAL" in desc_upper:
                    series = "Professional Series"
                elif "GALLERY" in desc_upper:
                    series = "Gallery Series"
                elif "ECO" in desc_upper:
                    series = "Eco Series"
                
                return {
                    "manufacturer_name": pattern_data["mfr"],
                    "brand_name": pattern_data["brand"],
                    "trade_name": pattern_data["trade"],
                    "series": series,
                    "mfr_url": f"https://www.{re.sub(r'[^a-zA-Z0-9]', '', pattern_data['brand']).lower()}.com"
                }
        
        # Keyword checks in description
        if "SPEED QUEEN" in desc_upper or " SQ " in desc_upper or desc_upper.startswith("SQ "):
            return {
                "manufacturer_name": "Alliance Laundry Systems LLC",
                "brand_name": "Speed Queen®",
                "trade_name": "Speed Queen",
                "series": "Classic Clean™ Series",
                "mfr_url": "https://www.speedqueen.com"
            }
        if "CAFE" in desc_upper or "CAFÉ" in desc_upper:
            return {
                "manufacturer_name": "GE Appliances, a Haier company",
                "brand_name": "Café™",
                "trade_name": "Café",
                "series": "Custom Series",
                "mfr_url": "https://www.cafeappliances.com"
            }
        if "KITCHEN AID" in desc_upper or "KITCHENAID" in desc_upper:
            return {
                "manufacturer_name": "Whirlpool Corporation",
                "brand_name": "KitchenAid®",
                "trade_name": "KitchenAid",
                "series": "Architect® Series",
                "mfr_url": "https://www.kitchenaid.com"
            }
        if "FRIGIDAIRE" in desc_upper:
            return {
                "manufacturer_name": "Rheem Manufacturing",
                "brand_name": "FRIGIDAIRE®",
                "trade_name": "Electrolux Home Products",
                "series": "Professional Series" if "PROFESSIONAL" in desc_upper else "Gallery Series",
                "mfr_url": "https://www.frigidaire.com"
            }
        if "LG " in desc_upper:
            return {
                "manufacturer_name": "LG Electronics USA, Inc.",
                "brand_name": "LG®",
                "trade_name": "LG Electronics",
                "series": "Smart Care Series",
                "mfr_url": "https://www.lg.com"
            }
        if "GE " in desc_upper:
            return {
                "manufacturer_name": "GE Appliances, a Haier company",
                "brand_name": "GE®",
                "trade_name": "GE Appliances",
                "series": "Profile Series",
                "mfr_url": "https://www.geappliances.com"
            }
        return None

    def _resolve_building_materials(self, e1: Optional[str], dib: Optional[str], desc: str, raw_manuf: str) -> Optional[Dict[str, str]]:
        """Resolve Trex, TimberTech, AZEK, LP SmartSide, James Hardie building products."""
        comb = f"{e1 or ''} {dib or ''} {desc}".upper()
        
        if "TIMBERTECH" in comb or "AZEK" in comb:
            series = "Vintage Collection" if "VINTAGE" in comb else "Terrain Collection"
            if "HARVEST" in comb:
                series = "Harvest Collection"
            elif "LANDMARK" in comb:
                series = "Landmark Collection"
            return {
                "manufacturer_name": "The AZEK Company",
                "brand_name": "TimberTech®",
                "trade_name": "AZEK®",
                "series": series,
                "mfr_url": "https://www.timbertech.com"
            }
        if "TREX" in comb:
            series = "Transcend Lineage" if "LINEAGE" in comb else ("Enhance Basics" if "BASICS" in comb else ("Enhance Naturals" if "NATURALS" in comb else "Select Collection"))
            if "TRANSCEND" in comb:
                series = "Transcend Collection"
            return {
                "manufacturer_name": "Trex Company, Inc.",
                "brand_name": "Trex®",
                "trade_name": "Trex",
                "series": series,
                "mfr_url": "https://www.trex.com"
            }
        if "LP SMARTSIDE" in comb or "SMARTSIDE" in comb:
            return {
                "manufacturer_name": "Louisiana-Pacific Corporation",
                "brand_name": "LP® SmartSide®",
                "trade_name": "LP Building Solutions",
                "series": "ExpertFinish® Series",
                "mfr_url": "https://www.lpcorp.com"
            }
        if "JAMESHARDIE" in comb or "HARDIE" in comb:
            return {
                "manufacturer_name": "James Hardie Building Products Inc.",
                "brand_name": "James Hardie®",
                "trade_name": "HardiePlank®",
                "series": "HardiePlank Lap Siding",
                "mfr_url": "https://www.jameshardie.com"
            }
        if "PROVIA" in comb:
            return {
                "manufacturer_name": "ProVia LLC",
                "brand_name": "ProVia®",
                "trade_name": "ProVia",
                "series": "Endure Series",
                "mfr_url": "https://www.provia.com"
            }
        if "CERTAINTEED" in comb:
            return {
                "manufacturer_name": "CertainTeed Corporation",
                "brand_name": "CertainTeed®",
                "trade_name": "CertainTeed",
                "series": "Monogram® Series",
                "mfr_url": "https://www.certainteed.com"
            }
        return None

    def _resolve_from_brand_name(self, brand: str, desc: str) -> Optional[Dict[str, str]]:
        """Resolve entity directly from a clean brand name."""
        b_upper = brand.upper()
        if "PHILIPS" in b_upper:
            return {
                "manufacturer_name": "Signify North America Corporation",
                "brand_name": "Philips®",
                "trade_name": "Philips Lighting",
                "series": "MasterClass Series",
                "mfr_url": "https://www.lighting.philips.com"
            }
        if "DIABLO" in b_upper:
            return {
                "manufacturer_name": "Freud America, Inc.",
                "brand_name": "Diablo®",
                "trade_name": "Freud",
                "series": "Steel Demon™ Series" if "STEEL DEMON" in desc.upper() else "Tracking Point™",
                "mfr_url": "https://www.diablotools.com"
            }
        if "DEWALT" in b_upper:
            return {
                "manufacturer_name": "Stanley Black & Decker",
                "brand_name": "DEWALT®",
                "trade_name": "DEWALT",
                "series": "20V MAX* XR® Series" if "XR" in desc.upper() else "20V MAX*",
                "mfr_url": "https://www.dewalt.com"
            }
        if "MILWAUKEE" in b_upper:
            return {
                "manufacturer_name": "Milwaukee Electric Tool Corp.",
                "brand_name": "Milwaukee®",
                "trade_name": "Milwaukee",
                "series": "M18 FUEL™" if "M18" in desc.upper() else ("M12 FUEL™" if "M12" in desc.upper() else "SHOCKWAVE™"),
                "mfr_url": "https://www.milwaukeetool.com"
            }
        if "LEVITON" in b_upper:
            return {
                "manufacturer_name": "Leviton Manufacturing Co., Inc.",
                "brand_name": "Leviton®",
                "trade_name": "Leviton",
                "series": "Decora® Series",
                "mfr_url": "https://www.leviton.com"
            }
        if "SATCO" in b_upper:
            return {
                "manufacturer_name": "Satco Products, Inc.",
                "brand_name": "SATCO®",
                "trade_name": "Nuvo®",
                "series": "Hi-Pro Series",
                "mfr_url": "https://www.satco.com"
            }
        if "SOUTHWIRE" in b_upper:
            return {
                "manufacturer_name": "Southwire Company, LLC",
                "brand_name": "Southwire®",
                "trade_name": "Southwire",
                "series": "Armorlite®",
                "mfr_url": "https://www.southwire.com"
            }
        if "3M" in b_upper:
            return {
                "manufacturer_name": "3M Company",
                "brand_name": "3M™",
                "trade_name": "Cubitron™ II",
                "series": "Cubitron™ II 775L",
                "mfr_url": "https://www.3m.com"
            }
        return None

    def _format_entity(self, ent: Dict[str, str], desc: str, mpn: str) -> Dict[str, str]:
        """Format resolved entity with category-specific series."""
        series = ent.get("series", "")
        desc_upper = desc.upper()
        
        # Check series patterns
        if "PROFESSIONAL" in desc_upper:
            series = "Professional Series"
        elif "ECO" in desc_upper:
            series = "Eco Series"
        elif "TRANSCEND" in desc_upper:
            series = "Transcend Lineage" if "LINEAGE" in desc_upper else "Transcend Series"
        elif "ENHANCE BASICS" in desc_upper:
            series = "Enhance Basics"
        elif "ENHANCE NATURALS" in desc_upper:
            series = "Enhance Naturals"
        elif "SELECT" in desc_upper and "TREX" in ent.get("brand", "").upper():
            series = "Select Series"
        elif "VINTAGE" in desc_upper:
            series = "Vintage Collection"
        elif "M18" in desc_upper:
            series = "M18 Series"
        elif "M12" in desc_upper:
            series = "M12 Series"
        elif "20V MAX" in desc_upper or "20V" in desc_upper:
            series = "20V MAX XR" if "XR" in desc_upper else "20V MAX"
        elif "CUBITRON" in desc_upper:
            series = "Cubitron II"
        elif "STIKIT" in desc_upper:
            series = "Stikit 775L"
        
        return {
            "manufacturer_name": ent.get("mfr", ""),
            "brand_name": ent.get("brand", ""),
            "trade_name": ent.get("trade", ""),
            "series": series,
            "mfr_url": ent.get("url", f"https://www.{re.sub(r'[^a-zA-Z0-9]', '', ent.get('brand', '')).lower()}.com")
        }
