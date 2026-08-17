"""
Comprehensive NLP, Edit-Distance, and Structured Evaluation Metrics for PIM Catalog Benchmarking.

Includes:
- Exact Match & Normalized Match
- Levenshtein Distance & Normalized Levenshtein Similarity
- Token Jaccard & Token Cosine Similarity
- Sentence BLEU (BLEU-1, BLEU-2, BLEU-4) with Brevity Penalty & Chen-Cherry Smoothing
- ROUGE (ROUGE-1, ROUGE-2, ROUGE-L via Longest Common Subsequence)
- Dynamic Triplet Attribute Precision, Recall, and F1
"""

import math
import re
import unicodedata
from collections import Counter
from typing import List, Tuple, Set, Dict, Any, Optional, Union


# ===========================================================================
# 1. Text Normalization & Tokenization
# ===========================================================================

def normalize_text(text: Optional[str]) -> str:
    """Normalize string by unicode folding, stripping whitespace, removing trademarks, and lowering case."""
    if text is None:
        return ""
    # Unicode NFKD normalization
    norm = unicodedata.normalize("NFKD", str(text))
    # Replace unicode quotes and dashes with ASCII equivalents
    norm = norm.replace("“", "\"").replace("”", "\"").replace("″", "\"")
    norm = norm.replace("‘", "'").replace("’", "'").replace("′", "'")
    norm = norm.replace("–", "-").replace("—", "-").replace("−", "-")
    # Strip trademark and copyright symbols
    norm = norm.replace("®", "").replace("™", "").replace("©", "")
    # Collapse multiple whitespaces
    norm = re.sub(r"\s+", " ", norm).strip().lower()
    return norm


def tokenize(text: Optional[str]) -> List[str]:
    """Tokenize text into lowercase alphanumeric and symbolic words."""
    if not text:
        return []
    norm = normalize_text(text)
    # Split on whitespace and non-alphanumeric punctuation boundaries
    tokens = re.findall(r"\b[\w\-\./%]+\b", norm)
    return tokens if tokens else [t for t in norm.split() if t]


# ===========================================================================
# 2. Exact Match & Normalized Equality
# ===========================================================================

def exact_match(reference: Optional[str], candidate: Optional[str]) -> float:
    """Binary exact match equality: 1.0 if identical, 0.0 otherwise."""
    ref_str = "" if reference is None else str(reference)
    cand_str = "" if candidate is None else str(candidate)
    return 1.0 if ref_str == cand_str else 0.0


def normalized_exact_match(reference: Optional[str], candidate: Optional[str]) -> float:
    """Normalized equality after case-folding, unicode normalization, and space stripping."""
    norm_ref = normalize_text(reference)
    norm_cand = normalize_text(candidate)
    return 1.0 if norm_ref == norm_cand else 0.0


# ===========================================================================
# 3. Levenshtein Distance & Normalized Similarity
# ===========================================================================

def levenshtein_distance(s1: Optional[str], s2: Optional[str]) -> int:
    """Calculate character-level Levenshtein edit distance using Wagner-Fischer algorithm with O(min(N, M)) memory."""
    str1 = "" if s1 is None else str(s1)
    str2 = "" if s2 is None else str(s2)

    if str1 == str2:
        return 0
    if len(str1) == 0:
        return len(str2)
    if len(str2) == 0:
        return len(str1)

    # Ensure str1 is the shorter string to optimize space
    if len(str1) > len(str2):
        str1, str2 = str2, str1

    previous_row = list(range(len(str1) + 1))
    current_row = [0] * (len(str1) + 1)

    for i, c2 in enumerate(str2):
        current_row[0] = i + 1
        for j, c1 in enumerate(str1):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row[j + 1] = min(insertions, deletions, substitutions)
        previous_row, current_row = current_row, previous_row

    return previous_row[len(str1)]


def levenshtein_similarity(reference: Optional[str], candidate: Optional[str]) -> float:
    """
    Normalized Levenshtein similarity score:
    Sim(s1, s2) = 1.0 - (LevenshteinDistance(s1, s2) / max(|s1|, |s2|))
    Returns 1.0 for two empty strings, 0.0 for one empty string vs non-empty.
    """
    ref_str = "" if reference is None else str(reference)
    cand_str = "" if candidate is None else str(candidate)

    if not ref_str and not cand_str:
        return 1.0
    max_len = max(len(ref_str), len(cand_str))
    if max_len == 0:
        return 1.0

    dist = levenshtein_distance(ref_str, cand_str)
    sim = 1.0 - (dist / max_len)
    return max(0.0, min(1.0, sim))


# ===========================================================================
# 4. Token Jaccard & Cosine Similarity
# ===========================================================================

