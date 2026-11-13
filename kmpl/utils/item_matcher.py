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
    DWG_REF_PATH = frappe.get_app_path("kmpl", "data", "kmpl_drawing_reference.json")
else:
    MASTER_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "kmpl_master_data.json")
    DWG_REF_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "kmpl_drawing_reference.json")

MASTER_BOP = {}
MASTER_FASTENERS = {}
MASTER_SHEETS = {}
MASTER_RM = {}
DWG_REF_MAP = {}

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

if os.path.exists(DWG_REF_PATH):
    try:
        with open(DWG_REF_PATH, "r", encoding="utf-8") as f:
            _raw_dwg = json.load(f)
            for k, v in _raw_dwg.items():
                ck = re.sub(r'[^A-Za-z0-9]', '', str(k)).upper()
                DWG_REF_MAP[ck] = v
    except Exception as e:
        print(f"Warning: could not load {DWG_REF_PATH}: {e}")

def lookup_drawing_reference(dwg_name: str) -> dict:
    """Looks up verified flat cutting dimensions and item details from Drawing Reference Master."""
    if not dwg_name:
        return None
    ck = re.sub(r'[^A-Za-z0-9]', '', str(dwg_name)).upper()
    if ck in DWG_REF_MAP:
        return DWG_REF_MAP[ck]
    for k, v in DWG_REF_MAP.items():
        if ck in k or k in ck:
            return v
    if "MIRROR" in ck:
        ck_clean = ck.replace("MIRROR", "")
        for k, v in DWG_REF_MAP.items():
            if ck_clean in k or k in ck_clean:
                return v
    return None

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
    "RM-SS14X1500M": 505.89,
    "RM-SS15X3000M": 542.03,
    "RM-SS16X1500M": 578.16,
    "RM-SS20X1500M": 722.70,
    "RM-SS25X1500M": 903.38,
    "RM-SS28X1500M": 1011.78,
    "RM-SS30X1500M": 1084.05,
    "RM-SS32X1500M": 1156.32,
    "RM-SS35X1500M": 1264.73,
    "RM-SS40X1500M": 1445.40,
    "RM-SS45X1500M": 1626.08,
    "RM-SS50X1500M": 1806.75,
    "RM-MS3MMX1500MM": 105.98,
    "RM-MS8X1500M": 282.60,
    "RM-MS10X1500M": 353.25,
    "RM-MS12X1500M": 423.90,
    "RM-MS15X1500M": 529.88,
    "RM-MS16X1500M": 565.20,
    "RM-MS20X1500M": 706.50,
    "RM-MS25X1500M": 883.13,
    "RM-MS38X1500M": 1342.35,
    "RM-REDSIS1200X3M": 10.98,
    "RM-US5X1220M": 14.13,
    "RM-PS2440X1220X5MM": 17.86,
    "RM-TS3X1000M": 6.60
}

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

