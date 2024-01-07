# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import _
from frappe.desk.doctype.dashboard_chart.dashboard_chart import get_result
from frappe.utils import getdate
from frappe.utils.dashboard import cache_source
from frappe.utils.dateutils import get_period

@frappe.whitelist()
@cache_source
def get_data(chart_name=None, chart=None, no_cache=None, filters=None,
			 from_date=None, to_date=None, timespan=None, time_interval=None,
			 heatmap_year=None) -> dict[str, list]:
	if filters:
		filters = frappe.parse_json(filters)
		company = filters.get("company")
		targets = get_budget(company)
		actual_data = actual_amount(company)

		labels = [target.get("name") for target in targets]
		budget_values = [target.get("budget_amount") for target in targets]
		actual_values = [ledger.get("opening_debit", 0) for ledger in actual_data]

		return {
			"labels": labels,
			"datasets": [
				{
					"name": _("Budget Amount"),
					"values": budget_values
				},
				{
					"name": _("Actual Amount"),
					"values": actual_values
				},
			],
		}

def get_budget(company: str) -> list[dict]:
	target_name = frappe.db.get_value("Budget", {'company': company,'fiscal_year':'2023 - 2024'}, ['name'])
	amounts = []
	if target_name:
		amount_records = frappe.get_all("Budget Account", {'parent': target_name}, ['budget_amount', 'account'])
		for record in amount_records:
			amounts.append({"name": record['account'], "budget_amount": record['budget_amount']})
	return amounts

def actual_amount(company: str) -> list[dict]:
	target_name = frappe.db.get_value("Budget", {'company': company}, ['name'])
	ledger_entries = []
	amount_records = frappe.get_all("Budget Account", {'parent': target_name}, ['account'])
	for record in amount_records:
		ledger = frappe.db.sql("""
			SELECT account, SUM(debit) as opening_debit
			FROM `tabGL Entry`
			WHERE company = %s AND account = %s
		""", (company, record['account']), as_dict=True)
		ledger_entries.extend(ledger)
	return ledger_entries
