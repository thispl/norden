# Copyright (c) 2025, Teampro and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	data = get_data(filters)
	columns = get_columns()
	return columns, data

def get_columns():
	return [
		_("PO No") + ":Link/Purchase Order:230",
		_("Date") + ":Date:150",
		_("Supplier") + ":Link/Supplier:580",
		_("Currency") + ":Link/Currency: 90",
		_("Amount") + ":Float:130",
	]
	
def get_data(filters):
	data = []
	conditions = {"docstatus": 1}
	conditions['company'] = filters['company']
	if filters:
		if filters.get("name"):
			conditions["name"] = filters["name"]
		if filters.get("from_date") and filters.get("to_date"):
			conditions["transaction_date"] = ["between", [filters["from_date"], filters["to_date"]]]
		if filters.get("supplier"):
			conditions["supplier"] = filters["supplier"]

			
	purchase_orders = frappe.get_all("Purchase Order", 
									 fields = ["name", "transaction_date", "supplier", "grand_total", "currency"],
									 filters = conditions,
									 order_by = "transaction_date"
									)
	for po in purchase_orders:
		data.append([po.name, po.transaction_date, po.supplier, po.currency, po.grand_total])
	
	return data