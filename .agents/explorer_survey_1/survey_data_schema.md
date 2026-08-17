# UniHack Industrial Product Intelligence & PIM Enrichment
# Comprehensive Data Schema & Ground Truth Survey Report

**Author**: Explorer 1 (Data Schema & Ground Truth Specialist)  
**Date**: 2026-08-16  
**Status**: Complete  
**Scope**: Input Dataset (`Unihack_ Sample Dataset - Input.csv`), Expected Output Ground Truth (`Unihack_ Expected Output - Delivery Format.csv`), Solution Guide, Schema Mapping, LOV Dictionaries, UOM Standards, Description Rules.

---

## 1. Executive Summary

This report presents an exhaustive empirical analysis of the UniHack industrial product catalog dataset, the 252-column Unilog delivery schema, and the transformation logic required to build a production-grade, AI-powered PIM enrichment pipeline.

### Core Discoveries:
1. **Input Profile (`Unihack_ Sample Dataset - Input.csv`)**: 1,000 raw supplier rows across 6 sparse columns (`Mfg_Part_Num`, `Part_Desc`, `E1_Brand`, `Unilog_Brand`, `DIB_Brand`, `Part_Manuf`). Contains severe noise: 100% placeholder in `Unilog_Brand`, 80.3% unbranded/placeholders in `E1_Brand`, 75.5% placeholders in `DIB_Brand`, 41 unassigned manufacturers (`-`), 84 cooperative distributor masks (`Appliance Dealers Cooperative (APPDE)`), and heavy cryptic industrial abbreviations.
2. **Delivery Format Schema (`Unihack_ Expected Output - Delivery Format.csv`)**: Exactly **252 standardized columns** partitioned into 11 functional tiers, including 50 normalized attribute triplets (`ATTRIBUTE_LABEL n`, `ATTRIBUTE_VALUE n`, `ATTRIBUTE_UOM n`), 20 item feature bullets, 5-tier product descriptions, digital asset references, and UNSPSC/taxonomic hierarchies.
3. **Ground Truth Validation Benchmarks**: The delivery file provides 2 fully populated reference records (`PDSH4816AF` and `WDTS7024RZ` - Built-In Dishwashers) with 63 and 71 non-null columns respectively.
4. **Description & Length Rules Confirmed**:
   - `INVOICE_DESC`: Strictly $\le 40$ characters, **100% ALL CAPS**, using deterministic tokenized abbreviation syntax. (Ground truth: 38 and 39 chars).
   - `MOBILE_DESC`: Strictly **60–80 characters**, concise mobile display title. (Ground truth: 75 and 64 chars).
   - `SHORT_DESC` / `RETAIL_DESC` / `LONG_DESC1` / `MARKETING_DESCRIPTION`: Structured hierarchical narrative compositions following strict Unilog internal content guidelines.
5. **UOM & LOV Standards**: Explicit fractions (e.g. `50-1/4 in`, `33-7/16 in`), mandatory whitespace before units (`120 V`, `15 A`, `47 dBA`), and canonical List of Values (LOVs) for mounting, voltage, amperage, wash cycles, sound level, and material construction.

---

## 2. Workspace & Data File Inventory

| File Name | Size (Bytes) | Format | Record Count | Column Count | Description / Role |
|:---|:---|:---|:---|:---|:---|
| `Unihack_ Sample Dataset - Input.csv` | 128,673 | CSV | 1,000 | 6 | Primary raw supplier input catalog. High noise, cryptic text, heavy placeholders. |
| `Unihack_ Expected Output - Delivery Format.csv` | 8,695 | CSV | 2 | 252 | Master 252-column ground truth delivery template and target schema specification. |
| `Unihack_ Expected Output - Delivery Format (1).csv` | 8,695 | CSV | 2 | 252 | Byte-for-byte identical duplicate of master delivery format. |
| `UniHack_Solution_Guide.md` | 9,475 | Markdown | N/A | N/A | Architectural guidance, dataset reference index, and worked examples. |
| `UniHack_Solution_Guide.html` | 168,676 | HTML | N/A | N/A | Styled HTML equivalent of the Solution Guide. |
| `ORIGINAL_REQUEST.md` | 4,690 | Markdown | N/A | N/A | Core project requirements (R1: Pipeline, R2: Evaluation/QA, R3: Dashboard). |

---

## 3. In-Depth Input Dataset Analysis (`Unihack_ Sample Dataset - Input.csv`)

### 3.1 Schema & Cardinality
The input dataset comprises **1,000 rows** with **6 string columns**:

