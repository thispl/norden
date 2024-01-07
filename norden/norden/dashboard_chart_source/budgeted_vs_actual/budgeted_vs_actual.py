# # Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# # License: GNU General Public License v3. See license.txt

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

        from_date = filters.get("from_date")
        to_date = filters.get("to_date")

        all_territories = get_all_territories()

        all_targets = get_all_targets()

        territory_names = territory_name(filters.get("company"))

        achievement_data = []

        for territory in territory_names:
            achievement = get_records(from_date, to_date, "posting_date", filters.get("company"), territory)
            territory_achievement = get_result(achievement, filters.get("time_interval"), from_date, to_date, "Sum")
            if any(r[1] != 0.0 for r in territory_achievement):
                achievement_data.extend(territory_achievement)

        if achievement_data:
            return {
                "labels": territory_names,
                "datasets": [
                    {"name": _("Target Amount"), "values": [format(all_targets.get(territory, 0.0)) for territory in all_territories]},
                    {"name": _("Achievement Amount"), "values": [format(r[1]) for r in achievement_data]},
                ],
            }

def get_records(from_date: str, to_date: str, datefield: str, company: str, territory:str) -> list[tuple[str, float, int]]:
	
	filters = [
		["Sales Invoice", "company", "=", company],
		["Sales Invoice", datefield, ">=", from_date, False],
		["Sales Invoice", datefield, "<=", to_date, False],
		["Sales Invoice", "territory", "=", territory, False],

	]
	
	data = frappe.db.get_list(
		"Sales Invoice",
		fields=[f"{datefield} as _unit", "SUM(grand_total) as total_amount", "COUNT(*) as count",'docstatus != 2'],
		filters=filters,
		group_by="_unit",
		order_by="_unit asc",
		as_list=True,
		ignore_ifnull=True,
	)
	return data

def get_all_territories() -> list:
	territories = frappe.get_all("Territory", fields=['name'])
	return [territory.get('name') for territory in territories]

def get_all_targets() -> dict:
	territories = get_all_territories()
	targets = {}

	for territory in territories:
		target_value = frappe.get_value("Target Detail", {'parent': territory}, 'target_amount')
		targets[territory] = float(target_value) if target_value else 0.0

	return targets

def territory_name(company: str) -> list:
    territory_names = frappe.get_all("Sales Invoice", {'company': company}, ['territory'], distinct=True)
    return [i.territory for i in territory_names]

