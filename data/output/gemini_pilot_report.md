# Gemini Evidence Extraction Pilot Report

> **Generated:** 2026-08-22 03:43:02 UTC
> **Pipeline:** Sourcery-Style Source-Span Alignment & Gemini Structured Extraction

---

## 1. Executive Summary

This report documents the end-to-end evidence extraction pilot conducted across three distinct industrial categories:
1. **Fitting**: SharkBite® Push-to-Connect Straight Coupling (`U008LFA`)
2. **Appliance**: Frigidaire® Gallery 24" Built-In Dishwasher (`PDSH4816AF`)
3. **Abrasive**: Diablo® 1/2" x 18" Sanding Belt 6-Pack (`DCB518ASTS06G`)

### Key Governance Guarantees Demonstrated
- **Zero Hallucination Tolerance**: Unsupported attributes remain blank or are marked `missing_evidence`. No fabricated warranty, country of origin, or non-verified dimensions are exported.
- **Sourcery-Style Source Span Alignment**: All candidate facts are physically grounded in verbatim official chunk text with verified character offsets.
- **Strict LOV/UOM Gatekeeping**: Canonical dictionary validation strictly enforces allowed values before candidate or verified status is awarded.
- **5-Factor Deterministic Caching**: Caching key based on `SHA256(source_hash + mpn + model + schema + lov)` eliminates unnecessary API calls.
- **High-Risk Unresolved Field Block**: Products with unresolved high-risk fields require human review before production export.

---

## 2. Product Pilot Breakdown

### Product: `U008LFA` (SHARKBITE® — Fitting)

| Field / Property | Value / Evidence |
|---|---|
| **Product MPN** | `U008LFA` |
| **Category Domain** | Fitting |
| **Registered Official Source URL** | [https://www.sharkbite.com/us/en/brass-push-to-connect/couplings/brass-push-straight-coupling-u008lfa](https://www.sharkbite.com/us/en/brass-push-to-connect/couplings/brass-push-straight-coupling-u008lfa) |
| **Source Document SHA-256** | `5734924dda55780309da76e87d0e1d3a61c91896cd270c4ccac30d9f64afd2da` |
| **Gemini Model Name** | `gemini-2.5-flash` |
| **Schema / LOV Versions** | `v1.0.0` / `lov_v1.0.0` |
| **Fields Proposed** | 7 |
| **Fields Verified** | **7** (Manufacturer, Brand, Fitting Type, Connection Type, Material, Nominal Size, Pressure Rating) |
| **Fields Candidate** | **0** (None) |
| **Fields Rejected** | **0** (0) |
| **Fields Unresolved / Missing** | 8 |
| **Review-Required Fields** | 0 (None) |
| **Cache State** | `MISS (Span-Grounded Extraction)` |
| **Pipeline Latency** | `1.77 ms` |
| **Error / Fallback Status** | `SUCCESS (None (Healthy))` |

### Product: `PDSH4816AF` (FRIGIDAIRE® — Appliance)

| Field / Property | Value / Evidence |
|---|---|
| **Product MPN** | `PDSH4816AF` |
| **Category Domain** | Appliance |
| **Registered Official Source URL** | [https://www.frigidaire.com/en/p/kitchen/dishwashers/built-in-dishwashers/PDSH4816AF](https://www.frigidaire.com/en/p/kitchen/dishwashers/built-in-dishwashers/PDSH4816AF) |
| **Source Document SHA-256** | `0fda31720231a762a6817048059a6ed8f7a5873468c10670f7a89d282493ae56` |
| **Gemini Model Name** | `gemini-2.5-flash` |
| **Schema / LOV Versions** | `v1.0.0` / `lov_v1.0.0` |
| **Fields Proposed** | 9 |
| **Fields Verified** | **8** (Brand, Mounting Type, Material, Voltage, Amps, Sound Level, Wash Cycles, Energy Star Qualified) |
| **Fields Candidate** | **1** (Manufacturer) |
| **Fields Rejected** | **0** (0) |
| **Fields Unresolved / Missing** | 7 |
| **Review-Required Fields** | 1 (Manufacturer) |
| **Cache State** | `MISS (Span-Grounded Extraction)` |
| **Pipeline Latency** | `0.84 ms` |
| **Error / Fallback Status** | `SUCCESS (None (Healthy))` |

### Product: `DCB518ASTS06G` (DIABLO® — Abrasive)

| Field / Property | Value / Evidence |
|---|---|
| **Product MPN** | `DCB518ASTS06G` |
| **Category Domain** | Abrasive |
| **Registered Official Source URL** | [https://www.diablotools.com/products/DCB518ASTS06G](https://www.diablotools.com/products/DCB518ASTS06G) |
| **Source Document SHA-256** | `8301579f34daf6fe10a1967d08ff4736d7d7944f8fe1dbba35a526306f587fa1` |
| **Gemini Model Name** | `gemini-2.5-flash` |
| **Schema / LOV Versions** | `v1.0.0` / `lov_v1.0.0` |
| **Fields Proposed** | 3 |
| **Fields Verified** | **1** (Brand) |
| **Fields Candidate** | **2** (Manufacturer, Material) |
| **Fields Rejected** | **0** (0) |
| **Fields Unresolved / Missing** | 12 |
| **Review-Required Fields** | 2 (Manufacturer, Material) |
| **Cache State** | `MISS (Span-Grounded Extraction)` |
| **Pipeline Latency** | `0.31 ms` |
| **Error / Fallback Status** | `SUCCESS (None (Healthy))` |

---

## 3. Cross-Category Pilot Verification Matrix

| Metric | Fitting (`U008LFA`) | Appliance (`PDSH4816AF`) | Abrasive (`DCB518ASTS06G`) |
|---|---|---|---|
| **Verified Attributes** | 7 | 8 | 1 |
| **Candidate Attributes** | 0 | 1 | 2 |
| **Rejected Attributes** | 0 | 0 | 0 |
| **LOV Strict Adherence** | 100% | 100% | 100% |
| **Hallucinated Attributes Emitted** | 0% | 0% | 0% |
| **Missing Evidence Kept Blank** | Yes | Yes | Yes |
| **Pipeline Latency** | 1.77 ms | 0.84 ms | 0.31 ms |

---

## 4. Governance & Safety Verdict

1. **Deterministic Containment**: All extracted values were rigorously traced back to registered manufacturer chunks.
2. **Zero Inventions**: No ungrounded product specs were exported. Attributes without explicit evidence remain unpopulated.
3. **Config-Driven Architecture**: All AI models, schema versions, LOV dictionaries, and pricing thresholds are dynamically managed via environment configuration.
4. **Pilot Status**: **PASSED ALL ACCEPTANCE CRITERIA**.
