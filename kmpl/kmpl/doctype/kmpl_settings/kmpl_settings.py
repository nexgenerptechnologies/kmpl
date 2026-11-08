import os
import json
import openpyxl
from frappe.model.document import Document
from frappe.utils import now_datetime
from frappe.utils.file_manager import get_file_path
import frappe


class KMPLSettings(Document):
    @frappe.whitelist()
    def sync_masters(self):
        """
        Loads BOP items and STD RM/Fasteners into KMPL BOP Master and KMPL RM Master.
        Can read from uploaded Excel files or from pre-bundled data.
        """
        if hasattr(frappe, "get_app_path"):
            json_cache = frappe.get_app_path("kmpl", "data", "kmpl_master_data.json")
        else:
            app_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            json_cache = os.path.join(app_path, "data", "kmpl_master_data.json")

        bop_count = 0
        rm_count = 0

        # ---------------------------------------------------------
        # 1. Sync BOP Items
        # ---------------------------------------------------------
        if self.bop_master_file:
            fpath = get_file_path(self.bop_master_file)
            wb_bop = openpyxl.load_workbook(fpath, data_only=True)
            ws_bop = wb_bop["Master Sheet"] if "Master Sheet" in wb_bop.sheetnames else wb_bop.active
            for r in range(2, ws_bop.max_row + 1):
                desc = ws_bop.cell(r, 4).value
                code = ws_bop.cell(r, 5).value
                if desc and code:
                    code_str = str(code).strip()
                    if not frappe.db.exists("KMPL BOP Master", code_str):
                        doc = frappe.new_doc("KMPL BOP Master")
                        doc.item_code = code_str
                        doc.item_name_description = str(desc).strip()
                        doc.main_group = str(ws_bop.cell(r, 2).value or "").strip()
                        doc.sub_group = str(ws_bop.cell(r, 3).value or "").strip()
                        doc.insert(ignore_permissions=True)
                        bop_count += 1
        elif os.path.exists(json_cache):
            with open(json_cache, "r", encoding="utf-8") as f:
                raw = json.load(f)
                bop_items = raw.get("bop_items", {})
                for desc, info in bop_items.items():
                    code_str = info.get("code")
                    if code_str and not frappe.db.exists("KMPL BOP Master", code_str):
                        doc = frappe.new_doc("KMPL BOP Master")
                        doc.item_code = code_str
                        doc.item_name_description = info.get("desc") or desc
                        doc.main_group = info.get("group", "")
                        doc.sub_group = info.get("sub_group", "")
                        doc.insert(ignore_permissions=True)
                        bop_count += 1

        # ---------------------------------------------------------
        # 2. Sync RM & Fasteners
        # ---------------------------------------------------------
        if self.std_summary_file:
            fpath = get_file_path(self.std_summary_file)
            wb_std = openpyxl.load_workbook(fpath, data_only=True)
            # Sheet codes
            if "STD SHEET ITEM CODE" in wb_std.sheetnames:
                ws_sh = wb_std["STD SHEET ITEM CODE"]
                for r in range(5, ws_sh.max_row + 1):
                    code = ws_sh.cell(r, 3).value
                    if code:
                        code_str = str(code).strip()
                        if not frappe.db.exists("KMPL RM Master", code_str):
                            doc = frappe.new_doc("KMPL RM Master")
                            doc.item_code = code_str
                            doc.rm_type = "Raw Material-PLATE"
                            doc.description = str(ws_sh.cell(r, 2).value or "")
                            doc.thickness_size = str(ws_sh.cell(r, 7).value or "")
                            try:
                                doc.full_sheet_weight = float(ws_sh.cell(r, 8).value or 0.0)
                            except:
                                pass
                            doc.moc = str(ws_sh.cell(r, 9).value or "AISI 304")
                            doc.insert(ignore_permissions=True)
                            rm_count += 1
            # Fasteners
            if "STD FASTNER SUMMARY" in wb_std.sheetnames:
                ws_fst = wb_std["STD FASTNER SUMMARY"]
                for r in range(3, ws_fst.max_row + 1):
                    code = ws_fst.cell(r, 3).value
                    if code:
                        code_str = str(code).strip()
                        if not frappe.db.exists("KMPL RM Master", code_str):
                            doc = frappe.new_doc("KMPL RM Master")
                            doc.item_code = code_str
                            doc.rm_type = "Raw Material-FASTENER"
                            doc.description = str(ws_fst.cell(r, 5).value or "")
                            doc.general_description = str(ws_fst.cell(r, 9).value or "")
                            doc.thickness_size = str(ws_fst.cell(r, 6).value or "")
                            doc.moc = str(ws_fst.cell(r, 12).value or "AISI 304")
                            doc.unit = "No."
                            doc.insert(ignore_permissions=True)
                            rm_count += 1
        elif os.path.exists(json_cache):
            with open(json_cache, "r", encoding="utf-8") as f:
                raw = json.load(f)
                # Sheets
                for code, sinfo in raw.get("sheet_codes", {}).items():
                    if not frappe.db.exists("KMPL RM Master", code):
                        doc = frappe.new_doc("KMPL RM Master")
                        doc.item_code = code
                        doc.rm_type = "Raw Material-PLATE"
                        doc.description = sinfo.get("desc", "")
                        doc.thickness_size = str(sinfo.get("thk") or "")
                        doc.full_sheet_weight = float(sinfo.get("full_sheet_weight") or 0.0)
                        doc.moc = sinfo.get("moc", "AISI 304")
                        doc.insert(ignore_permissions=True)
                        rm_count += 1
                # Fasteners
                for code, finfo in raw.get("fasteners", {}).items():
                    if not frappe.db.exists("KMPL RM Master", code):
                        doc = frappe.new_doc("KMPL RM Master")
                        doc.item_code = code
                        doc.rm_type = "Raw Material-FASTENER"
                        doc.description = finfo.get("desc", "")
                        doc.thickness_size = str(finfo.get("size") or "")
                        doc.moc = finfo.get("moc", "AISI 304")
                        doc.unit = "No."
                        doc.insert(ignore_permissions=True)
                        rm_count += 1
                # RM items
                for code, rinfo in raw.get("rm_items", {}).items():
                    if not frappe.db.exists("KMPL RM Master", code):
                        doc = frappe.new_doc("KMPL RM Master")
                        doc.item_code = code
                        doc.rm_type = rinfo.get("rm_type", "Raw Material-SQ PIPE")
                        doc.description = rinfo.get("desc", "")
                        doc.general_description = rinfo.get("gen_desc", "")
                        doc.thickness_size = str(rinfo.get("thk") or "")
                        doc.insert(ignore_permissions=True)
                        rm_count += 1

        self.last_synced_on = now_datetime()
        self.sync_status = "Synced"
        self.total_bop_items = frappe.db.count("KMPL BOP Master")
        self.total_rm_items = frappe.db.count("KMPL RM Master")
        self.save()

        msg = f"Masters synchronized successfully! Total Active: {self.total_bop_items} BOP items, {self.total_rm_items} RM & Fasteners."
        frappe.msgprint(msg)
        return msg
