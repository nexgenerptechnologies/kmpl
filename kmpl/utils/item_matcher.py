import os
import json
import re

try:
    import frappe
except ImportError:
    frappe = None

# Load complete master catalog from JSON (3,911 BOP, 536 Fasteners, 170 Sheet codes, 532 RM items)
if frappe and hasattr(frappe, "get_app_path"):
    MASTER_DATA_PATH = frappe.get_app_path("kmpl", "data", "kmpl_master_data.json")
else:
    MASTER_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "kmpl_master_data.json")

MASTER_BOP = {}
MASTER_FASTENERS = {}
MASTER_SHEETS = {}
MASTER_RM = {}

if os.path.exists(MASTER_DATA_PATH):
    try:
        with open(MASTER_DATA_PATH, "r", encoding="utf-8") as f:
            _raw = json.load(f)
            MASTER_BOP = _raw.get("bop_items", {})
            MASTER_FASTENERS = _raw.get("fasteners", {})
            MASTER_SHEETS = _raw.get("sheet_codes", {})
            MASTER_RM = _raw.get("rm_items", {})
    except Exception as e:
        print(f"Warning: could not load {MASTER_DATA_PATH}: {e}")

# Build dynamic standard sheet weights from master sheet codes
STD_SHEET_WEIGHTS = {}
for code, data in MASTER_SHEETS.items():
    if data.get("full_sheet_weight"):
        STD_SHEET_WEIGHTS[code] = data["full_sheet_weight"]

# Fallback defaults if not in master
DEFAULT_SHEET_WEIGHTS = {
    "RM-SS0.5X1500MM": 18.07,
    "RM-SS1X1500M": 36.14,
    "RM-SS1.2X1500M": 43.36,
    "RM-SS1.5X1500M": 54.20,
    "RM-SS2X1500M": 72.27,
    "RM-SS2.5X1500M": 90.34,
    "RM-SS3X1500M": 108.41,
    "RM-SS4X1500M": 144.54,
    "RM-SS5X1500": 180.68,
    "RM-SS6X1500M": 216.81,
    "RM-SS8X1500M": 289.08,
    "RM-SS10X1500M": 361.35,
    "RM-SS12X1500M": 433.62,
    "RM-SS15X3000M": 542.03,
    "RM-SS16X1500M": 578.16,
    "RM-SS20X1500M": 722.70,
    "RM-SS25X1500M": 903.38,
    "RM-MS3MMX1500MM": 105.98,
    "RM-MS8X1500M": 282.60,
    "RM-MS10X1500M": 353.25,
    "RM-MS12X1500M": 423.90,
    "RM-MS15X1500M": 529.88,
    "RM-MS20X1500M": 706.50,
    "RM-MS25X1500M": 883.13,
    "RM-REDSIS1200X3M": 8.93,
    "RM-US5X1220M": 14.88,
    "RM-PS2440X1220X5MM": 14.88,
    "RM-TS2X1000M": 4.40,
    "RM-TS3X1000M": 6.60,
    "RM-TS5X1000M": 11.00
}
for k, v in DEFAULT_SHEET_WEIGHTS.items():
    if k not in STD_SHEET_WEIGHTS:
        STD_SHEET_WEIGHTS[k] = v

# Standard weights per meter (kg/m) for profile items
WEIGHT_PER_METER = {
    # Square pipes
    "RM-SSQP30X3M": 2.69,
    "RM-SSQP40X3M": 3.49,
    "RM-SSQP50X3M": 4.12,
    
    # Angles
    "RM-SA40X3M": 1.80,
    
    # Round pipes
    "RM-SRP33.4X3M": 2.13,
    "RM-SRP48.3X1.65MM": 1.95,
    "RM-SRP48X3M": 3.11,
    "RM-SRP60.3X3.91M": 4.31,
    "RM-SRP73X5M": 8.75,
    "RM-MRP73X4M": 6.80,
    "RM-SRP114X5M": 12.18,
    "RM-P168.3X3.4THK": 13.85,
    
    # Round bars / rods (density based or standard kg/m)
    "RM-SR12M": 0.908,
    "RM-SR16M": 1.60,
    "RM-SR20M": 2.53,
    "RM-SR25M": 3.95,
    "RM-SR35MM": 5.70,
    "RM-SR40M": 10.10,
    "RM-SR45M": 12.80,
    "RM-SR50M": 15.80,
    "RM-SR60M": 22.75,
    "RM-SR75M": 35.55,
    "RM-SR80M": 40.40,
    "RM-SR105MM": 69.90,
    
    # Bronze / UHMWPE / Teflon rods
    "RM-BR20M": 2.70,
    "RM-BR55M": 20.40,
    "RM-BR65M": 28.50,
    "RM-TRD65": 7.30,
    "RM-UR55M": 2.30,
    "RM-UR75M": 4.30,
    
    # Square bar
    "RM-SB40M": 12.85
}

