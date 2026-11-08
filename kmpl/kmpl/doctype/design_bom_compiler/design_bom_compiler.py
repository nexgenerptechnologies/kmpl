import os
try:
    import frappe
    from frappe.model.document import Document
    from frappe.utils.file_manager import get_file_path, save_file
except ImportError:
    # Allow running outside Frappe for testing
    frappe = None
    class Document:
        pass

from kmpl.utils.bom_parser import parse_solidworks_bom
from kmpl.utils.weight_calculator import compile_summary
from kmpl.utils.excel_exporter import export_final_bom_excel


class DesignBOMCompiler(Document):
    def validate(self):
        self.calculate_totals()

    def calculate_totals(self):
        tot_wt = 0.0
        for itm in self.get("items", []):
            if itm.total_weight:
                tot_wt += float(itm.total_weight)
        self.total_weight_kg = round(tot_wt, 2)
        self.total_items_count = len(self.get("items", []))

    @frappe.whitelist()
    def compile_bom(self):
        """
        Parses uploaded SolidWorks BOM, auto-fills detailed items and summary.
        """
        if not self.design_bom_file:
            frappe.throw("Please attach the SolidWorks Design BOM Excel file first.")

        # Resolve file path in Frappe
        file_path = get_file_path(self.design_bom_file)
        if not os.path.exists(file_path):
            file_doc = frappe.get_doc("File", {"file_url": self.design_bom_file})
            file_path = file_doc.get_full_path()

        # Parse SolidWorks BOM
        bom_header, bom_items = parse_solidworks_bom(file_path, default_po_qty=self.po_qty or 1)

        # Update metadata if blank
        if not self.project_no and bom_header.get("project_no"):
            self.project_no = bom_header["project_no"]
        if not self.equipment_name and bom_header.get("equipment_name"):
            self.equipment_name = bom_header["equipment_name"]
        if not self.bom_name:
            self.bom_name = self.equipment_name

        # Populate Items table
        self.set("items", [])
        for row in bom_items:
            self.append("items", {
                "category": row.get("category", "C"),
                "rm_type": row.get("rm_type"),
                "dwg_no": row.get("dwg_no"),
                "item_code": row.get("item_code"),
                "description": row.get("description"),
                "length": row.get("length"),
                "width": row.get("width"),
                "thk": str(row.get("thk")) if row.get("thk") is not None else None,
                "unit_qty": row.get("unit_qty", 1),
                "unit_weight": row.get("unit_weight"),
                "total_weight": row.get("total_weight"),
                "moc": row.get("moc", "AISI 304"),
                "unit": row.get("unit", "Kg"),
                "remarks": str(row.get("remarks")) if row.get("remarks") is not None else None
            })

        # Generate and populate Summary table
        summary_rows = compile_summary(bom_items, project_no=self.project_no or "2559-01")
        self.set("summary_items", [])
        for srow in summary_rows:
            self.append("summary_items", {
                "project_no": self.project_no,
                "category": srow.get("category", "C"),
                "item_code": srow.get("item_code"),
                "rm_type": srow.get("rm_type"),
                "description": srow.get("description"),
                "thk_mm": str(srow.get("thk_mm")) if srow.get("thk_mm") is not None else None,
                "weight_kg": srow.get("weight_kg"),
                "unit_weight": srow.get("unit_weight"),
                "general_description": srow.get("general_description"),
                "length_qty": srow.get("length_qty"),
                "unit": srow.get("unit"),
                "moc": srow.get("moc", "AISI 304")
            })

        self.status = "Compiled"
        self.calculate_totals()
        self.save()
        frappe.msgprint(f"BOM compiled successfully: {len(self.items)} items, {len(self.summary_items)} summary rows.")
        return True

    @frappe.whitelist()
    def export_excel(self):
        """
        Generates formatted 001FINAL-PARTS BOMDF style Excel file and returns download URL.
        """
        if not self.items:
            frappe.throw("No items to export. Please compile the BOM first.")

        site_path = frappe.get_site_path()
        out_filename = f"{self.project_no or 'BOM'}-FINAL-PARTS-BOM.xlsx"
        out_path = os.path.join(site_path, "public", "files", out_filename)

        header_dict = {
            "project_no": self.project_no or "2559-01",
            "equipment_name": self.equipment_name or "Continuous Trail",
            "bom_name": self.bom_name or self.equipment_name,
            "bom_date": str(self.bom_date or "23.09.2026"),
            "po_qty": self.po_qty or 1,
            "unit": self.unit or "Nos."
        }

        bom_items_data = [d.as_dict() for d in self.items]
        summary_items_data = [d.as_dict() for d in self.summary_items]

        export_final_bom_excel(out_path, header_dict, bom_items_data, summary_items_data)

        # Save as Frappe File
        with open(out_path, "rb") as f:
            file_doc = save_file(out_filename, f.read(), self.doctype, self.name, is_private=0)

        self.status = "Exported"
        self.save()
        return file_doc.file_url

    @frappe.whitelist()
    def create_erpnext_bom(self):
        """
        Automatically creates standard ERPNext Items and Manufacturing BOM.
        """
        if not frappe.db.exists("DocType", "BOM"):
            frappe.throw("ERPNext Manufacturing module (BOM) is not installed.")

        # Ensure main item exists
        main_item_code = f"PROJ-{self.project_no}"
        if not frappe.db.exists("Item", main_item_code):
            main_item = frappe.get_doc({
                "doctype": "Item",
                "item_code": main_item_code,
                "item_name": self.equipment_name or main_item_code,
                "item_group": "Products",
                "is_stock_item": 1,
                "include_item_in_manufacturing": 1,
                "stock_uom": self.unit or "Nos"
            })
            main_item.insert(ignore_permissions=True)

        # Ensure raw materials and BOP items exist in Item Master
        for row in self.items:
            if not row.item_code:
                continue
            if not frappe.db.exists("Item", row.item_code):
                itm = frappe.get_doc({
                    "doctype": "Item",
                    "item_code": row.item_code,
                    "item_name": row.description or row.item_code,
                    "item_group": "Raw Material" if "Raw Material" in (row.rm_type or "") else "Bought Out Parts",
                    "is_stock_item": 1,
                    "stock_uom": row.unit or "Nos"
                })
                itm.insert(ignore_permissions=True)

        # Create ERPNext BOM
        bom_doc = frappe.get_doc({
            "doctype": "BOM",
            "item": main_item_code,
            "quantity": self.po_qty or 1,
            "is_active": 1,
            "is_default": 1,
            "with_operations": 0,
            "items": []
        })

        for row in self.items:
            if not row.item_code:
                continue
            bom_doc.append("items", {
                "item_code": row.item_code,
                "qty": row.unit_qty or 1,
                "uom": row.unit or "Nos",
                "stock_uom": row.unit or "Nos",
                "description": row.description
            })

        bom_doc.insert(ignore_permissions=True)
        self.status = "Synced with ERPNext"
        self.save()
        frappe.msgprint(f"ERPNext BOM <b>{bom_doc.name}</b> created successfully!")
        return bom_doc.name
