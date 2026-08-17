# UniHack Industrial Product Intelligence & PIM Enrichment
# Transformation Rules & Pipeline Logic Specification (R1)

**Document ID:** `survey_pipeline_logic.md`  
**Author:** Explorer 2 (Pipeline & Transformation Logic Specialist)  
**Date:** 2026-08-16  
**Status:** Completed Survey & Authoritative Specification  

---

## 1. Executive Summary & Pipeline Architecture

The **UniHack Industrial Product Intelligence & PIM Enrichment Engine** converts unstructured, cryptic, and abbreviated industrial distributor catalog records into standardized, search-ready, and 252-column schema-compliant product data.

### 1.1 Multi-Stage Pipeline Architecture

```
                                  RAW INPUT RECORD
        [Mfg_Part_Num, Part_Desc, E1_Brand, Unilog_Brand, DIB_Brand, Part_Manuf]
                                         │
                                         ▼
   ┌───────────────────────────────────────────────────────────────────────────┐
   │ STAGE 1: INGESTION & PLACEHOLDER SANITIZER                                │
   │ • Strip sentinel placeholders (-- Unbranded --, -- No Unilog Brand --)   │
   │ • Text hygiene: Unicode normalize, collapse whitespace, clean punctuation │
   │ • Isolate MPN and strip redundant leading MPN from description token stream│
   │ • Separate raw vendor name and supplier code (e.g. "Freud Inc (2435)")    │
   └─────────────────────────────────────┬─────────────────────────────────────┘
                                         │
                                         ▼
   ┌───────────────────────────────────────────────────────────────────────────┐
   │ STAGE 2: CANONICAL BRAND & MANUFACTURER ENTITY RESOLUTION                 │
   │ • Multi-tier resolution: Supplier Code -> Part_Desc NLP -> Brand Match    │
   │ • Exact legal casing and corporate suffixes (Inc, LLC, Ltd, Corp)         │
   │ • Trademark symbol assignment (®, ™) according to UniCat master data      │
   │ • Parent Manufacturer vs. Brand line mapping (e.g., Rheem -> FRIGIDAIRE®) │
   └─────────────────────────────────────┬─────────────────────────────────────┘
                                         │
                                         ▼
   ┌───────────────────────────────────────────────────────────────────────────┐
   │ STAGE 3: TAXONOMY & UNSPSC HIERARCHICAL CLASSIFICATION                    │
   │ • Classpath derivation: Dept > Class > Fine                               │
   │ • Commodity-level 8-digit UNSPSC code assignment                          │
   │ • Contextual category dispatch for domain-specific attribute extractors   │
   └─────────────────────────────────────┬─────────────────────────────────────┘
                                         │
                                         ▼
   ┌───────────────────────────────────────────────────────────────────────────┐
   │ STAGE 4: ATTRIBUTE EXTRACTION & CONTROLLED VOCABULARY (LOV) ENGINE        │
   │ • Pattern-based & rule-based technical spec extraction (Mounting, Voltage,│
   │   Amperage, Cycles, Dimensions, Connection Types, Sound Level, Material)  │
   │ • Strict LOV dictionary matching & synonym normalization                  │
   │ • Zero-hallucination policy: unmapped values routed to Additional Info    │
   └─────────────────────────────────────┬─────────────────────────────────────┘
                                         │
                                         ▼
   ┌───────────────────────────────────────────────────────────────────────────┐
   │ STAGE 5: UOM & FRACTION STANDARDIZATION ENGINE                            │
   │ • Exact 64th decimal-to-fraction converter (e.g., 50.25 in -> 50-1/4 in)  │
   │ • Mandatory space rule between number and unit (24 in, 120 V, 15 A, 47 dBA)│
   │ • Unilog Master UOM abbreviation standardization (in, ft, V, A, W, dBA)   │
   └─────────────────────────────────────┬─────────────────────────────────────┘
                                         │
                                         ▼
   ┌───────────────────────────────────────────────────────────────────────────┐
   │ STAGE 6: 5-TIER CONTENT & DESCRIPTION GENERATOR                           │
   │ • Tier 1: INVOICE_DESC (<= 40 chars, 100% ALL CAPS)                       │
   │ • Tier 2: MOBILE_DESC (Strict 60–80 chars range, Title Case)              │
   │ • Tier 3: SHORT_DESC / Product Title ([Brand] [Series] [MPN] [Type] [Specs])│
   │ • Tier 4: LONG_DESC1 (Comprehensive technical spec sentence)              │
   │ • Tier 5: RETAIL_DESC, MARKETING_DESCRIPTION & ITEM_FEATURES_1..N Bullets │
   └─────────────────────────────────────┬─────────────────────────────────────┘
                                         │
                                         ▼
                       ENRICHED 252-COLUMN PRODUCT RECORD
```

---

## 2. Stage 1: Ingestion & Placeholder Sanitizer

### 2.1 Input Data Ingestion Schema
The raw distributor catalog provides six base fields:

