"""
Stage 5: UOM & Fraction Standardization Engine.
"""

import json
import os
import re
from typing import Optional, Dict, Any, Tuple


class UOMStandardizer:
    """Standardizes Units of Measure (UOMs), converts decimals to 64th fractions, and enforces whitespace rules."""

    def __init__(self, dict_path: Optional[str] = None):
        if not dict_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            dict_path = os.path.join(base_dir, "data", "dictionaries", "uom_definitions.json")
        
        self.dec_to_frac = {}
        self.uom_synonyms = {}
        if os.path.exists(dict_path):
            with open(dict_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.dec_to_frac = data.get("decimal_to_fraction_64ths", {})
                self.uom_synonyms = data.get("uom_synonym_map", {})

    def normalize_uom(self, uom: Optional[str]) -> str:
        """Map raw UOM variant to canonical Unilog standard abbreviation."""
        if not uom:
            return ""
        clean = uom.strip().lower()
        if clean in self.uom_synonyms:
            return self.uom_synonyms[clean]
        # Common direct mappings
        if clean in ["v", "vac", "vdc"]:
            return "V"
        if clean in ["a", "amp", "amps"]:
            return "A"
        if clean in ["w", "watt", "watts"]:
            return "W"
        if clean in ["in", "inch", "inches", "\""]:
            return "in"
        if clean in ["ft", "foot", "feet", "'"]:
            return "ft"
        if clean in ["dba", "db", "decibels"]:
            return "dBA"
        if clean in ["lb", "lbs", "pound", "pounds"]:
            return "lb"
        if clean in ["kw-hr", "kwh", "kw hr"]:
            return "kW-hr"
        if clean in ["ea", "each"]:
            return "EA"
        if clean in ["pk", "pack"]:
            return "PK"
        if clean in ["lft", "linear foot", "linear feet"]:
            return "LFT"
        return uom.strip()

    def decimal_to_fraction(self, decimal_val: float) -> str:
        """Convert a decimal number to nearest 64th standard fraction string."""
        sign = "-" if decimal_val < 0 else ""
        abs_val = abs(decimal_val)
        whole = int(abs_val)
        remainder = round(abs_val - whole, 6)
        
        if remainder < 0.0078125:
            return f"{sign}{whole}" if whole != 0 else "0"
        if remainder >= 0.9921875:
            return f"{sign}{whole + 1}"
        
        # Find closest standard 64th
        best_frac = None
        min_diff = 1.0
        for dec_str, frac_str in self.dec_to_frac.items():
            dec_num = float(dec_str)
            diff = abs(remainder - dec_num)
            if diff < min_diff:
                min_diff = diff
                best_frac = frac_str
        
        if not best_frac:
            return f"{decimal_val:.2f}".rstrip("0").rstrip(".")
        
        if whole > 0:
            return f"{sign}{whole}-{best_frac}"
        return f"{sign}{best_frac}"

    def standardize_dimension_string(self, text: str) -> str:
        """Standardize dimensions with fractions and proper UOM spacing (e.g. 1/2\"x18\" -> 1/2 in x 18 in)."""
        if not text:
            return ""
        
        # Replace dimension delimiters
        s = text
        
        # Convert decimal inches: e.g. 50.25 in -> 50-1/4 in
        def replace_decimal(match):
            val = float(match.group(1))
            unit = match.group(2) or "in"
            frac = self.decimal_to_fraction(val)
            norm_unit = self.normalize_uom(unit)
            return f"{frac} {norm_unit}".strip()

        s = re.sub(r"(\d+\.\d+)\s*(in|inch|inches|\"|ft|'|mm|cm)?\b", replace_decimal, s, flags=re.I)
        
        # Replace quotes with 'in' and primes with 'ft'
        s = re.sub(r"(\d+(?:-\d+/\d+|\s+\d+/\d+|/\d+)?)\s*\"", r"\1 in", s)
        s = re.sub(r"(\d+(?:-\d+/\d+|\s+\d+/\d+|/\d+)?)\s*'", r"\1 ft", s)
        
        # Ensure ' x ' spacing between dimensions
        s = re.sub(r"\s*[xX]\s*", " x ", s)
        
        # Fix missing space before units
        s = re.sub(r"(\d+)(in|ft|V|A|W|dBA|lb|kW-hr)\b", r"\1 \2", s)
        
        # Normalize double spaces
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def format_value_with_uom(self, value: str, uom: Optional[str]) -> str:
        """Format a value with its canonical UOM enforcing the single space rule."""
        if not value:
            return ""
        val = str(value).strip()
        # Convert decimal if numeric
        try:
            val_float = float(val)
            if uom in ["in", "ft", "inch", "inches", "\""]:
                val = self.decimal_to_fraction(val_float)
        except ValueError:
            pass
        
        if not uom:
            return val
        norm_uom = self.normalize_uom(uom)
        return f"{val} {norm_uom}"