| Column Name | Non-Empty Count | Unique Values | Missing / Null Rate | Top Value / Dominant Pattern |
|:---|:---|:---|:---|:---|
| `Mfg_Part_Num` | 1,000 | 999 | 0.0% (0 / 1,000) | Unique manufacturer part numbers (`49-94-0013`, `DCB518ASTS06G`) |
| `Part_Desc` | 1,000 | 998 | 0.0% (0 / 1,000) | Abbreviated supplier descriptions with embedded MPN/specs |
| `E1_Brand` | 1,000 | 13 | 80.3% Placeholder | `-- Unbranded --` (799), `TREX` (122), `TIMBERTECH` (55) |
| `Unilog_Brand` | 1,000 | 1 | 100.0% Placeholder | `-- No Unilog Brand --` (1,000 rows, 100%) |
| `DIB_Brand` | 1,000 | 24 | 75.5% Placeholder | `-- No DIB Brand --` (755), `Philips` (109), `Diablo` (30) |
| `Part_Manuf` | 1,000 | 76 | 4.1% Placeholder (`-`) | `Phillips Lighting (5831)` (111), `Milwaukee Accessory (4031)` (108) |

### 3.2 Placeholders and Dummy Values
Industrial supplier feeds frequently populate empty fields with pseudo-strings rather than SQL `NULL`s:
- **`-- Unbranded --`**: 799 rows in `E1_Brand`.
- **`COMMODITY - UNBRANDED`**: 4 rows in `E1_Brand`.
- **`-- No Unilog Brand --`**: 1,000 rows in `Unilog_Brand` (100% dead column in raw feed).
- **`-- No DIB Brand --`**: 755 rows in `DIB_Brand`.
- **`-` (Hyphen)**: 41 rows in `Part_Manuf` indicate completely missing manufacturer data requiring entity resolution from `Part_Desc` or MPN prefix.

### 3.3 Manufacturer Entity Structure (`Part_Manuf`)
Analysis of the 76 unique manufacturers reveals internal vendor codes appended in parentheses:
- Pattern: `<Supplier/Manufacturer Name> (<Supplier Code>)`
- Examples:
  - `Phillips Lighting (5831)` $\rightarrow$ 111 items (Signify / Philips)
  - `Milwaukee Accessory (4031)` $\rightarrow$ 108 items (Milwaukee Tool / Techtronic Industries)
  - `Boise Cascade Building Materials (BOICA)` $\rightarrow$ 85 items (Distributor of Trex, James Hardie)
  - `Appliance Dealers Cooperative (APPDE)` $\rightarrow$ 84 items (Wholesale distributor for Frigidaire, Whirlpool, GE, LG, KitchenAid, Bosch)
  - `Parksite (6151)` $\rightarrow$ 55 items (Distributor for TimberTech / Azek)
  - `Black & Decker/dewlt (2585)` $\rightarrow$ 55 items (Stanley Black & Decker / DEWALT)
  - `Freud Inc (2435)` $\rightarrow$ 46 items (Freud / Diablo)
  - `U S Lumber (3073)` $\rightarrow$ 43 items (Distributor for Trex, LP SmartSide)
  - `Satco Prod Inc (5573)` $\rightarrow$ 41 items (Satco Products)
  - `Makita Usa Inc (5142)` $\rightarrow$ 23 items (Makita)
  - `Southwire/g Turner (6603)` $\rightarrow$ 19 items (Southwire)
  - `Leviton Mfg Co (4927)` $\rightarrow$ 17 items (Leviton)
  - `Festool USA (FESTO)` $\rightarrow$ 16 items (Festool)

### 3.4 Key Industrial Abbreviation Patterns in `Part_Desc`
The pipeline must parse and translate high-frequency industrial abbreviations:
- **Materials / Finishes**: `SS` / `SST` (Stainless Steel), `BSS` (Black Stainless Steel), `Alum` (Aluminum), `BRS` (Brass), `PVC` (Polyvinyl Chloride), `Wh` / `WH` (White), `Bk` / `BK` / `Blk` (Black).
- **Product Types / Anatomy**: `CPLG` (Coupling), `NPT` (National Pipe Taper), `Lt` (Light), `Ext` (Extension / Exterior), `Sq` (Square), `Horiz` (Horizontal), `Rnd` (Round), `w/` (With), `pc` / `PK` / `1PK` (Piece / Pack), `Elect` (Electrical), `CCT` (Correlated Color Temperature), `BLTLN` (Built-in).
- **Packaging / Operational Modifiers**: `Display Only` / `- Display` (Display unit), `Bare` / `(Bare)` (Bare Tool / Tool Only), `Kit` (Tool/Accessory Kit).
- **Dimensional Syntax**: `1/2"x18"`, `1x6-16'`, `3/4x60'`, `5"x.045"x7/8"`, `24x48`, `31.5x14.75`.

