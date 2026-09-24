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
	date = frappe.db.get_value("Custom Settings","Custom Settings","date")
	data = []
	if filters.item:
		item = frappe.get_all("Item",{"name":filters.item},["*"])

	if filters.like:
		like_filter = "%"+filters.like+"%"
		item = frappe.get_all("Item",{"name":["like",like_filter]},["*"])
	for i in item:
		stocks = frappe.db.sql("""select (sum(`tabBin`.actual_qty) - sum(reserved_stock)) as actual_qty from `tabBin`
							join `tabWarehouse` on `tabWarehouse`.name = `tabBin`.warehouse
							join `tabCompany` on `tabCompany`.name = `tabWarehouse`.company
							where `tabBin`.item_code = '%s' and `tabWarehouse`.company = '%s' and disabled = 0 """ % (i.name,filters.company), as_dict=True)[0]
		
		
		total_reserved_qty =0
		stock_entry = frappe.get_all("Stock Reservation Entry", {"company": filters.company,"item_code":i.name,"status": ["in", ["Reserved", "Partially Reserved"]]}, ['reserved_qty'])      
		for reser in stock_entry:
			total_reserved_qty += reser.reserved_qty
		if not stocks['actual_qty']:
			stocks['actual_qty'] = 0
		


		mrb_whouse = frappe.db.get_value("Warehouse",{"company":filters.company,"is_scrap":1},['name'])
		mrb_qty = frappe.db.get_value("Bin",{"item_code":i.name,"warehouse":mrb_whouse},["actual_qty"]) or 0


		new_po = frappe.db.sql("""select sum(`tabPurchase Order Item`.qty) as qty,sum(`tabPurchase Order Item`.received_qty) as d_qty from `tabPurchase Order`
		left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
		where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus = 1 and `tabPurchase Order`.company = '%s' and `tabPurchase Order Item`.qty >= `tabPurchase Order Item`.received_qty and `tabPurchase Order`.transaction_date >= '%s' """ % (i.name,filters.company,date), as_dict=True)[0]
		if not new_po['qty']:
			new_po['qty'] = 0
		if not new_po['d_qty']:
			new_po['d_qty'] = 0
		ppoc_total = new_po['qty'] - new_po['d_qty']

		if stocks["actual_qty"] > 0:
			ware = frappe.db.sql(""" SELECT name FROM `tabWarehouse` WHERE is_scrap = 1 AND disabled = 0 AND company = %s """, (filters.company), as_dict=True)
			total_scrap_qty = 0
			for house in ware:
				sc_qty = frappe.get_value("Bin", {"warehouse": house.name,"item_code":i.name}, ['actual_qty']) or 0
				total_scrap_qty += sc_qty
			row = {'company':filters.company,'item':i.name,'item_name':i.item_name,'total_qty':stocks["actual_qty"] - total_scrap_qty +total_reserved_qty ,'reserved_qty':total_reserved_qty or 0,'free_qty':stocks["actual_qty"] - total_scrap_qty,'non_sale_qty':mrb_qty or 0,'po_qty':ppoc_total or 0,'unit':i.stock_uom}
		else:
			row = {'company':filters.company,'item':i.name,'item_name':i.item_name,'total_qty':0+total_reserved_qty ,'reserved_qty':total_reserved_qty or 0,'free_qty':0,'non_sale_qty':mrb_qty or 0,'po_qty':ppoc_total or 0,'unit':i.stock_uom}
		data.append(row)
	return data