# Copyright (c) 2023, Teampro and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
import erpnext

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	columns = []
	columns += [
		_('Item') + ":Link/Item:200",
		_("Item Name") + ":Data/:250",
		_("Item Group") + ":Link/Item Group:190",
		_("Company") + ":Link/Company:190",
		_("Total Qty") + ":Data/:100",
		_("Allocated Qty") + ":Data/:100",
		_("Free Qty") + ":Data/:100",
		_("Non Sale Qty") + ":Data/:100",
		_("PO Qty") + ":Data/:100",
		_("Unit") + ":Data/:100",
	]
	
	return columns

def get_data(filters):
	data = []
	row = []
	if not filters.item:
		item = frappe.get_all("Item",["*"])
	if filters.item:
		item = frappe.get_all("Item",{"name":filters.item},["*"])
	if filters.like:
		like_filter = "%"+filters.like+"%"
		item = frappe.get_all("Item",{"name":["like",like_filter]},["*"])
	if filters.item_group:
		item = frappe.get_all("Item",{"item_sub_group":filters.item_group},["*"])
	
	for i in item:
		stocks = frappe.db.sql("""select sum(`tabBin`.actual_qty) as actual_qty from `tabBin`
							join `tabWarehouse` on `tabWarehouse`.name = `tabBin`.warehouse
							join `tabCompany` on `tabCompany`.name = `tabWarehouse`.company
							where `tabBin`.item_code = '%s' and `tabWarehouse`.company = '%s' """ % (i.name,filters.company), as_dict=True)[0]
		
		
		all_whouse = frappe.db.get_value("Warehouse",{"company":filters.company,"is_allocate":1},['name'])
		all_qty = frappe.db.get_value("Bin",{"item_code":i.name,"warehouse":all_whouse},["actual_qty"]) or 0

		if not stocks['actual_qty']:
			stocks['actual_qty'] = 0

		mrb_whouse = frappe.db.get_value("Warehouse",{"company":filters.company,"is_mrb":1},['name'])
		mrb_qty = frappe.db.get_value("Bin",{"item_code":i.name,"warehouse":mrb_whouse},["actual_qty"]) or 0


		new_po = frappe.db.sql("""select sum(`tabPurchase Order Item`.qty) as qty,sum(`tabPurchase Order Item`.received_qty) as d_qty from `tabPurchase Order`
		left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
		where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus = 1 and `tabPurchase Order`.company = '%s' """ % (i.name,filters.company), as_dict=True)[0]
		if not new_po['qty']:
			new_po['qty'] = 0
		if not new_po['d_qty']:
			new_po['d_qty'] = 0
		ppoc_total = new_po['qty'] - new_po['d_qty']
		if filters.non_zero == "With Zero":
		
			row = [i.name,i.item_name,i.item_sub_group,filters.company,stocks["actual_qty"],all_qty or 0,stocks["actual_qty"]-all_qty,mrb_qty or 0,ppoc_total or 0,i.stock_uom]
		else:
			if stocks["actual_qty"] == 0:
				continue
			else:
				row = [i.name,i.item_name,i.item_sub_group,filters.company,stocks["actual_qty"],all_qty or 0,stocks["actual_qty"]-all_qty,mrb_qty or 0,ppoc_total or 0,i.stock_uom]
			
		data.append(row)
	return data