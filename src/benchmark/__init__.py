"""
UniHack Industrial Product Intelligence & PIM Enrichment: Benchmarking & QA Suite.
"""

from .metrics import (
    exact_match,
    normalized_exact_match,
    levenshtein_distance,
    levenshtein_similarity,
    token_jaccard,
    token_cosine,
    sentence_bleu,
    bleu_1,
    bleu_2,
    bleu_4,
    rouge_n,
    rouge_l,
    evaluate_triplet_attributes,
    calculate_text_similarity_suite
)

from .hard_gates import (
    validate_invoice_desc,
    validate_invoice_desc_batch,
    validate_mobile_desc,
    validate_mobile_desc_batch,
    validate_lov_hallucinations,
    validate_schema_252,
    HardGateViolation,
    HardGateResult,
    HardGateSuite,
    HardGateSuiteReport,
    EXPECTED_252_COLUMNS
)

from .confidence import (
    ConfidenceBreakdown,
    AnomalyFlag,
    ProductConfidenceReport,
    BatchConfidenceReport,
    ConfidenceScorer,
    score_catalog_batch,
    CONFIDENCE_WEIGHTS,
    CONFIDENCE_THRESHOLD_VALIDATED,
    CONFIDENCE_THRESHOLD_ENRICHED
)

from .evaluator import (
    ColumnMetricResult,
    DescriptionTierMetricResult,
    BenchmarkReport,
    CatalogEvaluator
)

__all__ = [
    # Metrics
    "exact_match",
    "normalized_exact_match",
    "levenshtein_distance",
    "levenshtein_similarity",
    "token_jaccard",
    "token_cosine",
    "sentence_bleu",
    "bleu_1",
    "bleu_2",
    "bleu_4",
    "rouge_n",
    "rouge_l",
    "evaluate_triplet_attributes",
    "calculate_text_similarity_suite",
    # Hard Gates
    "validate_invoice_desc",
    "validate_invoice_desc_batch",
    "validate_mobile_desc",
    "validate_mobile_desc_batch",
    "validate_lov_hallucinations",
    "validate_schema_252",
    "HardGateViolation",
    "HardGateResult",
    "HardGateSuite",
    "HardGateSuiteReport",
    "EXPECTED_252_COLUMNS",
    # Confidence
    "ConfidenceBreakdown",
    "AnomalyFlag",
    "ProductConfidenceReport",
    "BatchConfidenceReport",
    "ConfidenceScorer",
    "score_catalog_batch",
    "CONFIDENCE_WEIGHTS",
    "CONFIDENCE_THRESHOLD_VALIDATED",
    "CONFIDENCE_THRESHOLD_ENRICHED",
    # Evaluator
    "ColumnMetricResult",
    "DescriptionTierMetricResult",
    "BenchmarkReport",
    "CatalogEvaluator",
]