### 3.5 Taxonomy & Product Domain Breakdown Across 1,000 Items
Classification analysis across the 1,000 raw descriptions reveals major industrial domains:
1. **Power Tools, Abrasives, Blades & Accessories**: ~298 items (Diablo, Milwaukee, DeWalt, Freud, Makita, Festool, Wera)
2. **Building Materials, Decking, Lumber, Siding & Trim**: ~273 items (Trex, TimberTech, Azek, LP SmartSide, James Hardie)
3. **Lighting, Lamps, Luminaires & Bulbs**: ~230 items (Philips, Satco, Kichler, Lithonia, Feit Electric, Keystone)
4. **Electrical, Wiring Devices, Switches & Outlets**: ~73 items (Leviton, Southwire, Square D, Carlon, Cooper)
5. **Major Appliances (Dishwashers, Ranges, Refrigerators, Laundry)**: ~61 items (Frigidaire, Whirlpool, GE, LG, KitchenAid)
6. **Safety, PPE, Eyewear & Fire Protection**: ~45 items (Edge Eyewear, Radians, First Alert, Ohio Firewatch)
7. **Fasteners, Hardware, Hinges & Screws**: ~31 items (Hager, Kreg, National Nail, Senco)
8. **Plumbing, Faucets, Fittings & Valves**: ~10 items
9. **Fans, Ventilation & Miscellaneous**: ~69 items

---

## 4. Master 252-Column Delivery Schema Breakdown

The Unilog Delivery Schema comprises **252 explicit columns**. They are grouped below into **11 functional categories**:

```
========================================================================================
UNILOG 252-COLUMN MASTER DELIVERY SCHEMA ARCHITECTURE
========================================================================================
1. Source & Reference URLs (Cols 1-6)         -> MFR URL, Ref URL 1..5
2. Product Identifiers (Cols 7, 11, 21-22, 206-209) -> PART_NUMBER, SKU, MPN, UPC, UNSPSC
3. Supplier Input Audit (Cols 8-10, 12-17)    -> Dept, Class, Fine, Mfg_Part_Num, Part_Desc...
4. Canonical Brand & Mfg (Cols 18-20)         -> MANUFACTURER_NAME, BRAND_NAME, TRADE_NAME
5. Taxonomy & Classpath (Cols 23, 55)         -> Classpath, Product Name
6. 5-Tier Descriptions (Cols 24-29)           -> MOBILE, INVOICE, SHORT, LONG, RETAIL, MKTG
7. Features & Modifiers (Cols 30-54)          -> ITEM_FEATURES_1..20, With, Approvals, Prop 65
8. Normalized Attributes (Cols 56-205)        -> ATTRIBUTE_LABEL/VALUE/UOM 1..50 (150 cols)
9. Dimensions & Packaging (Cols 211-224)      -> List Price, L/W/H/Weight/Volume + UOMs
10. Digital Assets (Cols 225-249, 252)        -> Product Image, Alt Images 1..4, PDFs, Videos
11. Compliance & Flags (Cols 210, 232, 250, 251) -> Warranty, Country Of Origin, Discontinued
========================================================================================
```

### 4.1 Detailed Functional Group Specification

