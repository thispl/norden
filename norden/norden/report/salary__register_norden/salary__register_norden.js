// Copyright (c) 2016, Teampro and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Salary  Register Norden"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"default":frappe.datetime.month_start(),
			"reqd": 1,
			"fieldtype": "Date",
			
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"default":frappe.datetime.month_end(),
			"reqd": 1,
			"fieldtype": "Date",
			
		},
		{
			"fieldname":"employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": "100px"
		},
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"width": "100px",
			"reqd": 1
		},
		{
			"fieldname":"docstatus",
			"label":__("Document Status"),
			"fieldtype":"Select",
			"options":["Draft", "Submitted", "Cancelled"],
			"width": "100px"
		}

	]
};
