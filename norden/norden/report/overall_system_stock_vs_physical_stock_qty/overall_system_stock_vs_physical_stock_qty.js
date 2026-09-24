// Copyright (c) 2024, Teampro and contributors
// For license information, please see license.txt

frappe.query_reports["Overall System Stock vs Physical Stock Qty"] = {
	"filters": [
		{
			"label": __("Product"),
			"fieldname": "item",
			"fieldtype": "Link",
			"options": "Item",
		},
		{
			"label": __("Stock Analysis"),
			"fieldname": "stock_analysis",
			"fieldtype": "Link",
			"options": "Stock Analysis",
		},
	]
};
