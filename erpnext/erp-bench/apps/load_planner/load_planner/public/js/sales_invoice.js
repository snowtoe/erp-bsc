frappe.ui.form.on("Sales Invoice", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Gebinde berechnen"), function () {
            frappe.call({
                method: "load_planner.api.sales_invoice.calculate_packages",
                args: {
                    sales_invoice_name: frm.doc.name
                },
                freeze: true,
                freeze_message: __("Gebindeberechnung läuft ..."),
                callback: function (r) {
                    if (!r.exc) {
                        frappe.show_alert({
                            message: __("Gebindeberechnung abgeschlossen"),
                            indicator: "green"
                        });
                        frm.reload_doc();
                    }
                }
            });
        }, __("Load Planner"));

        if (frm.doc.lp_package_plan) {
            frm.add_custom_button(__("Gebindeplan öffnen"), function () {
                frappe.set_route("Form", "LP Package Plan", frm.doc.lp_package_plan);
            }, __("Load Planner"));
        }
    }
});
