frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Item Group Wise - Sales Invoice"] = {
	method: "norden.norden.dashboard_chart_source.item_group_wise___sales_invoice.item_group_wise___sales_invoice.get_data",
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default:  frappe.datetime.month_end(),
		},
		// {
		// 	fieldname: "time_interval",
		// 	label: __("Time Interval"),
		// 	fieldtype: "Select",
		// 	options: ["Monthly", "Quarterly", "Yearly"],
		// 	default:  "Yearly",
		// 	reqd: 1
		// },
	]
};