| Field Name | Type | Description | Sample Raw Value |
|---|---|---|---|
| `Mfg_Part_Num` | String | Vendor part number or catalog SKU | `DCB518ASTS06G`, `PDSH4816AF`, `49-94-0501` |
| `Part_Desc` | String | Raw abbreviated distributor product description | `PDSH4816AF Dishwasher SS - Display Only` |
| `E1_Brand` | String | Enterprise ERP Brand field (frequently placeholder) | `-- Unbranded --`, `TREX`, `TIMBERTECH` |
| `Unilog_Brand`| String | Unilog Brand field (frequently placeholder) | `-- No Unilog Brand --` |
| `DIB_Brand` | String | Distributor Buying Group Brand field | `-- No DIB Brand --`, `Philips`, `Diablo` |
| `Part_Manuf` | String | Supplier name with vendor ID in parentheses | `Appliance Dealers Cooperative (APPDE)` |

### 2.2 Placeholder Detection & Nullification Rules
All sentinel and placeholder strings must be identified and replaced with empty string `""` / `None` prior to downstream processing.

#### Placeholder Blacklist Table
```python
PLACEHOLDER_SET = {
    "-- unbranded --",
    "-- no unilog brand --",
    "-- no dib brand --",
    "commodity - unbranded",
    "-",
    "none",
    "n/a",
    "na",
    "null",
    "unknown",
    ".",
    "unbranded",
    "no brand"
}
```

### 2.3 Text Hygiene & Sanitization Rules
1. **Unicode Normalization**: Convert Unicode quotation marks, dashes, primes, and spaces:
   - Double quotes: `“`, `”`, `″` $\rightarrow$ `"`
   - Single quotes: `‘`, `’`, `′` $\rightarrow$ `'`
   - Dashes: `–` (en-dash), `—` (em-dash), `−` (minus) $\rightarrow$ `-`
   - Spaces: `\u00a0` (non-breaking space), `\t`, `\r`, `\n` $\rightarrow$ `' '`
2. **Whitespace Collapsing**: Collapse consecutive whitespace characters `\s+` to a single space `' '` and trim leading/trailing whitespace.
3. **Redundant Suffix Removal**: Strip display-only/distributor annotations:
   - `- Display Only` $\rightarrow$ Stripped from core description tokens, flagged as display unit.
   - `(Bare)` / `(Bare Tool)` $\rightarrow$ Extracted as tool configuration attribute `Bare Tool`.
   - `(Linear Foot)` $\rightarrow$ Extracted as selling UOM `LFT`.
4. **Supplier Code Isolation**:
   - Supplier string format: `<Supplier Name> (<Supplier Code>)`
   - Regex: `r'^(?P<name>.*?)(?:\s*\((?P<code>[A-Za-z0-9]+)\))?$'`
   - Examples:
     - `Freud Inc (2435)` $\rightarrow$ `raw_supplier_name = "Freud Inc"`, `supplier_code = "2435"`
     - `Appliance Dealers Cooperative (APPDE)` $\rightarrow$ `raw_supplier_name = "Appliance Dealers Cooperative"`, `supplier_code = "APPDE"`
     - `Black & Decker/dewlt (2585)` $\rightarrow$ `raw_supplier_name = "Black & Decker/dewlt"`, `supplier_code = "2585"`
5. **MPN Isolation from Description**:
   - Over 67.3% of raw descriptions repeat the MPN at index 0 (e.g., `DCB518ASTS06G Diablo 1/2"x18"...`).
   - If `Part_Desc.startswith(Mfg_Part_Num)`, remove `Mfg_Part_Num` from the description token stream to isolate the core descriptive tokens.

---

## 3. Stage 2: Canonical Brand & Manufacturer Entity Resolution

Industrial distributors often list a regional cooperative or master distributor (e.g. `Appliance Dealers Cooperative`, `Boise Cascade`, `Parksite`, `U S Lumber`) as `Part_Manuf`. The true manufacturer and brand must be resolved.

### 3.1 Entity Resolution Priority Hierarchy
1. **Direct Brand Resolution**: If `DIB_Brand` or `E1_Brand` contains a valid, non-placeholder brand name, map to canonical brand.
2. **Description NLP & Token Discovery**: Scan `Part_Desc` for known brand trademarks, trade names, and abbreviations (e.g. `Diablo`, `Frigidaire`, `Whirlpool`, `Milw` $\rightarrow$ `Milwaukee`, `Dewalt` $\rightarrow$ `DEWALT`, `Kichler`, `Philips`, `Satco`, `Southwire`, `Trex`, `TimberTech`, `AZEK`).
3. **Distributor-Cooperative Lookup**: If `Part_Manuf` is a distributor cooperative (e.g. `APPDE`), infer the true manufacturer from the resolved brand (e.g., `FRIGIDAIRE` $\rightarrow$ `Rheem Manufacturing` / `Electrolux`; `Whirlpool` $\rightarrow$ `Whirlpool Corporation`).
4. **Manufacturer Fallback**: If no distinct brand is found, use the sanitized `Part_Manuf` as both manufacturer and brand.

### 3.2 Canonical Manufacturer & Brand Master Mapping Dictionary