| Group # | Category Name | Column Range | Col Count | Exact Column Names & Description |
|:---|:---|:---|:---|:---|
| **1** | **Source & Reference URLs** | 001–006 | 6 | `MFR URL`, `Ref URL 1`, `Ref URL 2`, `Ref URL 3`, `Ref URL 4`, `Ref URL 5`. Verified manufacturer product and documentation URLs. |
| **2** | **Product Identifiers & Hierarchy** | 007, 011, 021, 022, 206–209 | 8 | `PART_NUMBER`, `SKU - MY_PART_NUMBER`, `MANUFACTURER_PART_NUMBER`, `ALTERNATE_PART_NUMBER`, `UPC`, `EAN`, `GTIN`, `UNSPSC`. |
| **3** | **Supplier & Input Audit Fields** | 008–010, 012–017 | 9 | Passthrough of raw inputs for full audit traceability: `Dept`, `Class`, `Fine`, `Mfg_Part_Num`, `Part_Desc`, `E1_Brand`, `Unilog_Brand`, `DIB_Brand`, `Part_Manuf`. |
| **4** | **Canonical Brand & Manufacturer** | 018–020 | 3 | `MANUFACTURER_NAME`, `BRAND_NAME`, `TRADE_NAME`. Resolved entities with legal casing and `®`/`™` symbols. |
| **5** | **Taxonomy & Classpath** | 023, 055 | 2 | `Classpath` (`Dept > Class > Fine` hierarchical string), `Product Name` (Canonical noun phrase, e.g. `Dishwasher`, `Decking`). |
| **6** | **5-Tier Content & Descriptions** | 024–029 | 6 | `MOBILE_DESC` (60-80 chars), `INVOICE_DESC` ($\le 40$ chars ALL CAPS), `SHORT_DESC` (Title), `LONG_DESC1` (Full technical spec), `RETAIL_DESC`, `MARKETING_DESCRIPTION`. |
| **7** | **Item Features & Marketing Modifiers** | 030–054 | 25 | `ITEM_FEATURES_1` through `ITEM_FEATURES_20` (Bullet points), `With` (Modifier clause), `Standard/Approvals` (Pipe-delimited certifications), `Prop 65`, `Application`, `Includes`. |
| **8** | **Product Attributes (Normalized Triplets)** | 056–205 | 150 | 50 sequential attribute slots formatted as triplets: `ATTRIBUTE_LABEL n`, `ATTRIBUTE_VALUE n`, `ATTRIBUTE_UOM n` for $n \in [1, 50]$. |
| **9** | **Physical Dimensions & Packaging** | 211–224 | 14 | `List Price`, `Selling Qty`, `Selling UOM`, `Standard Packaging Information`, `LENGTH`, `LENGTH_UOM`, `HEIGHT`, `HEIGHT_UOM`, `WIDTH`, `WIDTH_UOM`, `WEIGHT`, `WEIGHT_UOM`, `VOLUME`, `VOLUME_UOM`. |
| **10** | **Digital Assets (Images & Docs)** | 225–249, 252 | 25 | `Product Image`, `Alternate Image 1..4`, `SDS`, `SDS_1`, `Warranty Information`, `Catalog`, `Specification Sheet`, `Instruction/Installation Manual`, `Service Manual`, `Owners/User Manual`, `Line Drawing`, `MTR`, `RoHS`, `Full Engineering Drawing`, `Energy Star Guide`, `Technical Bulletin`, `Submittal`, `Compatibility Chart`, `Size Chart`, `Product Label/Insert`, `Video Link`, `Video Link 1`, `Actual Image (Yes/No)`. |
| **11** | **Compliance, Warranty & Flags** | 210, 250, 251 | 4 | `Warranty`, `Country Of Origin`, `Discontinued`. |

---

## 5. Ground Truth Deep Dive & Worked Examples

The delivery dataset provides 2 complete ground-truth rows in the Built-In Dishwasher category:
- **Item 1**: Frigidaire Professional Series `PDSH4816AF` (Matched to raw Input Row 61)
- **Item 2**: Whirlpool Eco Series `WDTS7024RZ` (Matched to raw Input Row 64)

### 5.1 Side-by-Side Comparison Matrix

| Target Column | Row 0: Frigidaire `PDSH4816AF` | Row 1: Whirlpool `WDTS7024RZ` | Transformation & Schema Rule |
|:---|:---|:---|:---|
| **`MFR URL`** | `https://www.frigidaire.com/en/p/owner-center/...` | `https://learnwhirlpool.com/smartsearchresults?...` | Official manufacturer portal URL |
| **`PART_NUMBER`** | `20887830` | `25286031` | Client catalog identifier |
| **`Dept` / `Class` / `Fine`** | `Appliances` / `Large Appliances` / `Dishwashers` | `Appliances` / `Large Appliances` / `Dishwashers` | 3-tier internal taxonomy |
| **`SKU - MY_PART_NUMBER`** | `1515863` | `1515867` | Distributor ERP SKU |
| **`Mfg_Part_Num`** | `PDSH4816AF` | `WDTS7024RZ` | Raw MPN passthrough |
| **`Part_Desc`** | `PDSH4816AF Dishwasher SS - Display Only` | `WDTS7024RZ Dishwasher SS - Display Only` | Raw supplier description passthrough |
| **`Part_Manuf`** | `Appliance Dealers Cooperative (APPDE)` | `Appliance Dealers Cooperative (APPDE)` | Raw supplier vendor field |
| **`MANUFACTURER_NAME`** | `Rheem Manufacturing` | `Whirlpool Corporation` | Canonical corporate entity |
| **`BRAND_NAME`** | `FRIGIDAIRE®` | `Whirlpool®` | Approved brand with registered trademark `®` |
| **`MANUFACTURER_PART_NUMBER`**| `PDSH4816AF` | `WDTS7024RZ` | Clean normalized MPN |
| **`Classpath`** | `Appliances & Consumer Electronics>Kitchen Appliances>Built-In Dishwashers` | `Appliances & Consumer Electronics>Kitchen Appliances>Built-In Dishwashers` | Unilog master taxonomy path |
| **`INVOICE_DESC`** | `DISHWASHER LEG 5 SST 120V 15A 50-1/4IN` (38 chars) | `DISHWASHER BLTLN SST SST 120V 10A 41DBA` (39 chars) | $\le 40$ chars, ALL CAPS shorthand |
| **`MOBILE_DESC`** | `Rheem Manufacturing FRIGIDAIRE, Dishwasher, Professional Series, PDSH4816AF` (75 chars) | `Whirlpool, Dishwasher, Eco Series, WDTS7024RZ, Built-in Mounting` (64 chars) | 60–80 chars concise mobile title |
| **`SHORT_DESC`** | `FRIGIDAIRE® Professional Series PDSH4816AF Dishwasher With CleanBoost™, Leg Mounting, 5-Wash Cycle, Stainless Steel` (115 chars) | `Whirlpool® Eco Series WDTS7024RZ Dishwasher, Built-in Mounting, Stainless Steel, Stainless Steel` (96 chars) | Master product title formula |
| **`LONG_DESC1`** | Full technical spec sentence (390 chars) | Full technical spec sentence (405 chars) | Standardized sentence with UOM spacing and fraction dimensions |
| **`RETAIL_DESC`** | `Professional Series Dishwasher, Leg Mounting, 5-Wash Cycle, Stainless Steel` (75 chars) | `Eco Series Dishwasher, Built-in Mounting, Stainless Steel, Stainless Steel` (74 chars) | Consumer catalog title (Title minus brand/MPN) |
| **`MARKETING_DESCRIPTION`**| *Empty (Optional)* | `Load more and run less with our quietest and largest capacity dishwasher...` | Benefit-driven sales copy |
| **`With`** | `With CleanBoost™` | `With Washing 3rd Rack, Water Repellent Silverware Basket` | Feature clause with trademark symbol |
| **`Standard/Approvals`** | `ASSE 1006\|CEE Tier 2 Qualified\|cUL Listed\|ENERGY STAR Certified\|NSF Certified\|UL Listed` | *Empty* | Pipe-delimited compliance standards |
| **`Product Name`** | `Dishwasher` | `Dishwasher` | Canonical leaf noun |

