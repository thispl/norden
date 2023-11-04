// Copyright (c) 2023, Teampro and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Direct Transfer Report"] = {
	"filters": [
		{
			"fieldname": "from_date",
            "label": __("Transfer From Date"),
            "fieldtype": "Date",
			// "reqd":1
		},
		{
	
			"fieldname": "to_date",
			"label": __("Transfer To Date"),
			"fieldtype": "Date",
			// "reqd":1
		},
        {
			"fieldname": "from_warehouse",
            "label": __("From Warehouse"),
            "fieldtype": "Link",
			"options":"Warehouse",
			// "reqd":1
		},
		{
	
			"fieldname": "to_warehouse",
			"label": __("To Warehouse"),
			"fieldtype": "Link",
			"options":"Warehouse",
			// "reqd":1
		},
		{
			"fieldname":"transfer_no",
			"label": __("Transfer No"),
			"fieldtype": "Link",
			"options": "Stock Entry",
		},
	]
};
