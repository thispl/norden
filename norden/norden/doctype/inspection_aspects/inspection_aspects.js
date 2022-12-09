// Copyright (c) 2022, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on('Inspection Aspects', {
	onload: function (frm) {
		frappe.call({
			method: "frappe.client.get_list",
			args: {
				"doctype": "Specification",
				"fields": ['*'],
				"limit_page_length": 9999
			},
			callback(r) {
				
				$.each(r.message, function (index, v) {

					if (frm.doc.aspects == "Visual Aspects"){
						if(v['aspects'] == "Visual Aspects") {
								let row = frm.add_child("inspection_specification_child");
								row.specification = v['specification']
							}
						
					} 
					frm.refresh_field("inspection_specification_child");
				})
				
			}

		})

		frappe.call({
			method: "frappe.client.get_list",
			args: {
				"doctype": "Specification",
				"fields": ['*'],
				"limit_page_length": 9999
			},
			callback(r) {
				
				$.each(r.message, function (index, v) {

					if (frm.doc.aspects == "Functional Aspects"){
						if(v['aspects'] == "Functional Aspects") {
								let row = frm.add_child("inspection_specification_child");
								row.specification = v['specification']
							}
						
					} 
					frm.refresh_field("inspection_specification_child");
				})
				
			}


		})

		frappe.call({
			method: "frappe.client.get_list",
			args: {
				"doctype": "Specification",
				"fields": ['*'],
				"limit_page_length": 9999
			},
			callback(r) {
				
				$.each(r.message, function (index, v) {

					if (frm.doc.aspects == "Material Aspects"){
						if(v['aspects'] == "Material Aspects") {
								let row = frm.add_child("inspection_specification_child");
								row.specification = v['specification']
							}
						
					} 
					frm.refresh_field("inspection_specification_child");
				})
				
			}


		})


		frappe.call({
			method: "frappe.client.get_list",
			args: {
				"doctype": "Specification",
				"fields": ['*'],
				"limit_page_length": 9999
			},
			callback(r) {
				
				$.each(r.message, function (index, v) {

					if (frm.doc.aspects == "Dimensional Aspects"){
						if(v['aspects'] == "Dimensional Aspects") {
								let row = frm.add_child("inspection_specification_child");
								row.specification = v['specification']
							}
						
					} 
					frm.refresh_field("inspection_specification_child");
				})
				
			}


		})
				


	}
	// refresh: function(frm) {

	// }
	
});
