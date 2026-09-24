# Copyright (c) 2023, Teampro and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from six import string_types
import frappe
from frappe import _, msgprint

def execute(filters=None):
# def execute():
	# filters={'company':'Norden Communication Middle East FZE','item' :'114-10001104GY'}
	columns, data = [] ,[]
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	columns = [
		_('Item') + ":Link/Item:190",
	]
	col = frappe.db.get_list("Warehouse",{'company':filters.company},["name"])
	# frappe.get_value("Bin",{"warehouse":col.name,"item_code":i.name},["actual_qty"])
	for c in col: 
		aq = frappe.get_value("Bin",{"warehouse":c.name,"item_code":filters.item},["actual_qty"])   
		if aq is not None and aq > 0:

			columns.append({
				"label": c.name
			})
	return columns


def get_data(filters):
	data = []
	row = []
	if filters.item:
		item = frappe.db.get_list("Item",{"name":filters.item},['name'])
	else:
		item = frappe.db.get_list("Item",['name'])
	for i in item:
		row = [i.name]
		warehouse = frappe.db.get_list("Warehouse",{'company':filters.company},["name"])
		for wh in warehouse:
			pr = frappe.get_value("Bin",{"warehouse":wh.name,"item_code":i.name},["actual_qty"])
			
			if pr and pr > 0:
				row += [pr]
			# else:
			# 	row += [0]
		data.append(row)
	return data