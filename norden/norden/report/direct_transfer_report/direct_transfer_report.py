# Copyright (c) 2023, Teampro and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	columns = [
		_("Transfer No") + ":Link/Stock Entry:150",
		_("Transfer Date") + ":Date:150",
		_("From Warehouse") + ":Link/Warehouse:150",
		_("To Warehouse") + ":Link/Warehouse:150",
		_("Item") + ":Link/Item:150",
		_("Description") + ":Data:150",
		_("Quantity") + ":Float:150",
	]
	return columns

def get_data(filters):
	data = []
	
	conditions = {}
	
	if filters.get("from_date") and filters.get("to_date"):
		conditions["posting_date"] = ["between", [filters.get("from_date"), filters.get("to_date")]]
	
	if filters.get("from_warehouse"):
		conditions["s_warehouse"] =  filters.get("from_warehouse")

	if filters.get("to_warehouse"):
		conditions["t_warehouse"] = filters.get("to_warehouse")
	
	if filters.get("transfer_no"):
		conditions["name"] = filters.get("transfer_no")
	
	stock_entries = frappe.get_all("Stock Entry",filters={"stock_entry_type": "Material Transfer", **conditions}, fields=["name", "posting_date"])
	
	for i in stock_entries:
		doc = frappe.get_doc("Stock Entry", i.name)
		for item in doc.items:
			row = [
				doc.name,
				doc.posting_date,
				item.s_warehouse,
				item.t_warehouse,
				item.item_code,
				item.description,
				item.qty
			]
			data.append(row)
	
	return data
