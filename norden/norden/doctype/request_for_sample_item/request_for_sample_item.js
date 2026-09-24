// Copyright (c) 2022, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on('Request for Sample Item', {
	onload(frm) {
	    if(frm.doc.__islocal){
			frm.set_value("is_stock_returned",0)
			frm.set_value("custom_is_stock_issued",0)
		}
	}
	// before_workflow_action: async (frm) => {
	// 	if (frm.doc.workflow_state == "Pending for IT") {
	// 		let promise = new Promise((resolve, reject) => {
	// 			if (frm.selected_workflow_action == "Confirm") {
	// 				frm.trigger("issue_item")
	// 			}
	// 			resolve();
	// 		});
	// 		await promise.catch((error) => frappe.throw(error));
	// 	}
	// 	if(frm.doc.workflow_state == "Issued"){
	// 		let promise = new Promise((resolve, reject) => {
	// 			if (frm.selected_workflow_action == "Return") {
	// 				frm.trigger("returnitem")
	// 			}
	// 			resolve();
	// 		});
	// 		await promise.catch(() => frappe.throw());
	// 	}
	// 	if(frm.doc.workflow_state == "Returned"){
	// 		let promise = new Promise((resolve, reject) => {
	// 			if (frm.selected_workflow_action == "Issue") {
	// 				frm.trigger("issue_item")
	// 			}
	// 			resolve();
	// 		});
	// 		await promise.catch(() => frappe.throw());
	// 	}
	// },
	// issue_item(frm){
	// 	frm.call('transfer_item').then(r=>{
	// 		if (r.message) {
	// 		}
	// 	})	
	// },
	// returnitem(frm){
	// 	frm.call('return_item').then(r=>{
	// 		if (r.message) {
	// 		}
	// 	})	
	// },

	
});

frappe.ui.form.on('Sample Items', {

	item(frm, cdt, cdn){
        var child = locals[cdt][cdn]
		if(child.item){
		frm.call('get_rate').then(r=>{
			if (r.message) {
				child.rate = r.message[0]
				child.doc_currency = r.message[1]
			}
			frm.refresh_field("items")
		})	
		}
	},

})