| Raw Supplier / Token | Canonical Manufacturer (`MANUFACTURER_NAME`) | Canonical Brand (`BRAND_NAME`) | Trade Name (`TRADE_NAME`) |
|---|---|---|---|
| `Appliance Dealers Cooperative` + `PDSH...` / `Frigidaire` | `Rheem Manufacturing` | `FRIGIDAIRE®` | `Electrolux Home Products` |
| `Appliance Dealers Cooperative` + `WDTS...` / `Whirlpool` | `Whirlpool Corporation` | `Whirlpool®` | `Whirlpool` |
| `Appliance Dealers Cooperative` + `PDT...` / `GE` | `GE Appliances, a Haier company` | `GE®` | `GE Profile™` |
| `Appliance Dealers Cooperative` + `LDPH...` / `LG` | `LG Electronics USA, Inc.` | `LG®` | `LG` |
| `Appliance Dealers Cooperative` + `KDFM...` / `KitchenAid`| `Whirlpool Corporation` | `KitchenAid®` | `KitchenAid` |
| `Freud Inc (2435)` / `Diablo` | `Freud America, Inc.` | `Diablo®` | `Freud` |
| `Milwaukee Accessory (4031)` / `Milw` | `Milwaukee Electric Tool Corp.` | `Milwaukee®` | `Milwaukee` |
| `Black & Decker/dewlt (2585)` / `Dewalt` | `Stanley Black & Decker` | `DEWALT®` | `DEWALT` |
| `Boise Cascade` / `U S Lumber` + `Trex` | `Trex Company, Inc.` | `Trex®` | `Trex` |
| `Parksite` / `U S Lumber` + `TimberTech` / `AZEK` | `The AZEK Company` | `TimberTech®` | `AZEK®` |
| `Phillips Lighting (5831)` / `Philips` | `Signify North America Corporation` | `Philips®` | `Philips Lighting` |
| `Satco Prod Inc (5573)` / `Satco` | `Satco Products, Inc.` | `SATCO®` | `Nuvo®` |
| `Kichler Lighting (KICLI)` / `Kichler` | `Kichler Lighting LLC` | `Kichler®` | `Kichler` |
| `Leviton Mfg Co (4927)` / `Leviton` | `Leviton Manufacturing Co., Inc.` | `Leviton®` | `Leviton` |
| `Southwire/g Turner (6603)` / `Southwire` | `Southwire Company, LLC` | `Southwire®` | `Southwire` |
| `Festool USA (FESTO)` / `Festool` | `Festool USA` | `Festool®` | `Festool` |
| `Makita Usa Inc (5142)` / `Makita` | `Makita U.S.A., Inc.` | `Makita®` | `Makita` |
| `Kreg Tool Company (KRETO)` / `Kreg` | `Kreg Tool Company` | `Kreg®` | `Kreg` |
| `3 M Co (5293)` / `Jam Industrial` + `3M` | `3M Company` | `3M™` | `Cubitron™ II` |
| `Mirka Abrasives Inc (MIRUS)` / `Mirka` | `Mirka USA Inc.` | `Mirka®` | `Abranet®` / `HIOLIT®` |
| `Square D Con Prod Dv (6825)` | `Schneider Electric USA, Inc.` | `Square D™` | `Square D` |
| `Robt Bosch Tool Corp (6564)` / `Bosch` | `Robert Bosch Tool Corporation` | `Bosch®` | `Bosch` |
| `United Window & Door Manufacturing` | `United Window & Door Manufacturing`| `United Window & Door` | `4500 Series` |
| `ProVia (PRODO)` | `ProVia LLC` | `ProVia®` | `ProVia` |
| `Certainteed Gypsum (2765)` | `CertainTeed Corporation` | `CertainTeed®` | `CertainTeed` |

---

## 4. Stage 3: Taxonomy & UNSPSC Classification

The delivery format mandates both a 3-tier hierarchical category breakdown (`Dept`, `Class`, `Fine`) and a full delimited string (`Classpath`), plus an 8-digit UNSPSC code.

### 4.1 Taxonomy Hierarchy Format
- `Dept`: Department level (e.g. `Appliances`, `Building Materials`, `Lighting & Electrical`, `Tools & Hardware`)
- `Class`: Major category class (e.g. `Large Appliances`, `Decking & Railing`, `Lamps & Bulbs`, `Abrasives`)
- `Fine`: Leaf product node (e.g. `Dishwashers`, `Composite Decking`, `LED Bulbs`, `Sanding Belts & Discs`)
- `Classpath`: Concat format `Dept > Class > Fine` (in ground truth: `Appliances & Consumer Electronics>Kitchen Appliances>Built-In Dishwashers`)

### 4.2 Primary Taxonomy & UNSPSC Catalog Rules

