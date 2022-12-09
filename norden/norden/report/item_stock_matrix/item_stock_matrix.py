# Copyright (c) 2013, Teampro and contributors
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
		_('Item') + ':Data:180',
		_('Item Name') + ':Data:250',
		_('Uom') + ':data:100',
		_('Stock') + ':data:100',
		# _('Internal Cost') + ':Currency:100',
		# _('Sales price') + ':Currency:100',
		# # _('Selling Price') + ':Currency:150',
		# # _('Internal_cost') + ':Currency:100',
		# # # _('Warehouse') + ':Data:120',
		# # _('Stock UOM') + ':Data:150',
		# _('Balance') + ':Data:150',
	]
	return column

def get_data(filters):
	data = []
	item = frappe.get_all("Item",["item_code","item_name","stock_uom"])	
	for i in item:
		country = frappe.get_value("Company",{"name":filters.company},["country"])
		warehouse_stock = frappe.db.sql("""
		select sum(b.actual_qty) as qty from `tabBin` b 
		join `tabWarehouse` wh on wh.name = b.warehouse
		join `tabCompany` c on c.name = wh.company
		where c.country = '%s' and b.item_code = '%s' and wh.company = '%s'
		""" % (country,i["item_code"],filters.company),as_dict=True)[0]
		if warehouse_stock["qty"]:
			row = [i.item_code,i.item_name,i.stock_uom,warehouse_stock["qty"]]
			data.append(row)
	return data	
		
		
			

		
	
		
		
