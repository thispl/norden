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
		_("PO NO") + ":Link/Purchase Order:110",
		_("File NO") + ":Data:100",
		_("Title") + ":Data:100",
		_("Vendor") + ":Data:100",
		_("Order Date") + ":Data:100",
		_("Status") + ":Data:100",
		_("Grand Total") + ":Data:100",
		_("Grand Total (BC)") + ":Data:110"
	]
	return columns

def get_conditions(filters):
	conditions = ""
	if filters.get("from_date") and filters.get("to_date"):
		conditions += " transaction_date between %(from_date)s and %(to_date)s"
	if filters.get("supplier"):
		conditions += " and supplier= %(supplier)s"
	if filters.get("status"):
		conditions += " and status = %(status)s"
	
	return conditions, filters

def get_data(filters):
	data = []
	conditions, filters = get_conditions(filters)
	sa = []
	sa = frappe.db.sql("""select * from `tabPurchase Order` where %s """%conditions, filters,as_dict=True)
	if sa:
		for i in sa:
			row=[i.name,i.file_number,i.title,i.supplier,i.transaction_date,i.status,i.grand_total,i.base_grand_total]
			data.append(row)
			frappe.errprint(row)
	return data