def token_jaccard(reference: Optional[str], candidate: Optional[str]) -> float:
    """
    Token Jaccard similarity:
    Jaccard(T1, T2) = |T1 ∩ T2| / |T1 ∪ T2|
    """
    tokens_ref = set(tokenize(reference))
    tokens_cand = set(tokenize(candidate))

    if not tokens_ref and not tokens_cand:
        return 1.0
    if not tokens_ref or not tokens_cand:
        return 0.0

    intersection = tokens_ref.intersection(tokens_cand)
    union = tokens_ref.union(tokens_cand)

    return len(intersection) / len(union) if union else 0.0


def token_cosine(reference: Optional[str], candidate: Optional[str]) -> float:
    """Token-level Cosine similarity using Term Frequency (TF) vectors."""
    tokens_ref = tokenize(reference)
    tokens_cand = tokenize(candidate)

    if not tokens_ref and not tokens_cand:
        return 1.0
    if not tokens_ref or not tokens_cand:
        return 0.0

    count_ref = Counter(tokens_ref)
    count_cand = Counter(tokens_cand)

    all_vocab = set(count_ref.keys()).union(set(count_cand.keys()))
    dot_product = sum(count_ref[w] * count_cand[w] for w in all_vocab)
    norm_ref = math.sqrt(sum(v * v for v in count_ref.values()))
    norm_cand = math.sqrt(sum(v * v for v in count_cand.values()))

    if norm_ref == 0 or norm_cand == 0:
        return 0.0

    return dot_product / (norm_ref * norm_cand)


# ===========================================================================
# 5. Sentence BLEU Score (BLEU-1, BLEU-2, BLEU-4)
# ===========================================================================

def _get_ngrams(tokens: List[str], n: int) -> Counter:
    """Extract n-gram frequency counter from list of tokens."""
    if len(tokens) < n or n <= 0:
        return Counter()
    return Counter(tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1))


def sentence_bleu(
    reference: Optional[str],
    candidate: Optional[str],
    weights: Tuple[float, ...] = (0.25, 0.25, 0.25, 0.25),
    smoothing: bool = True
) -> float:
    """
    Calculate Sentence BLEU score with modified n-gram precisions, brevity penalty,
    and Chen & Cherry / Laplace smoothing for higher-order n-grams.
    """
    ref_tokens = tokenize(reference)
    cand_tokens = tokenize(candidate)

    # Empty edge cases
    if not ref_tokens and not cand_tokens:
        return 1.0
    if not cand_tokens:
        return 0.0
    if not ref_tokens:
        return 0.0

    c = len(cand_tokens)
    r = len(ref_tokens)

    # 1. Brevity Penalty
    if c > r:
        bp = 1.0
    elif c == 0:
        bp = 0.0
    else:
        bp = math.exp(1.0 - (r / c))

    # 2. Modified N-gram precisions
    max_order = len(weights)
    p_n = []

    for n in range(1, max_order + 1):
        cand_ngrams = _get_ngrams(cand_tokens, n)
        ref_ngrams = _get_ngrams(ref_tokens, n)

        total_cand_ngrams = sum(cand_ngrams.values())
        if total_cand_ngrams == 0:
            if smoothing:
                p_n.append(1.0 / (c + 1))
            else:
                p_n.append(0.0)
            continue

        # Clipped counts
        clipped_count = 0
        for ngram, count in cand_ngrams.items():
            clipped_count += min(count, ref_ngrams.get(ngram, 0))

        if clipped_count == 0:
            if smoothing:
                # Chen-Cherry Method 1 smoothing
                p_n.append(1.0 / (total_cand_ngrams + 1.0))
            else:
                p_n.append(0.0)
        else:
            p_n.append(clipped_count / total_cand_ngrams)

    # 3. Geometric mean of log precisions
    score = 0.0
    for w, p in zip(weights, p_n):
        if w > 0:
            if p <= 0:
                return 0.0
            score += w * math.log(p)

    bleu = bp * math.exp(score)
    return max(0.0, min(1.0, bleu))


def bleu_1(reference: Optional[str], candidate: Optional[str]) -> float:
    """Sentence BLEU-1 (Unigram Precision with Brevity Penalty)."""
    return sentence_bleu(reference, candidate, weights=(1.0,))


def bleu_2(reference: Optional[str], candidate: Optional[str]) -> float:
    """Sentence BLEU-2 (Bigram Precision with Brevity Penalty)."""
    return sentence_bleu(reference, candidate, weights=(0.5, 0.5))


def bleu_4(reference: Optional[str], candidate: Optional[str]) -> float:
    """Sentence BLEU-4 (4-gram Precision with Brevity Penalty)."""
    return sentence_bleu(reference, candidate, weights=(0.25, 0.25, 0.25, 0.25))


# ===========================================================================
# 6. ROUGE (ROUGE-1, ROUGE-2, ROUGE-L via Longest Common Subsequence)
# ===========================================================================

