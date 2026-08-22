"""
Stage 3: Explainable Taxonomy & UNSPSC Hierarchical Classification Engine.

Implements:
1. Multi-candidate ranking (returns top candidate classpaths with scores).
2. Transparent explainability: matching terms, source evidence, rule confidence vs evidence confidence, and tie-break rationale.
3. Ambiguity & fallback detection with automatic routing to human review.
"""

import json
import os
import re
from typing import Dict, Any, Optional, List, Tuple
from .models import TaxonomyCandidate, TaxonomyExplanation


class TaxonomyClassifier:
    """Classifies sanitized product records into explainable hierarchical Classpaths and UNSPSC codes."""

    def __init__(self, dict_path: Optional[str] = None):
        if not dict_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            dict_path = os.path.join(base_dir, "data", "dictionaries", "taxonomy_classpaths.json")
        
        self.rules = []
        if os.path.exists(dict_path):
            with open(dict_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.rules = data.get("rules", [])

    def classify(
        self,
        sanitized: Dict[str, Any],
        entity: Dict[str, str],
        has_official_evidence: bool = False
    ) -> Dict[str, Any]:
        """
        Determine Department, Class, Fine, Classpath, UNSPSC, Product Name, and attribute template.
        Returns explainable candidate rankings and human review routing decisions.
        """
        raw_desc = sanitized.get("raw_desc", "")
        desc_lower = raw_desc.lower()
        desc_tokens = sanitized.get("desc_tokens", "").lower()
        brand = entity.get("brand_name", "").lower()
        comb = f"{desc_lower} {desc_tokens} {brand}"

        scored_candidates: List[TaxonomyCandidate] = []

        for rule in self.rules:
            score = 0.0
            matched_terms: List[str] = []
            
            for kw in rule.get("keywords", []):
                pattern = r"\b" + re.escape(kw) + r"\b"
                if re.search(pattern, comb, re.I):
                    kw_weight = len(kw) * 1.5
                    score += kw_weight
                    matched_terms.append(kw)
                elif kw in comb:
                    kw_weight = len(kw) * 0.6
                    score += kw_weight
                    matched_terms.append(kw)

            if score > 0 and matched_terms:
                max_term_len = max(len(t) for t in matched_terms)
                rule_conf = min(1.0, 0.70 + (max_term_len / 25.0) * 0.30)
                ev_conf = 0.98 if has_official_evidence else 0.60
                
                cand = TaxonomyCandidate(
                    classpath=rule.get("classpath", ""),
                    unspsc=rule.get("unspsc", ""),
                    dept=rule.get("dept", ""),
                    class_name=rule.get("class_name", ""),
                    fine=rule.get("fine", ""),
                    product_name=rule.get("product_name", ""),
                    matching_terms=matched_terms,
                    score=round(score, 2),
                    source_evidence=f"Matched keywords [{', '.join(matched_terms)}] in input description '{raw_desc}'",
                    rule_confidence=round(rule_conf, 2),
                    evidence_confidence=round(ev_conf, 2)
                )
                scored_candidates.append(cand)

        # Sort candidates by score descending
        scored_candidates.sort(key=lambda c: c.score, reverse=True)

        # Fallback handling if no rule matched
        if not scored_candidates:
            fallback_rule = {
                "dept": "Industrial Supplies",
                "class_name": "General Maintenance & Repair",
                "fine": "General Hardware & Tools",
                "classpath": "Industrial Supplies>Maintenance & Repair>General Hardware",
                "unspsc": "27110000",
                "product_name": "Industrial Component",
                "attribute_template": ["Material", "Finish", "Size", "Additional Information"]
            }
            fallback_cand = TaxonomyCandidate(
                classpath=fallback_rule["classpath"],
                unspsc=fallback_rule["unspsc"],
                dept=fallback_rule["dept"],
                class_name=fallback_rule["class_name"],
                fine=fallback_rule["fine"],
                product_name=fallback_rule["product_name"],
                matching_terms=[],
                score=0.0,
                source_evidence=f"No matching taxonomy keywords found in '{raw_desc}'",
                rule_confidence=0.50,
                evidence_confidence=0.20,
                tie_break_reason="Fallback assigned due to zero matching taxonomy keywords."
            )
            top_candidate = fallback_cand
            top_candidates_list = [fallback_cand]
            is_fallback = True
            is_ambiguous = False
            routing_decision = "ROUTED_TO_HUMAN_REVIEW"
            rationale = "No category rules matched; routed to human review with generic fallback classification."
            rule_template = fallback_rule["attribute_template"]
        else:
            top_candidate = scored_candidates[0]
            top_candidates_list = scored_candidates[:5]
            is_fallback = False
            
            # Check for Ambiguity between Top 2 Candidates
            if len(scored_candidates) >= 2:
                first = scored_candidates[0]
                second = scored_candidates[1]
                score_diff = first.score - second.score
                score_ratio = second.score / max(0.01, first.score)
                
                # Close score margin or ratio indicates ambiguous classification
                if (score_diff <= 2.5 or score_ratio >= 0.85) and first.classpath != second.classpath:
                    is_ambiguous = True
                    routing_decision = "ROUTED_TO_HUMAN_REVIEW"
                    rationale = f"Ambiguous classification between '{first.classpath}' (score {first.score}) and '{second.classpath}' (score {second.score}); routed to human review."
                    top_candidate.tie_break_reason = f"Ranked #1 by slight score margin ({first.score} vs {second.score}), but flagged as ambiguous."
                else:
                    is_ambiguous = False
                    routing_decision = "AUTO_APPROVED"
                    rationale = f"Classified as '{first.classpath}' with high confidence based on matching terms {first.matching_terms}."
                    top_candidate.tie_break_reason = f"Selected unambiguously over rank #2 ('{second.classpath}', score {second.score}) by decisive score gap ({score_diff:.1f})."
            else:
                is_ambiguous = False
                routing_decision = "AUTO_APPROVED"
                rationale = f"Classified unambiguously as '{top_candidate.classpath}' based on matching terms {top_candidate.matching_terms}."
                top_candidate.tie_break_reason = "Unambiguous single category match."

            # Find matching rule for attribute template
            matched_rule = next((r for r in self.rules if r.get("classpath") == top_candidate.classpath), None)
            rule_template = matched_rule.get("attribute_template", []) if matched_rule else ["Material", "Finish", "Size"]

        explanation = TaxonomyExplanation(
            selected_classpath=top_candidate.classpath,
            selected_unspsc=top_candidate.unspsc,
            is_ambiguous=is_ambiguous,
            is_fallback=is_fallback,
            top_candidates=top_candidates_list,
            rationale=rationale,
            routing_decision=routing_decision
        )

        return {
            "dept": top_candidate.dept,
            "class_name": top_candidate.class_name,
            "fine": top_candidate.fine,
            "classpath": top_candidate.classpath,
            "unspsc": top_candidate.unspsc,
            "product_name": top_candidate.product_name,
            "attribute_template": rule_template,
            "taxonomy_candidates": top_candidates_list,
            "taxonomy_explanation": explanation,
            "is_ambiguous": is_ambiguous,
            "is_fallback": is_fallback,
            "rule_confidence": top_candidate.rule_confidence,
            "evidence_confidence": top_candidate.evidence_confidence
        }
