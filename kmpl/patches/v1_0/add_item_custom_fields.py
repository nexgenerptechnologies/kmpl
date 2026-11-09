import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

ITEM_CUSTOM_FIELDS = {
    "Item": [
        {
            "fieldname": "custom_kmpl_section",
            "label": "KMPL Design & RM Specifications",
            "fieldtype": "Section Break",
            "insert_after": "brand",
            "collapsible": 0
        },
        {
            "fieldname": "custom_rm_type",
            "label": "Type of RM",
            "fieldtype": "Select",
            "options": "Raw Material-PLATE\nRaw Material-SQ PIPE\nRaw Material-REC PIPE\nRaw Material-PIPE\nRaw Material-ISA ANGLE\nRaw Material-ROD\nRaw Material-SQ BAR\nRaw Material-REC BAR\nRaw Material-FLAT\nRaw Material-CIRCLE\nRaw Material-BLOCK\nRaw Material-FASTENER\nRaw Material-BOP",
            "insert_after": "custom_kmpl_section",
            "in_list_view": 1,
            "in_standard_filter": 1
        },
        {
            "fieldname": "custom_thickness_size",
            "label": "Thickness / Size (mm)",
            "fieldtype": "Data",
            "insert_after": "custom_rm_type",
            "in_list_view": 1
        },
        {
            "fieldname": "custom_moc",
            "label": "MOC",
            "fieldtype": "Data",
            "default": "AISI 304",
            "insert_after": "custom_thickness_size"
        },
        {
            "fieldname": "custom_kmpl_col_break",
            "fieldtype": "Column Break",
            "insert_after": "custom_moc"
        },
        {
            "fieldname": "custom_full_sheet_weight",
            "label": "Full Sheet Standard Weight (kg)",
            "fieldtype": "Float",
            "precision": "2",
            "description": "Used to calculate full sheets needed (Total Weight / Full Sheet Wt)",
            "insert_after": "custom_kmpl_col_break"
        },
        {
            "fieldname": "custom_weight_per_meter",
            "label": "Weight per Meter (kg/m)",
            "fieldtype": "Float",
            "precision": "3",
            "description": "Used to calculate weights and procurement meters for pipes, angles, rods",
            "insert_after": "custom_full_sheet_weight"
        },
        {
            "fieldname": "custom_design_pattern",
            "label": "Design Description Pattern",
            "fieldtype": "Small Text",
            "description": "SolidWorks description pattern / alias used for auto-matching",
            "insert_after": "custom_weight_per_meter"
        }
    ]
}

def execute():
    """
    Directly creates the custom fields on standard Item DocType and commits to database.
    """
    # 1. Use Frappe standard create_custom_fields
    create_custom_fields(ITEM_CUSTOM_FIELDS, update=True)

    # 2. Also ensure each field exists via direct document check as a fallback
    for field_dict in ITEM_CUSTOM_FIELDS["Item"]:
        fn = field_dict["fieldname"]
        cf_name = f"Item-{fn}"
        if not frappe.db.exists("Custom Field", cf_name):
            try:
                cf = frappe.new_doc("Custom Field")
                cf.dt = "Item"
                cf.fieldname = fn
                cf.label = field_dict.get("label")
                cf.fieldtype = field_dict.get("fieldtype")
                cf.options = field_dict.get("options")
                cf.insert_after = field_dict.get("insert_after")
                cf.default = field_dict.get("default")
                cf.precision = field_dict.get("precision")
                cf.description = field_dict.get("description")
                cf.collapsible = field_dict.get("collapsible", 0)
                cf.in_list_view = field_dict.get("in_list_view", 0)
                cf.in_standard_filter = field_dict.get("in_standard_filter", 0)
                cf.insert(ignore_permissions=True)
            except Exception:
                pass

    frappe.clear_cache(doctype="Item")
    frappe.db.commit()
