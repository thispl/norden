// Copyright (c) 2023, Teampro and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Serial No Inventory Report"] = {
	"filters": [

		{
			"fieldname": "item_code",
			"label": __("Item Code"),
			"fieldtype": "Link",
			"width": "100",
			"options": "Item",

		},
		
		{
			"fieldname": "serial_no",
			"label": __("Serial Number"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Serial No",

		},

	]
};
