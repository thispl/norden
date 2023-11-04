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
		_("PO NO") + ":Link/Purchase Invoice:110",
		_("PO Date") + ":Data:200",
		_("Vendor") + ":Data:100",
		_("INV NO") + ":Data:100",
		_("Base Currency") + ":Data:80",
		_("Grand Total") + ":Data:90",
		_("VAT(BC)") + ":Data:80",
		_("Grand Total(BC)") + ":Data:90",
	]
	return columns


def get_conditions(filters):
	conditions = ""
	if filters.get("from_date") and filters.get("to_date"):
		conditions += "  posting_date between %(from_date)s and %(to_date)s"
	if filters.get("supplier"):
		conditions += " and supplier= %(supplier)s"
	
	return conditions, filters

def get_data(filters):
	data = []
	conditions, filters = get_conditions(filters)
	sa = []
	sa = frappe.db.sql("""select * from `tabPurchase Invoice` where %s """%conditions, filters,as_dict=True)
	if sa:
		for i in sa:
			row=[i.name,i.posting_date,i.supplier,i.bill_no,"AED",i.grand_total,i.base_total_taxes_and_charges,i.base_grand_total]
			data.append(row)
			frappe.errprint(row)
	return data