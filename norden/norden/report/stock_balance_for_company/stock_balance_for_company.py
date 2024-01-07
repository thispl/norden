# Copyright (c) 2023, Teampro and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from six import string_types
import frappe
import json
from frappe.utils import (getdate, cint, add_months, date_diff, add_days,
    nowdate, get_datetime_str, cstr, get_datetime, now_datetime, format_datetime)
from frappe.utils import get_first_day, today, get_last_day, format_datetime, add_years, date_diff, add_days, getdate, cint, format_date,get_url_to_form
from frappe.utils import add_months, add_days, format_time, today, nowdate, getdate, format_date
from datetime import datetime, time, timedelta
import datetime
from calendar import monthrange
from frappe import _, msgprint
from frappe.utils import flt
from frappe.utils import cstr, cint, getdate


def execute(filters=None):
	columns, data = [] ,[]
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	column = [
		_('Item') + ':Data:160',
		_('Item Name') + ':Data:350'
	]
	if filters.company:
		company = frappe.db.sql(""" select name from `tabCompany` where company = "%s" """ %(filters.company),as_dict=True)
	if not filters.company:
		company = frappe.db.sql(""" select name from `tabCompany` """,as_dict=True)
	for c in company:
		if c.name == 'Norden Communication India':
			c.name = "NC"
		if c.name == 'Norden Communication Middle East FZE':
			c.name = "NCME"
		if c.name == 'Norden Communication Pvt Ltd':
			c.name = "NCPL"
		if c.name == 'NCPL -Bangalore':
			c.name = "NCPLB"
		if c.name == 'Norden Singapore PTE LTD':
			c.name = "NSPL"
		if c.name == 'Norden Communication UK Limited':
			c.name = "NCUL"
		if c.name == 'Sparcom Ningbo Telecom Ltd':
			c.name = "SNTL"
		if c.name == 'Norden research and Innovation Centre  Pvt. Ltd':
			c.name = "NRIC"
		if c.name == 'Norden Africa':
			c.name = "NSA"	
		column.append(_(c.name) + ':Data:140')
		column.append(_(c.name + " Val Rate") + ':Float:140')
	return column

def get_data(filters):
	data = []
	company = frappe.db.sql(""" select name from `tabCompany` """,as_dict=True)
	# for s in company:
	if filters.item_code:
		item = frappe.get_all("Item",{"name":filters.item_code},["*"])
	if not filters:
		item = frappe.get_all("Item",["*"])
	valuation_rate = 0
	qty = 0
	for i in item:
		row = [i.item_code,i.item_name]
		for c in company:

			warehouse_stock = frappe.db.sql("""
            select sum(b.actual_qty) as qty from `tabBin` b 
            join `tabWarehouse` wh on wh.name = b.warehouse
            join `tabCompany` c on c.name = wh.company
            where b.item_code = '%s' and wh.company = '%s' and b.valuation_rate > 0
            """ % (i.item_code,c.name),as_dict=True)[0]
			source_warehouse = frappe.db.get_value('Warehouse', {'default_for_stock_transfer':1,'company':c.name }, ["name"])

			warehouse_vr = frappe.db.sql("""
            select min(b.valuation_rate) as valuation_rate from `tabBin` b 
            join `tabWarehouse` wh on wh.name = b.warehouse
            join `tabCompany` c on c.name = wh.company
            where b.item_code = '%s' and wh.company = '%s' and b.valuation_rate > 0
            """ % (i.item_code,c.name),as_dict=True)[0]
			frappe.errprint(warehouse_vr["valuation_rate"])
			if warehouse_stock["qty"] and warehouse_vr["valuation_rate"]:
				qty = warehouse_stock["qty"]
				valuation_rate = warehouse_vr["valuation_rate"]
				row += [qty,valuation_rate]
			else:
				row += [0,0]

		data.append(row)
	return data	