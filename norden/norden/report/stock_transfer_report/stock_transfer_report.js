// Copyright (c) 2023, Teampro and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Stock Transfer Report"] = {
	"filters": [

		{
			"fieldname":"bill_of_entry",
			"label": __("Bill of Entry"),
			"fieldtype": "Link",
			"options": "Bill of Entry",
			// "reqd": 1
		},


		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			// "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			// "reqd": 1
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			// "default": frappe.datetime.get_today(),
			// "reqd": 1
		},

		{
			"fieldname":"source_warehouse",
			"label": __("Source Warehouse"),
			"fieldtype": "Link",
			"options": "Warehouse",
		},

		{
			"fieldname":"target_warehouse",
			"label": __("Target Warehouse"),
			"fieldtype": "Link",
			"options": "Warehouse",
		},

		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",

		},


	]
};
