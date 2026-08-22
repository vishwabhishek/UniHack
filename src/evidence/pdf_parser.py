"""
Official Manufacturer PDF Specification Sheet Parser with Page-Level Traceability.

Extracts text and key-value specs from official manufacturer PDF spec sheets using pypdf.
"""

import io
import re
import logging
from typing import List, Dict, Tuple, Any, Union

logger = logging.getLogger(__name__)


def parse_manufacturer_pdf_file(
    file_input: Union[str, bytes, io.BytesIO],
    title: str = "Official Specification Sheet"
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Parse a binary PDF file or bytes with page-level granularity using pypdf.
    Extracts text per page, preserves exact page numbers, and parses section blocks.
    """
    sections: List[Dict[str, Any]] = []

    try:
        from pypdf import PdfReader

        if isinstance(file_input, (bytes, bytearray)):
            stream = io.BytesIO(file_input)
        elif isinstance(file_input, str):
            stream = open(file_input, "rb")
        else:
            stream = file_input

        reader = PdfReader(stream)
        total_pages = len(reader.pages)

        for page_idx, page in enumerate(reader.pages):
            page_num = page_idx + 1
            page_text = page.extract_text() or ""
            if not page_text.strip():
                continue

            _, page_sections = parse_manufacturer_pdf_text(page_text, title=f"{title} (Page {page_num})")
            for sec in page_sections:
                sec["page_number"] = page_num
                sections.append(sec)

        if isinstance(file_input, str) and hasattr(stream, "close"):
            stream.close()

    except Exception as e:
        logger.warning(f"pypdf extraction failed, falling back to text regex parser: {e}")

    if not sections and isinstance(file_input, (bytes, bytearray)):
        try:
            raw_text = file_input.decode("utf-8", errors="replace")
            _, sections = parse_manufacturer_pdf_text(raw_text, title=title)
        except Exception:
            pass

    return title, sections


def parse_manufacturer_pdf_text(text_content: str, title: str = "Official Specification Sheet") -> Tuple[str, List[Dict[str, Any]]]:
    """
    Parse text extracted from an official manufacturer PDF or spec sheet.
    Splits into logical sections by major specification headers.
    """
    sections: List[Dict[str, Any]] = []
    
    header_regex = re.compile(
        r"(?:^|\n)(PRODUCT SPECIFICATIONS|ELECTRICAL SPECIFICATIONS|DIMENSIONS & WEIGHT|GENERAL SPECIFICATIONS|PERFORMANCE|CONTROLS|INSTALLATION|WARRANTY|FEATURES & BENEFITS|CAPACITY|WATER & ENERGY|SPECIFICATIONS)\b",
        re.IGNORECASE
    )
    
    lines = text_content.splitlines()
    current_heading = "General Specifications"
    current_lines = []
    page_num = 1
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
            
        page_match = re.match(r"(?:Page|PAGE)\s*(\d+)", stripped)
        if page_match:
            try:
                page_num = int(page_match.group(1))
            except ValueError:
                pass
            continue
            
        if header_regex.match(stripped) or (len(stripped) < 40 and stripped.isupper() and len(stripped.split()) <= 4):
            if current_lines:
                body = "\n".join(current_lines)
                specs = _extract_specs_from_text(body)
                sections.append({
                    "heading": current_heading,
                    "page_number": page_num,
                    "text": body,
                    "specs": specs
                })
                current_lines = []
            current_heading = stripped
        else:
            current_lines.append(stripped)
            
    if current_lines:
        body = "\n".join(current_lines)
        specs = _extract_specs_from_text(body)
        sections.append({
            "heading": current_heading,
            "page_number": page_num,
            "text": body,
            "specs": specs
        })
        
    return title, sections


def _extract_specs_from_text(text: str) -> Dict[str, str]:
    """Extract 'Key: Value' or tabular pairs from text."""
    specs = {}
    for line in text.splitlines():
        m = re.match(r"^\s*([A-Za-z0-9\s/_\-()]{3,35})\s*[:\t]\s*(.+)$", line)
        if m:
            k, v = m.group(1).strip(), m.group(2).strip()
            if len(k) > 2 and len(v) > 0 and len(v) < 100:
                specs[k] = v
        else:
            parts = re.split(r"\s{3,}", line.strip())
            if len(parts) == 2:
                k, v = parts[0].strip(), parts[1].strip()
                if len(k) > 2 and len(v) > 0 and len(v) < 100:
                    specs[k] = v
    return specs

