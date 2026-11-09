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
            w = float(mdia.group(1))
            t = float(mdia.group(2))
            l = w
        else:
            mdia_l = re.search(r'DIA[- ]*(\d+(?:\.\d+)?).*?L[- ]*(\d+(?:\.\d+)?)', u_desc)
            if mdia_l:
                w = float(mdia_l.group(1))
                l = float(mdia_l.group(2))
                t = w
                
    # 3. OD pattern for Pipes/Rods: PIPE O.D 33.40 X 2.77 X L- 25.00
    elif "O.D" in u_desc or "OD" in u_desc:
        mod = re.search(r'O\.?D\.?\s*(\d+(?:\.\d+)?).*?(?:THK|SCH)?\s*(\d+(?:\.\d+)?).*?L[- ]*(\d+(?:\.\d+)?)', u_desc)
        if mod:
            w = float(mod.group(1))
            t = float(mod.group(2))
            l = float(mod.group(3))
        else:
            mod_simple = re.search(r'O\.?D\.?\s*(\d+(?:\.\d+)?).*?L[- ]*(\d+(?:\.\d+)?)', u_desc)
            if mod_simple:
                w = float(mod_simple.group(1))
                l = float(mod_simple.group(2))
                t = w

    # 4. Standard 2D pattern: 40.00x40.00
    elif not l:
        m2d = re.search(r'(\d+(?:\.\d+)?)\s*[xX*]\s*(\d+(?:\.\d+)?)', u_desc)
        if m2d:
            v1, v2 = float(m2d.group(1)), float(m2d.group(2))
            l = v1
            w = v2

    # Column fallbacks if missing
    if not l and length_col:
        l = parse_number(length_col)
    if not l and bb_l:
        l = parse_number(bb_l)
    if not w and bb_w:
        w = parse_number(bb_w)
    if not t and bb_thk:
        t = parse_number(bb_thk)
        
    return l, w, t


def parse_solidworks_bom(file_path: str, default_po_qty: float = 1.0):
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
        wt_col = ws.cell(r, 18).value  # Column 18: Weight(KG)
        
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
        item_code = match_item_code(rm_type, desc, t_val, w_val, l_val, moc, pnum=pnum_clean)
        
        # Unit Weight calculation
        unit_wt = calculate_item_weight(rm_type, l_val, w_val, t_val, moc, item_code, desc)
        
        # Fallback for Sheet Metal items where geometric L/W/T is blank in SolidWorks
        if rm_type == "Raw Material-PLATE" and unit_wt <= 0:
            sw_wt = parse_number(wt_col)
            if sw_wt:
                # SolidWorks exports weight in grams (e.g. 2231.47 g -> 2.231 kg)
                unit_wt = round(sw_wt / 1000.0, 3) if sw_wt > 50 else round(sw_wt, 3)
                if not t_val:
                    t_val = 1.5
                item_code = match_item_code(rm_type, desc, t_val, w_val, l_val, moc, pnum=pnum_clean)
        
        # Total Weight
        if unit_wt > 0 and rm_type not in ["Raw Material-FASTENER", "Raw Material-BOP"]:
            tot_wt = round(unit_wt * qty * bom_header["po_qty"], 3)
            unit = "Kg"
        else:
            tot_wt = qty
            unit = "No." if rm_type in ["Raw Material-FASTENER", "Raw Material-BOP"] else "Nos."
        
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
