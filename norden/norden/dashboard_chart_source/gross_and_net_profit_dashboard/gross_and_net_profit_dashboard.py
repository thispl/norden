# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import copy

import frappe
from frappe import _
from frappe.utils import flt
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
		fiscal_year = filters.get("fiscal_year")
		company = filters.get("company")
		gross = gross_profit(fiscal_year, filters.get("company"))
		net = net_proft(fiscal_year, filters.get("company"))
		return {
			"labels": [company],
			"datasets": [
				{"name": _("Gross Profit"), "values": [gross]},
				{"name": _("Net Profit"), "values": [gross - net]},
			],
		}

def gross_profit(fiscal_year:str, company: str) -> list[tuple[str, float, int]]:
	input_string = company
	first_letters = [word[0] for word in input_string.split()]
	output_string = ''.join(first_letters)
	total1 = 0
	total2 = 0
	total = 0
	to_tal=0
	to_tal1=0
	to_tal2=0
	input_string = company
	first_letters = [word[0] for word in input_string.split()]
	output_string = ''.join(first_letters) 	
	gl_entries = frappe.get_all("GL Entry", {'is_cancelled':'0','company': company, 'account': f"Stock Adjustment - {output_string}", 'fiscal_year': fiscal_year}, ['credit','debit'])
	for entry in gl_entries:
		total1 += entry.credit
		total2 += entry.debit
		total = total1-total2
	gl_entries = frappe.get_all("GL Entry",{'is_cancelled':'0','company':company,'account': ('in',[f"Sales - {output_string}",f"Customs Duty Scrip - Discount received - {output_string}"]),'fiscal_year':fiscal_year}, ['credit','debit'])
	for entry in gl_entries:
		to_tal1 += entry.credit
		to_tal2 += entry.debit
		to_tal = to_tal1-to_tal2
	return to_tal
	

def net_proft(fiscal_year:str ,company: str) -> list[tuple[str, float, int]]:
	total = 0
	total1=0
	total2=0
	to_tal1=0
	to_tal2=0
	to_tal = 0
	value =0
	value1=0
	value2=0
	sold=0
	sold1=0
	sold2=0
	sold3=0
	sold4=0
	sold5=0
	input_string = company
	first_letters = [word[0] for word in input_string.split()]
	output_string = ''.join(first_letters)
	account = frappe.get_all('Account',['name','parent_account'])
	for i in account:	
		if i.name ==f'Customs and clearance Charge - {output_string}':	
			gl_entries = frappe.get_all("GL Entry", {'is_cancelled':'0','company':company,'account':i.name,'fiscal_year':fiscal_year}, ['debit','credit'])
			for entry in gl_entries:
				total1 += entry.debit
				total2 += entry.credit
				total = total1 - total2
		if i.name == f'Loading & Unloading charge - {output_string}':
			gl_entries = frappe.get_all("GL Entry", {'is_cancelled':'0','company':company,'account': i.name,'fiscal_year':fiscal_year}, ['debit','credit'])
			for entry in gl_entries:
				to_tal1 += entry.debit
				to_tal2 += entry.credit
				to_tal = to_tal1-to_tal2
		if i.name == f'Cost of Goods Sold - {output_string}':
			gl_entries = frappe.get_all("GL Entry", {'is_cancelled':'0','company':company,'account': i.name,'fiscal_year':fiscal_year}, ['debit','credit'])
			for entry in gl_entries:
				sold1 += entry.debit
				sold2 += entry.credit
				sold = sold1-sold2
		if i.name == f'Packing Material - {output_string}':
			gl_entries = frappe.get_all("GL Entry", {'is_cancelled':'0','company':company,'account': i.name,'fiscal_year':fiscal_year}, ['debit','credit'])
			for entry in gl_entries:
				sold3 += entry.debit
				sold4 += entry.credit
				sold5 = sold3-sold4
		if i.parent_account == f'Indirect Expenses - {output_string}':
			gl_entries = frappe.get_all("GL Entry", {'is_cancelled':'0','company':company,'account': i.name,'fiscal_year':fiscal_year}, ['debit','credit'])
			for entry in gl_entries:
				value1 += entry.debit
				value2 += entry.credit
				value = value1-value2
	return total+to_tal+value+sold+sold5