// Copyright (c) 2022, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on('Request for Sample Item', {
	// refresh: function(frm) {

	// }

	
});

frappe.ui.form.on('Sample Items', {

	item(frm, cdt, cdn){
        var child = locals[cdt][cdn]
		if(child.item){
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
