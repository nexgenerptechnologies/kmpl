import os
import json
import frappe
from frappe.utils import now_datetime

def execute():
    """
    Automatically loads the initial 5,190+ master records from kmpl_master_data.json
    into KMPL BOP Master and KMPL RM Master on bench migrate.
    """
    if hasattr(frappe, "get_app_path"):
        json_path = frappe.get_app_path("kmpl", "data", "kmpl_master_data.json")
    else:
        app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        json_path = os.path.join(app_dir, "data", "kmpl_master_data.json")

    if not os.path.exists(json_path):
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    now = now_datetime()

    # 1. Populate KMPL BOP Master
    if frappe.db.count("KMPL BOP Master") == 0:
        bop_items = data.get("bop_items", {})
        for key, item in bop_items.items():
            code = item.get("code")
            if code and not frappe.db.exists("KMPL BOP Master", code):
                doc = frappe.new_doc("KMPL BOP Master")
                doc.item_code = code
                doc.item_name_description = item.get("desc") or key
                doc.main_group = item.get("group", "")
                doc.sub_group = item.get("sub_group", "")
                doc.is_active = 1
                doc.insert(ignore_permissions=True)

    # 2. Populate KMPL RM Master (Sheet codes, Fasteners, Profiles)
    if frappe.db.count("KMPL RM Master") == 0:
        # Sheet codes
        for code, sinfo in data.get("sheet_codes", {}).items():
            if not frappe.db.exists("KMPL RM Master", code):
                doc = frappe.new_doc("KMPL RM Master")
                doc.item_code = code
                doc.rm_type = "Raw Material-PLATE"
                doc.description = sinfo.get("desc", "")
                doc.thickness_size = str(sinfo.get("thk") or "")
                doc.full_sheet_weight = float(sinfo.get("full_sheet_weight") or 0.0)
                doc.moc = sinfo.get("moc", "AISI 304")
                doc.unit = "No"
                doc.insert(ignore_permissions=True)

        # Fasteners
        for code, finfo in data.get("fasteners", {}).items():
            if not frappe.db.exists("KMPL RM Master", code):
                doc = frappe.new_doc("KMPL RM Master")
                doc.item_code = code
                doc.rm_type = "Raw Material-FASTENER"
                doc.description = finfo.get("desc", "")
                doc.thickness_size = str(finfo.get("size") or "")
                doc.moc = finfo.get("moc", "AISI 304")
                doc.unit = "No."
                doc.insert(ignore_permissions=True)

        # RM items
        for code, rinfo in data.get("rm_items", {}).items():
            if not frappe.db.exists("KMPL RM Master", code):
                doc = frappe.new_doc("KMPL RM Master")
                doc.item_code = code
                doc.rm_type = rinfo.get("rm_type", "Raw Material-SQ PIPE")
                doc.description = rinfo.get("desc", "")
                doc.general_description = rinfo.get("gen_desc", "")
                doc.thickness_size = str(rinfo.get("thk") or "")
                doc.moc = "AISI 304"
                doc.unit = "m"
                doc.insert(ignore_permissions=True)

    # Update KMPL Settings
    try:
        settings = frappe.get_single("KMPL Settings")
        settings.last_synced_on = now
        settings.sync_status = "Synced"
        settings.total_bop_items = frappe.db.count("KMPL BOP Master")
        settings.total_rm_items = frappe.db.count("KMPL RM Master")
        settings.save(ignore_permissions=True)
    except Exception:
        pass