# Direct lookup dictionary for known BOP items
BOP_CATALOG = {
    "CASTOR WHEEL": "HW-TWWB42140K",
    "CASTOR WHEEL WITH BRAKE": "HW-TWWB42140K",
    "CASTOR WHEEL WITHOUT BRAKE": "HW-TWWOB42140K",
    "KARMIC 4 INCH": "HW-TWWB42140K",
    "GLAND PG11": "ECO-CAGLANDPG11",
    "GLAND PG16": "ECO-CAGLANDPG16",
    "PG 11": "ECO-CAGLANDPG11",
    "PG 16": "ECO-CAGLANDPG16",
    "CABLE GLAND PG11": "ECO-CAGLANDPG11",
    "CABLE GLAND PG16": "ECO-CAGLANDPG16",
    "33108": "BE-TR33108",
    "33207": "BE-TR33207",
    "UCP 206": "BE-CP206NT",
    "UCP 209": "BE-CP209NT",
    "KM 7": "BE-KM7",
    "KM7": "BE-KM7",
    "MB 7": "F-BELOCKNUTMB7",
    "MB7": "F-BELOCKNUTMB7",
    "LOCK NUT MB7": "F-BELOCKNUTMB7",
    "LOCKING DEVICE": "F-BELOCKNUTMB7",
    "45X75X10": "RB-S45X75X10HMS5RG",
    "45X55X7": "RB-S45X55X7HMS5RG",
    "33X50X6": "RB-S33X50X6M",
    "100X120X10": "RB-S100X120X10HMS5RG",
    "RUBBER GASKET 1/4 BSP": "RB-1/4\"BSP",
    "OIL LEVEL INDICATOR": "RB-1/4\"BSP",
    "BALL VALVE 1-1/2": "V-BV1-1/2\"3PC",
    "1.5 INCH 3 PIECE BALL VALVE": "V-BV1-1/2\"3PC",
    "BALL VALVE 1": "FT-BV1\"3P",
    "1 INCH 3 PIECE BALL VALVE": "FT-BV1\"3P",
    "GEARMOTOR": "GM-W751.1KW31R",
    "W75": "GM-W751.1KW31R",
    "MOTOR ASSY": "GM-W751.1KW31R",
    "SPROCKET 26T": "SP-MSP26T1\"",
    "26SB75": "SP-MSP26T1\"",
    "16B-2": "SP-MSP26T1\"",
    "SPROCKET 13T": "SP-MSDS13TP1I",
    "SPROCKET 20T": "SP-MSDST20X15.87P",
    "PRT_2526_01_01_044": "SP-MSDST20X15.87P",
    "PRT_2526_01_01_043": "SP-MSDST20X15.87P",
    "PUMP": "PU-VLCLASSIV-XI-2-0223087",
    "PIAB": "PU-VLCLASSIV-XI-2-0223087",
    "PRESSURE GAUGE": "PN-GAUGE100MMD0.5",
    "PRESSURE GUAGE": "PN-GAUGE100MMD0.5",
    "FILTER REGULATOR AW4004": "PN-AW4004BG01",
    "AW40": "PN-AW4004BG01",
    "AIR REGULATOR": "PN-AW4004BG01",
    "LUBRICATOR AFJ4004": "PN-AFJ4004B5T",
    "AFJ40": "PN-AFJ4004B5T",
    "AIR FILTER": "PN-AFJ4004B5T",
    "FITTING KQ2H": "PN-KQ2H1204AS",
    "KQ2H": "PN-KQ2H1204AS",
    "PU PIPE 12": "PN-PP12M",
    "PU PIPE": "PN-PP12M",
    "PU PNEUMATIC PIPE": "PN-PP12M",
    "PVC HOSE 1": "H-PBFP01\"",
    "FLEXIBLE PIPE": "H-PBFP01\"",
    "HOSE CLAMP 1": "FT-HCLAMP1\"",
    "HOSE AND TUBE CLAMP": "FT-HCLAMP1\"",
    "LONG RADIUS BEND 33.4": "FT-LRB33.4",
    "LRB 90D 1\"": "FT-LRB33.4",
    "45D LONG RADIUS BEND O.D 33.4": "FT-LRB33.4",
    "90D LONG RADIUS BEND O.D 33.4": "FT-LRB33.4",
    "90D BEND OD 101.6": "FT-B101.6X2.1TH",
    "BEND OD 101.6": "FT-B101.6X2.1TH",
    "SMS UNION 101": "FT-SUM101.6M",
    "SUM PIPE 101.6": "FT-SUM101.6M",
    "CAP SEAL 30": "CAP-MSEAL30MM",
    "CAP SEAL 45": "CAP-MSEAL45MM",
    "MECHANICAL SEAL": "CAP-MSEAL30MM",
    "DUPLEX CHAIN": "SF-DC1",
    "1\" PITCH DUPLEX CHAIN": "SF-DC1"
}


