// // Copyright (c) 2022, Teampro and contributors
// // For license information, please see license.txt

// frappe.ui.form.on('Item Inspection', {
// 	onload: function (frm) {
// 		frappe.call({
// 			method: "frappe.client.get_list",
// 			args: {
// 				"doctype": "Item Inspection Specification",
// 				"fields": ['*'],
// 				"limit_page_length": 9999
// 			},
// 			callback(r) {
				
// 				$.each(r.message, function (index, v) {
					
// 					if (v['title'] == "VISUAL ASPECTS") {
// 						let row = frm.add_child("visual_aspects");
// 						row.specification = v['specification']
// 					}
// 					frm.refresh_field("visual_aspects");
// 				})
				
// 			}

// 		})
// 		frappe.call({
// 			method: "frappe.client.get_list",
// 			args: {
// 				"doctype": "Item Inspection Specification",
// 				"fields": ['*'],
// 				"limit_page_length": 9999
// 			},
// 			callback(r) {
				
// 				$.each(r.message, function (index, v) {
					
// 					if (v['title'] == "FUNCTIONAL") {
// 						let row = frm.add_child("functional");
// 						row.specification = v['specification']
// 					}
// 					frm.refresh_field("functional");
// 				})
				
// 			}

// 		})
// 		frappe.call({
// 			method: "frappe.client.get_list",
// 			args: {
// 				"doctype": "Item Inspection Specification",
// 				"fields": ['*'],
// 				"limit_page_length": 9999
// 			},
// 			callback(r) {
				
// 				$.each(r.message, function (index, v) {
					
// 					if (v['title'] == "DIMENSIONAL ASPECTS ")
// 					{
// 						let row = frm.add_child("dimensional_aspects");
// 						row.specification = v['specification']
// 					}
// 					frm.refresh_field("dimensional_aspects");
// 				})
				
// 			}

// 		})
// 		frappe.call({
// 			method: "frappe.client.get_list",
// 			args: {
// 				"doctype": "Item Inspection Specification",
// 				"fields": ['*'],
// 				"limit_page_length": 9999
// 			},
// 			callback(r) {
				
// 				$.each(r.message, function (index, v) {
					
// 					if (v['title'] == "MATERIAL ") {
// 						let row = frm.add_child("material");
// 						row.specification = v['specification']
// 					}
// 					frm.refresh_field("material");
// 				})
				
// 			}

// 		})

// 	}
// });
