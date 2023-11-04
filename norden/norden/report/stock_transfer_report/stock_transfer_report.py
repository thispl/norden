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
		_('Item Code') + ':Data:150',
		_('Item Name') + ':Data:300',
		_('UOM') + ':Data:100',
		_('Quantity') + ':Data:120',
		_('Bill of Entry') + ':Data:120',
		_('Source Warehouse') + ':Data:150',
		_('Target Warehouse') + ':Data:150',
		_('Voucher') + ':Data:150',
		_('Company') + ':Data:150',
		# _('Selling Price') + ':float:150',
		# _('Internal_cost') + ':Currency:100',
		# # _('Warehouse') + ':Data:120',
		# _('Stock UOM') + ':Data:150',
		# _('Balance') + ':Data:150',
	]
	return column


def get_data(filters):
	data = []
	if filters.from_date and filters.to_date and filters.warehouse:
		item = frappe.db.sql("""select `tabStock Entry`.company,`tabStock Entry`.name,`tabStock Entry Detail`.t_warehouse,`tabStock Entry Detail`.s_warehouse,`tabStock Entry Detail`.uom,`tabStock Entry`.bill_of_entry,`tabStock Entry Detail`.serial_no,`tabStock Entry`.to_warehouse,`tabStock Entry Detail`.item_code,`tabStock Entry Detail`.item_name,`tabStock Entry Detail`.qty from `tabStock Entry`
			left join `tabStock Entry Detail` on `tabStock Entry`.name = `tabStock Entry Detail`.parent
			where `tabStock Entry`.bill_of_entry = '%s' and posting_date between '%s' and '%s' and  `tabStock Entry Detail`.s_warehouse = '%s' and `tabStock Entry`.docstatus != 2 """%(filters.bill_of_entry,filters.from_date,filters.to_date,filters.warehouse),as_dict=True)
	
	if filters.bill_of_entry:
		item = frappe.db.sql("""select `tabStock Entry`.company,`tabStock Entry`.name,`tabStock Entry Detail`.t_warehouse,`tabStock Entry Detail`.s_warehouse,`tabStock Entry Detail`.uom,`tabStock Entry`.bill_of_entry,`tabStock Entry Detail`.serial_no,`tabStock Entry`.to_warehouse,`tabStock Entry Detail`.item_code,`tabStock Entry Detail`.item_name,`tabStock Entry Detail`.qty from `tabStock Entry`
		left join `tabStock Entry Detail` on `tabStock Entry`.name = `tabStock Entry Detail`.parent
		where `tabStock Entry`.bill_of_entry = '%s' and `tabStock Entry`.docstatus != 2 """%(filters.bill_of_entry),as_dict=True)

	if filters.from_date and filters.to_date and filters.bill_of_entry:
		item = frappe.db.sql("""select `tabStock Entry`.company,`tabStock Entry`.name,`tabStock Entry Detail`.t_warehouse,`tabStock Entry Detail`.s_warehouse,`tabStock Entry Detail`.uom,`tabStock Entry`.bill_of_entry,`tabStock Entry Detail`.serial_no,`tabStock Entry`.to_warehouse,`tabStock Entry Detail`.item_code,`tabStock Entry Detail`.item_name,`tabStock Entry Detail`.qty from `tabStock Entry`
			left join `tabStock Entry Detail` on `tabStock Entry`.name = `tabStock Entry Detail`.parent
			where `tabStock Entry`.bill_of_entry = '%s' and posting_date between '%s' and '%s' and `tabStock Entry`.docstatus != 2 """%(filters.bill_of_entry,filters.from_date,filters.to_date),as_dict=True)

	if filters.bill_of_entry and filters.source_warehouse:
		item = frappe.db.sql("""select `tabStock Entry`.company,`tabStock Entry`.name,`tabStock Entry Detail`.t_warehouse,`tabStock Entry Detail`.s_warehouse,`tabStock Entry Detail`.uom,`tabStock Entry`.bill_of_entry,`tabStock Entry Detail`.serial_no,`tabStock Entry`.to_warehouse,`tabStock Entry Detail`.item_code,`tabStock Entry Detail`.item_name,`tabStock Entry Detail`.qty from `tabStock Entry`
			left join `tabStock Entry Detail` on `tabStock Entry`.name = `tabStock Entry Detail`.parent
			where `tabStock Entry`.bill_of_entry = '%s' and  `tabStock Entry Detail`.s_warehouse = '%s' and `tabStock Entry`.docstatus != 2 """%(filters.bill_of_entry,filters.source_warehouse),as_dict=True)
	
	if filters.bill_of_entry and filters.target_warehouse:
		item = frappe.db.sql("""select `tabStock Entry`.company,`tabStock Entry`.name,`tabStock Entry Detail`.t_warehouse,`tabStock Entry Detail`.s_warehouse,`tabStock Entry Detail`.uom,`tabStock Entry`.bill_of_entry,`tabStock Entry Detail`.serial_no,`tabStock Entry`.to_warehouse,`tabStock Entry Detail`.item_code,`tabStock Entry Detail`.item_name,`tabStock Entry Detail`.qty from `tabStock Entry`
			left join `tabStock Entry Detail` on `tabStock Entry`.name = `tabStock Entry Detail`.parent
			where `tabStock Entry`.bill_of_entry = '%s' and  `tabStock Entry Detail`.t_warehouse = '%s' and `tabStock Entry`.docstatus != 2 """%(filters.bill_of_entry,filters.target_warehouse),as_dict=True)
	
	if filters.target_warehouse:
		item = frappe.db.sql("""select `tabStock Entry`.company,`tabStock Entry`.name,`tabStock Entry Detail`.t_warehouse,`tabStock Entry Detail`.s_warehouse,`tabStock Entry Detail`.uom,`tabStock Entry`.bill_of_entry,`tabStock Entry Detail`.serial_no,`tabStock Entry`.to_warehouse,`tabStock Entry Detail`.item_code,`tabStock Entry Detail`.item_name,`tabStock Entry Detail`.qty from `tabStock Entry`
			left join `tabStock Entry Detail` on `tabStock Entry`.name = `tabStock Entry Detail`.parent
			where `tabStock Entry Detail`.t_warehouse = '%s' and `tabStock Entry`.docstatus != 2 """%(filters.target_warehouse),as_dict=True)
	
	if filters.source_warehouse:
		item = frappe.db.sql("""select `tabStock Entry`.company,`tabStock Entry`.name,`tabStock Entry Detail`.t_warehouse,`tabStock Entry Detail`.s_warehouse,`tabStock Entry Detail`.uom,`tabStock Entry`.bill_of_entry,`tabStock Entry Detail`.serial_no,`tabStock Entry`.to_warehouse,`tabStock Entry Detail`.item_code,`tabStock Entry Detail`.item_name,`tabStock Entry Detail`.qty from `tabStock Entry`
			left join `tabStock Entry Detail` on `tabStock Entry`.name = `tabStock Entry Detail`.parent
			where `tabStock Entry Detail`.s_warehouse = '%s' and `tabStock Entry`.docstatus != 2 """%(filters.source_warehouse),as_dict=True)
	
	if filters.company:
		item = frappe.db.sql("""select `tabStock Entry`.company,`tabStock Entry`.name,`tabStock Entry Detail`.t_warehouse,`tabStock Entry Detail`.s_warehouse,`tabStock Entry Detail`.uom,`tabStock Entry`.bill_of_entry,`tabStock Entry Detail`.serial_no,`tabStock Entry`.to_warehouse,`tabStock Entry Detail`.item_code,`tabStock Entry Detail`.item_name,`tabStock Entry Detail`.qty from `tabStock Entry`
			left join `tabStock Entry Detail` on `tabStock Entry`.name = `tabStock Entry Detail`.parent
			where `tabStock Entry`.company = '%s' and `tabStock Entry`.docstatus != 2 """%(filters.company),as_dict=True)

	if not filters:
		item = frappe.db.sql("""select `tabStock Entry`.company,`tabStock Entry`.name,`tabStock Entry Detail`.t_warehouse,`tabStock Entry Detail`.s_warehouse,`tabStock Entry Detail`.uom,`tabStock Entry`.bill_of_entry,`tabStock Entry Detail`.serial_no,`tabStock Entry`.to_warehouse,`tabStock Entry Detail`.item_code,`tabStock Entry Detail`.item_name,`tabStock Entry Detail`.qty from `tabStock Entry`
			left join `tabStock Entry Detail` on `tabStock Entry`.name = `tabStock Entry Detail`.parent
			where `tabStock Entry`.docstatus != 2 """,as_dict=True)

	for i in item:
		# frappe.errprint(i.item_code,i.qty)
		row = [i.item_code,i.item_name,i.uom,i.qty,i.bill_of_entry,i.s_warehouse,i.t_warehouse,i.name,i.company]
		data.append(row)
	return data	

# def get_conditions(filters):
# 	conditions = ""
# 	if filters.bill_of_entry:
# 		conditions += " and `tabStock Entry`.bill_of_entry = %s ",%(filters.bill_of_entry)

# 	return conditions

