// Copyright (c) 2023, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on('Product Search', {
	item_code(frm){
		frm.call('get_data').then(r=>{
			if (r.message) {
				frm.fields_dict.html.$wrapper.empty().append(r.message)
			}
		})
		frm.call('get_data_norden').then(r=>{
			if (r.message) {
				frm.fields_dict.html_other.$wrapper.empty().append(r.message)
			}
		})
		frappe.call({
			method:"norden.utils.get_electra_item",
			args:{
				item:frm.doc.item_code
			},
			callback(r){
				$.each(r.message,function(i,d){
					frm.fields_dict.html1.$wrapper.empty().append(d)
				})
			}
		})
		frappe.call({
			method:"norden.utils.electra_item",
			args:{
				item:frm.doc.item_code
			},
			callback(r){
				console.log(r.message)
				$.each(r.message,function(i,d){
				frm.fields_dict.html_electra.$wrapper.empty().append(d)
				})
			}
		})		
	},
});