| Fine Product Type | Department (`Dept`) | Class (`Class`) | Full Classpath (`Classpath`) | UNSPSC Code |
|---|---|---|---|---|
| **Built-In Dishwashers** | `Appliances` | `Large Appliances` | `Appliances & Consumer Electronics>Kitchen Appliances>Built-In Dishwashers` | `52141505` |
| **Refrigerators** | `Appliances` | `Large Appliances` | `Appliances & Consumer Electronics>Kitchen Appliances>Refrigerators` | `52141501` |
| **Ranges & Cooktops** | `Appliances` | `Large Appliances` | `Appliances & Consumer Electronics>Kitchen Appliances>Ranges` | `52141515` |
| **Composite Decking** | `Building Materials` | `Decking & Railing` | `Building Materials>Decking & Railing>Composite Decking` | `30103603` |
| **Railing Kits & Balusters**| `Building Materials`| `Decking & Railing` | `Building Materials>Decking & Railing>Railing Systems` | `30103604` |
| **Post Sleeves & Trim** | `Building Materials` | `Decking & Railing` | `Building Materials>Decking & Railing>Post Sleeves & Caps` | `30103605` |
| **LED Bulbs** | `Lighting & Electrical`| `Lamps & Bulbs` | `Lighting & Electrical>Lamps & Bulbs>LED Bulbs` | `39101628` |
| **Chandeliers & Pendants** | `Lighting & Electrical`| `Fixtures` | `Lighting & Electrical>Fixtures>Chandeliers & Pendants` | `39111500` |
| **Cord Grips & Connectors**| `Lighting & Electrical`| `Fittings & Conduit`| `Lighting & Electrical>Fittings & Conduit>Cord Grips` | `39121400` |
| **Sanding Belts & Discs** | `Tools & Hardware` | `Abrasives` | `Tools & Hardware>Abrasives>Sanding Belts & Discs` | `31191500` |
| **Grinding Wheels** | `Tools & Hardware` | `Abrasives` | `Tools & Hardware>Abrasives>Grinding Wheels` | `31191600` |
| **Power Tools** | `Tools & Hardware` | `Power Tools` | `Tools & Hardware>Power Tools>Cordless Power Tools` | `27112700` |
| **Saw Blades & Bits** | `Tools & Hardware` | `Accessories` | `Tools & Hardware>Power Tool Accessories>Blades & Bits` | `27112800` |
| **Patio Doors & Windows** | `Building Materials` | `Doors & Windows` | `Building Materials>Doors & Windows>Patio Doors` | `30171505` |

---

## 5. Stage 4: Attribute Extraction & Controlled Vocabulary (LOV) Engine

### 5.1 252-Column Attribute Slot Model
The delivery schema allocates 50 slot triples:
- `ATTRIBUTE_LABEL n`: Exact canonical label of attribute $n$ (e.g. `Series`, `Voltage Rating`, `Mounting Type`, `Sound Level`, `Material`).
- `ATTRIBUTE_VALUE n`: Normalized attribute value strictly compliant with LOV (e.g. `Professional Series`, `120`, `Built-in`, `47`, `Stainless Steel`).
- `ATTRIBUTE_UOM n`: Unit of measure if quantitative (e.g. `V`, `A`, `in`, `dBA`, `W`).