def classify_rm_type(desc: str, pnum: str = "", moc: str = "") -> str:
    """Classifies a SolidWorks item into a standard Type of RM."""
    u_desc = (desc or "").upper()
    u_pnum = (pnum or "").upper()
    u_moc = (moc or "").upper()
    combined = f"{u_pnum} {u_desc}"
    
    # 1. Fasteners
    if any(k in combined for k in [
        "BOLT", "NUT", "WASHER", "STUD", "GRUB SCREW", "GURB SCREW",
        "ALLEN CAP", "CSK", "COUNTERSUNK", "BUTTON HEAD", "SCREW"
    ]):
        if "LEVELING BOLT" not in combined and "MOTOR TILTING" not in combined and "SCREW-CLOCKWISE" not in combined and "SCREW-ANTICLOCK" not in combined:
            return "Raw Material-FASTENER"
        if any(k in combined for k in ["STUD M", "HEX NUT", "PLAIN WASHER", "SPRING WASHER"]):
            return "Raw Material-FASTENER"
        
    # 2. Square pipes
    if any(k in combined for k in ["TUBE, SQUARE", "SQ. PIPE", "SQUARE TUBE", "SQ PIPE"]):
        return "Raw Material-SQ PIPE"
        
    # 3. Angle
    if "ANGLE" in combined or "ISA ANGLE" in combined:
        return "Raw Material-ISA ANGLE"
        
    # 4. Round Pipes
    if "ROUND PIPE" in combined or "PIPE O.D" in combined or ("PIPE" in combined and "SQ" not in combined and "TUBE" not in combined and "PU" not in combined):
        return "Raw Material-PIPE"
        
    # 5. Rods / Round bars
    if any(k in combined or k in u_moc for k in ["BRASS", "UHMW", "UHMWPE", "TEFLON", "PTFE"]):
        if "PLATE" not in combined and "SHEET" not in combined:
            return "Raw Material-ROD"

    if "ROD" in combined or "ROUND BAR" in combined or "ROUND DIA" in combined or "ROUND  DIA" in combined or "BRASS BUSH" in combined or "SCREW-CLOCKWISE" in combined or "SCREW-ANTICLOCK" in combined:
        return "Raw Material-ROD"
        
    # 6. Square Bars
    if "SQ. BAR" in combined or "SQUARE BAR" in combined:
        return "Raw Material-SQ BAR"
        
    # 7. Blocks
    if "BLOCK" in combined and "BEARING BLOCK" not in combined and "UCP" not in combined:
        return "Raw Material-BLOCK"
        
    # 8. Bought out parts (BOP) - Check before general plate/sheet
    if any(k in combined for k in [
        "BEARING", "CASTOR", "GLAND", "VALVE", "SPROCKET", "MOTOR", "PUMP",
        "GAUGE", "GUAGE", "SEAL", "HOSE", "BEND", "UNION", "CLAMP", "CHAIN",
        "FILTER", "REGULATOR", "LUBRICATOR", "LOCKING DEVICE", "LOCK WASHER", "LOCK NUT",
        "ABRAZADERA", "ENCLOSURE", "PUSH BUTTON", "SWITCH", "INDICATOR"
    ]):
        return "Raw Material-BOP"
        
    # 9. Plates and sheets
    if any(k in combined for k in ["PLATE", "SHEET", "CHECKER SHEET", "END PLATE", "FLANGE", "COVER", "HOPPER"]):
        return "Raw Material-PLATE"
        
    return "Raw Material-PLATE"