def _lcs_length(seq1: List[str], seq2: List[str]) -> int:
    """Compute Longest Common Subsequence (LCS) length between two token lists."""
    m = len(seq1)
    n = len(seq2)
    if m == 0 or n == 0:
        return 0

    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if seq1[i - 1] == seq2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    return dp[m][n]


def rouge_n(reference: Optional[str], candidate: Optional[str], n: int = 1) -> Dict[str, float]:
    """Calculate ROUGE-N precision, recall, and F1."""
    ref_tokens = tokenize(reference)
    cand_tokens = tokenize(candidate)

    if not ref_tokens and not cand_tokens:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    if not ref_tokens or not cand_tokens:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    ref_ngrams = _get_ngrams(ref_tokens, n)
    cand_ngrams = _get_ngrams(cand_tokens, n)

    ref_total = sum(ref_ngrams.values())
    cand_total = sum(cand_ngrams.values())

    if ref_total == 0 or cand_total == 0:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    overlap = 0
    for ngram, count in cand_ngrams.items():
        overlap += min(count, ref_ngrams.get(ngram, 0))

    precision = overlap / cand_total
    recall = overlap / ref_total
    f1 = (2.0 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4)
    }


def rouge_l(reference: Optional[str], candidate: Optional[str], beta: float = 1.0) -> Dict[str, float]:
    """
    Calculate ROUGE-L using Longest Common Subsequence (LCS).
    Returns dict with precision, recall, and F1.
    """
    ref_tokens = tokenize(reference)
    cand_tokens = tokenize(candidate)

    if not ref_tokens and not cand_tokens:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    if not ref_tokens or not cand_tokens:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    lcs = _lcs_length(cand_tokens, ref_tokens)
    precision = lcs / len(cand_tokens) if len(cand_tokens) > 0 else 0.0
    recall = lcs / len(ref_tokens) if len(ref_tokens) > 0 else 0.0

    beta_sq = beta * beta
    denom = recall + beta_sq * precision
    f1 = ((1 + beta_sq) * recall * precision) / denom if denom > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4)
    }


# ===========================================================================
# 7. Dynamic Triplet Attribute Set-Matching Evaluation
# ===========================================================================

def evaluate_triplet_attributes(
    expected_triplets: List[Tuple[str, str, str]],
    predicted_triplets: List[Tuple[str, str, str]]
) -> Dict[str, float]:
    """
    Evaluate structured attribute triplets (Label, Value, UOM).
    Computes precision, recall, and F1 based on normalized set matching.
    """
    # Normalize tuples: (norm_label, norm_val, norm_uom)
    exp_set = {
        (normalize_text(l), normalize_text(v), normalize_text(u))
        for l, v, u in expected_triplets
        if l and v
    }
    pred_set = {
        (normalize_text(l), normalize_text(v), normalize_text(u))
        for l, v, u in predicted_triplets
        if l and v
    }

    if not exp_set and not pred_set:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0, "match_count": 0}
    if not exp_set:
        return {"precision": 0.0, "recall": 1.0, "f1": 0.0, "match_count": 0}
    if not pred_set:
        return {"precision": 1.0, "recall": 0.0, "f1": 0.0, "match_count": 0}

    matched = exp_set.intersection(pred_set)
    precision = len(matched) / len(pred_set)
    recall = len(matched) / len(exp_set)
    f1 = (2.0 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "match_count": len(matched),
        "expected_count": len(exp_set),
        "predicted_count": len(pred_set)
    }


# ===========================================================================
# 8. Complete Multi-Metric Suite
# ===========================================================================

def calculate_text_similarity_suite(reference: Optional[str], candidate: Optional[str]) -> Dict[str, float]:
    """Calculate all standard text similarity and NLP quality metrics between reference and candidate."""
    r_l = rouge_l(reference, candidate)
    r_1 = rouge_n(reference, candidate, n=1)
    r_2 = rouge_n(reference, candidate, n=2)

    return {
        "exact_match": exact_match(reference, candidate),
        "normalized_match": normalized_exact_match(reference, candidate),
        "levenshtein_distance": float(levenshtein_distance(reference, candidate)),
        "levenshtein_similarity": round(levenshtein_similarity(reference, candidate), 4),
        "token_jaccard": round(token_jaccard(reference, candidate), 4),
        "token_cosine": round(token_cosine(reference, candidate), 4),
        "bleu_1": round(bleu_1(reference, candidate), 4),
        "bleu_2": round(bleu_2(reference, candidate), 4),
        "bleu_4": round(bleu_4(reference, candidate), 4),
        "rouge_1_f1": r_1["f1"],
        "rouge_2_f1": r_2["f1"],
        "rouge_l_f1": r_l["f1"],
        "rouge_l_precision": r_l["precision"],
        "rouge_l_recall": r_l["recall"]
    }
