frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Expense Claim Budget vs Actual"] = {
	method: "norden.norden.dashboard_chart_source.expense_claim_budget_vs_actual.expense_claim_budget_vs_actual.get_data",
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: "Norden Communication Pvt Ltd"
		},

	]
};