def match_item_code(rm_type: str, desc: str, thk: float = None, width: float = None, length: float = None, moc: str = "AISI 304", pnum: str = "") -> str:
    """Derives standard Item Code based on RM Type, dimensions, MOC, commercial stock rounding, and part number."""
    u_desc = (desc or "").upper()
    u_pnum = (pnum or "").upper()
    u_moc = (moc or "").upper()
    combined = re.sub(r'\s+', ' ', f"{u_pnum} {u_desc}").upper()
    is_ms = "MS" in u_moc or "MILD STEEL" in u_moc or "STEEL" in u_moc or "MS" in combined
    
    # 1. BLOCK
    if rm_type == "Raw Material-BLOCK":
        if "233" in combined or (length and abs(length - 233) < 5):
            return "RM-MS233X143X38MM"
        return "RM-MS38X1500M"

    # 2. PLATE
    if rm_type == "Raw Material-PLATE":
        if "CHECKER" in combined or "CHEQUER" in combined:
            if is_ms:
                return "RM-MCS1220X3MM"
            if thk == 5:
                return "RM-SCP51220MM"
            return "RM-SCP31220M"
        if "SILICON" in u_moc or "SILICON" in combined or "REDSIS" in combined:
            return "RM-REDSIS1200X3M"
        if "UHMWPE" in combined or "UHMWPE" in u_moc or "UHMW" in u_moc:
            return "RM-US5X1220M"
        if "POLYCORBONAT" in u_moc or "POLYCARBONAT" in u_moc or "POLYCARBONATE" in combined:
            return "RM-PS2440X1220X5MM"
        if "TEFLON" in combined:
            return "RM-TS3X1000M"
            
        t = thk if thk is not None else None
        if t is None:
            return ""
        t_str = f"{t:g}"
        
        if is_ms:
            if t == 3: return "RM-MS3MMX1500MM"
            return f"RM-MS{t_str}X1500M"
        else:
            if t == 5: return "RM-SS5X1500"
            if t == 15: return "RM-SS15X3000M"
            return f"RM-SS{t_str}X1500M"
            
    # 3. SQUARE PIPE
    elif rm_type == "Raw Material-SQ PIPE":
        w = int(round(width or 50))
        t = int(round(thk or 3))
        return f"RM-SSQP{w}X{t}M"
        
    # 4. ANGLE
    elif rm_type == "Raw Material-ISA ANGLE":
        w = int(round(width or 40))
        t = int(round(thk or 3))
        return f"RM-SA{w}X{t}M"
        
    # 5. ROUND PIPE (Standard Commercial Piping Sizes)
    elif rm_type == "Raw Material-PIPE":
        if "168.3" in combined or (width and abs(width - 168.3) < 1):
            return "RM-P168.3X3.4THK"
        if "73" in combined or (width and abs(width - 73) < 1):
            if is_ms or any(k in combined for k in ["SCH 40", "SCH-40", "THK-4", "THK 4"]):
                return "RM-MRP73X4M"
            return "RM-SRP73X5M"
        if any(k in combined for k in ["48.3", "50.8"]) or (width and abs(width - 48.3) < 3):
            if "1.65" in combined or (thk and abs(thk - 1.65) < 0.1):
                return "RM-SRP48.3X1.65MM"
            return "RM-SRP48X3M"
        if "60" in combined or (width and abs(width - 60) < 1):
            return "RM-SRP60.3X3.91M"
        if "114" in combined or (width and abs(width - 114) < 1):
            return "RM-SRP114X5M"
        if "33.4" in combined or (width and abs(width - 33.4) < 1):
            return "RM-SRP33.4X3M"
        return "RM-SRP33.4X3M"
        
    # 6. ROD (Commercial Raw Stock Rounding)
    elif rm_type == "Raw Material-ROD":
        d = width or thk or 25.0
        
        # Brass rod
        if "BRASS" in u_moc or "BRASS" in combined:
            if d <= 20: return "RM-BR20M"
            elif d <= 55: return "RM-BR55M"
            else: return "RM-BR65M"
            
        # Teflon / PTFE rod
        if any(k in combined or k in u_moc for k in ["TEFLON", "PTFE"]):
            return "RM-TRD65"
            
        # UHMWPE / UHMW rod
        if any(k in combined or k in u_moc for k in ["UHMWPE", "UHMW"]):
            if d <= 55: return "RM-UR55M"
            else: return "RM-UR75M"
            
        # Stainless Steel Rods (Machined Diameter -> Commercial Stock Size)
        if d <= 12: return "RM-SR12M"
        elif d <= 16: return "RM-SR16M"
        elif d <= 20: return "RM-SR20M"
        elif d <= 25: return "RM-SR25M"
        elif d <= 34: return "RM-SR35MM"
        elif d <= 35: return "RM-SR40M"
        elif d <= 40: return "RM-SR45M"
        elif d <= 45: return "RM-SR50M"
        elif d <= 55: return "RM-SR60M"
        elif d <= 70: return "RM-SR75M"
        elif d <= 80: return "RM-SR80M"
        elif d <= 104: return "RM-SR105MM"
        else:
            return f"RM-SR{int(round(d))}M"
            
    # 7. SQUARE BAR
    elif rm_type == "Raw Material-SQ BAR":
        return "RM-SB40M"
        
    # 8. FASTENERS
    elif rm_type == "Raw Material-FASTENER":
        m_match = re.search(r'\b(M\d+)\b', combined)
        m_size = m_match.group(1) if m_match else "M8"
        m_num = m_size[1:]
        
        l_match = re.search(r'(?:L\s*[-=]?\s*|X\s*L?\s*[-=]?\s*)(\d+)', combined)
        l_val = l_match.group(1) if l_match else None
        
        target_code = None
        
        if "NUT" in combined:
            target_code = f"F-HN{m_size}"
        elif "SPRING WASHER" in combined or "SWM" in combined:
            target_code = f"F-SW{m_size}"
        elif "WASHER" in combined or "PWM" in combined:
            target_code = f"F-PW{m_size}"
        elif "STUD" in combined:
            target_code = f"F-ST{m_size}"
        elif any(k in combined for k in ["CSK", "COUNTERSUNK"]):
            target_code = f"F-ALCSKB{m_num}X{l_val}" if l_val else f"F-ALCSKB{m_num}"
        elif any(k in combined for k in ["BUTTON HEAD", "BHB"]):
            target_code = f"F-BHB{m_num}X{l_val}" if l_val else f"F-BHB{m_size}"
        elif any(k in combined for k in ["GRUB", "GURB"]):
            target_code = f"F-GS{m_num}X{l_val}" if l_val else f"F-GS{m_num}"
        elif "HEX" in combined:
            target_code = f"F-HB{m_size}X{l_val}" if l_val else f"F-HB{m_size}"
        else:
            target_code = f"F-ALB{m_size}X{l_val}" if l_val else f"F-ALB{m_size}"
            
        if target_code in MASTER_FASTENERS:
            return target_code
            
        variations = [
            target_code,
            f"F-BHBM{m_num}X{l_val}" if l_val else None,
            f"F-HBM{m_num}X{l_val}" if l_val else None,
            f"F-HB{m_num}X{l_val}" if l_val else None,
            f"F-ALCSKB{m_num}X{l_val}MM" if l_val else None,
            f"F-GS{m_num}X{l_val}M" if l_val else None,
            f"F-STM{m_num}",
            f"F-HNM{m_num}",
            f"F-PWM{m_num}",
            f"F-SWM{m_num}"
        ]
        for var in variations:
            if var and var in MASTER_FASTENERS:
                return var
                
        return target_code
        
    # 9. BOP
    elif rm_type == "Raw Material-BOP":
        if "ABRAZADERA" in combined or ("HOSE" in combined and "CLAMP" in combined):
            return "FT-HCLAMP1\""

        if frappe and hasattr(frappe, "db") and frappe.db:
            try:
                db_item = frappe.db.get_value(
                    "Item",
                    {"custom_design_pattern": ["like", f"%{desc.strip()}%"], "disabled": 0},
                    "name"
                )
                if not db_item:
                    db_item = frappe.db.get_value(
                        "Item",
                        {"item_name": desc.strip(), "disabled": 0},
                        "name"
                    )
                if db_item:
                    return db_item
            except Exception:
                pass

        for k, v in BOP_CATALOG.items():
            if k in combined:
                return v

        if u_desc in MASTER_BOP:
            return MASTER_BOP[u_desc]["code"]
        if u_pnum in MASTER_BOP:
            return MASTER_BOP[u_pnum]["code"]
            
        tokens = [w for w in re.split(r'[\s,\-_/]+', combined) if len(w) > 2 and w not in ["MAKE", "NOS", "FOR", "AND", "TYPE", "PART", "ASSY"]]
        if tokens:
            for m_desc, m_info in MASTER_BOP.items():
                if all(tok in m_desc for tok in tokens):
                    return m_info["code"]
                    
        return ""
        
    return ""


def get_standard_sheet_weight(item_code: str) -> float:
    """Returns standard full sheet weight for plate item codes."""
    if item_code in STD_SHEET_WEIGHTS:
        return STD_SHEET_WEIGHTS[item_code]
    return DEFAULT_SHEET_WEIGHTS.get(item_code, 108.41)
