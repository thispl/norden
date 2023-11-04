// Copyright (c) 2023, Teampro and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sales Person Wise Report"] = {
	"filters": [
		{
			"fieldname": "sales_person",
			"label": __("Sales Person"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Sales Person",
		},

		{
			"fieldname": "quarter",
			"label": __("Quarter"),
			"fieldtype": "Select",
			"width": "80",
			"options": ["Quarter 1","Quarter 2","Quarter 3","Quarter 4"]
		},

		{
			"fieldname":"item_code",
			"label": __("Item"),
			"fieldtype": "Link",
			"options": "Item",
			"width": "100px",
			"reqd": 1
		},
		{
			"fieldname": "customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Customer",
		},

	]
};
