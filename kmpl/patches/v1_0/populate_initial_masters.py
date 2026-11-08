import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from kmpl.hooks import custom_fields

def execute():
    """
    Ensures KMPL custom fields are created directly on standard ERPNext Item DocType
    and clears the Item cache so the section appears immediately.
    """
    create_custom_fields(custom_fields, update=True)
    frappe.clear_cache(doctype="Item")
