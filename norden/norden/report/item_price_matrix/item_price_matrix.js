// Copyright (c) 2016, Teampro and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Item Price Matrix"] = {
	"filters": [

		{
			"fieldname": "territory",
			"label": __("Territory"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Territory",
			"mandatory": 1,
			"default": frappe.defaults.get_default("company")
		},

	]
};