### 5.2 Key Technical Attribute Extraction & LOV Rules

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               TECHNICAL ATTRIBUTE EXTRACTORS                           │
├─────────────────────┬─────────────────────────────────────┬────────────────────────────┤
│ Attribute           │ Regex / Extraction Pattern          │ Canonical LOV / Normalizer │
├─────────────────────┼─────────────────────────────────────┼────────────────────────────┤
│ Voltage Rating      │ r'(?i)(\d+(?:\.\d+)?)\s*(?:V|VAC|...│ Value: "120", UOM: "V"     │
│ Amperage Rating     │ r'(?i)(\d+(?:\.\d+)?)\s*(?:A|Amp|...│ Value: "15", UOM: "A"      │
│ Sound Level         │ r'(?i)(\d+(?:\.\d+)?)\s*(?:dBA|dB) '│ Value: "47", UOM: "dBA"    │
│ Number of Cycles    │ r'(?i)(\d+)\s*(?:-| )?Wash Cycles? '│ Value: "5" (Integer string)│
│ Mounting Type       │ r'(?i)\b(Built-in|Leg|Undermount... │ LOV: Built-in, Leg, ...    │
│ Material            │ r'(?i)\b(SS|SST|Stainless Steel...  │ LOV: Stainless Steel, ...  │
│ Color / Finish      │ r'(?i)\b(SS|SST|Black|White|Clay) ' │ LOV: Stainless Steel, ...  │
│ Series              │ r'(?i)(Professional|Eco|Transcend) '│ Canonical Series Name      │
│ Size / Dimensions   │ r'(?i)(\d+(?:-\d+/\d+|\.\d+)?\s*... │ Unilog Fraction String     │
│ Depth With Door Open│ r'(?i)(\d+(?:-\d+/\d+|\.\d+)?)\s*...│ Value: "50-1/4", UOM: "in" │
└─────────────────────┴─────────────────────────────────────┴────────────────────────────┘
```

#### Detailed LOV Dictionaries & Synonym Tables

1. **Mounting Type LOV**:
   - Permitted values: `Built-in`, `Leg`, `Undermount`, `Drop-in`, `Surface`, `Flush`, `Wall`, `Ceiling`, `Post`, `Freestanding`, `Deck`.
   - Synonym mapping: `BLTLN` $\rightarrow$ `Built-in`, `SURF` $\rightarrow$ `Surface`, `UNDR` $\rightarrow$ `Undermount`.

2. **Material Construction LOV**:
   - Permitted values: `Stainless Steel`, `Aluminum`, `PVC`, `Composite`, `Brass`, `Cast Iron`, `Vinyl`, `Steel`, `Polycarbonate`, `Wood`, `Gypsum`.
   - Synonym mapping: `SS`, `SST` $\rightarrow$ `Stainless Steel`; `Alum`, `Alm` $\rightarrow$ `Aluminum`; `Brs` $\rightarrow$ `Brass`; `Comp` $\rightarrow$ `Composite`.

3. **Color LOV**:
   - Permitted values: `Stainless Steel`, `Black Stainless Steel`, `White`, `Black`, `Clay`, `Bronze`, `Brushed Nickel`, `Chrome`, `Tide Pool`, `Spiced Rum`, `Island Mist`, `Havana Gold`, `Gravel Path`.
   - Synonym mapping: `Wh`, `WH` $\rightarrow$ `White`; `Blk`, `BLK`, `Bk` $\rightarrow$ `Black`; `BSS` $\rightarrow$ `Black Stainless Steel`.

4. **Series LOV**:
   - Appliances: `Professional Series`, `Eco Series`, `Gallery Series`, `Custom Series`, `Studio Series`.
   - Decking & Railing: `Enhance Basics`, `Enhance Naturals`, `Transcend`, `Select`, `Reserve`, `Finyline`, `Heritage`, `Elite`.
   - Power Tools & Abrasives: `M12`, `M18`, `20V MAX XR`, `Cubitron II`, `Stikit`, `HIOLIT`, `Abranet`.

5. **With Clause / Features**:
   - Format: `With [Key Differentiating Feature]`
   - Examples: `With CleanBoost™`, `With Washing 3rd Rack, Water Repellent Silverware Basket`, `With Sq Composite Balusters`, `With LED Display`.

6. **Standards & Approvals**:
   - Delimited with pipe `|`: `ASSE 1006|CEE Tier 2 Qualified|cUL Listed|ENERGY STAR Certified|NSF Certified|UL Listed`.

---

## 6. Stage 5: UOM & Fraction Standardization Engine

Trade buyers search in fractions; engineering specs are often published in decimals. Unilog enforces strict house formatting rules.

### 6.1 Exact 64th Fraction Conversion Matrix
Any decimal inch measurement must be converted to the nearest exact standard fraction (up to 1/64 increments).

```
   0.015625 = 1/64        0.265625 = 17/64       0.515625 = 33/64       0.765625 = 49/64
   0.031250 = 1/32        0.281250 = 9/32        0.531250 = 17/32       0.781250 = 25/32
   0.046875 = 3/64        0.296875 = 19/64       0.546875 = 35/64       0.796875 = 51/64
   0.062500 = 1/16        0.312500 = 5/16        0.562500 = 9/16        0.812500 = 13/16
   0.078125 = 5/64        0.328125 = 21/64       0.578125 = 37/64       0.828125 = 53/64
   0.093750 = 3/32        0.343750 = 11/32       0.593750 = 19/32       0.843750 = 27/32
   0.109375 = 7/64        0.359375 = 23/64       0.609375 = 39/64       0.859375 = 55/64
   0.125000 = 1/8         0.375000 = 3/8         0.625000 = 5/8         0.875000 = 7/8
   0.140625 = 9/64        0.390625 = 25/64       0.640625 = 41/64       0.890625 = 57/64
   0.156250 = 5/32        0.406250 = 13/32       0.656250 = 21/32       0.906250 = 29/32
   0.171875 = 11/64       0.421875 = 27/64       0.671875 = 43/64       0.921875 = 59/64
   0.187500 = 3/16        0.437500 = 7/16        0.687500 = 11/16       0.937500 = 15/16
   0.203125 = 13/64       0.453125 = 29/64       0.703125 = 45/64       0.953125 = 61/64
   0.218750 = 7/32        0.468750 = 15/32       0.718750 = 23/32       0.968750 = 31/32
   0.234375 = 15/64       0.484375 = 31/64       0.734375 = 47/64       0.984375 = 63/64
   0.250000 = 1/4         0.500000 = 1/2         0.750000 = 3/4
```

### 6.2 Formatting Syntax Rules
1. **Mixed Fraction Hyphenation**:
   - `Whole-Numerator/Denominator` (e.g. `50-1/4`, `33-7/16`, `23-7/8`, `22-5/8`, `50-3/16`).
   - Pure fractions less than 1 do not have a hyphen: `1/2`, `3/8`, `1/4`, `5/8`, `3/16`.
   - Whole numbers have no fraction: `24`, `16`, `6`.
2. **Mandatory Space Rule**:
   - A single space is mandatory between the numerical value and the unit abbreviation:
     - Correct: `24 in`, `120 V`, `15 A`, `47 dBA`, `65 W`, `16 ft`, `50-1/4 in`
     - Forbidden: `24in`, `120V`, `15A`, `47dBA`, `24"`, `16'`
3. **Compound Dimension Syntax**:
   - Multiple dimensions are joined with ` x `:
     - Size: `33-7/16 in H x 23-7/8 in W x 22-5/8 in D`
     - Abrasive Disc/Wheel: `4 in Dia x 1/4 in THK x 5/8 in Arbor`
     - Decking Board: `1 in THK x 6 in W x 16 ft L`

### 6.3 Approved Unit Abbreviations Table

