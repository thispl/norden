// Copyright (c) 2021, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on('Logistics Request', {
	// refresh: function(frm) {

	// },
	po_so(frm){
		frm.set_value('order_no','')
	},
	logistic_type(frm){
		if(frm.doc.logistic_type == 'Export'){
			frm.set_value('po_so','Sales Order')
		}
		else if(frm.doc.logistic_type == 'Import'){
			frm.set_value('po_so','Purchase Order')
		}
	},
	grand_total(frm){
		if(frm.doc.grand_total){
			frm.set_value('custom_duty',frm.doc.grand_total * 0.45)
		}
	}
});
