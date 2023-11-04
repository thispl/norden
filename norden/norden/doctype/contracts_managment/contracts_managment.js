// Copyright (c) 2023, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on('Contracts Managment', {
	// refresh: function(frm) {

	// }

	days_left(frm) {
		
		if (frm.doc.days_left <= 30) {
			console.log(frm.doc.days_left)
			frm.set_value("renewal_status", "Due for Renewal")
		}
		else{
			frm.set_value("renewal_status", "Valid")
		}
	},

	renewability_status(frm) {
		if (frm.doc.renewability_status == "Unlimited Validity") {
			frm.set_value("renewal_status", "Unlimited");
		}
		if (frm.doc.renewability_status == "Not Renewable") {
			frm.set_value("renewal_status", "Not Renewable")
		}

		if (frm.doc.renewability_status	== "Renewable") {
			frm.set_value("renewal_status", "Valid")
		}
	},

	contact_number(frm) {
		var no = String(frm.doc.contact_number)
		console.log(no.length);
		if (no.length < 10) {
			frappe.msgprint(__("Contact Number should not be 'less' or 'more' than 10 Digit"));
			frappe.validated = false;
		}
	},

	last_renewal_date(frm){
		if(frm.doc.renewal_frequency > 0){
			var next_due_date = frappe.datetime.add_days(frm.doc.last_renewal_date, frm.doc.renewal_frequency);
			frm.set_value("next_due", next_due_date);
			var diff = frappe.datetime.get_diff(next_due_date, frappe.datetime.nowdate())
			frm.set_value("days_left", diff);
		}
	},

	validate(frm){
		frm.trigger("days_left")
		frm.trigger("last_renewal_date")
	},

	next_due_date(frm) {
		frm.trigger("days_left")
	},
	frequency_of_renewal_days(frm){
		frm.trigger("last_renewal_date")
	},

});
