// Copyright (c) 2026, Teampro and contributors
// For license information, please see license.txt

frappe.query_reports["Item Group summary"] = {
	"filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "reqd": 1,
            "default": frappe.datetime.month_start()
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "reqd": 1,
            "default": frappe.datetime.month_end()
        },
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "reqd": 1,
            "default": frappe.defaults.get_user_default("Company")
        },
        {
            "fieldname": "item_group",
            "label": __("Item Group"),
            "fieldtype": "Link",
            "options": "Item Group"
        },
        {
            "fieldname": "cost_type",
            "label": __("Cost Type"),
            "fieldtype": "Select",
            "options": ["Base Cost", "Landing Cost"],
            "reqd": 1,
            "default": "Base Cost"
        }
    ],

    "onload": function(report) {
        // Optional: auto refresh on load
        report.trigger_refresh();
    },

    // "formatter": function(value, row, column, data, default_formatter) {
    //     value = default_formatter(value, row, column, data);

    //     // Highlight Gross Profit
    //     if (column.fieldname === "gross_profit") {
    //         if (data && data.gross_profit < 0) {
    //             value = `<span style="color:red;">${value}</span>`;
    //         } else {
    //             value = `<span style="color:green;">${value}</span>`;
    //         }
    //     }

    //     // Highlight GP %
    //     if (column.fieldname === "gp_percent") {
    //         if (data && data.gp_percent < 10) {
    //             value = `<span style="color:red;">${value}</span>`;
    //         } else {
    //             value = `<span style="color:blue;">${value}</span>`;
    //         }
    //     }

    //     return value;
    // }
};