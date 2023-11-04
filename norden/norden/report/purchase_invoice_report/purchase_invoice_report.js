// Copyright (c) 2023, Teampro and contributors
// For license information, please see license.txt
/* eslint-disable */
// Copyright (c) 2023, Teampro and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Purchase Invoice Report"] = {
	"filters": [
		
		{
			"fieldname": "from_date",
            "label": __(" Invoice Date From"),
            "fieldtype": "Date",
			"reqd": 1
		},
		{
	
			"fieldname": "to_date",
			"label": __("Invoice Date To"),
			"fieldtype": "Date",
			"reqd": 1
		},
		{
			"fieldname": "supplier",
			"fieldtype": "Link",
			"options": "Supplier",
			"label": __("Vendor"),
			"width": "50px"
        },
		{
			"fieldname": "project",
			"fieldtype": "Link",
			"options": "Project",
			"label": __("Project"),
			"width": "50px"
        },
	]
};
