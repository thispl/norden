// Copyright (c) 2023, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payroll Category', {
	payroll_category(frm){
		var category = frm.doc.payroll_category
		var change_to_upper_case = category.toUpperCase()
		frm.set_value('payroll_category',change_to_upper_case)
	}
});
