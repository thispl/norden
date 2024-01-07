frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Company Wise Sales Person Target"] = {
	method: "norden.norden.dashboard_chart_source.company_wise_sales_person_target.company_wise_sales_person_target.get_data",
	filters: [
		// {
		// 	fieldname: "sales_person",
		// 	label: __("Sales Person"),
		// 	fieldtype: "Link",
		// 	options: "Sales Person",
		// 	default: frappe.defaults.get_user_default("Sales Person"),
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
			fieldname: "start_date",
			label: __("Start Date"),
			fieldtype: "Date",
			default: '2022-01-01',
			reqd: 1,
		},
		{
			fieldname: "end_date",
			label: __("End Date"),
			fieldtype: "Date",
			default: '2022-12-31',
		},
		{
			fieldname: "time_interval",
			label: __("Time Interval"),
			fieldtype: "Select",
			options: ["Monthly", "Quarterly", "Yearly"],
			default:  "Yearly",
			reqd: 1
		},
	]
};
