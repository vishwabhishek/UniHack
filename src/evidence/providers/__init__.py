"""
Official Manufacturer Evidence Extraction Providers.
Supports Gemini AI structured extraction and deterministic rule fallback.
"""

from .base import (
    BaseEvidenceExtractionProvider,
    ExtractionRequest,
    ExtractionResult,
    GeminiExtractedFact,
    GeminiExtractionOutput,
)
from .gemini import GeminiEvidenceExtractionProvider

__all__ = [
    "BaseEvidenceExtractionProvider",
    "ExtractionRequest",
    "ExtractionResult",
    "GeminiExtractedFact",
    "GeminiExtractionOutput",
    "GeminiEvidenceExtractionProvider",
]
