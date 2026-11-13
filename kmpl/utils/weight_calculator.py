import math
from collections import defaultdict
from .item_matcher import STD_SHEET_WEIGHTS, WEIGHT_PER_METER

try:
    import frappe
except ImportError:
    frappe = None

SS_DENSITY = 0.00000803  # kg / mm^3 (AISI 304)
MS_DENSITY = 0.00000785  # kg / mm^3 (Mild steel)
PLASTIC_DENSITY = 0.00000100  # kg / mm^3 (Teflon / UHMWPE / Silicon)

def get_density_for_moc(moc: str = "AISI 304", desc: str = "") -> float:
    u_moc = (moc or "").upper()
    u_desc = (desc or "").upper()
    if any(k in u_desc or k in u_moc for k in ["SILICON", "UHMWPE", "TEFLON", "PUR", "PVC"]):
        return PLASTIC_DENSITY
    if "MS" in u_moc or "MILD STEEL" in u_moc:
        return MS_DENSITY
    return SS_DENSITY


def calculate_item_weight(rm_type: str, length: float, width: float, thk: float, moc: str = "AISI 304", item_code: str = "", desc: str = "") -> float:
    """Calculates unit weight in kg based on RM Type, dimensions, and MOC."""
    density = get_density_for_moc(moc, desc)
    
    # 1. Plates & Blocks
    if rm_type in ["Raw Material-PLATE", "Raw Material-BLOCK"]:
        l = length or 0.0
        w = width or 0.0
        t = thk or 0.0
        if l > 0 and w > 0 and t > 0:
            return round(l * w * t * density, 5)
        return 0.0
        
    # 2. Profiles with known weight per meter (Square Pipe, Angle, Round Pipe, Rod, SQ Bar)
    if item_code in WEIGHT_PER_METER and length:
        wt_per_m = WEIGHT_PER_METER[item_code]
        return round((wt_per_m / 1000.0) * length, 5)
        
    # 3. Geometric calculation if profile not in table
    if rm_type == "Raw Material-SQ PIPE" and length and width and thk:
        # Cross sectional area of square tube = (width^2 - (width - 2*thk)^2)
        inner = max(0.0, width - 2 * thk)
        area = (width * width) - (inner * inner)
        return round(area * length * density, 5)
        
    if rm_type == "Raw Material-ROD" and length and (thk or width):
        dia = thk or width
        radius = dia / 2.0
        area = math.pi * radius * radius
        return round(area * length * density, 5)
        
    if rm_type == "Raw Material-PIPE" and length and width and thk:
        # Round pipe area = pi * (od - thk) * thk
        od = width
        area = math.pi * (od - thk) * thk
        return round(area * length * density, 5)

    if rm_type == "Raw Material-SQ BAR" and length:
        w = width or 40.0
        t = thk or w
        return round(w * t * length * density, 4)
        
    if rm_type == "Raw Material-FASTENER" and "STUD" in (desc or "").upper() and length:
        # Stud length in meters
        return round(length / 1000.0, 3)

    return 0.0


