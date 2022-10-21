// Copyright (c) 2022, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on('Block Warehouse', {
	// refresh: function(frm) {

	// },
});

frappe.ui.form.on('Block Warehouse Items', {

	item_code(frm, cdt, cdn){
        var child = locals[cdt][cdn]
		if(child.item_code){
		frm.call('get_rate').then(r=>{
			if (r.message) {
				console.log(r.message)
				child.rate = r.message
			}
			frm.refresh_field("items")
		})	
		
		}
		
	},

})