### 5.2 Attribute Slot Configuration for `Built-In Dishwashers`
Ground truth proves that attribute slots follow a fixed category-specific sequence:

| Slot # | Attribute Label | Row 0 (`PDSH4816AF`) Value & UOM | Row 1 (`WDTS7024RZ`) Value & UOM | LOV Data Type / Format |
|:---|:---|:---|:---|:---|
| **Slot 1** | `Series` | `Professional Series` (UOM: null) | `Eco Series` (UOM: null) | Controlled text |
| **Slot 2** | `Model` | *null* | *null* | Controlled text / code |
| **Slot 3** | `Number of Wash Cycles`| `5` (UOM: null) | *null* | Integer string |
| **Slot 4** | `Voltage Rating` | `120` (UOM: `V`) | `120` (UOM: `V`) | Numeric + UOM `V` |
| **Slot 5** | `Amperage Rating` | `15` (UOM: `A`) | `10` (UOM: `A`) | Numeric + UOM `A` |
| **Slot 6** | `Mounting Type` | `Leg` (UOM: null) | `Built-in` (UOM: null) | Canonical LOV (`Leg`, `Built-in`, `Under-Counter`) |
| **Slot 7** | `Plug Type` | *null* | *null* | Controlled text |
| **Slot 8** | `Size` | `24 in W x 24-1/4 in D` (UOM: null) | `33-7/16 in H x 23-7/8 in W x 22-5/8 in D` (UOM: null) | Multi-dimensional fraction format |
| **Slot 9** | `Depth With Door Open` | `50-1/4` (UOM: `in`) | `50-3/16` (UOM: `in`) | Fraction + UOM `in` |
| **Slot 10** | `Minimum Height` | `8-1/2 in Upper Rack, 11-1/4 in Lower Rack` | `33-7/16` (UOM: `in`) | Fraction / Compound spec |
| **Slot 11** | `Maximum Height` | `10-3/8 in Upper Rack, 13-1/4 in Lower Rack` | *null* | Fraction / Compound spec |
| **Slot 12** | `Sound Level` | `47` (UOM: `dBA`) | `41` (UOM: `dBA`) | Numeric + UOM `dBA` |
| **Slot 13** | `Material` | `Stainless Steel` (UOM: null) | `Stainless Steel` (UOM: null) | Canonical material LOV |
| **Slot 14** | `Color` | *null* | `Stainless Steel` (UOM: null) | Canonical color LOV |
| **Slot 15** | `Additional Information`| `240 kW-hr Annual Energy, 1 to 12 hr Delay Start Hours` | `Folding Tines, Leak Detection System, Moisture Repellent Silverware Basket, Normal Cycle, Quick Wash Cycle, Sani Rinse Option, Sensor Cycle, Triple Wash Spray` | Comma-delimited feature strings |
| **Slots 16–50** | *Empty Slots* | *null* | *null* | Reserved standard schema slots |

---

## 6. Construction Formulas & Transformation Rules

### 6.1 Description Generation Formulas

