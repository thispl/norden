// Copyright (c) 2024, Teampro and contributors
// For license information, please see license.txt

frappe.query_reports["Stock Analysis Report"] = {
	"filters": [
		{
			"label": __("Team"),
			"fieldname": "team",
			"fieldtype": "Link",
			"options": "Stock Team",
		},
		{
			"label": __("Stock Analysis"),
			"fieldname": "stock_analysis",
			"fieldtype": "Link",
			"options": "Stock Analysis",
		},
		{
			"label": __("Product"),
			"fieldname": "item",
			"fieldtype": "Link",
			"options": "Item",
		},
		{
			"label": __("Rack"),
			"fieldname": "rack",
			"fieldtype": "Link",
			"options": "Rack",
		},
	]
};
