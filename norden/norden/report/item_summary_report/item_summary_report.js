// Copyright (c) 2023, Teampro and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Item Summary Report"] = {
	"filters": [
		{
			"fieldname": "item",
			"label": __("Item"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Item",
			// "reqd":1
		},
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd":1
		},
		
		{
			"fieldname": "item_group",
			"label": __("Item Group"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Item Group",
		},
		{
			"fieldname": "like",
			"label": __("Like"),
			"fieldtype": "Data",
		},
		
	],
	"formatter": function (value, row, column, data, default_formatter) {
		if (column.fieldname == "item" && data ) {
			value = data["item"];			
			column.link_onclick = "frappe.query_reports['Item Summary Report'].set_route_to_allocation(" + JSON.stringify(data) + ")";
		}
		value = default_formatter(value, row, column, data);
		return value;
	},
	"set_route_to_allocation": function (data) {
		frappe.route_options = {
			"item_code": data["item"],
		}
		window.open(
			frappe.urllib.get_full_url("/app/allocation-details/Allocation%20Details?item_code="+encodeURIComponent(data["company"] +':'+ data["item"])));
	},
};
