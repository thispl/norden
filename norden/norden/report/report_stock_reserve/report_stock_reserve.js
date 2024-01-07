// Copyright (c) 2023, Teampro and contributors
// For license information, please see license.txt

frappe.query_reports["Report Stock Reserve"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
		},
		{
			"fieldname":"custom_reservation_status",
			"label": __("Reservation Status"),
			"fieldtype": "Select",
			"options": ["","Reserved"],
		},

	]
};
