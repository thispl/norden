// Copyright (c) 2025, Teampro and contributors
// For license information, please see license.txt

frappe.query_reports["Purchase Order"] = {
	"filters": [
        {
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Company",
			"reqd":1,
			"default": frappe.defaults.get_default("company")
		},
		{
            "label": __("From Date"),
            "fieldname": "from_date",
            "fieldtype": "Date",
            "default": "2024-01-01",
        },
        {
            "label": __("To Date"),
            "fieldname": "to_date",
            "fieldtype": "Date",
            "default": "2024-12-31",
        },
		{
			"label": __("Supplier"),
			"fieldname": "supplier",
			"fieldtype": "Link",
			"options": "Supplier",
		},
	]
};
