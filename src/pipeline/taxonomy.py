"""
Stage 3: Taxonomy & UNSPSC Hierarchical Classification.
"""

import json
import os
import re
from typing import Dict, Any, Optional, List


class TaxonomyClassifier:
    """Classifies sanitized product records into hierarchical Classpaths and UNSPSC codes."""

    def __init__(self, dict_path: Optional[str] = None):
        if not dict_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            dict_path = os.path.join(base_dir, "data", "dictionaries", "taxonomy_classpaths.json")
        
        self.rules = []
        if os.path.exists(dict_path):
            with open(dict_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.rules = data.get("rules", [])

    def classify(self, sanitized: Dict[str, Any], entity: Dict[str, str]) -> Dict[str, Any]:
        """Determine Department, Class, Fine, Classpath, UNSPSC, Product Name, and attribute template."""
        desc = sanitized.get("raw_desc", "").lower()
        desc_tokens = sanitized.get("desc_tokens", "").lower()
        brand = entity.get("brand_name", "").lower()
        comb = f"{desc} {desc_tokens} {brand}"

        # Match rules in priority sequence
        best_rule = None
        max_score = 0

        for rule in self.rules:
            score = 0
            for kw in rule.get("keywords", []):
                pattern = r"\b" + re.escape(kw) + r"\b"
                if re.search(pattern, comb, re.I):
                    score += len(kw)  # longer matching keyword gives higher weight
                elif kw in comb:
                    score += len(kw) * 0.5

            if score > max_score:
                max_score = score
                best_rule = rule

        # Fallback if no rule matched with high confidence
        if not best_rule or max_score == 0:
            best_rule = {
                "dept": "Industrial Supplies",
                "class_name": "General Maintenance & Repair",
                "fine": "General Hardware & Tools",
                "classpath": "Industrial Supplies>Maintenance & Repair>General Hardware",
                "unspsc": "27110000",
                "product_name": "Industrial Component",
                "attribute_template": ["Material", "Finish", "Size", "Additional Information"]
            }

        return {
            "dept": best_rule.get("dept", ""),
            "class_name": best_rule.get("class_name", ""),
            "fine": best_rule.get("fine", ""),
            "classpath": best_rule.get("classpath", ""),
            "unspsc": best_rule.get("unspsc", ""),
            "product_name": best_rule.get("product_name", ""),
            "attribute_template": best_rule.get("attribute_template", [])
        }