# Known BOP dictionary mapping normalized search strings to Item Codes
BOP_CATALOG = {
    "CASTOR WHEEL": "HW-TWWB42140K",
    "CASTOR WHEEL WITH BRAKE": "HW-TWWB42140K",
    "CASTOR WHEEL WITHOUT BRAKE": "HW-TWWOB42140K",
    "KARMIC 4 INCH": "HW-TWWB42140K",
    "GLAND PG11": "ECO-CAGLANDPG11",
    "GLAND PG16": "ECO-CAGLANDPG16",
    "CABLE GLAND PG11": "ECO-CAGLANDPG11",
    "CABLE GLAND PG16": "ECO-CAGLANDPG16",
    "BEARING 33108": "BE-TR33108",
    "BEARING 33207": "BE-TR33207",
    "BEARING UCP 206": "BE-CP206NT",
    "BEARING UCP 209": "BE-CP209NT",
    "BEARING KM7": "BE-KM7",
    "LOCK NUT MB7": "F-BELOCKNUTMB7",
    "OIL SEAL 45X75X10": "RB-S45X75X10HMS5RG",
    "OIL SEAL 45X55X7": "RB-S45X55X7HMS5RG",
    "OIL SEAL 33X50X6": "RB-S33X50X6M",
    "RUBBER GASKET 1/4 BSP": "RB-1/4\"BSP",
    "BALL VALVE 1-1/2": "V-BV1-1/2\"3PC",
    "BALL VALVE 1": "FT-BV1\"3P",
    "GEARMOTOR": "GM-W751.1KW31R",
    "SPROCKET 26T": "SP-MSP26T1\"",
    "SPROCKET 13T": "SP-MSDS13TP1I",
    "SPROCKET 20T": "SP-MSDST20X15.87P",
    "PUMP": "PU-VLCLASSIV-XI-2-0223087",
    "PRESSURE GAUGE": "PN-GAUGE100MMD0.5",
    "FILTER REGULATOR AW4004": "PN-AW4004BG01",
    "LUBRICATOR AFJ4004": "PN-AFJ4004B5T",
    "FITTING KQ2H": "PN-KQ2H1204AS",
    "PU PIPE 12": "PN-PP12M",
    "PVC HOSE 1": "H-PBFP01\"",
    "HOSE CLAMP 1": "FT-HCLAMP1\"",
    "LONG RADIUS BEND 33.4": "FT-LRB33.4",
    "BEND 101.6": "FT-B101.6X2.1TH",
    "SUM PIPE 101.6": "FT-SUM101.6M",
    "CAP SEAL 30": "CAP-MSEAL30MM",
    "CAP SEAL 45": "CAP-MSEAL45MM",
    "DUST CAP": "SF-DC1"
}


