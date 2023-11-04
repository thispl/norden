# Copyright (c) 2023, Teampro and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from six import string_types
import frappe
from frappe import _, msgprint

def execute(filters=None):
	columns, data = [] ,[]
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	column = [
		_('Purchase Receipt') + ":Link/Purchase Receipt:190",
		_('Item Name') + ':Data:350',
		_('Ordered Qty') + ':Data:163',
		_('Received Qty') + ':Data:163',
		_('Accepted Qty') + ':Data:163',
		_('Balance Qty') + ':Data:163',
	]
	return column


def get_data(filters):
	data = []
	row = []
	pr = frappe.db.get_list("Purchase Receipt",{'docstatus':0},["name"])
	for i in pr:
		pr_item = frappe.get_doc("Purchase Receipt",i.name)
		for k in pr_item.items:
			if not k.skip_qc:
				qc = frappe.db.get_value("Item",k.item_code,['request_for_quality_inspection'])
				if qc:
					inspect = frappe.db.exists("Item Inspection",{"pr_number":i.name,"item_code":k.item_code})
					if not inspect:
						frappe.errprint(k.balance)
						row = [i.name,k.item_code,k.ordered or 0,k.received_qty or 0,k.qty or 0,k.balance or 0]
			data.append(row)
	return data