#!/usr/bin/env python3
"""
Standalone CLI Benchmark Runner for Industrial Product Intelligence & PIM Enrichment.
"""

import sys
import os

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.benchmark.cli import run_benchmark_cli


if __name__ == "__main__":
    sys.exit(run_benchmark_cli())
