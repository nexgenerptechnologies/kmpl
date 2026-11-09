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
    Normalizes broken numbers with whitespace (e.g., 155.0 0 -> 155.00).
    """
    u_desc = desc.upper()
    u_desc = re.sub(r'(\d+)\s*\.\s*(\d+)', r'\1.\2', u_desc)
    u_desc = re.sub(r'(\d+\.\d+)\s+(\d+)', r'\1\2', u_desc)
    
    l, w, t = None, None, None
    
    # 1. 3D dimension pattern: 50.00 X 50.00 X 3.00
    m3d = re.search(r'(\d+(?:\.\d+)?)\s*[xX*]\s*(\d+(?:\.\d+)?)\s*[xX*]\s*(\d+(?:\.\d+)?)', u_desc)
    if m3d:
        v1, v2, v3 = float(m3d.group(1)), float(m3d.group(2)), float(m3d.group(3))
        if "TUBE, SQUARE" in u_desc or "SQ. PIPE" in u_desc or "ANGLE" in u_desc:
            w = v1
            t = v3
            l = parse_number(length_col) or v1
        else:
            l, w, t = v1, v2, v3
            
    # 2. DIA pattern: PLATE DIA 100.0 X THK 10.0 or ROUND DIA75.00x20.00 or ROD DIA 16.00
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
            else:
                mdia_single = re.search(r'DIA[- ]*(\d+(?:\.\d+)?)', u_desc)
                if mdia_single:
                    w = float(mdia_single.group(1))
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
    Implements intelligent row collapsing for fabrication parts and precise RM assignment.
    """
    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb.active
    sw_rows = list(ws.iter_rows(values_only=True))
    
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
    for r in range(1, min(len(sw_rows), 25)):
        p = clean_str(sw_rows[r][8])
        m_proj = re.search(r'(\d{4}(?:-\d{2})?)', p)
        if m_proj:
            found_proj = m_proj.group(1)
            if "-" not in found_proj:
                found_proj += "-01"
            bom_header["project_no"] = found_proj
            break
                
    # Pre-scan rows to detect which part drawings have child cut-pieces below them
    has_cut_pieces = {}
    for i in range(1, len(sw_rows)):
        pnum_clean = clean_str(sw_rows[i][8])
        next_pnum_clean = clean_str(sw_rows[i+1][8]) if i+1 < len(sw_rows) else "END"
        has_cut_pieces[i] = (bool(pnum_clean) and not bool(next_pnum_clean))

    current_dwg_no = ""
    parent_qty = 1.0
    bom_items = []
    sn = 1
    
    for r in range(1, len(sw_rows)):
        row = sw_rows[r]
        pnum_raw = row[8]
        desc_raw = row[10]
        l_col = row[11]
        bb_l = row[12]
        bb_w = row[13]
        bb_thk = row[14]
        mat_col = row[15]
        qty_col = row[16]
        wt_col = row[17]
        
        if not desc_raw and not pnum_raw:
            continue
            
        pnum_clean = clean_str(pnum_raw)
        desc = clean_str(desc_raw)
        moc = clean_str(mat_col) or "AISI 304"
        if "NOT SPECIFIED" in moc.upper():
            moc = "AISI 304"
            
        qty = parse_number(qty_col) or 1.0
        combined = re.sub(r'\s+', ' ', f"{pnum_clean} {desc}").upper()
        
        # Skip top-level assembly headers (e.g. LEG FRAME ASSY, GEAR BOX ASSY, etc.)
        if "ASSY" in pnum_clean.upper() and ("ASSY" in desc.upper() or not desc or "FRAME" in desc.upper() or "GEAR BOX" in desc.upper()):
            continue
            
        # Check if this row is a part header with child cut-pieces below it
        if pnum_clean and has_cut_pieces.get(r, False):
            current_dwg_no = pnum_clean
            parent_qty = qty
            continue
            
        # Determine actual drawing number and quantity
        if not pnum_clean:
            actual_dwg = current_dwg_no
            actual_qty = qty * parent_qty
        else:
            actual_dwg = pnum_clean
            actual_qty = qty
            current_dwg_no = pnum_clean
            parent_qty = 1.0
            
        # Extract dimensions
        l_val, w_val, t_val = extract_dimensions_from_desc(desc, l_col, bb_l, bb_w, bb_thk)
        
        # Classify Type of RM
        rm_type = classify_rm_type(desc, pnum_clean, moc)
        
        # Match Item Code
        item_code = match_item_code(rm_type, desc, t_val, w_val, l_val, moc, pnum=pnum_clean)
        
        # Specific overrides for known hardware / fittings
        if "OIL LEVEL" in combined:
            rm_type = "Raw Material-BOP"
            item_code = "RB-1/4\"BSP"
        elif "1.5 INCH" in combined or "1-1/2" in combined:
            if "VALVE" in combined:
                rm_type = "Raw Material-BOP"
                item_code = "V-BV1-1/2\"3PC"
        elif "1 INCH" in combined or '1"' in combined:
            if "VALVE" in combined:
                rm_type = "Raw Material-BOP"
                item_code = "FT-BV1\"3P"
        elif any(k in combined for k in ["LRB 90D", "45D LONG RADIUS BEND", "90D LONG RADIUS BEND"]) or ("BEND" in combined and "33.4" in combined):
            rm_type = "Raw Material-BOP"
            item_code = "FT-LRB33.4"
        elif "90D BEND" in combined and "101.6" in combined:
            rm_type = "Raw Material-BOP"
            item_code = "FT-B101.6X2.1TH"
        elif "SMS UNION" in combined:
            rm_type = "Raw Material-BOP"
            item_code = "FT-SUM101.6M"
        elif "HOSE" in combined and "CLAMP" in combined:
            rm_type = "Raw Material-BOP"
            item_code = "FT-HCLAMP1\""
        elif "FLEXIBLE PIPE" in combined:
            rm_type = "Raw Material-BOP"
            item_code = "H-PBFP01\""
        elif "PU PIPE" in combined or "PNEUMATIC PU PIPE" in combined:
            rm_type = "Raw Material-BOP"
            item_code = "PN-PP12M"
        elif "KQ2H" in combined:
            rm_type = "Raw Material-BOP"
            item_code = "PN-KQ2H1204AS"
        elif "M16.00X135" in combined:
            rm_type = "Raw Material-FASTENER"
            item_code = "F-STM16"
        elif "KM 7" in combined or "KM7" in combined:
            rm_type = "Raw Material-BOP"
            item_code = "BE-KM7"
        elif "MB 7" in combined or "MB7" in combined:
            rm_type = "Raw Material-BOP"
            item_code = "F-BELOCKNUTMB7"
            
        # Unit Weight calculation
        unit_wt = calculate_item_weight(rm_type, l_val, w_val, t_val, moc, item_code, desc)
        
        # Fallback for Sheet Metal leaf parts where geometric L/W/T is blank
        if rm_type == "Raw Material-PLATE" and unit_wt <= 0:
            sw_wt = parse_number(wt_col)
            if sw_wt:
                unit_wt = round(sw_wt / 1000.0, 3) # Convert grams to kg
                u_moc = moc.upper()
                if "SILICON" in u_moc or "SILICON" in combined:
                    t_val = 3.0
                    item_code = "RM-REDSIS1200X3M"
                elif "POLYCORBONAT" in u_moc or "POLYCARBONAT" in u_moc:
                    t_val = 5.0
                    item_code = "RM-PS2440X1220X5MM"
                elif any(k in combined for k in ["COVER PLATE", "TOP COVER PLATE", "SUPPORT PLATE"]):
                    t_val = 5.0
                    item_code = "RM-SS5X1500"
                else:
                    t_val = 1.5
                    item_code = "RM-SS1.5X1500M"
                    
        # Total Weight
        if unit_wt > 0 and rm_type not in ["Raw Material-FASTENER", "Raw Material-BOP"]:
            tot_wt = round(unit_wt * actual_qty * bom_header["po_qty"], 3)
            unit = "Kg"
        else:
            tot_wt = actual_qty
            unit = "No." if rm_type in ["Raw Material-FASTENER", "Raw Material-BOP"] else "Nos."
            
        # Handle Castor Wheels: if 4 castors, split 2 with brake and 2 without brake like in original file
        if item_code == "HW-TWWB42140K" and actual_qty == 4.0:
            bom_items.append({
                "idx": sn, "category": "C", "rm_type": rm_type, "dwg_no": actual_dwg,
                "item_code": "HW-TWWB42140K", "description": "CASTOR WHEEL",
                "length": None, "width": None, "thk": None, "unit_qty": 2.0,
                "unit_weight": None, "total_weight": 2.0, "moc": moc, "unit": "No.", "remarks": None
            })
            sn += 1
            bom_items.append({
                "idx": sn, "category": "C", "rm_type": rm_type, "dwg_no": actual_dwg,
                "item_code": "HW-TWWOB42140K", "description": "CASTOR WHEEL",
                "length": None, "width": None, "thk": None, "unit_qty": 2.0,
                "unit_weight": None, "total_weight": 2.0, "moc": moc, "unit": "No.", "remarks": None
            })
            sn += 1
            continue
            
        bom_items.append({
            "idx": sn,
            "category": "C",
            "rm_type": rm_type,
            "dwg_no": actual_dwg,
            "item_code": item_code,
            "description": desc,
            "length": l_val,
            "width": w_val,
            "thk": t_val,
            "unit_qty": actual_qty,
            "unit_weight": unit_wt if unit_wt > 0 else None,
            "total_weight": tot_wt,
            "moc": moc,
            "unit": unit,
            "remarks": l_val if rm_type in ["Raw Material-SQ PIPE", "Raw Material-PIPE", "Raw Material-ISA ANGLE", "Raw Material-ROD"] else None
        })
        sn += 1
        
    return bom_header, bom_items
