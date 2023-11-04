# Copyright (c) 2023, Teampro and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	columns=get_columns(filters)
	data = get_data(filters) 
	return columns, data

def get_columns(filters):
	columns = []
	columns += [
		_("Order No") + ":Link/Sales Order:110",
		_("File No") + ":Data:200",
		_("Customer Name") + ":Data:200",
		_("Sales Person")+":Link/Sales Person:110",
		_("Order Date") + ":Data:100",
		_("Delivery Date") + ":Data:100",
		_("Status") + ":Data:100",
		_("Currency") + ":Data:80",
		_("Grand Total") + ":Data:90",
		_("VAT") + ":Data:80",
		_("Grand Total(BC)") + ":Data:90",
		
	]
	return columns

def get_conditions(filters):
	conditions = ""
	if filters.from_date and filters.to_date:
		conditions += "  transaction_date between %(from_date)s and %(to_date)s"
	if filters.get("sales_person_user"):
		conditions += " and sales_person_user = %(sales_person_user)s"
	if filters.get("customer"):
		conditions += " and customer= %(customer)s"
	if filters.get("status"):
		conditions += " and status= %(status)s"
	if filters.get("company"):
		conditions += " and company= %(company)s"
	if filters.get("sales_person_user"):
		conditions +=" and sales_person_user=%(sales_person_user)s"
	return conditions, filters



def get_data(filters):
	data = []
	frappe.errprint('hi')
	conditions, filters = get_conditions(filters)
	sa = []
	if filters:
		sa = frappe.db.sql("""select * from `tabSales Order` where status != "Cancelled" and  %s """%conditions, filters,as_dict=True)
	if sa:
		for i in sa:
			row=[i.name,i.file_number,i.customer,i.sales_person_user,i.transaction_date,i.delivery_date,i.sales_person_user,i.status,i.currency,i.total,i.total_taxes_and_charges,i.grand_total]
			data.append(row)
	return data
