// Copyright (c) 2022, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on('Block Warehouse', {
	refresh: function(frm) {
		frm.set_query("target", function () {
			return {
				filters: {
					"company":frm.doc.company,"is_block":1
				}
			}
		})

		frm.set_query("source", function () {
			return {
				filters: {
					"company":frm.doc.company
				}
			}
		})
	},

	employee(frm){
		frappe.db.get_value('Employee',{"name":frm.doc.employee},'company')
        .then(r => {
			frm.set_value("company",r.message.company)

		frappe.db.get_value('Warehouse',{"company":r.message.company,"is_block":1},'name')
        .then(d => {
			frm.set_value("target",d.message.name)

			
        })
			
        })
	},

	// setup: function (frm) {

	// }	
});

frappe.ui.form.on('Block Warehouse Items', {

	item_code(frm, cdt, cdn){
        var child = locals[cdt][cdn]
		if(child.item_code){

		frappe.db.get_value('Item',{"name":child.item_code},'description')
        .then(r => {
           child.description = r.message.description
          
        })	
		
		}
		
	},

})

