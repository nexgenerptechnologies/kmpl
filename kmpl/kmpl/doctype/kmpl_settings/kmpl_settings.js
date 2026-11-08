frappe.ui.form.on('KMPL Settings', {
    refresh: function(frm) {
        frm.add_custom_button(__('Sync Masters from Excel'), function() {
            frappe.confirm(
                __('This will synchronize and update the master items from the attached Excel files (or pre-bundled dataset). Proceed?'),
                function() {
                    frm.call({
                        method: 'sync_masters',
                        doc: frm.doc,
                        freeze: true,
                        freeze_message: __('Synchronizing 5,000+ Master Items...'),
                        callback: function(r) {
                            frm.reload_doc();
                        }
                    });
                }
            );
        }).addClass('btn-primary');
    }
});
