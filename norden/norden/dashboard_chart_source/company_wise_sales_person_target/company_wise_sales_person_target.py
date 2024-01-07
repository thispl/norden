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
		start_date = filters.get("start_date")
		end_date = filters.get("end_date")
		company = filters.get("company")
		all_salespersons = frappe.get_all("Sales Person", filters={"company": company}, pluck="name")
		all_labels = []
		all_target_values = []
		all_achievement_values = []
		all_achievement_values_2022 =[]
		for sales_person in all_salespersons:
			target = get_target(sales_person)
			achievement = get_records(from_date, to_date, "posting_date", company, sales_person)
			achievement_2022 =get_records(start_date, end_date, "posting_date", company, sales_person)
			achievement_data = get_result(achievement, filters.get("time_interval"), from_date, to_date, "Sum")
			achievement_data_2022 = get_result(achievement_2022, filters.get("time_interval"), from_date, to_date, "Sum")
			all_labels.extend([sales_person for _ in achievement_data])
			all_target_values.extend([format(target) for _ in achievement_data])
			all_achievement_values.extend([format(r[1]) for r in achievement_data])
			all_achievement_values_2022.extend([format(r[1]) for r in achievement_data_2022])
		return {
			"labels": all_labels,
			"datasets": [
				{"name": _("Target Amount"), "values": all_target_values},
				{"name": _("Achievement Amount 2022"), "values": all_achievement_values_2022},
				{"name": _("Achievement Amount 2023"), "values": all_achievement_values},
			],
		}

def get_records(from_date: str, to_date: str, datefield: str, company: str, sales_person:str) -> list[tuple[str, float, int]]:
	filters = [
		["Sales Invoice", "company", "=", company],
		["Sales Invoice", datefield, ">=", from_date, False],
		["Sales Invoice", datefield, "<=", to_date, False],
		["Sales Invoice", "sales_person_user", "=", sales_person, False],

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

def get_target(sales_person: str) -> float:
	target = frappe.db.get_value("Sales Person", {'name': sales_person}, ['target'])
	return float(target) if target else 0.0

def get_records(start_date: str, end_date: str, datefield: str, company: str, sales_person:str) -> list[tuple[str, float, int]]:
	filters = [
		["Sales Invoice", "company", "=", company],
		["Sales Invoice", datefield, ">=", start_date, False],
		["Sales Invoice", datefield, "<=", end_date, False],
		["Sales Invoice", "sales_person_user", "=", sales_person, False],

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

