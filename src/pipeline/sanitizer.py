"""
Stage 1: Ingestion Sanitizer & Placeholder Nullifier.
"""

import re
import unicodedata
from typing import Dict, Any, Optional, Tuple, List
from .models import RawProduct


class ProductSanitizer:
    """Sanitizes raw distributor records, removes sentinel placeholders, and normalizes text."""

    PLACEHOLDER_SET = {
        "-- unbranded --",
        "-- no unilog brand --",
        "-- no dib brand --",
        "commodity - unbranded",
        "-",
        "none",
        "n/a",
        "na",
        "null",
        "unknown",
        ".",
        "unbranded",
        "no brand",
        "empty",
        "undefined"
    }

    SUPPLIER_CODE_REGEX = re.compile(r"^(?P<name>.*?)(?:\s*\((?P<code>[A-Za-z0-9]+)\))?$")

    @classmethod
    def clean_placeholder(cls, value: Optional[str]) -> Optional[str]:
        """Convert sentinel placeholders to None or clean string."""
        if not value:
            return None
        cleaned = value.strip()
        if cleaned.lower() in cls.PLACEHOLDER_SET:
            return None
        return cleaned

    @classmethod
    def normalize_unicode(cls, text: str) -> str:
        """Normalize Unicode characters, smart quotes, dashes, whitespace, and strip control codes."""
        if not text:
            return ""
        # NFKD normalization
        norm = unicodedata.normalize("NFKD", text)
        
        # Strip unprintable control characters and zero-width / bidi formatting codes
        norm = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u200b-\u200f\u202a-\u202e\ufeff]", "", norm)
        
        # Replace smart quotes, guillemets, & primes
        norm = norm.replace("“", "\"").replace("”", "\"").replace("″", "\"").replace("„", "\"").replace("«", "\"").replace("»", "\"")
        norm = norm.replace("‘", "'").replace("’", "'").replace("′", "'").replace("‚", "'").replace("‛", "'")
        
        # Replace en-dash, em-dash, minus, horizontal bar with standard hyphen
        norm = norm.replace("–", "-").replace("—", "-").replace("−", "-").replace("―", "-").replace("‐", "-").replace("‑", "-")
        
        # Replace non-breaking spaces and line breaks
        norm = norm.replace("\u00a0", " ").replace("\u202f", " ").replace("\u3000", " ").replace("\t", " ").replace("\r", " ").replace("\n", " ")
        
        # Collapse multiple spaces
        norm = re.sub(r"\s+", " ", norm).strip()
        return norm

    @classmethod
    def parse_supplier(cls, part_manuf: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        """Parse supplier string into clean vendor name and supplier code."""
        cleaned = cls.clean_placeholder(part_manuf)
        if not cleaned:
            return None, None
        
        cleaned = cls.normalize_unicode(cleaned)
        match = cls.SUPPLIER_CODE_REGEX.match(cleaned)
        if match:
            name = match.group("name").strip()
            code = match.group("code")
            return name if name else None, code if code else None
        return cleaned, None

    @classmethod
    def sanitize(cls, raw: RawProduct) -> Dict[str, Any]:
        """Perform comprehensive sanitization on raw product input."""
        mfg_part_num = cls.normalize_unicode(raw.mfg_part_num.strip())
        raw_desc = cls.normalize_unicode(raw.part_desc.strip())
        
        e1_brand = cls.clean_placeholder(raw.e1_brand)
        unilog_brand = cls.clean_placeholder(raw.unilog_brand)
        dib_brand = cls.clean_placeholder(raw.dib_brand)
        supplier_name, supplier_code = cls.parse_supplier(raw.part_manuf)
        
        # Extract display modifier
        is_display = False
        desc_clean = raw_desc
        if re.search(r"(?i)-\s*display\s*(?:only)?\b|\bdisplay\s*only\b", desc_clean):
            is_display = True
            desc_clean = re.sub(r"(?i)-\s*display\s*(?:only)?\b|\bdisplay\s*only\b", "", desc_clean).strip()
        
        # Extract bare tool modifier
        is_bare_tool = False
        if re.search(r"(?i)\(bare(?:\s*tool)?\)", desc_clean):
            is_bare_tool = True
            desc_clean = re.sub(r"(?i)\(bare(?:\s*tool)?\)", "", desc_clean).strip()
        
        # Extract linear foot modifier
        is_linear_foot = False
        if re.search(r"(?i)\(linear\s*foot\)", desc_clean):
            is_linear_foot = True
            desc_clean = re.sub(r"(?i)\(linear\s*foot\)", "", desc_clean).strip()

        # Strip redundant leading MPN from description
        desc_tokens = desc_clean
        # Check if description starts with MPN (case-insensitive or exact)
        if mfg_part_num and desc_tokens.lower().startswith(mfg_part_num.lower()):
            desc_tokens = desc_tokens[len(mfg_part_num):].strip()
            # remove leading hyphens, colons, spaces
            desc_tokens = re.sub(r"^[\s\-:]+", "", desc_tokens).strip()

        # Clean trailing and leading dashes
        desc_tokens = re.sub(r"^[\s\-:]+|[\s\-:]+$", "", desc_tokens).strip()
        desc_tokens = cls.normalize_unicode(desc_tokens)

        return {
            "mfg_part_num": mfg_part_num,
            "raw_desc": raw_desc,
            "desc_clean": desc_clean,
            "desc_tokens": desc_tokens,
            "e1_brand": e1_brand,
            "unilog_brand": unilog_brand,
            "dib_brand": dib_brand,
            "supplier_name": supplier_name,
            "supplier_code": supplier_code,
            "is_display": is_display,
            "is_bare_tool": is_bare_tool,
            "is_linear_foot": is_linear_foot,
        }
