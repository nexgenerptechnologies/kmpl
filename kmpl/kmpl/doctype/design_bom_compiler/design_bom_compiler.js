frappe.ui.form.on('Design BOM Compiler', {
    refresh: function(frm) {
        if (!frm.is_new()) {
            // Button: Compile BOM
            frm.add_custom_button(__('Compile BOM'), function() {
                frappe.confirm(
                    __('This will parse the attached SolidWorks BOM and regenerate items and summary. Proceed?'),
                    function() {
                        frm.call({
                            method: 'compile_bom',
                            doc: frm.doc,
                            freeze: true,
                            freeze_message: __('Compiling SolidWorks BOM and generating summary...'),
                            callback: function(r) {
                                frm.reload_doc();
                            }
                        });
                    }
                );
            }).addClass('btn-primary');

            // Button: Export Final Excel
            if (frm.doc.items && frm.doc.items.length > 0) {
                frm.add_custom_button(__('Download Final Excel'), function() {
                    frm.call({
                        method: 'export_excel',
                        doc: frm.doc,
                        freeze: true,
                        freeze_message: __('Generating formatted Final Parts BOM Excel...'),
                        callback: function(r) {
                            if (r.message) {
                                window.open(r.message);
                            }
                        }
                    });
                }, __('Actions'));

                // Button: Create ERPNext Manufacturing BOM
                frm.add_custom_button(__('Create ERPNext BOM'), function() {
                    frappe.confirm(
                        __('Create standard ERPNext Items and Manufacturing BOM for this equipment?'),
                        function() {
                            frm.call({
                                method: 'create_erpnext_bom',
                                doc: frm.doc,
                                freeze: true,
                                freeze_message: __('Creating ERPNext Items and BOM...'),
                                callback: function(r) {
                                    frm.reload_doc();
                                }
                            });
                        }
                    );
                }, __('Actions'));
            }
        }
    }
});
