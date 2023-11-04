// Copyright (c) 2023, Teampro and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Stock Ageing Report"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1
		},
		{
			"fieldname":"to_date",
			"label": __("As On Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
		{
			"fieldname":"warehouse",
			"label": __("Warehouse"),
			"fieldtype": "Link",
			"options": "Warehouse",
			get_query: () => {
				const company = frappe.query_report.get_filter_value("company");
				return {
					filters: {
						...company && {company},
					}
				};
			}
		},
		{
			"fieldname":"item_code",
			"label": __("Item"),
			"fieldtype": "Link",
			"options": "Item"
		},
		{
			"fieldname":"brand",
			"label": __("Brand"),
			"fieldtype": "Link",
			"options": "Brand"
		},
		{
			"fieldname":"range",
			"label": __("Ageing Range"),
			"fieldtype": "Int",
			"default": "180",
			"reqd": 1
		},
		// {
		// 	"fieldname":"range2",
		// 	"label": __("Ageing Range 2"),
		// 	"fieldtype": "Int",
		// 	"default": "60",
		// 	"reqd": 1
		// },
		// {
		// 	"fieldname":"range3",
		// 	"label": __("Ageing Range 3"),
		// 	"fieldtype": "Int",
		// 	"default": "90",
		// 	"reqd": 1
		// },

		// {
		// 	"fieldname":"range4",
		// 	"label": __("Ageing Range 4"),
		// 	"fieldtype": "Int",
		// 	"default": "180",
		// 	"reqd": 1
		// },

		{
			"fieldname":"show_warehouse_wise_stock",
			"label": __("Show Warehouse-wise Stock"),
			"fieldtype": "Check",
			"default": 0
		}

	]
};