| Measurement Type | Canonical Abbreviation | Prohibited Variants | Example |
|---|---|---|---|
| **Length / Width / Height** | `in` | `inch`, `inches`, `"`, `IN.` | `24 in`, `50-1/4 in` |
| **Linear Length (Feet)** | `ft` | `foot`, `feet`, `'`, `FT.` | `16 ft`, `6 ft` |
| **Voltage** | `V` | `v`, `volt`, `volts`, `VAC`, `VDC` | `120 V`, `20 V` |
| **Current / Amperage** | `A` | `a`, `amp`, `amps`, `Amp`, `Amps` | `15 A`, `10 A` |
| **Power / Wattage** | `W` | `w`, `watt`, `watts`, `Watt` | `65 W`, `1500 W` |
| **Acoustic Noise Level** | `dBA` | `db`, `dba`, `dB`, `DBA`, `decibels` | `47 dBA`, `41 dBA` |
| **Energy Consumption** | `kW-hr` | `kWh`, `kw-hr`, `kwh`, `KW-HR` | `240 kW-hr` |
| **Weight** | `lb` | `lbs`, `LBS`, `pound`, `pounds` | `45 lb` |
| **Flow Rate** | `gpm` | `GPM`, `gal/min` | `1.5 gpm` |
| **Time Duration** | `hr` | `hrs`, `hour`, `hours`, `HR` | `1 to 12 hr` |

---

## 7. Stage 6: 5-Tier Content & Description Generator

The core output requirement is generating five synchronized tiers of product descriptions, each satisfying strict length, casing, and information density constraints.

### 7.1 Tier 1: `INVOICE_DESC` (Point of Sale / ERP / Billing)
- **Constraint**: **Length $\le$ 40 characters**, **100% ALL CAPS**.
- **Role**: Printed on trade customer till receipts, packing slips, and ERP line items.
- **Formula**:
  $$\text{INVOICE\_DESC} = \text{[ITEM TYPE]} + \text{ [MOUNT/STYLE]} + \text{ [SPEC]} + \text{ [MAT/COLOR]} + \text{ [VOLT]} + \text{ [AMP]} + \text{ [DIM/NOISE]}$$
- **Standard Abbreviations**:
  - `DISHWASHER` $\rightarrow$ `DISHWASHER` / `DISHWASH`
  - `Built-in` $\rightarrow$ `BLTLN`
  - `Leg Mounting` $\rightarrow$ `LEG`
  - `Stainless Steel` $\rightarrow$ `SST`
  - `Aluminum` $\rightarrow$ `ALUM`
  - `Composite` $\rightarrow$ `COMP`
  - Units in Invoice: `120V`, `15A`, `50-1/4IN`, `41DBA` (condensed without spaces to conserve character budget).
- **Worked Ground-Truth Examples**:
  1. `DISHWASHER LEG 5 SST 120V 15A 50-1/4IN` (38 characters $\le 40$)
  2. `DISHWASHER BLTLN SST SST 120V 10A 41DBA` (39 characters $\le 40$)
- **Guaranteed Truncation Algorithm**:
  If generated candidate length $> 40$, sequentially apply abbreviations and drop lowest-priority modifier tokens until length $\le 40$.

---

### 7.2 Tier 2: `MOBILE_DESC` (Mobile eCommerce / App Summary)
- **Constraint**: **Length strictly within 60 to 80 characters**. Title / Standard Case.
- **Role**: Compact mobile search result listings and quick-order pads.
- **Formula**:
  $$\text{MOBILE\_DESC} = \text{[MFR / Brand]}, \text{ [Product Type]}, \text{ [Series]}, \text{ [MPN]}[, \text{Key Spec / Mounting}]$$
- **Worked Ground-Truth Examples**:
  1. `Rheem Manufacturing FRIGIDAIRE, Dishwasher, Professional Series, PDSH4816AF` (75 characters, in range 60–80)
  2. `Whirlpool, Dishwasher, Eco Series, WDTS7024RZ, Built-in Mounting` (64 characters, in range 60–80)
- **Length Calibration Algorithm**:
  - If length $< 60$: Append key attribute modifier (e.g. `, Built-in Mounting`, `, Stainless Steel`, `, 120 V`).
  - If length $> 80$: Drop secondary spec token or trim manufacturer prefix to Brand name.

---

### 7.3 Tier 3: `SHORT_DESC` / Product Title (eCommerce Desktop Title)
- **Constraint**: Clear, high-SEO title containing all primary search facets.
- **Formula**:
  $$\text{SHORT\_DESC} = \text{[BRAND®]} \text{ [Series]} \text{ [MPN]} \text{ [Product Type]} \text{ [With Clause]}, \text{ [Mounting]}, \text{ [Key Specs]}, \text{ [Material/Color]}$$
- **Worked Ground-Truth Examples**:
  1. `FRIGIDAIRE® Professional Series PDSH4816AF Dishwasher With CleanBoost™, Leg Mounting, 5-Wash Cycle, Stainless Steel`
  2. `Whirlpool® Eco Series WDTS7024RZ Dishwasher, Built-in Mounting, Stainless Steel, Stainless Steel`

---

### 7.4 Tier 4: `LONG_DESC1` (Comprehensive Technical Specification Sentence)
- **Constraint**: Complete, grammatically structured technical specification sentence with fully normalized UOMs and formatted fractions.
- **Formula**:
  $$\text{LONG\_DESC1} = \text{[BRAND®]} \text{ [Product Name]} \text{ [With Clause]}, \text{ [Series]}, \text{ [Cycles/Capacity]}, \text{ [Voltage Rating]} \text{ V}, \text{ [Amperage Rating]} \text{ A}, \text{ [Mounting]} \text{ Mounting}, \text{ [Dimensions]}, \text{ [Door/Rack Heights]}, \text{ [Sound Level]} \text{ Sound Level}, \text{ [Material]}, \text{ [Color]}, \text{Additional Information: } \text{[Details]}$$
