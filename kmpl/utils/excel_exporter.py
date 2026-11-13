import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def export_final_bom_excel(output_path: str, bom_header: dict, bom_items: list, summary_items: list):
    """
    Exports compiled BOM items and summary to a professionally styled Excel file
    matching 001FINAL-PARTS BOMDF.xlsx format.
    """
    wb = openpyxl.Workbook()
    
    # ----------------------------------------------------
    # Styles
    # ----------------------------------------------------
    font_title = Font(name="Calibri", size=11, bold=True)
    font_header = Font(name="Calibri", size=10, bold=True, color="000000")
    font_data = Font(name="Calibri", size=10)
    
    fill_header = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    fill_sum_header = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    fill_manual_yellow = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
    
    thin_border_side = Side(border_style="thin", color="D3D3D3")
    border_cell = Border(
        left=thin_border_side,
        right=thin_border_side,
        top=thin_border_side,
        bottom=thin_border_side
    )
    
    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")

    project_no = bom_header.get("project_no") or "2559-01"
    bom_name = bom_header.get("bom_name") or "Continuous Trail"
    equip_name = bom_header.get("equipment_name") or "Continuous Trail"
    bom_date = bom_header.get("bom_date") or "23.09.2026"
    po_qty = bom_header.get("po_qty") or 1
    unit_str = bom_header.get("unit") or "Nos."

    # ----------------------------------------------------
    # Sheet 1: Detailed BOM (e.g. 2559-01)
    # ----------------------------------------------------
    ws_bom = wb.active
    ws_bom.title = project_no[:31] # Excel sheet name limit 31 chars
    
    # Row 1: Title
    ws_bom.cell(1, 1, value=bom_name).font = font_title
    
    # Row 2: Headers
    bom_cols = [
        "S.N", "BOM Date ", "BOM NAME", "Project No.", "Equipment Name",
        "P.O Qty.", "UNIT", "Category", "Type of RM", "Dwg. No.",
        "ITEM CODE", "Description ", "Length", "Width", "thk/Dia",
        "Unit Qty.", "Unit Weight/Qty. ", "Total Weight/Qty.", "MOC", "Units", "Remarks"
    ]
    for c_idx, h in enumerate(bom_cols, 1):
        cell = ws_bom.cell(2, c_idx, value=h)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center
        cell.border = border_cell
        
    for r_idx, itm in enumerate(bom_items, 3):
        row_vals = [
            itm.get("idx", r_idx - 2),
            bom_date,
            bom_name,
            project_no,
            equip_name,
            po_qty,
            unit_str,
            itm.get("category", "C"),
            itm.get("rm_type"),
            itm.get("dwg_no"),
            itm.get("item_code"),
            itm.get("description"),
            itm.get("length"),
            itm.get("width"),
            itm.get("thk"),
            itm.get("unit_qty"),
            itm.get("unit_weight"),
            itm.get("total_weight"),
            itm.get("moc"),
            itm.get("unit"),
            itm.get("remarks")
        ]
        is_manual_row = itm.get("is_manual", False)
        for c_idx, val in enumerate(row_vals, 1):
            cell = ws_bom.cell(r_idx, c_idx, value=val)
            cell.font = font_data
            cell.border = border_cell
            if is_manual_row:
                cell.fill = fill_manual_yellow
            elif c_idx == 11 and (not val or itm.get("remarks") == "Pending Master Mapping"):
                cell.fill = fill_sum_header
            elif c_idx == 21 and itm.get("remarks") == "Pending Master Mapping":
                cell.fill = fill_sum_header
            if c_idx in [1, 2, 4, 6, 7, 8, 16, 20]:
                cell.alignment = align_center
            elif c_idx in [13, 14, 15, 17, 18, 21]:
                cell.alignment = align_right
                if isinstance(val, (int, float)):
                    cell.number_format = "#,##0.00"
            else:
                cell.alignment = align_left

    # ----------------------------------------------------
    # Sheet 2: SUMMARY
    # ----------------------------------------------------
    ws_sum = wb.create_sheet(title="SUMMARY")
    
    # Row 1: Title Box
    title_text = f"SUMMARY RM\n {project_no}\n{equip_name}\nQTY - {po_qty} No"
    cell_t = ws_sum.cell(1, 1, value=title_text)
    cell_t.font = font_title
    cell_t.alignment = align_left
    ws_sum.row_dimensions[1].height = 45

    # Row 2: Headers
    sum_cols = [
        "Sr.No.", "Project No.", "Category", "Item code", "RM Type",
        "Description", "thk mm", "Weight / kg", "Unit", "General Description",
        "Length / Qty", "Unit", "MOC"
    ]
    for c_idx, h in enumerate(sum_cols, 1):
        cell = ws_sum.cell(2, c_idx, value=h)
        cell.font = font_header
        cell.fill = fill_sum_header
        cell.alignment = align_center
        cell.border = border_cell
        
    for r_idx, sitm in enumerate(summary_items, 3):
        row_vals = [
            sitm.get("idx", r_idx - 2),
            sitm.get("project_no", project_no),
            sitm.get("category", "C"),
            sitm.get("item_code"),
            sitm.get("rm_type"),
            sitm.get("description"),
            sitm.get("thk_mm"),
            sitm.get("weight_kg"),
            sitm.get("unit_weight"),
            sitm.get("general_description"),
            sitm.get("length_qty"),
            sitm.get("unit"),
            sitm.get("moc")
        ]
        is_manual_sum = sitm.get("is_manual", False)
        for c_idx, val in enumerate(row_vals, 1):
            cell = ws_sum.cell(r_idx, c_idx, value=val)
            cell.font = font_data
            cell.border = border_cell
            if is_manual_sum:
                cell.fill = fill_manual_yellow
            if c_idx in [1, 2, 3, 9, 12, 13]:
                cell.alignment = align_center
            elif c_idx in [7, 8, 11]:
                cell.alignment = align_right
                if isinstance(val, (int, float)):
                    cell.number_format = "#,##0.00"
            else:
                cell.alignment = align_left

    # Auto-adjust column widths
    for sheet in [ws_bom, ws_sum]:
        for col in sheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            sheet.column_dimensions[col_letter].width = min(max(max_len + 2, 10), 45)

    wb.save(output_path)
    return output_path
