frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Stock Value Changes on month basis"] = {
	method: "norden.norden.dashboard_chart_source.stock_value_changes_on_month_basis.stock_value_changes_on_month_basis.get_data",
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: "Norden Communication Pvt Ltd"
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: '2023-01-01',
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: '2023-12-31',
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
