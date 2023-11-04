// Copyright (c) 2023, Teampro and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sales Invoice Report"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Company",
			"default": frappe.defaults.get_default("company")
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"width": "80",
			"reqd": 1,
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"width": "80",
			"reqd": 1,
		},
		{
			"fieldname":"customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Customer",
		},
		{
			"fieldname":"sales_person_user",
			"label": __("Sales Person"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Sales Person",
			// "reqd": 1,
			// "default": frappe.defaults.get_default("Sales Person")
		},
		{
			"fieldname":'status',
			"label": __("Status"),
			"fieldtype": "Select",
			"width": "90",
			"options":["",
			"Draft",
			'Return',
			'Credit Note Issued',
			'Submitted',
			'Paid',
			'Partly Paid',
			'Unpaid',
			'Unpaid and Discounted',
			'Partly Paid and Discounted',
			'Overdue and Discounted',
			'Overdue',
			'Internal Transfer'
		]
		}
	]
};
