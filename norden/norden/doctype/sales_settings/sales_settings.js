// Copyright (c) 2021, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Settings', {
	refresh: function(frm) {
		frappe.breadcrumbs.add("CRM");
	}
});
