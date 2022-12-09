// Copyright (c) 2022, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on('Monthly ESI Payable Employes List', {
	refresh(frm) {
		frm.add_custom_button(__("Print Preview"), function () {
			var f_name = frm.doc.name
			var print_format = "ESI-Form";
			window.open(frappe.urllib.get_full_url("/api/method/frappe.utils.print_format.download_pdf?"
				+ "doctype=" + encodeURIComponent("Monthly ESI Payable Employes List")
				+ "&name=" + encodeURIComponent(f_name)
				+ "&trigger_print=1"
				+ "&format=" + print_format
				+ "&no_letterhead=0"
			));
	}); 
	}
    
});
