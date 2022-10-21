// Copyright (c) 2016, Teampro and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Item Stock Status"] = {
	"filters": [
		{
			"fieldname":"item_code",
			"label": __("Item"),
			"fieldtype": "Link",
			"options": "Item",
		},

	]
};
