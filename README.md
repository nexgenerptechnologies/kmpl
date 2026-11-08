# KMPL - SolidWorks Design BOM Compiler for ERPNext v16

[![Frappe Version](https://img.shields.io/badge/frappe-v16-blue.svg)](https://frappeframework.com/)
[![ERPNext Version](https://img.shields.io/badge/erpnext-v16-green.svg)](https://erpnext.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**KMPL** is a native ERPNext v16 app that extends standard ERPNext **Item** Master with engineering/design specifications and compiles SolidWorks BOM files (`001SW-PARTS BOM.xlsx`) into production BOMs, cut-lists, and raw material summaries (`001FINAL-PARTS BOMDF.xlsx`), creating official ERPNext Manufacturing Items and BOMs.

---

## Unified Architecture (Standard ERPNext Item Master)

Instead of managing separate duplicate master lists, KMPL adds custom engineering fields directly to the standard ERPNext **Item** master:

* **Type of RM** (`custom_rm_type`): Select (*Raw Material-PLATE, Raw Material-SQ PIPE, Raw Material-PIPE, Raw Material-ISA ANGLE, Raw Material-ROD, Raw Material-FASTENER, Raw Material-BOP*).
* **Thickness / Size** (`custom_thickness_size`): e.g. `1.5`, `3`, `50x3`, `M24`.
* **Standard Full Sheet Weight (kg)** (`custom_full_sheet_weight`): e.g. `54.20`, `108.41` (used to calculate full sheets needed: `Total Weight / Full Sheet Wt`).
* **Weight per Meter (kg/m)** (`custom_weight_per_meter`): e.g. `4.12`, `3.49` (used to calculate weights and procurement meters for pipes, angles, rods).
* **MOC** (`custom_moc`): e.g. `AISI 304`, `MS`.
* **Design Description Pattern** (`custom_design_pattern`): SolidWorks drawing keywords used for auto-matching.

---

## Features

1. **Zero Duplicate Masters**:
   - Manage all items directly in ERPNext's native **Item** master.
   - Use standard ERPNext **Data Import** to bulk-import items from Excel anytime.

2. **Automatic Tree Hierarchy Resolution**:
   - Evaluates indentation in SolidWorks BOM exports (`PART NUMBER` column).
   - Automatically tracks parent drawing numbers (`Dwg. No.`) and propagates them to child cut pieces.

3. **Intelligent Material Weight & Summary Calculation**:
   - **Plates & Sheets**: Calculates total weight and required full sheet counts (`Total Weight / Standard Full Sheet Weight`).
   - **Pipes, Angles & Rods**: Calculates total weight and required procurement length in meters (`Sum of lengths / 1000`).
   - **Fasteners & BOP**: Groups and rolls up total piece counts.

4. **1-Click Manufacturing BOM & Excel Export**:
   - Generates exact formatted Excel workbooks with two sheets: `[Project-No]` detailed sheet and `SUMMARY` sheet.
   - Automatically creates standard ERPNext `Item` records (if not present) and creates the official manufacturing `BOM` in ERPNext.

---

## Installation on ERPNext v16 Bench

```bash
# 1. Fetch the app into your bench
bench get-app https://github.com/nexgenerptechnologies/kmpl.git

# 2. Install the app onto your site
bench --site <your-site-name> install-app kmpl

# 3. Run migrations (automatically creates custom fields on Item)
bench --site <your-site-name> migrate
```

---

## How to Manage Items in ERPNext

### Option A: Add a Single Item
1. Open **Item** $\rightarrow$ Click **+ Add Item**.
2. Enter Item Code, Item Name, Item Group, and UOM.
3. In the **KMPL Design & RM Specifications** section, enter Thickness, Full Sheet Weight, or Weight per Meter.
4. Click **Save**.

### Option B: Bulk Import via Standard ERPNext Data Import
1. Go to **Data Import** in ERPNext.
2. Select DocType: **Item**.
3. Upload `sample_files/ITEM_MASTER_IMPORT_READY.xlsx` (pre-populated with 5,140+ master items and custom fields).
4. Click **Start Import**.

---

## How to Compile a SolidWorks BOM

1. Open **Design BOM Compiler** in ERPNext.
2. Enter **Project No.** (e.g. `2559-01`), **Equipment Name** (e.g. `Continuous Trail`), **P.O. Qty**, and attach `001SW-PARTS BOM.xlsx`.
3. Click **Compile BOM**:
   * Auto-populates **BOM Items** (cut pieces, plates, pipes, fasteners, drawing numbers).
   * Auto-populates **Summary Items** (grouped sheets, meter totals, counts).
4. Click **Download Final Excel** to download the formatted `.xlsx` workbook.
5. Click **Create ERPNext BOM** to generate the native manufacturing BOM in ERPNext.

---

## License

MIT License. Developed by Nexgen ERP Technologies.
