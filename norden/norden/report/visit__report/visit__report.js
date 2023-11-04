// Copyright (c) 2023, Teampro and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Visit  Report"] = {
	"filters": [
		{
			"fieldname":"sales_person",
			"label": __("Sales Person"),
			"fieldtype": "Link",
			"options": "Sales Person",
			// "reqd": 1

		},
		{
			"fieldname":"date_of_visit",
			"label": __("From Date"),
			"fieldtype": "Date",
			"width": "100px",
			// "reqd": 1
		},
		{
			"fieldname":"expected_closing_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"width": "100px",
			// "reqd": 1
		},
		{
			"fieldname":"region",
			"label": __("Country"),
			"fieldtype": "Link",
			"width": "100px",
			"options": "Territory",
			// "reqd": 1
		},
		{
			"fieldname":"name_of_the_customer__distributor__si__eu__consultant",
			"label": __("Customer"),
			"fieldtype": "Data",
			"width": "100px",
			// "reqd": 1
		},

	]
};
