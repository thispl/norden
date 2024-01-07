# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import _
from frappe.desk.doctype.dashboard_chart.dashboard_chart import get_result
from frappe.utils import getdate
from frappe.utils.dashboard import cache_source
from frappe.utils.dateutils import get_period

# ... (import statements remain unchanged)

# ... (existing code remains unchanged)

@frappe.whitelist()
@cache_source
def get_data(chart_name=None, chart=None, no_cache=None, filters=None,
			 from_date=None, to_date=None, timespan=None, time_interval=None,
			 heatmap_year=None) -> dict[str, list]:
	if filters:
		filters = frappe.parse_json(filters)

		from_date = filters.get("from_date")
		to_date = filters.get("to_date")
		company = filters.get("company")
		success, achievement = get_records(from_date, to_date, "posting_date", company)
		success, achievement_data = get_values(from_date, to_date, "posting_date")
		if success and company:
			labels = [str(r[0]) for r in achievement]
			values = [float(r[1]) for r in achievement]

			return {
				"labels": labels,
				"datasets": [
					{
						"name": _("Item Group"),
						"values": values
					},
				],
			}
		else:
			labels = [str(r[0]) for r in achievement_data]
			values = [float(r[1]) for r in achievement_data]

			return {
				"labels": labels,
				"datasets": [
					{
						"name": _("Item Group"),
						"values": values
					},
				],
			}

def get_records(from_date: str, to_date: str, datefield: str, company: str) -> tuple[bool, list[tuple[str, float]]]:
    item_groups = {}
    sales_invoices = frappe.get_all("Sales Invoice", {
        'company': company,
        'docstatus': ('!=', 2),
        'posting_date': ('between', [from_date, to_date])
    }, ['name'])

    for invoice in sales_invoices:
        items = frappe.get_all("Sales Invoice Item", {'parent': invoice.name}, ['item_group', 'base_amount'])
        for item in items:
            item_group = item.item_group
            base_amount = item.base_amount
            item_groups.setdefault(item_group, 0)
            item_groups[item_group] += base_amount

    
    return True, list(item_groups.items())

def get_values(from_date: str, to_date: str, datefield: str) -> tuple[bool, list[tuple[str, float]]]:
    item_groups = {}
    sales_invoices = frappe.get_all("Sales Invoice", {
        'docstatus': ('!=', 2),
        'posting_date': ('between', [from_date, to_date])
    }, ['name'])

    for invoice in sales_invoices:
        items = frappe.get_all("Sales Invoice Item", {'parent': invoice.name}, ['item_group', 'base_amount'])
        for item in items:
            item_group = item.item_group
            base_amount = item.base_amount
            item_groups.setdefault(item_group, 0)
            item_groups[item_group] += base_amount

    
    return True, list(item_groups.items())