def classify_rm_type(desc: str, pnum: str = "", moc: str = "") -> str:
    """Classifies a SolidWorks item into a standard Type of RM."""
    u_desc = (desc or "").upper()
    u_pnum = (pnum or "").upper()
    
    # 1. Fasteners
    if any(k in u_desc for k in ["BOLT", "NUT", "WASHER", "STUD", "GRUB SCREW", "ALLEN CAP", "CSK", "SCREW"]):
        if "LEVELING BOLT" not in u_desc and "MOTOR TILTING" not in u_desc:
            return "Raw Material-FASTENER"
        
    # 2. Square pipes
    if "TUBE, SQUARE" in u_desc or "SQ. PIPE" in u_desc or "SQUARE TUBE" in u_desc or "SQ PIPE" in u_desc:
        return "Raw Material-SQ PIPE"
        
    # 3. Angle
    if "ANGLE" in u_desc or "ISA ANGLE" in u_desc:
        return "Raw Material-ISA ANGLE"
        
    # 4. Round Pipes
    if "ROUND PIPE" in u_desc or "PIPE O.D" in u_desc or ("PIPE" in u_desc and "SQ" not in u_desc and "TUBE" not in u_desc):
        return "Raw Material-PIPE"
        
    # 5. Rods / Round bars
    if "ROD" in u_desc or "ROUND BAR" in u_desc:
        return "Raw Material-ROD"
        
    # 6. Square Bars
    if "SQ. BAR" in u_desc or "SQUARE BAR" in u_desc:
        return "Raw Material-SQ BAR"
        
    # 7. Blocks
    if "BLOCK" in u_desc:
        return "Raw Material-BLOCK"
        
    # 8. Plates and sheets
    if any(k in u_desc for k in ["PLATE", "SHEET", "CHECKER SHEET", "END PLATE", "FLANGE", "COVER"]):
        return "Raw Material-PLATE"
        
    # 9. Bought out parts (BOP)
    if any(k in u_desc for k in ["BEARING", "CASTOR", "GLAND", "VALVE", "SPROCKET", "MOTOR", "PUMP", "GAUGE", "SEAL", "HOSE"]):
        return "Raw Material-BOP"
    if any(k in u_pnum for k in ["CASTOR", "GLAND", "VALVE", "BEARING"]):
        return "Raw Material-BOP"
        
    return "Raw Material-PLATE"


