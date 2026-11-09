app_name = "kmpl"
app_title = "KMPL"
app_publisher = "Nexgen ERP Technologies"
app_description = "KMPL SolidWorks Design BOM Compiler and ERPNext v16 Integration"
app_email = "info@nexgenerptechnologies.com"
app_license = "mit"

# Fixtures to sync custom fields during migrate
fixtures = [
    {
        "dt": "Custom Field",
        "filters": [
            ["dt", "=", "Item"],
            ["fieldname", "in", [
                "custom_kmpl_section",
                "custom_rm_type",
                "custom_thickness_size",
                "custom_moc",
                "custom_kmpl_col_break",
                "custom_full_sheet_weight",
                "custom_weight_per_meter",
                "custom_design_pattern"
            ]]
        ]
    }
]

# Custom fields added directly to standard ERPNext Item Master
custom_fields = {
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
