// Copyright (c) 2024, Teampro and contributors
// For license information, please see license.txt

frappe.query_reports["Stock Balance Report - Warehouse Wise"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Company",
			"default": frappe.defaults.get_default("company"),
			"reqd":1
		},
		{
			"fieldname": "item_group",
			"label": __("Item Group"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Item Group",
			"reqd":1
		}
	]
};
