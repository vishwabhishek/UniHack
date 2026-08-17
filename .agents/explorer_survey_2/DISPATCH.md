## 2026-08-16T11:23:10Z
You are Explorer 2 (Pipeline & Transformation Logic Specialist) for the UniHack Industrial Product Intelligence & PIM Enrichment project.
Your working directory is /home/abhishek-vishwakarma/Documents/Hackathons/Unilog/.agents/explorer_survey_2.
Create your working directory if needed.

Read /home/abhishek-vishwakarma/Documents/Hackathons/Unilog/ORIGINAL_REQUEST.md.

Investigate the transformation rules and pipeline requirements for R1:
1. Ingestion & Sanitizer:
   - Rules for stripping dummy placeholders, trimming, whitespace normalization, cleaning product numbers.
2. Canonical Brand & Manufacturer Entity Resolution:
   - Mapping rules for raw supplier strings to canonical manufacturer names & brands (legal casing, suffixes Inc/LLC/Ltd, symbols ®, ™).
3. Taxonomy & UNSPSC Classification:
   - Hierarchical Classpath logic (Dept > Class > Fine) and UNSPSC code mapping.
4. Attribute Extraction & Controlled Vocabulary (LOV):
   - Extraction regex/NLP/rule patterns for key technical specifications (Mounting, Voltage, Amperage, Wash Cycles, Dimensions, Connection Types, Sound Level, Material Construction).
   - Strict LOV dictionary matching and handling of unknown values.
5. UOM & Fraction Standardization:
   - Conversion of decimal inches to fraction format (e.g. 50.25 in -> 50-1/4 in), mandatory space between number and unit (24 in, 120 V, 15 A, 47 dBA), standard unit abbreviations.
6. 5-Tier Content & Description Generator:
   - INVOICE_DESC (<= 40 chars, ALL CAPS).
   - MOBILE_DESC (60-80 chars).
   - SHORT_DESC / Title ([Brand] + [Series] + [MPN] + [Item Type] + [Key Specs]).
   - LONG_DESC1 (Full technical spec sentence with normalized units).
   - MARKETING_DESCRIPTION / Feature bullets.

Write a comprehensive, detailed report to /home/abhishek-vishwakarma/Documents/Hackathons/Unilog/.agents/explorer_survey_2/survey_pipeline_logic.md.
Also write your handoff.md in your working directory.
When finished, send a message back to parent (ccd71a4e-664b-41b5-b4c0-b843693a438e) with a concise summary and the file path.
