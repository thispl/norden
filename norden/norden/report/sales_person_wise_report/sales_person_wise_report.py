# Copyright (c) 2023, Teampro and contributors
# For license information, please see license.txt

# import frappe
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
from frappe.utils import cstr, cint
from erpnext.setup.utils import get_exchange_rate


def execute(filters=None):
	columns, data = [] ,[]
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	column = [
		_('Sales Person') + ':Data:160',
		# _('Item Name') + ':Data:350',
	]
	Quarter_1= ["Jan","Feb","Mar"]
	Quarter_2 =["Apr","May","Jun"]
	Quarter_3 =["Jul","Aug","Sep"]
	Quarter_4 =["Oct","Nov","Dec"]
	
	if filters.quarter == "Quarter 1":
		for s in Quarter_1:
			column.append(_(s) + ':Float:/250')
		column.append(_("Total") + ':Float:/250')
		column.append(_("Pending Order") + ':Float:/250')
		column.append(_("Total Expected") + ':Float:/250')
		column.append(_("Jan") + ':Date:/250')
		column.append(_("Feb") + ':Date:/250')
		column.append(_("Mar") + ':Date:/250')
		

	if filters.quarter == "Quarter 2":
		for s in Quarter_2:
			column.append(_(s) + ':Float:/250')
		column.append(_("Total") + ':Float:/250')
		column.append(_("Pending Order") + ':Float:/250')
		column.append(_("Total Expected") + ':Float:/250')
		column.append(_("Jan") + ':Date:/250')
		column.append(_("Feb") + ':Date:/250')
		column.append(_("Mar") + ':Date:/250')

	if filters.quarter == "Quarter 3":
		for s in Quarter_3:
			column.append(_(s) + ':Currency:/250')
		column.append(_("Total") + ':Float:/250')
		column.append(_("Pending Order") + ':Float:/250')
		column.append(_("Total Expected") + ':Float:/250')
		column.append(_("Jan") + ':Date:/250')
		column.append(_("Feb") + ':Date:/250')
		column.append(_("Mar") + ':Date:/250')

	if filters.quarter == "Quarter 4":
		for s in Quarter_3:
			column.append(_(s) + ':Currency:/250')
		column.append(_("Total") + ':Float:/250')
		column.append(_("Pending Order") + ':Float:/250')
		column.append(_("Total Expected") + ':Float:/250')
		column.append(_("Jan") + ':Date:/250')
		column.append(_("Feb") + ':Date:/250')
		column.append(_("Mar") + ':Date:/250')

	return column


def get_data(filters):
	data = []
	if filters.sales_person:
		sp = frappe.get_all("Sales Person",{"name":filters.sales_person,},["*"])

	elif filters.customer:
		sp = frappe.get_all("Sales Person",{"customer":filters.company,},["*"])

	# elif filters.item_code:
	# 	sp = frappe.db.sql(""" select sales_person from `tabSales Invoice Item` where `tabSales Invoice Item`.item_code = '%s' """ %(filters.item_code),as_dict=True)
	for s in sp:
		# so_1 = frappe.db.sql(""" select grand_total from `tabSales Order` where transaction_date between "2023-01-01" and "2023-03-31" and sale_person = %s """ %(),as_dict=True)
		emp = frappe.get_value("Sales Person",{"name":s.name},["employee"])
		target = frappe.get_value("Sales Person",{"name":s.name},["target"])
		user = frappe.get_value("Employee",{"name":emp},["user_id"])
		if filters.quarter == "Quarter 1":
			si_1 = frappe.get_all("Sales Invoice",{"sale_person":user,"posting_date": ["between", ["2023-01-01", "2023-01-31"]]},["*"])
			si_2 = frappe.get_all("Sales Invoice",{"sale_person":user,"posting_date": ["between", ["2023-02-01", "2023-02-28"]]},["*"])
			si_3 = frappe.get_all("Sales Invoice",{"sale_person":user,"posting_date": ["between", ["2023-03-01", "2023-03-31"]]},["*"])
			# so_1 = frappe.get_all("Sales Order",{"sale_person":user,"transaction_date": ["between", ["2023-01-01", "2023-03-31"]],"status":["!=","Completed"]},["*"])
			so_1 = frappe.db.sql(""" select grand_total ,currency from `tabSales Order` where transaction_date between "2023-01-01" and "2023-03-31" and sale_person = '%s' and status != "Completed" """ %(user),as_dict=True)
			frappe.errprint (so_1)