- **Worked Ground-Truth Examples**:
  1. `FRIGIDAIRE® Dishwasher With CleanBoost™, Professional Series, 5 Wash Cycles, 120 V, 15 A, Leg Mounting, 24 in W x 24-1/4 in D, 50-1/4 in Depth With Door Open, 8-1/2 in Upper Rack, 11-1/4 in Lower Rack Minimum Height, 10-3/8 in Upper Rack, 13-1/4 in Lower Rack Maximum Height, 47 dBA Sound Level, Stainless Steel, Additional Information: 240 kW-hr Annual Energy, 1 to 12 hr Delay Start Hours`
  2. `Whirlpool® Dishwasher, Eco Series, 120 V, 10 A, Built-in Mounting, 33-7/16 in H x 23-7/8 in W x 22-5/8 in D, 50-3/16 in Depth With Door Open, 33-7/16 in Minimum Height, 41 dBA Sound Level, Stainless Steel, Stainless Steel, Additional Information: Folding Tines, Leak Detection System, Moisture Repellent Silverware Basket, Normal Cycle, Quick Wash Cycle, Sani Rinse Option, Sensor Cycle, Triple Wash Spray`

---

### 7.5 Tier 5: `RETAIL_DESC`, `MARKETING_DESCRIPTION` & Feature Bullets
1. **`RETAIL_DESC`**:
   - Formula: `[Series] [Product Name], [Mounting Type] Mounting, [Key Specs], [Material]`
   - Example 1: `Professional Series Dishwasher, Leg Mounting, 5-Wash Cycle, Stainless Steel`
   - Example 2: `Eco Series Dishwasher, Built-in Mounting, Stainless Steel, Stainless Steel`
2. **`MARKETING_DESCRIPTION`**:
   - Consumer and trade sales narrative highlighting user benefits and core engineering value.
   - Example: `Load more and run less with our quietest and largest capacity dishwasher. A 3rd Rack provides dedicated space for mugs and bowls, while an adjustable 2nd Rack helps fit all the dishes and pans your family piles up.`
3. **`ITEM_FEATURES_1` through `ITEM_FEATURES_N`**:
   - Structured array of discrete feature statements:
     - `ITEM_FEATURES_1`: `3rd rack with extra wash action`
     - `ITEM_FEATURES_2`: `Adjustable 2nd Rack`
     - `ITEM_FEATURES_3`: `41 dBA`
     - `ITEM_FEATURES_4`: `Moisture Repellent Silverware Basket`
     - `ITEM_FEATURES_5`: `Sensor cycle`
     - `ITEM_FEATURES_6`: `Sani Rinse Option`
     - `ITEM_FEATURES_7`: `Leak Detection System`
     - `ITEM_FEATURES_8`: `Folding Tines`

---

## 8. End-to-End Verification Traces

### 8.1 Trace 1: Frigidaire Dishwasher (Ground Truth Match)
- **Input**:
  - `Mfg_Part_Num`: `PDSH4816AF`
  - `Part_Desc`: `PDSH4816AF Dishwasher SS - Display Only`
  - `E1_Brand`: `-- Unbranded --`
  - `Unilog_Brand`: `-- No Unilog Brand --`
  - `DIB_Brand`: `-- No DIB Brand --`
  - `Part_Manuf`: `Appliance Dealers Cooperative (APPDE)`
- **Pipeline Execution**:
  1. *Sanitization*: Strip placeholders $\rightarrow$ brands `None`; clean `Part_Desc` $\rightarrow$ remove `PDSH4816AF` and `- Display Only` $\rightarrow$ tokens `Dishwasher SS`; supplier code `APPDE`.
  2. *Entity Resolution*: MPN `PDSH4816AF` resolves to Brand `FRIGIDAIRE®` and Manufacturer `Rheem Manufacturing`.
  3. *Classification*: Classpath `Appliances & Consumer Electronics>Kitchen Appliances>Built-In Dishwashers`, UNSPSC `52141505`.
  4. *Attribute Extraction*:
     - Series: `Professional Series`
     - Wash Cycles: `5`
     - Voltage: `120 V`
     - Amperage: `15 A`
     - Mounting: `Leg`
     - Size: `24 in W x 24-1/4 in D`
     - Depth With Door Open: `50-1/4 in`
     - Sound Level: `47 dBA`
     - Material: `Stainless Steel`
  5. *UOM Formatting*: `50.25` $\rightarrow$ `50-1/4 in`, `24.25` $\rightarrow$ `24-1/4 in`.
  6. *Description Generation*:
     - `INVOICE_DESC`: `DISHWASHER LEG 5 SST 120V 15A 50-1/4IN` (38 chars $\le 40$)
     - `MOBILE_DESC`: `Rheem Manufacturing FRIGIDAIRE, Dishwasher, Professional Series, PDSH4816AF` (75 chars $\in [60, 80]$)
     - `SHORT_DESC`: `FRIGIDAIRE® Professional Series PDSH4816AF Dishwasher With CleanBoost™, Leg Mounting, 5-Wash Cycle, Stainless Steel`

