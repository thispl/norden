// Copyright (c) 2024, Teampro and contributors
// For license information, please see license.txt

frappe.query_reports["Stock Taken Report"] = {
	"filters": [
		{
			"label": __("Product"),
			"fieldname": "item",
			"fieldtype": "Link",
			"options": "Item",
		},
	]
};
