"""
QA Benchmarking & Ground-Truth Evaluation Endpoints.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends

from ..auth import User, get_current_user
from ..state import catalog_state
from ..schemas import BenchmarkRunRequest

router = APIRouter(prefix="/api/benchmark", tags=["Benchmarking & QA"])


@router.get("/results")
def get_benchmark_results(current_user: User = Depends(get_current_user)):
    """Retrieve ground-truth QA evaluation metrics, hard-gate compliance, and 252-column match rates."""
    rep = catalog_state.get_benchmark_report(force_recompute=False)
    if isinstance(rep, dict):
        res = dict(rep)
        if "hard_rule_gates" in res and "hard_gates" not in res:
            res["hard_gates"] = res["hard_rule_gates"]
        if "overall_scores" in res and "metrics" not in res:
            res["metrics"] = res["overall_scores"]
        return res
    return rep


@router.post("/run")
def trigger_benchmark_run(
    payload: BenchmarkRunRequest = None,
    current_user: User = Depends(get_current_user)
):
    """Recompute full 252-column QA benchmark against ground truth."""
    force = payload.force_recompute if payload else True
    report = catalog_state.get_benchmark_report(force_recompute=force)
    return {
        "status": "success",
        "message": "Benchmark recomputed successfully.",
        "report": report
    }
