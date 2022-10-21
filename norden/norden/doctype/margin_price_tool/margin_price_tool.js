// Copyright (c) 2022, Teampro and contributors
// For license information, please see license.txt
frappe.ui.form.on('Margin Price Tool', {
	refresh: function (frm) {
		frm.add_custom_button(__("Update all location"), function () {
			frm.call('update_all_region').then(r=>{
				frappe.msgprint("Updating in Background...")
			})	

        });

	},

	setup(frm){
		frm.get_docfield('singapore').allow_bulk_edit = 1
		frm.get_docfield('philippines').allow_bulk_edit = 1
		frm.get_docfield('malaysia').allow_bulk_edit = 1
		frm.get_docfield('vietnam').allow_bulk_edit = 1
		frm.get_docfield('combodia').allow_bulk_edit = 1
		frm.get_docfield('indonesia').allow_bulk_edit = 1
		frm.get_docfield('bangladesh').allow_bulk_edit = 1
		frm.get_docfield('srilanka').allow_bulk_edit = 1
		frm.get_docfield('india').allow_bulk_edit = 1
		frm.get_docfield('uk').allow_bulk_edit = 1
		frm.get_docfield('africa').allow_bulk_edit = 1
		frm.get_docfield('dubai').allow_bulk_edit = 1
	},
	// onload(frm) {
	// 	var group = ['Cabinet Accessories', 'Cabinets', 'CCTV - Non EyeNor',
	// 		//  'CellNor', 'Coaxial Cables', 'Control and Instrumentation Cables', 'Data Cables', 'Eyenor',
	// 		// 	'Fast Moving Coaxial Cables', 'Fast Moving Data Cables', 'Fiber Accessories 1', 'Fiber Cables', 'Fibre Cables - Cut Piece', 'Fire Cables', 'MI ACCESSORIES', 'N VOICE SYSTEM',
	// 		// 	'Networking Accessories 1', 'SAFENOR', 'Secnor - Electronics', 'Telecom Accessories', 'Telephone cables', 'Telephone cables - Cut Piece'
	// 	]
	// 	frm.clear_table('singapore')
	// 	$.each(group, function (i, d) {
	// 		frm.add_child('singapore', {
	// 			"item_group": d,
	// 		})
	// 	})
	// 	frm.refresh_field('singapore')
	// 	// frm.clear_table('price_india')
	// 	// $.each(group, function (i, d) {
	// 	// 	frm.add_child('price_india', {
	// 	// 		"item_group": d,
	// 	// 	})
	// 	// })
	// 	// frm.refresh_field('price_india')
	// },
	update_singapore(frm) {
		frappe.call({
			method : "norden.norden.doctype.margin_price_tool.margin_price_tool.enqueue_update_item_price",
			args: {
				table : frm.doc.singapore,
				country : "Singapore"
			}
		})
		frappe.msgprint("Updating Item Price. Please check Item Price List after sometime.")
		frm.save()
	},
	update_philippines(frm) {
		frappe.call({
			method : "norden.norden.doctype.margin_price_tool.margin_price_tool.enqueue_update_item_price",
			args: {
				table : frm.doc.philippines,
				country : "Philippines"
			}
		})
		frappe.msgprint("Updating Item Price. Please check Item Price List after sometime.")
		frm.save()
	},
	update_malaysia(frm) {
		frappe.call({
			method : "norden.norden.doctype.margin_price_tool.margin_price_tool.enqueue_update_item_price",
			args: {
				table : frm.doc.malaysia,
				country : "Malaysia"
			}
		})
		frappe.msgprint("Updating Item Price. Please check Item Price List after sometime.")
		frm.save()
	},
	update_indonesia(frm) {
		frappe.call({
			method : "norden.norden.doctype.margin_price_tool.margin_price_tool.enqueue_update_item_price",
			args: {
				table : frm.doc.indonesia,
				country : "Indonesia"
			}
		})
		frappe.msgprint("Updating Item Price. Please check Item Price List after sometime.")
		frm.save()
	},
	update_vietnam(frm) {
		frappe.call({
			method : "norden.norden.doctype.margin_price_tool.margin_price_tool.enqueue_update_item_price",
			args: {
				table : frm.doc.vietnam,
				country : "Vietnam"
			}
		})
		frappe.msgprint("Updating Item Price. Please check Item Price List after sometime.")
		frm.save()
	},
	update_combodia(frm) {
		frappe.call({
			method : "norden.norden.doctype.margin_price_tool.margin_price_tool.enqueue_update_item_price",
			args: {
				table : frm.doc.combodia,
				country : "Cambodia"
			}
		})
		frappe.msgprint("Updating Item Price. Please check Item Price List after sometime.")
		frm.save()
	},
	update_bangladesh(frm) {
		frappe.call({
			method : "norden.norden.doctype.margin_price_tool.margin_price_tool.enqueue_update_item_price",
			args: {
				table : frm.doc.bangladesh,
				country : "Bangladesh"
			}
		})
		frappe.msgprint("Updating Item Price. Please check Item Price List after sometime.")
		frm.save()
	},
	update_srilanka(frm) {
		frappe.call({
			method : "norden.norden.doctype.margin_price_tool.margin_price_tool.enqueue_update_item_price",
			args: {
				table : frm.doc.srilanka,
				country : "Srilanka"
			}
		})
		frappe.msgprint("Updating Item Price. Please check Item Price List after sometime.")
		frm.save()
	},
	update_india(frm) {
		frappe.call({
			method : "norden.norden.doctype.margin_price_tool.margin_price_tool.enqueue_update_item_price_india",
			args: {
				table : frm.doc.india,
			}
		})
		frappe.msgprint("Updating Item Price. Please check Item Price List after sometime.")
		frm.save()
	},
	update_uk(frm) {
		frappe.call({
			method : "norden.norden.doctype.margin_price_tool.margin_price_tool.enqueue_update_item_price_uk",
			args: {
				table : frm.doc.uk,
			}
		})
		frappe.msgprint("Updating Item Price. Please check Item Price List after sometime.")
		frm.save()
	},

	update_africa(frm) {
		frappe.call({
			method : "norden.norden.doctype.margin_price_tool.margin_price_tool.enqueue_update_item_price_africa",
			args: {
				table : frm.doc.africa,
			}
		})
		frappe.msgprint("Updating Item Price. Please check Item Price List after sometime.")
		frm.save()
	},

	// update_dubai(frm) {
	// 	frappe.call({
	// 		method : "norden.norden.doctype.margin_price_tool.margin_price_tool.enqueue_update_item_price_dubai",
	// 		args: {
	// 			table : frm.doc.dubai,
	// 		}
	// 	})
	// 	frappe.msgprint("Updating Item Price. Please check Item Price List after sometime.")
	// 	frm.save()
	// },
});