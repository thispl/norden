// Copyright (c) 2023, Teampro and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["OT Process Report"] = {
	"filters": [
		{
			fieldname:"employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
		},
		{
			"fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
			"reqd":1
		},
		{
	
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"reqd":1
		},

	]
};
