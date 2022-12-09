// Copyright (c) 2016, Teampro and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Item Stock Matrix"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Company",
			"mandatory": 1,
			"default": frappe.defaults.get_default("company")
		},
	]
};