def compile_summary(bom_items: list, project_no: str = "") -> list:
    """
    Rolls up detailed BOM items into SUMMARY sheet rows.
    Returns a list of dictionaries for each summary row.
    """
    grouped = defaultdict(lambda: {
        "item_code": "",
        "rm_type": "",
        "desc": "",
        "thk": None,
        "moc": "AISI 304",
        "total_weight": 0.0,
        "total_qty": 0.0,
        "total_length_mm": 0.0,
        "is_plate": False,
        "is_profile": False,
        "is_fastener": False,
        "is_bop": False
    })
    
    for item in bom_items:
        icode = (item.get("item_code") or "").strip()
        if not icode:
            continue
            
        rm_type = item.get("rm_type", "")
        u_qty = float(item.get("unit_qty") or 1)
        tot_wt = float(item.get("total_weight") or 0.0)
        l_mm = float(item.get("length") or 0.0)
        thk = item.get("thk")
        moc = item.get("moc") or "AISI 304"
        desc = item.get("description") or ""
        
        grp = grouped[icode]
        grp["item_code"] = icode
        grp["desc"] = desc
        grp["thk"] = thk or grp["thk"]
        grp["moc"] = moc
        grp["total_weight"] += tot_wt
        grp["total_qty"] += u_qty
        grp["total_length_mm"] += (l_mm * u_qty)
        if item.get("is_manual"):
            grp["is_manual"] = True
        
        is_std_plate = ((icode.startswith("RM-SS") or icode.startswith("RM-MS") or icode.startswith("RM-SCP") or icode.startswith("RM-MCS")) 
                        and "X" in icode 
                        and any(sz in icode for sz in ["1500", "3000", "1220", "2440"]))
        if is_std_plate or rm_type == "Raw Material-PLATE":
            rm_type = "Raw Material-PLATE"
            grp["is_plate"] = True
            grp["is_profile"] = False
            grp["is_fastener"] = False
            grp["is_bop"] = False
            grp["is_block"] = False
        elif rm_type == "Raw Material-BLOCK":
            grp["is_block"] = True
            grp["is_plate"] = False
            grp["is_profile"] = False
            grp["is_fastener"] = False
            grp["is_bop"] = False
        elif rm_type in ["Raw Material-SQ PIPE", "Raw Material-PIPE", "Raw Material-ISA ANGLE", "Raw Material-ROD", "Raw Material-SQ BAR"]:
            grp["is_profile"] = True
        elif rm_type == "Raw Material-FASTENER":
            grp["is_fastener"] = True
        else:
            grp["is_bop"] = True

        if not grp["rm_type"] or rm_type in ["Raw Material-PLATE", "Raw Material-BLOCK"]:
            grp["rm_type"] = rm_type

    summary_rows = []
    sr = 1
    
    for icode, data in grouped.items():
        rm_type = data["rm_type"]
        moc = data["moc"]
        tot_wt = round(data["total_weight"], 2)
        
        # Calculate summary length/qty & unit
        if data["is_plate"]:
            std_sheet_wt = STD_SHEET_WEIGHTS.get(icode, 54.20)
            if frappe and hasattr(frappe, "db") and frappe.db:
                try:
                    db_sh_wt = frappe.db.get_value("Item", icode, "custom_full_sheet_weight")
                    if db_sh_wt:
                        std_sheet_wt = float(db_sh_wt)
                except Exception:
                    pass
            length_qty = round(tot_wt / std_sheet_wt, 3) if std_sheet_wt > 0 else round(tot_wt, 2)
            unit = "No"
            gen_desc = f"{moc} SHEET {data['desc']} X {data['thk'] or ''}".strip()
        elif data.get("is_block"):
            length_qty = int(round(data["total_qty"]))
            unit = "No"
            thk_str = f"X{data['thk']}" if data['thk'] else ""
            gen_desc = f"{moc} BLOCK {thk_str}".strip()
        elif data["is_profile"]:
            length_qty = round(data["total_length_mm"] / 1000.0, 3)
            unit = "m"
            gen_desc = f"{moc} {data['desc']}".strip()
        elif data["is_fastener"]:
            if "STUD" in data["desc"].upper() or "F-ST" in icode:
                length_qty = round(data["total_length_mm"] / 1000.0, 3)
                unit = "Mtr"
            else:
                length_qty = int(round(data["total_qty"]))
                unit = "No."
            gen_desc = f"{data['desc']} {moc}".strip()
        else:
            # BOP
            length_qty = int(round(data["total_qty"]))
            unit = "No."
            gen_desc = data["desc"]

        is_man = data.get("is_manual", False)
        if is_man:
            gen_desc = f"{gen_desc} [Manually Added (Not in 3D CAD)]".strip()

        summary_rows.append({
            "idx": sr,
            "project_no": project_no,
            "category": "C",
            "item_code": icode,
            "rm_type": rm_type,
            "description": data["desc"],
            "thk_mm": data["thk"],
            "weight_kg": tot_wt if tot_wt > 0 else None,
            "unit_weight": "Kg" if tot_wt > 0 else None,
            "general_description": gen_desc,
            "length_qty": length_qty,
            "unit": unit,
            "moc": moc,
            "is_manual": is_man
        })
        sr += 1
        
    return summary_rows