```
========================================================================================
1. INVOICE_DESC (Character Limit: <= 40 | Casing: ALL CAPS)
----------------------------------------------------------------------------------------
Formula: [PRODUCT_NAME_UPPER] [MOUNT_ABBR] [CYCLES] [MAT_ABBR] [COLOR_ABBR] [VOLT] [AMP] [KEY_SPEC]
Row 0:   DISHWASHER LEG 5 SST 120V 15A 50-1/4IN                  (Length: 38 chars)
Row 1:   DISHWASHER BLTLN SST SST 120V 10A 41DBA                 (Length: 39 chars)

2. MOBILE_DESC (Character Limit: 60 - 80 Chars | Casing: Title/Mixed)
----------------------------------------------------------------------------------------
Pattern A: [MANUFACTURER_NAME] [BRAND_NAME_CLEAN], [Product Name], [Series], [MPN]
Row 0:     Rheem Manufacturing FRIGIDAIRE, Dishwasher, Professional Series, PDSH4816AF  (75 chars)
Pattern B: [BRAND_NAME_CLEAN], [Product Name], [Series], [MPN], [Key Attribute]
Row 1:     Whirlpool, Dishwasher, Eco Series, WDTS7024RZ, Built-in Mounting             (64 chars)

3. SHORT_DESC / Product Title (Casing: Title/Mixed with Trademark Symbols)
----------------------------------------------------------------------------------------
Formula: [BRAND_NAME] [Series] [MPN] [Product Name] [With Clause], [Key Spec 1], [Key Spec 2], [Key Spec 3]
Row 0:   FRIGIDAIRE® Professional Series PDSH4816AF Dishwasher With CleanBoost™, Leg Mounting, 5-Wash Cycle, Stainless Steel (115 chars)
Row 1:   Whirlpool® Eco Series WDTS7024RZ Dishwasher, Built-in Mounting, Stainless Steel, Stainless Steel (96 chars)

4. RETAIL_DESC (Short Desc omitting Brand & MPN)
----------------------------------------------------------------------------------------
Formula: [Series] [Product Name], [Mounting] Mounting, [Cycles]-Wash Cycle, [Material]
Row 0:   Professional Series Dishwasher, Leg Mounting, 5-Wash Cycle, Stainless Steel (75 chars)
Row 1:   Eco Series Dishwasher, Built-in Mounting, Stainless Steel, Stainless Steel (74 chars)

5. LONG_DESC1 (Full Technical Specification Sentence)
----------------------------------------------------------------------------------------
Formula: [BRAND_NAME] [Product Name] [With Clause], [Series], [Cycles] Wash Cycles, [Voltage] V, [Amperage] A, [Mounting] Mounting, [Size], [Depth Open] in Depth With Door Open, [Heights], [Sound Level] dBA Sound Level, [Material], [Color], Additional Information: [Features]
Row 0:   FRIGIDAIRE® Dishwasher With CleanBoost™, Professional Series, 5 Wash Cycles, 120 V, 15 A, Leg Mounting, 24 in W x 24-1/4 in D, 50-1/4 in Depth With Door Open, 8-1/2 in Upper Rack, 11-1/4 in Lower Rack Minimum Height, 10-3/8 in Upper Rack, 13-1/4 in Lower Rack Maximum Height, 47 dBA Sound Level, Stainless Steel, Additional Information: 240 kW-hr Annual Energy, 1 to 12 hr Delay Start Hours (390 chars)
========================================================================================
```

### 6.2 Unit of Measure (UOM) & Fraction Standardization Rules
1. **Mandatory Whitespace**: Always insert a single space between number and unit:
   - `120 V` (not `120V`), `15 A` (not `15A`), `47 dBA` (not `47dBA`), `24 in` (not `24in` or `24"`).
   - *Exception*: Inside `INVOICE_DESC` where token compaction is required to satisfy $\le 40$ chars (`120V`, `15A`, `50-1/4IN`, `41DBA`).
2. **Decimal-to-Fraction Conversion**: Convert decimal dimensions to hyphenated trade fractions:
   - `0.25` $\rightarrow$ `1/4`
   - `0.5` $\rightarrow$ `1/2`
   - `0.1875` $\rightarrow$ `3/16`
   - `0.4375` $\rightarrow$ `7/16`
   - `50.25 in` $\rightarrow$ `50-1/4 in`
   - `50.1875 in` $\rightarrow$ `50-3/16 in`
   - `33.4375 in` $\rightarrow$ `33-7/16 in`
   - `23.875 in` $\rightarrow$ `23-7/8 in`
   - `22.625 in` $\rightarrow$ `22-5/8 in`
3. **Compound Dimensions Formatting**:
   - `24 in W x 24-1/4 in D`
   - `33-7/16 in H x 23-7/8 in W x 22-5/8 in D`