---

### 8.2 Trace 2: Diablo Sanding Belt
- **Input**:
  - `Mfg_Part_Num`: `DCB518ASTS06G`
  - `Part_Desc`: `DCB518ASTS06G Diablo 1/2"x18" - Sanding Belt 6pc`
  - `Part_Manuf`: `Freud Inc (2435)`
- **Pipeline Execution**:
  1. *Sanitization*: Strip leading MPN; clean tokens `Diablo 1/2"x18" - Sanding Belt 6pc`.
  2. *Entity Resolution*: Brand `Diablo®`, Manufacturer `Freud America, Inc.`, Parent `Robert Bosch Tool Corporation`.
  3. *Classification*: Classpath `Tools & Hardware>Abrasives>Sanding Belts & Discs`, UNSPSC `31191500`.
  4. *Attribute Extraction*:
     - Belt Width: `1/2 in`
     - Belt Length: `18 in`
     - Product Type: `Sanding Belt`
     - Pack Count: `6` (Selling UOM: `PK`, Selling Qty: `6`)
  5. *UOM Formatting*: `1/2"` $\rightarrow$ `1/2 in`, `18"` $\rightarrow$ `18 in`.
  6. *Description Generation*:
     - `INVOICE_DESC`: `SANDING BELT 1/2X18IN 6PK` (24 chars $\le 40$)
     - `MOBILE_DESC`: `Freud Diablo, Sanding Belt, 1/2 in W x 18 in L, DCB518ASTS06G, 6-Pack` (68 chars $\in [60, 80]$)
     - `SHORT_DESC`: `Diablo® DCB518ASTS06G Sanding Belt, 1/2 in W x 18 in L, 6-Pack`
     - `LONG_DESC1`: `Diablo® Sanding Belt, 1/2 in W x 18 in L, Pack of 6, Designed for Detail Belt Sanders`

---

### 8.3 Trace 3: Trex Composite Decking Board
- **Input**:
  - `Mfg_Part_Num`: `1513724`
  - `Part_Desc`: `1nx6-16' Tide Pool Sq Edge - Trex Enhance Basics Decking`
  - `Part_Manuf`: `Boise Cascade Building Materials (BOICA)`
- **Pipeline Execution**:
  1. *Sanitization*: Clean tokens `1 in x 6 in x 16 ft Tide Pool Square Edge Trex Enhance Basics Decking`.
  2. *Entity Resolution*: Brand `Trex®`, Manufacturer `Trex Company, Inc.`.
  3. *Classification*: Classpath `Building Materials>Decking & Railing>Composite Decking`, UNSPSC `30103603`.
  4. *Attribute Extraction*:
     - Series: `Enhance Basics`
     - Edge Profile: `Square Edge`
     - Color: `Tide Pool`
     - Thickness: `1 in`
     - Width: `6 in`
     - Length: `16 ft`
     - Material: `Composite`
  5. *UOM Formatting*: `1 in THK x 6 in W x 16 ft L`.
  6. *Description Generation*:
     - `INVOICE_DESC`: `DECK BOARD TREX ENH SQ 1X6 16FT TIDEPOOL` (39 chars $\le 40$)
     - `MOBILE_DESC`: `Trex Company, Decking Board, Enhance Basics, 1513724, Tide Pool` (63 chars $\in [60, 80]$)
     - `SHORT_DESC`: `Trex® Enhance Basics 1513724 Composite Decking Board, Square Edge, 1 in THK x 6 in W x 16 ft L, Tide Pool`
     - `LONG_DESC1`: `Trex® Composite Decking Board, Enhance Basics Series, Square Edge Profile, 1 in THK x 6 in W x 16 ft L, Tide Pool Color, High-Performance Composite Material`

---

## 9. Modular Code Blueprint for Implementation

The enrichment pipeline will be structured in modular Python packages under `src/pipeline/`:

```
src/
├── pipeline/
│   ├── __init__.py
│   ├── ingestion.py           # Ingestion, placeholder stripping, text hygiene
│   ├── entity_resolver.py     # Canonical Brand & Manufacturer resolution
│   ├── taxonomy.py            # Hierarchical Classpath & UNSPSC classification
│   ├── attribute_extractor.py # Regex/NLP spec extraction & LOV validation
│   ├── uom_formatter.py       # 64th decimal-to-fraction & unit standardization
│   ├── description_gen.py     # 5-tier description building algorithms
│   ├── schema_mapper.py       # 252-column schema assembler
│   └── enrichment_engine.py   # Master pipeline orchestrator
├── data/
│   ├── manufacturers.json     # 27,000+ approved manufacturers & brands
│   ├── taxonomy_unscpsc.json  # Classpath and UNSPSC lookup dictionaries
│   ├── lov_dictionaries.json  # Controlled vocabulary LOV tables
│   └── fraction_table.json    # 63 standard 64th decimal-fraction pairs
└── benchmark/
    └── evaluate.py            # R2 Ground-truth benchmarking & QA suite
```

---

## 10. Summary & Sign-off

This specification establishes deterministic, zero-hallucination, and strictly verified transformation rules for all six processing stages of the **UniHack Catalog Enrichment Engine**. Downstream implementers can translate these algorithmic rules and lookup dictionaries directly into high-performance Python modules.
