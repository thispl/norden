frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Budgeted vs Actual"] = {
	method: "norden.norden.dashboard_chart_source.budgeted_vs_actual.budgeted_vs_actual.get_data",
	filters: [
		// {
		// 	fieldname: "territory",
		// 	label: __("Territory"),
		// 	fieldtype: "Link",
		// 	options: "Territory",
		// 	reqd: 1,
		// },
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company")
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
		{
			fieldname: "time_interval",
			label: __("Time Interval"),
			fieldtype: "Select",
			options: ["Monthly", "Quarterly", "Yearly"],
			default:  "Monthly",
			reqd: 1
		},
	]
};
