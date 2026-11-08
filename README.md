# KMPL - SolidWorks Design BOM Compiler for ERPNext v16

[![Frappe Version](https://img.shields.io/badge/frappe-v16-blue.svg)](https://frappeframework.com/)
[![ERPNext Version](https://img.shields.io/badge/erpnext-v16-green.svg)](https://erpnext.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**KMPL** is a custom Frappe app designed for ERPNext v16 to automate the parsing, material classification, weight calculation, and summary compilation of SolidWorks Design BOM files (`001SW-PARTS BOM.xlsx`) into standard Production BOMs and Raw Material/Fastener/BOP summaries (`001FINAL-PARTS BOMDF.xlsx`), with seamless integration into native ERPNext Manufacturing Items and BOMs.

---

## Features

1. **Automatic Tree Hierarchy Resolution**:
   - Parses indentation levels in SolidWorks BOM exports.
   - Automatically tracks drawing numbers (`Dwg. No.`) from parent subassemblies and propagates them to child cut pieces.

2. **Intelligent Material Classification & Dimension Extraction**:
   - Classifies items into `Raw Material-PLATE`, `Raw Material-SQ PIPE`, `Raw Material-PIPE`, `Raw Material-ISA ANGLE`, `Raw Material-ROD`, `Raw Material-SQ BAR`, `Raw Material-BLOCK`, `Raw Material-FASTENER`, and `Raw Material-BOP`.
   - Extracts 3D dimensions (Length, Width, Thickness / Diameter, M-sizes) directly from SolidWorks descriptions and bounding boxes.

3. **Master List Lookups & Standard Item Codes**:
   - Matches raw material codes (e.g. `RM-SS1.5X1500M`, `RM-SSQP50X3M`, `RM-SA40X3M`, `RM-SR25M`) based on standard thickness and section charts.
   - Matches Fasteners (`F-ALBM...`, `F-HBM...`, `F-HNM...`, `F-STM...`) based on standard fastener tables.
   - Maps Bought Out Parts (`BE-...`, `HW-...`, `ECO-...`, `V-...`, `GM-...`, `SP-...`, `PU-...`, `PN-...`, `RB-...`) against the 3,900+ BOP master catalog.

4. **Automated Summary Rollup**:
   - **Plates & Sheets**: Calculates total weight and required full sheet counts (`Total Weight / Standard Full Sheet Weight`).
   - **Pipes, Angles & Rods**: Calculates total weight and required procurement length in meters (`Sum of lengths / 1000`).
   - **Fasteners & BOP**: Groups and rolls up total piece counts.

5. **Full Master Data Management from ERPNext UI**:
   - **KMPL BOP Master**: Add, edit, or import bought-out items (bearings, motors, valves, castors, glands) directly in ERPNext.
   - **KMPL RM Master**: Add new raw material sheets, pipe sizes, or fasteners on the fly.
   - **KMPL Settings**: Upload updated `MASTER ITEM LIST BOP.xlsx` or `STD SUMMARY FOR RM & FASTENERS.xlsx` to bulk-sync 5,000+ items with 1 click!

6. **ERPNext v16 Integration & Excel Exporter**:
   - Generates exact formatted Excel workbooks with two sheets: `[Project-No]` detailed sheet and `SUMMARY` sheet.
   - Automatically creates standard ERPNext `Item` records and multi-level manufacturing `BOM`s in ERPNext.

---

## Installation on ERPNext v16 Bench

```bash
# 1. Fetch the app into your bench
bench get-app https://github.com/nexgenerptechnologies/kmpl.git

# 2. Install the app onto your site
bench --site <your-site-name> install-app kmpl

# 3. Run migrations
bench --site <your-site-name> migrate
```

---

## How to Use inside ERPNext

1. Open **Desk** $\rightarrow$ Search for **Design BOM Compiler**.
2. Click **Add Design BOM Compiler**:
   * Enter **Project No.** (e.g. `2559-01`).
   * Enter **Equipment Name** (e.g. `Continuous Trail`).
   * Enter **P.O. Qty** and **BOM Date**.
   * Attach your SolidWorks BOM Excel file (`001SW-PARTS BOM.xlsx`).
3. Click **Compile BOM**:
   * The system automatically parses all components, resolves drawing numbers, extracts dimensions, computes weights, and populates both the **BOM Items** and **BOM Summary** child tables.
4. Click **Download Final Excel**:
   * Exports the formatted Excel workbook identical to `001FINAL-PARTS BOMDF.xlsx`.
5. Click **Create ERPNext BOM**:
   * Generates native ERPNext `Item` records for items not yet in the master and creates the official manufacturing `BOM`.

---

## Standalone CLI Usage (Without Bench)

You can run the compiler directly from the command line:

```bash
python kmpl/compile_cli.py "001SW-PARTS BOM.xlsx" "001FINAL-PARTS BOMDF-GENERATED.xlsx"
```

---

## Repository Structure

```text
kmpl/
├── pyproject.toml
├── requirements.txt
├── README.md
├── license.txt
└── kmpl/
    ├── hooks.py
    ├── compile_cli.py                 # Standalone CLI compiler
    ├── kmpl/
    │   └── doctype/
    │       ├── design_bom_compiler/   # Main DocType & Controller
    │       ├── design_bom_item/       # Detailed BOM child table
    │       └── design_bom_summary_item/# Summary child table
    └── utils/
        ├── bom_parser.py              # SolidWorks tree parser & dimension extractor
        ├── item_matcher.py            # Master item code and classification rules
        ├── weight_calculator.py       # Weights, sheet fractions, and meter totals
        └── excel_exporter.py          # Professional Excel workbook generator
```

---

## License

MIT License. Developed by Nexgen ERP Technologies.
