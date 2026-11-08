import re
import openpyxl
from .item_matcher import classify_rm_type, match_item_code
from .weight_calculator import calculate_item_weight

def clean_str(val):
    if val is None:
        return ""
    return str(val).strip().replace('\r', '').replace('\n', ' ')

def parse_number(val):
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        # Extract first number from string
        m = re.search(r'(\d+(?:\.\d+)?)', str(val))
        if m:
            return float(m.group(1))
    return None

def extract_dimensions_from_desc(desc: str, length_col=None, bb_l=None, bb_w=None, bb_thk=None):
    """
    Extracts (length, width, thk) from description and column fallbacks.
    """
    u_desc = desc.upper()
    l, w, t = None, None, None
    
    # 1. 3D dimension pattern: 50.00 X 50.00 X 3.00
    m3d = re.search(r'(\d+(?:\.\d+)?)\s*[xX*]\s*(\d+(?:\.\d+)?)\s*[xX*]\s*(\d+(?:\.\d+)?)', u_desc)
    if m3d:
        v1, v2, v3 = float(m3d.group(1)), float(m3d.group(2)), float(m3d.group(3))
        # If square pipe or angle
        if "TUBE, SQUARE" in u_desc or "SQ. PIPE" in u_desc or "ANGLE" in u_desc:
            w = v1
            t = v3
            l = parse_number(length_col) or v1
        else:
            # Plate: L x W x Thk
            l, w, t = v1, v2, v3
            
    # 2. DIA pattern: PLATE DIA 100.0 X THK 10.0
    elif "DIA" in u_desc:
        mdia = re.search(r'DIA[- ]*(\d+(?:\.\d+)?)\s*[xX*]\s*(?:THK[- ]*)?(\d+(?:\.\d+)?)', u_desc)
        if mdia:
            d_val = float(mdia.group(1))
            t_val = float(mdia.group(2))
            l, w, t = d_val, d_val, t_val
        else:
            # ROD DIA 30.00x26.00 (Dia x Length)
            mrod = re.search(r'DIA[- ]*(\d+(?:\.\d+)?)(?:[xX*L ]*(\d+(?:\.\d+)?))?', u_desc)
            if mrod:
                d_val = float(mrod.group(1))
                l_val = float(mrod.group(2)) if mrod.group(2) else parse_number(length_col)
                w, t, l = None, d_val, l_val
                
    # 3. Pipe Schedule pattern: O.D 33.4 X SCH-10 X L-662.65
    elif "SCH" in u_desc:
        mod = re.search(r'O\.D\s*(\d+(?:\.\d+)?)', u_desc)
        mlen = re.search(r'L[- ]*(\d+(?:\.\d+)?)', u_desc)
        if mod:
            w = float(mod.group(1))
            t = 2.77 if "SCH-10" in u_desc else 3.38
        if mlen:
            l = float(mlen.group(1))
            
    # 4. Standard Pipe with O.D and THK: PIPE O.D 48.30 X THK-1.65 X L-1030.00
    elif "PIPE" in u_desc and "O.D" in u_desc:
        mod = re.search(r'O\.D\s*(\d+(?:\.\d+)?)', u_desc)
        mthk = re.search(r'THK[- ]*(\d+(?:\.\d+)?)', u_desc)
        mlen = re.search(r'L[- ]*(\d+(?:\.\d+)?)', u_desc)
        if mod:
            w = float(mod.group(1))
        if mthk:
            t = float(mthk.group(1))
        if mlen:
            l = float(mlen.group(1))
            
    # 5. Studs: STUD M24 X L-180
    elif "STUD" in u_desc:
        mstud = re.search(r'M(\d+)(?:[xX*L ]*(\d+))?', u_desc)
        if mstud:
            t = f"M{mstud.group(1)}"
            if mstud.group(2):
                l = float(mstud.group(2))
                
    # Fallback to column values
    if l is None:
        l = parse_number(length_col) or parse_number(bb_l)
    if w is None:
        w = parse_number(bb_w)
    if t is None:
        t = parse_number(bb_thk)
        
    return l, w, t


