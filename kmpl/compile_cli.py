#!/usr/bin/env python3
"""
KMPL BOM Compiler CLI Runner
Usage:
    python compile_cli.py "001SW-PARTS BOM.xlsx" "OUTPUT-FINAL-BOM.xlsx"
"""
import sys
import os

# Add parent directory to sys.path so kmpl can be imported directly
cur_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(cur_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from kmpl.utils.bom_parser import parse_solidworks_bom
from kmpl.utils.weight_calculator import compile_summary
from kmpl.utils.excel_exporter import export_final_bom_excel


def main():
    input_file = sys.argv[1] if len(sys.argv) > 1 else "001SW-PARTS BOM.xlsx"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "001FINAL-PARTS BOMDF-GENERATED.xlsx"

    print(f"--> Parsing SolidWorks BOM: {input_file}")
    bom_header, bom_items = parse_solidworks_bom(input_file, default_po_qty=1)
    print(f"--> Parsed {len(bom_items)} items successfully.")

    # Override with standard project header info if blank
    if not bom_header.get("project_no"):
        bom_header["project_no"] = "2559-01"
    if not bom_header.get("equipment_name"):
        bom_header["equipment_name"] = "Continuous Trail"
    if not bom_header.get("bom_name"):
        bom_header["bom_name"] = bom_header["equipment_name"]
    if not bom_header.get("bom_date"):
        bom_header["bom_date"] = "23.09.2026"

    print(f"--> Compiling Summary for Project: {bom_header['project_no']}...")
    summary_items = compile_summary(bom_items, project_no=bom_header["project_no"])
    print(f"--> Generated {len(summary_items)} summary rows.")

    print(f"--> Exporting formatted Excel file to: {output_file}...")
    export_final_bom_excel(output_file, bom_header, bom_items, summary_items)
    print(f"--> [SUCCESS] Successfully compiled and exported to {output_file}!")


if __name__ == "__main__":
    main()