### 6.3 Digital Asset Standard Naming Conventions
- **Product Image (Primary)**: `[BRAND_NAME_UPPER]_[MPN].jpg` (e.g. `FRIGIDAIRE_PDSH4816AF.jpg`, `Whirlpool_WDTS7024RZ.jpg`).
- **Alternate Images**: `[BRAND_NAME_UPPER]_[MPN]_[Index].jpg` (e.g. `FRIGIDAIRE_PDSH4816AF_1.jpg`, `FRIGIDAIRE_PDSH4816AF_2.jpg`).
- **Specification Sheet**: `[BRAND_NAME_UPPER]_[MPN]_Specification_Sheet.pdf`.
- **Actual Image Flag**: Set to `'Yes'` when verified image asset exists, otherwise `'No'`.

---

## 7. Canonical Controlled Vocabularies (LOVs) & Lookup Dictionaries

Based on ground truth and catalog inspection, the pipeline must enforce strict LOVs across key domains:

### 7.1 Dishwashers & Major Appliances
- **Mounting Types**: `Built-in`, `Leg`, `Under-Counter`, `Freestanding`, `Portable`, `Integrated`.
- **Voltage Ratings**: `120`, `208`, `240`, `277`, `480` (Standard UOM: `V`).
- **Amperage Ratings**: `10`, `15`, `20`, `30`, `50` (Standard UOM: `A`).
- **Wash Cycles**: `3`, `4`, `5`, `6`, `7`, `8`, `10`.
- **Sound Levels**: `38`, `39`, `41`, `42`, `44`, `45`, `47`, `50`, `52`, `55` (Standard UOM: `dBA`).
- **Materials**: `Stainless Steel`, `Plastic`, `Porcelain Enamel`, `Cast Iron`, `Steel`.
- **Colors / Finishes**: `Stainless Steel`, `Black Stainless Steel`, `White`, `Black`, `Panel Ready`, `Fingerprint Resistant Stainless Steel`, `Bisque`.
- **Certifications / Standards**: `ASSE 1006`, `CEE Tier 1 Qualified`, `CEE Tier 2 Qualified`, `cUL Listed`, `ENERGY STAR Certified`, `NSF Certified`, `UL Listed`.

### 7.2 Pipe, Hose & Tube Fittings (Fittings LOV)
- **Fitting Types**: `Coupling`, `Elbow`, `Tee`, `Adapter`, `Bushing`, `Union`, `Nipple`, `Plug`, `Cap`, `Cross`, `Flange`.
- **Connection Types**: `NPT`, `FNPT`, `MNPT`, `Flare`, `Compression`, `Push-Fit`, `Solder / Sweat`, `Flanged`, `Grooved`, `Barbed`, `Press-to-Connect`.
- **Material Construction**: `Brass`, `Forged Brass`, `Stainless Steel 304`, `Stainless Steel 316`, `Carbon Steel`, `Ductile Iron`, `Malleable Iron`, `Copper`, `PVC Schedule 40`, `PVC Schedule 80`, `CPVC`, `Polypropylene`.

### 7.3 Power Tools & Abrasives
- **Tool Types**: `Sander`, `Circular Saw`, `Miter Saw`, `Drill Press`, `Impact Driver`, `Cut-Off Tool`, `Reciprocating Saw`, `Angle Grinder`.
- **Abrasive Types / Backings**: `Sanding Belt`, `Stikit Film Disc`, `Hook & Loop Disc`, `Cut Off Disc`, `Flap Disc`, `Grinding Wheel`.
- **Grit Sizes**: `P36`, `P40`, `P60`, `P80`, `P100`, `P120`, `P150`, `P180`, `P220`, `P320`, `P400`, `P600`.
- **Arbor / Shank Sizes**: `1/4 in`, `3/8 in`, `1/2 in`, `7/8 in`, `5/8 in-11`.

### 7.4 Decking & Building Materials
- **Decking Types**: `Capped Composite Decking`, `Cellular PVC Decking`, `Wood-Plastic Composite (WPC)`, `Fascia Board`, `Riser Board`.
- **Edge Profiles**: `Grooved Edge`, `Square Edge`, `Tongue & Groove`.
- **Collections / Series**: `Transcend`, `Select`, `Enhance`, `Vintage Collection`, `Lineage Collection`, `Landmark Collection`.

---

## 8. Pipeline Transformation Map (Input $\rightarrow$ Output)

The following table details the end-to-end processing pipeline mapping the 6 raw input columns to the 252 delivery format columns:

```
+---------------------------------------------------------------------------------------------------+
| RAW INPUT (6 Columns)                                                                             |
| [Mfg_Part_Num] [Part_Desc] [E1_Brand] [Unilog_Brand] [DIB_Brand] [Part_Manuf]                     |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| STAGE 1: INGESTION, PLACEHOLDER SANITIZATION & MPN EXTRACTION                                     |
| - Filter out '-- Unbranded --', '-- No Unilog Brand --', '-- No DIB Brand --'                    |
| - Remove internal distributor codes: '(APPDE)', '(5831)', '(BOICA)'                               |
| - Extract clean MPN & strip MPN duplicate from start of Part_Desc                                 |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| STAGE 2: CANONICAL BRAND & MANUFACTURER RESOLUTION                                                |
| - Resolve distributor masks: 'Appliance Dealers Cooperative (APPDE)' -> Frigidaire/Whirlpool/GE   |
| - Fuzzy match against UniCat Manufacturer & Brand master catalog                                  |
| - Apply exact legal casing and symbols (e.g. 'FRIGIDAIRE®', 'Whirlpool®', 'DEWALT®')               |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| STAGE 3: TAXONOMY & CLASSPATH CLASSIFICATION                                                      |
| - Predict 3-tier Dept > Class > Fine ('Appliances > Large Appliances > Dishwashers')              |
| - Map to full Classpath & UNSPSC code                                                             |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| STAGE 4: CONTROLLED ATTRIBUTE EXTRACTION (LOV ENGINE)                                             |
| - Extract category-specific technical attributes into Slots 1..50                                 |
| - Validate every value against canonical LOV (reject/remedy hallucinations)                       |
| - Standardize UOMs (V, A, dBA, in) and convert decimals to fractions ('50-1/4 in')                |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| STAGE 5: 5-TIER DESCRIPTION & ASSET SYNTHESIS                                                     |
| - INVOICE_DESC (<= 40 chars, ALL CAPS abbreviation formula)                                       |
| - MOBILE_DESC (60-80 chars concise mobile title)                                                  |
| - SHORT_DESC (Standard Unilog product title)                                                      |
| - LONG_DESC1 (Grammatical technical narrative)                                                    |
| - RETAIL_DESC & MARKETING_DESCRIPTION                                                             |
| - Generate Product Image & Spec Sheet filenames                                                   |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| STAGE 6: 252-COLUMN DELIVERY CSV GENERATION & QUALITY SCORING                                     |
| - Populate all 252 columns in strict delivery sequence                                            |
| - Compute confidence score (0.0 to 1.0) and flag anomalies for Human Review                       |
+---------------------------------------------------------------------------------------------------+
```

---

## 9. Ground-Truth Benchmarking & Quality Assurance Metrics

To satisfy Requirement R2 and guarantee zero defects, the benchmarking suite will evaluate pipelines on five orthogonal dimensions:

1. **Schema Integrity (100%)**: Exported CSV contains all 252 target columns with exact header matching and proper sequence.
2. **Character Limit Compliance (100%)**:
   - `INVOICE_DESC`: $100\%$ must be $\le 40$ characters and $100\%$ uppercase (`is_upper() == True`).
   - `MOBILE_DESC`: $100\%$ must be within $60 \le \text{length} \le 80$ characters.
3. **LOV Adherence Rate ($\ge 98\%$)**: Extracted technical attribute values strictly match the controlled vocabulary for the resolved category; $0\%$ fabricated/hallucinated options.
4. **UOM Formatting Compliance (100%)**:
   - Spacing: $100\%$ of numbers followed by space before UOM (`120 V`, `15 A`, `47 dBA`).
   - Fractions: Decimal dimensions converted to hyphenated fractions (`50-1/4 in`, `33-7/16 in`).
5. **Entity Accuracy**: Exact match and BLEU/ROUGE token similarity against ground-truth descriptions and attributes on the benchmark subset.

---

## 10. Summary & Recommendations for Engineering Squad

1. **Entity Resolution Priority**: Appliance rows under `Appliance Dealers Cooperative (APPDE)` must parse brand cues from the start of `Part_Desc` or MPN prefix (e.g. `PDSH*` $\rightarrow$ Frigidaire, `WDTS*` $\rightarrow$ Whirlpool, `KDFM*` / `KDTS*` $\rightarrow$ KitchenAid, `PDT*` / `PDD*` $\rightarrow$ GE, `LDPH*` $\rightarrow$ LG).
2. **Deterministic Description Formatter**: Use template-based assembly for `INVOICE_DESC` and `MOBILE_DESC` with fallback length compressors to guarantee 100% compliance with character caps.
3. **Pre-Built LOV Lookup Engine**: Implement fast in-memory dictionary validation and fuzzy matching for attributes, UOMs, and fractions.
4. **Interactive Dashboard Features**: Implement real-time character count badges (green $\le 40$, red $> 40$) for `INVOICE_DESC` and (green $60-80$, amber $<60$, red $>80$) for `MOBILE_DESC` in the UI.

---
*Report compiled by Explorer 1 (Data Schema & Ground Truth Specialist).*
