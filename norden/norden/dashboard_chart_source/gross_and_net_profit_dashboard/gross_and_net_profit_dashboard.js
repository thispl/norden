frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Gross and Net Profit Dashboard"] = {
	method: "norden.norden.dashboard_chart_source.gross_and_net_profit_dashboard.gross_and_net_profit_dashboard.get_data",
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: "Norden Communication Pvt Ltd"
		},
		{
			fieldname: "fiscal_year",
			label: __("Fiscal Year"),
			fieldtype: "Link",
			options: "Fiscal Year",
			default: "2023 - 2024"
		},
		


	]
};