def parse_solidworks_bom(file_path: str, default_po_qty: int = 1):
    """
    Parses a SolidWorks BOM Excel file and returns detailed BOM rows and metadata.
    """
    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb.active
    
    # Read headers
    bom_header = {
        "bom_date": "",
        "bom_name": "",
        "project_no": "",
        "equipment_name": "",
        "po_qty": default_po_qty,
        "unit": "Nos."
    }
    
    # Extract project number from part numbers if not in header
    for r in range(2, min(ws.max_row + 1, 20)):
        p = clean_str(ws.cell(r, 9).value)
        m_proj = re.search(r'(\d{4}(?:-\d{2})?)', p)
        if m_proj:
            found_proj = m_proj.group(1)
            if "-" not in found_proj:
                found_proj += "-01"
            bom_header["project_no"] = found_proj
            break
                
    current_dwg_no = ""
    current_parent_assembly = ""
    bom_items = []
    sn = 1
    
    for r in range(2, ws.max_row + 1):
        pnum_raw = ws.cell(r, 9).value # Column 9: PART NUMBER
        desc_raw = ws.cell(r, 11).value # Column 11: DESCRIPTION
        l_col = ws.cell(r, 12).value # LENGTH
        bb_l = ws.cell(r, 13).value
        bb_w = ws.cell(r, 14).value
        bb_thk = ws.cell(r, 15).value
        mat_col = ws.cell(r, 16).value # MATERIAL
        qty_col = ws.cell(r, 17).value # QTY
        
        if not desc_raw and not pnum_raw:
            continue
            
        desc = clean_str(desc_raw)
        pnum_str = str(pnum_raw) if pnum_raw is not None else ""
        pnum_clean = clean_str(pnum_raw)
        moc = clean_str(mat_col) or "AISI 304"
        if "NOT SPECIFIED" in moc.upper():
            moc = "AISI 304"
            
        qty = parse_number(qty_col) or 1.0
        
        # Hierarchy check via indentation spaces in PART NUMBER
        # 0 spaces = top assembly
        # 2 spaces = subassembly / part dwg no
        # 4+ spaces = cut pieces / child components
        is_subassembly = pnum_str.startswith("  ") and not pnum_str.startswith("    ")
        is_top_assembly = not pnum_str.startswith(" ") and bool(pnum_clean)
        
        if is_top_assembly:
            current_parent_assembly = pnum_clean
            if not current_dwg_no:
                current_dwg_no = pnum_clean
            # Skip assembly itself from cut-piece line items if it has sub-components
            if "ASSY" in pnum_clean.upper():
                continue
                
        elif is_subassembly:
            # Subassembly or bought out part at level 1
            current_dwg_no = pnum_clean
            # If it's a bought out part like CASTOR WHEEL, include it directly
            if not any(k in pnum_clean.upper() for k in ["PRT", "ASSY"]):
                pass # Include as BOM item
            elif "PRT" in pnum_clean.upper() and ("ASSY" in desc.upper() or "FRAME" in desc.upper()):
                # It is a fabrication drawing header, wait for child cut pieces
                continue
                
        # Extract dimensions
        l_val, w_val, t_val = extract_dimensions_from_desc(desc, l_col, bb_l, bb_w, bb_thk)
        
        # Classify Type of RM
        rm_type = classify_rm_type(desc, pnum_clean, moc)
        
        # Match Item Code
        item_code = match_item_code(rm_type, desc, t_val, w_val, l_val, moc)
        
        # Unit Weight calculation
        unit_wt = calculate_item_weight(rm_type, l_val, w_val, t_val, moc, item_code, desc)
        
        # Total Weight = Unit Weight * Unit Qty * P.O Qty
        tot_wt = round(unit_wt * qty * bom_header["po_qty"], 3) if unit_wt > 0 else (qty if rm_type in ["Raw Material-FASTENER", "Raw Material-BOP"] else 0.0)
        
        # Unit field
        unit = "Kg" if unit_wt > 0 else ("No." if rm_type in ["Raw Material-FASTENER", "Raw Material-BOP"] else "Nos.")
        
        bom_items.append({
            "idx": sn,
            "category": "C",
            "rm_type": rm_type,
            "dwg_no": current_dwg_no or pnum_clean,
            "item_code": item_code,
            "description": desc,
            "length": l_val,
            "width": w_val,
            "thk": t_val,
            "unit_qty": qty,
            "unit_weight": unit_wt if unit_wt > 0 else None,
            "total_weight": tot_wt,
            "moc": moc,
            "unit": unit,
            "remarks": l_val if rm_type in ["Raw Material-SQ PIPE", "Raw Material-PIPE", "Raw Material-ISA ANGLE", "Raw Material-ROD"] else None
        })
        sn += 1
        
    return bom_header, bom_items
