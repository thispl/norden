// Copyright (c) 2016, Teampro and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Item Price Details"] = {
	"filters": [
		// {
		// 	"fieldname": "company",
		// 	"label": __("Company"),
		// 	"fieldtype": "Link",
		// 	"width": "80",
		// 	"options": "Company",
		// 	"mandatory": 1,
		// 	"default": frappe.defaults.get_default("company")
		// },

		// {
		// 	"fieldname": "Territory",
		// 	"label": __("territory"),
		// 	"fieldtype": "Link",
		// 	"width": "80",
		// 	"options": "Territory",
		// 	"mandatory": 1,
		// 	// "default": frappe.defaults.get_default("company")
		// },

		// {
		// 	"fieldname": "price_list",
		// 	"label": __("Price List"),
		// 	"fieldtype": "Link",
		// 	"width": "80",
		// 	"options": "Price List",
			// "mandatory": 1,
			// "get_query": function() {
			// 	const company = frappe.query_report.get_filter_value('Price List');
			// 	return {
			// 		filters: { 'permission': 1}
			// 	}
			// }
		// },

		{
			"fieldname": "item_code",
			"label": __("Item Code"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Item",
			// "reqd":1,
			"get_query": function() {
				return {
					query: "erpnext.controllers.queries.item_query",
				};
			}
		},
		{
			"fieldname": "item_group",
			"label": __("Item Group"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Item Group",
		},
		

	],

	// refresh(frm){
	// 	if(frm.doc.filter){
	// 		frappe.msgprint("Preparing Report...")
	// 	}
	// }
};
