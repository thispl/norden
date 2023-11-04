// Copyright (c) 2023, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on('Electra Product Search', {
	item(frm){
		frappe.call({
			method:"norden.utils.get_electra_item",
			args:{
				item:frm.doc.item
			},
			callback(r){
				$.each(r.message,function(i,d){
					frm.fields_dict.html.$wrapper.empty().append(d)
				})
			}
		})
	}
});
