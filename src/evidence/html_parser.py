"""
Official Manufacturer HTML Product Page Parser.

Extracts structured technical specifications, headings, and spec tables from official HTML.
"""

from html.parser import HTMLParser
from typing import List, Dict, Tuple, Optional, Any
import re


class ManufacturerHTMLParser(HTMLParser):
    """Event-driven HTML parser for manufacturer technical specifications."""
    
    def __init__(self):
        super().__init__()
        self.sections: List[Dict[str, Any]] = []
        self.current_heading: str = "General Overview"
        self.current_text: List[str] = []
        self.current_specs: Dict[str, str] = {}
        self.current_table_rows: List[List[str]] = []
        self.current_row: List[str] = []
        self.current_cell: List[str] = []
        self.in_heading = False
        self.in_table = False
        self.in_cell = False
        self.in_script_or_style = False
        self.title: str = ""
        self.in_title = False

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        tag_lower = tag.lower()
        if tag_lower in ("script", "style", "noscript", "svg", "nav", "footer"):
            self.in_script_or_style = True
        elif tag_lower == "title":
            self.in_title = True
        elif tag_lower in ("h1", "h2", "h3", "h4"):
            self._flush_section()
            self.in_heading = True
        elif tag_lower == "table":
            self.in_table = True
            self.current_table_rows = []
        elif tag_lower == "tr" and self.in_table:
            self.current_row = []
        elif tag_lower in ("td", "th") and self.in_table:
            self.in_cell = True
            self.current_cell = []

    def handle_endtag(self, tag: str):
        tag_lower = tag.lower()
        if tag_lower in ("script", "style", "noscript", "svg", "nav", "footer"):
            self.in_script_or_style = False
        elif tag_lower == "title":
            self.in_title = False
        elif tag_lower in ("h1", "h2", "h3", "h4"):
            self.in_heading = False
        elif tag_lower in ("td", "th") and self.in_table:
            self.in_cell = False
            cell_text = " ".join("".join(self.current_cell).split())
            if cell_text:
                self.current_row.append(cell_text)
            self.current_cell = []
        elif tag_lower == "tr" and self.in_table:
            if len(self.current_row) == 2:
                k, v = self.current_row[0].strip(), self.current_row[1].strip()
                if len(k) > 1 and len(v) > 0:
                    self.current_specs[k] = v
            if self.current_row:
                self.current_table_rows.append(self.current_row)
            self.current_row = []
        elif tag_lower == "table":
            self.in_table = False
            if self.current_table_rows:
                table_lines = [f"{r[0]}: {r[1]}" if len(r) == 2 else " | ".join(r) for r in self.current_table_rows]
                self.current_text.extend(table_lines)
            self.current_table_rows = []

    def handle_data(self, data: str):
        if self.in_script_or_style:
            return
        cleaned = data.strip()
        if not cleaned:
            return
            
        if self.in_title:
            self.title = (self.title + " " + cleaned).strip()
        elif self.in_heading:
            self.current_heading = cleaned
        elif self.in_cell:
            self.current_cell.append(data)
        else:
            self.current_text.append(cleaned)

    def _flush_section(self):
        text_body = "\n".join(self.current_text).strip()
        specs = dict(self.current_specs)
        # Also parse line-by-line 'Key: Value' from non-table text
        for line in self.current_text:
            m = re.match(r"^\s*([A-Za-z0-9\s/_\-()]{2,35})\s*:\s*(.+)$", line)
            if m:
                k, v = m.group(1).strip(), m.group(2).strip()
                if k not in specs:
                    specs[k] = v

        if text_body or self.current_heading or specs:
            self.sections.append({
                "heading": self.current_heading or "General Information",
                "text": text_body,
                "specs": specs
            })
        self.current_text = []
        self.current_specs = {}

    def finish(self) -> Tuple[str, List[Dict[str, Any]]]:
        self._flush_section()
        # Filter empty sections
        valid_sections = [s for s in self.sections if s["text"] or s["specs"]]
        return self.title or "Official Manufacturer Product Specifications", valid_sections


def parse_manufacturer_html(html_content: str) -> Tuple[str, List[Dict[str, Any]]]:
    """Parse raw HTML content and return (title, list of structured sections)."""
    parser = ManufacturerHTMLParser()
    parser.feed(html_content)
    return parser.finish()
