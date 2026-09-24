// Copyright (c) 2023, Teampro and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Item Summary Report"] = {
	"filters": [
		// {
		// 	"fieldname": "item",
		// 	"label": __("Item"),
		// 	"fieldtype": "Link",
		// 	"width": "80",
		// 	"options": "Item",
		// 	// "reqd":1
		// },
		{
			"fieldname":"based_on_type",
			"label": __("Type"),
			// "reqd":1,
			"fieldtype": "Link",
			"options": "DocType",
			"default":"Item",
			"get_query": function() {
				return {
					filters: {"name": ["in", ["Item", "Item Group"]]}
				}
			}
		},
		{
			"fieldname":"based_on",
			"label": __("Item Code / Item Group"),
			"fieldtype": "Dynamic Link",
			"get_options": function() {
				var based_on_type = frappe.query_report.get_filter_value('based_on_type');
				var based_on = frappe.query_report.get_filter_value('based_on');
				if(based_on && !based_on_type) {
					frappe.throw(__("Please select Party Type first"));
				}
				return based_on_type;
			}
		},
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd":1
		},
		
		// {
		// 	"fieldname": "item_group",
		// 	"label": __("Item Group"),
		// 	"fieldtype": "Link",
		// 	"width": "80",
		// 	"options": "Item Group",
		// },
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
		console.log(this.filters)
		window.open(
			frappe.urllib.get_full_url("/app/allocation-details/Allocation%20Details?item_code="+encodeURIComponent(data["company"] +':'+ data["item"])));
	},
};