def match_item_code(rm_type: str, desc: str, thk: float = None, width: float = None, length: float = None, moc: str = "AISI 304") -> str:
    """Derives standard Item Code based on RM Type, dimensions, and MOC."""
    u_desc = (desc or "").upper()
    u_moc = (moc or "").upper()
    is_ms = "MS" in u_moc or "MILD STEEL" in u_moc or "MS" in u_desc
    
    # 1. PLATE
    if rm_type in ["Raw Material-PLATE", "Raw Material-BLOCK"]:
        # Check special materials
        if "REDSIS" in u_desc or "SILICON" in u_desc:
            return "RM-REDSIS1200X3M"
        if "UHMWPE" in u_desc:
            return "RM-US5X1220M"
        if "POLYCARBONATE" in u_desc or "ACRYLIC" in u_desc:
            return "RM-PS2440X1220X5MM"
        if "TEFLON" in u_desc:
            t = int(round(thk or 3))
            return f"RM-TS{t}X1000M"
            
        # Standard metal plate
        t = thk if thk is not None else 3.0
        # Format thickness string
        t_str = f"{t:g}"
        
        if is_ms:
            if t == 3:
                return "RM-MS3MMX1500MM"
            return f"RM-MS{t_str}X1500M"
        else:
            if t == 5:
                return "RM-SS5X1500"
            if t == 15:
                return "RM-SS15X3000M"
            return f"RM-SS{t_str}X1500M"
            
    # 2. SQUARE PIPE
    elif rm_type == "Raw Material-SQ PIPE":
        w = int(round(width or 50))
        t = int(round(thk or 3))
        return f"RM-SSQP{w}X{t}M"
        
    # 3. ANGLE
    elif rm_type == "Raw Material-ISA ANGLE":
        w = int(round(width or 40))
        t = int(round(thk or 3))
        return f"RM-SA{w}X{t}M"
        
    # 4. ROUND PIPE
    elif rm_type == "Raw Material-PIPE":
        if width:
            od_str = f"{width:g}"
            if thk:
                t_str = f"{thk:g}"
                if is_ms:
                    return f"RM-MRP{od_str}X{t_str}M"
                if t_str == "1.65":
                    return f"RM-SRP{od_str}X1.65MM"
                return f"RM-SRP{od_str}X{t_str}M"
            return f"RM-SRP{od_str}X3M"
        return "RM-SRP33.4X3M"
        
    # 5. ROD (Round Bar)
    elif rm_type == "Raw Material-ROD":
        dia = int(round(thk or width or 25))
        if "BRONZE" in u_desc or "BR" in u_desc:
            return f"RM-BR{dia}M"
        if "TEFLON" in u_desc:
            return f"RM-TRD{dia}"
        if "UHMWPE" in u_desc:
            return f"RM-UR{dia}M"
        if dia == 35 or dia == 30:
            return "RM-SR35MM"
        if dia == 105:
            return "RM-SR105MM"
        return f"RM-SR{dia}M"
        
    # 6. SQUARE BAR
    elif rm_type == "Raw Material-SQ BAR":
        w = int(round(width or 40))
        return f"RM-SB{w}M"
        
    # 7. FASTENER
    elif rm_type == "Raw Material-FASTENER":
        # Extract thread size
        m_match = re.search(r'M(\d+)', u_desc)
        m_size = f"M{m_match.group(1)}" if m_match else "M6"
        
        # Extract length if bolt or stud
        l_match = re.search(r'[X\s](\d+)(?:MM|L|$)', u_desc)
        l_val = l_match.group(1) if l_match else ""
        
        target_code = ""
        if "STUD" in u_desc or "THREADED" in u_desc:
            target_code = f"F-ST{m_size}"
        elif "NUT" in u_desc:
            target_code = f"F-HN{m_size}"
        elif "SPRING WASHER" in u_desc:
            target_code = f"F-SW{m_size}"
        elif "WASHER" in u_desc:
            target_code = f"F-PW{m_size}"
        elif "CSK" in u_desc:
            target_code = f"F-ALCSKB{m_size[1:]}X{l_val}MM" if l_val else f"F-ALCSKB{m_size}"
        elif "HEX" in u_desc:
            target_code = f"F-HB{m_size}X{l_val}" if l_val else f"F-HB{m_size}"
        elif "GRUB" in u_desc:
            target_code = f"F-GS{m_size[1:]}X{l_val}" if l_val else f"F-GS{m_size}"
        else:
            target_code = f"F-ALB{m_size}X{l_val}" if l_val else f"F-ALB{m_size}"
            
        # Verify if exists in master fasteners, or find close match
        if target_code in MASTER_FASTENERS:
            return target_code
        # Check without MM or with MM
        alt_code = target_code + "MM" if not target_code.endswith("MM") else target_code[:-2]
        if alt_code in MASTER_FASTENERS:
            return alt_code
        return target_code
        
    # 8. BOP
    elif rm_type == "Raw Material-BOP":
        # Check live ERPNext database first (if any item was added via UI)
        if frappe and hasattr(frappe, "db") and frappe.db:
            try:
                db_code = frappe.db.get_value("KMPL BOP Master", {"item_name_description": ["like", f"%{desc.strip()}%"]}, "item_code")
                if db_code:
                    return db_code
            except Exception:
                pass

        # Direct exact match in 3,911 Master BOP catalog
        if u_desc in MASTER_BOP:
            return MASTER_BOP[u_desc]["code"]
            
        # Check known BOP dictionary
        for k, v in BOP_CATALOG.items():
            if k in u_desc:
                return v
                
        # Token-based search in 3,911 Master BOP items
        tokens = [w for w in re.split(r'[\s,\-_/]+', u_desc) if len(w) > 2 and w not in ["MAKE", "NOS", "FOR", "AND", "TYPE"]]
        if tokens:
            for m_desc, m_info in MASTER_BOP.items():
                if all(tok in m_desc for tok in tokens):
                    return m_info["code"]
            # Partial match with high relevance
            for m_desc, m_info in MASTER_BOP.items():
                match_count = sum(1 for tok in tokens if tok in m_desc)
                if match_count >= 2 and match_count >= len(tokens) - 1:
                    return m_info["code"]

        return "BOP-STD"

    return "RM-STD"
