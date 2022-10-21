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
		_('Item') + ':Data:120',
		_('Item Name') + ':Data:300',
		# _('UOM') + ':Data:100',
		_('Selling Price') + ':Currency:150',
		# _('Internal_cost') + ':Currency:100',
		# # _('Warehouse') + ':Data:120',
		# _('Stock UOM') + ':Data:150',
		# _('Balance') + ':Data:150',
	]
	return column


def get_data(filters):
	data = []
	frappe.errprint(filters.item_code)
	if filters.price_list:
		item = frappe.db.sql(""" select * from `tabItem Price` where price_list = '%s' """%(filters.price_list),as_dict=True)
	
	if filters.item_code and filters.price_list:
		item = frappe.db.sql(""" select * from `tabItem Price` where price_list = '%s' and item_code = '%s' """%(filters.price_list,filters.item_code),as_dict=True)
	
	for i in item:
		frappe.errprint(i.item_code)
		row = [i.item_code,i.item_name,i.price_list_rate]
		data.append(row)
	return data	
	# 	data.append(row)
	# item_price = frappe.get_all("Item Price",["*"])
	# if filters.item_code:
	# 	item_price = frappe.get_all("Item Price",{"item_code":filters.item_code},["*"])
	# 	frappe.errprint("1")

	# # elif filters.price_list:
	# # 	frappe.errprint("2")
	# # 	item_price = frappe.get_all("Item Price",{"price_list":filters.price_list,"item_code":filters.item_code},["*"])

	# else:
	# 	frappe.errprint("3")
	# 	item_price = frappe.get_all("Item Price",["*"])
	# for i in item_price[:100]:
	# 	frappe.errprint(i.price_list_rate)
	# 	row = [i.item_code,i.price_list_rate]
	# 	data.append(row)

	# role = frappe.session.user
	# country = frappe.get_all("User Permission",{'user':role},["*"])
	# for a in country:
	# 	if a.allow == "Company":
	# 		frappe.errprint(a.for_value)
	# for i in item:
	# 	if filters.company == "Norden Singapore PTE LTD":
	# 		internal_cost = frappe.get_value("Item Price",{"price_list":"Singapore Internal Cost","item_code":i.name},["price_list_rate"])
	# 		sales_price = frappe.get_value("Item Price",{"price_list":"Singapore Sales Price","item_code":i.name},["price_list_rate"])

	# 	if filters.company == "Norden Communication Middle East FZE":
	# 		internal_cost =frappe.get_value("Item Price",{"price_list":"Internal - NCMEF","item_code":i.name},["price_list_rate"])
	# 		sales_price = frappe.get_value("Item Price",{"price_list":"Base Sales Price - NCMEF","item_code":i.name},["price_list_rate"])

	# 	if filters.company == "Norden Communication India" or filters.company == "Norden Communication Pvt Ltd":
	# 		internal_cost =frappe.get_value("Item Price",{"price_list":"India Landing","item_code":i.name},["price_list_rate"])
	# 		sales_price = frappe.get_value("Item Price",{"price_list":"Standard Selling","item_code":i.name},["price_list_rate"])

	# 	if filters.company == "Norden Communication UK Limited":
	# 		internal_cost =frappe.get_value("Item Price",{"price_list":"UK Destination Charges","item_code":i.name},["price_list_rate"])
	# 		sales_price = frappe.get_value("Item Price",{"price_list":"UK Price list","item_code":i.name},["price_list_rate"])

	# 	if internal_cost and sales_price:
	# 		row = [i.name,i.item_name,i.stock_uom,sales_price,internal_cost]
	# 		data.append(row)
	