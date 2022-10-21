// Copyright (c) 2022, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on('File Number Global Search', {
	// refresh: function(frm) {

	// }

	file_number(frm){
		if(frm.doc.file_number){
		frm.call('get_data').then(r=>{
			if (r.message) {
				frm.fields_dict.documents.$wrapper.empty().append(r.message)
			}
		})	
	}
	}
});
