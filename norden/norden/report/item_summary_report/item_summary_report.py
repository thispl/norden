import frappe
from frappe import _
from frappe.utils import flt
import erpnext

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	columns = [
		{
			"label": _("Item"),
			"fieldname": "item",
			"fieldtype": "Link",
			"options": "Item",
		},
		{
			"label": _("Company"),
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"hidden":1
		},
		{
			"label": _("Item Name"),
			"fieldname": "item_name",
			"fieldtype": "Data",
		},
		{
			"label": _("Total Qty"),
			"fieldname": "total_qty",
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"label": _("Reserved Qty"),
			"fieldname": "reserved_qty",
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"label": _("Free Qty"),
			"fieldname": "free_qty",
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"label": _("Non Sale Qty"),
			"fieldname": "non_sale_qty",
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"label": _("Demo Qty"),
			"fieldname": "demo_qty",
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"label": _("PO Qty"),
			"fieldname": "po_qty",
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"label": _("SO Pending Qty"),
			"fieldname": "so_qty",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": _("Unit"),
			"fieldname": "unit",
			"fieldtype": "Data",
			"width": 130,
		},

	]
	
	return columns

def get_data(filters):
	data = []
	date = frappe.db.get_value("Custom Settings","Custom Settings","date")
	# row = []
	if (filters.based_on_type and filters.based_on) or filters.like:
	# if not filters.item:
	# 	item = frappe.get_all("Item",["*"])
		if filters.based_on_type == "Item":
			item = frappe.get_all("Item",{"name":filters.based_on},["*"])
		if filters.based_on_type == "Item Group":
			item = frappe.get_all("Item",{"item_group":filters.based_on},["*"])
		if filters.like:
			like_filter = "%"+filters.like+"%"
			item = frappe.get_all("Item",{"name":["like",like_filter]},["*"])
		for i in item:
			# stocks = frappe.db.sql("""select (sum(`tabBin`.actual_qty) - sum(reserved_stock)) as actual_qty from `tabBin`
			# 					join `tabWarehouse` on `tabWarehouse`.name = `tabBin`.warehouse
			# 					join `tabCompany` on `tabCompany`.name = `tabWarehouse`.company
			# 					where `tabBin`.item_code = '%s' and `tabWarehouse`.company = '%s' and disabled = 0 and `tabWarehouse`.custom_stock_is_shown_only_in_product_search = 0 """ % (i.name,filters.company), as_dict=True)[0]
			stocks = frappe.db.sql("""
				select (sum(`tabBin`.actual_qty) - sum(reserved_stock)) as actual_qty from `tabBin`
				join `tabWarehouse` on `tabWarehouse`.name = `tabBin`.warehouse
				join `tabCompany` on `tabCompany`.name = `tabWarehouse`.company
				where `tabBin`.item_code = %s and `tabWarehouse`.company = %s and `tabWarehouse`.disabled = 0
				and `tabWarehouse`.custom_stock_is_shown_only_in_product_search = 0
				and `tabWarehouse`.custom_is_service_stock = 0
			""", (i.name, filters.company), as_dict=True)[0]
			
			total_reserved_qty =0
			stock_entry = frappe.get_all("Stock Reservation Entry", {"company": filters.company,"item_code":i.name,"status": ["in", ["Reserved", "Partially Reserved"]]}, ['reserved_qty'])      
			prq = frappe.db.sql("""select (reserved_qty - delivered_qty) as partially_delivered from `tabStock Reservation Entry`
								where item_code = '%s' and company = '%s' and status = 'Partially Delivered'""" % (i.name,filters.company), as_dict=True)
			
			for reser in stock_entry:
				total_reserved_qty += reser.reserved_qty
			if prq:
				total_reserved_qty += flt(prq[0]['partially_delivered']) or 0
			if not stocks['actual_qty']:
				stocks['actual_qty'] = 0
			
			frappe.log_error("trq",total_reserved_qty)
			# mrb_qty = frappe.db.sql("""select (sum(`tabBin`.actual_qty) - sum(reserved_stock)) as actual_qty from `tabBin`
			# 					join `tabWarehouse` on `tabWarehouse`.name = `tabBin`.warehouse
			# 					join `tabCompany` on `tabCompany`.name = `tabWarehouse`.company
			# 					where `tabBin`.item_code = '%s' and `tabWarehouse`.company = '%s' and `tabWarehouse`.custom_is_non_sale = 1 """ % (i.name,filters.company), as_dict=True)[0]
			
			mrb_qty = frappe.db.sql("""
				select (sum(`tabBin`.actual_qty) - sum(reserved_stock)) as actual_qty from `tabBin`
				join `tabWarehouse` on `tabWarehouse`.name = `tabBin`.warehouse
				join `tabCompany` on `tabCompany`.name = `tabWarehouse`.company
				where `tabBin`.item_code = %s and `tabWarehouse`.company = %s and `tabWarehouse`.custom_is_non_sale = 1
				and `tabWarehouse`.custom_is_service_stock = 0
			""", (i.name, filters.company), as_dict=True)[0]


			if not mrb_qty['actual_qty']:
				mrb_qty['actual_qty'] = 0


			# demo_qty = frappe.db.sql("""select (sum(`tabBin`.actual_qty) - sum(reserved_stock)) as actual_qty from `tabBin`
			# 					join `tabWarehouse` on `tabWarehouse`.name = `tabBin`.warehouse
			# 					join `tabCompany` on `tabCompany`.name = `tabWarehouse`.company
			# 					where `tabBin`.item_code = '%s' and `tabWarehouse`.company = '%s' and custom_is_demo = 1 """ % (i.name,filters.company), as_dict=True)[0]
			
			demo_qty = frappe.db.sql("""
				select (sum(`tabBin`.actual_qty) - sum(reserved_stock)) as actual_qty from `tabBin`
				join `tabWarehouse` on `tabWarehouse`.name = `tabBin`.warehouse
				join `tabCompany` on `tabCompany`.name = `tabWarehouse`.company
				where `tabBin`.item_code = %s and `tabWarehouse`.company = %s and `tabWarehouse`.custom_is_demo = 1
				and `tabWarehouse`.custom_is_service_stock = 0
			""", (i.name, filters.company), as_dict=True)[0]


			if not demo_qty['actual_qty']:
				demo_qty['actual_qty'] = 0

			new_po = frappe.db.sql("""select sum(`tabPurchase Order Item`.qty) as qty,sum(`tabPurchase Order Item`.received_qty) as d_qty from `tabPurchase Order`
			left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
			where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus = 1 and `tabPurchase Order`.company = '%s' and `tabPurchase Order Item`.qty >= `tabPurchase Order Item`.received_qty and `tabPurchase Order`.transaction_date >= '%s' """ % (i.name,filters.company,date), as_dict=True)[0]
			if not new_po['qty']:
				new_po['qty'] = 0
			if not new_po['d_qty']:
				new_po['d_qty'] = 0
			ppoc_total = new_po['qty'] - new_po['d_qty']

			new_so = frappe.db.sql("""select sum(`tabSales Order Item`.qty) as qty,sum(`tabSales Order Item`.delivered_qty) as d_qty from `tabSales Order`
			left join `tabSales Order Item` on `tabSales Order`.name = `tabSales Order Item`.parent
			where `tabSales Order Item`.item_code = '%s' and `tabSales Order`.docstatus = 1 and `tabSales Order`.company = '%s' and `tabSales Order Item`.qty >= `tabSales Order Item`.delivered_qty and `tabSales Order`.transaction_date >= '%s' """ % (i.name,filters.company,date), as_dict=True)[0]
			
			if not new_so['qty']:
				new_so['qty'] = 0
			if not new_so['d_qty']:
				new_so['d_qty'] = 0
			psoc_total = new_so['qty'] - new_so['d_qty']
			if stocks["actual_qty"] > 0:
				ware = frappe.db.sql(""" SELECT name FROM `tabWarehouse` WHERE is_scrap = 1 AND disabled = 0 AND company = %s """, (filters.company), as_dict=True)
				total_scrap_qty = 0
				for house in ware:
					sc_qty = frappe.get_value("Bin", {"warehouse": house.name,"item_code":i.name}, ['actual_qty']) or 0
					total_scrap_qty += sc_qty
				row = {'company':filters.company,'item':i.name,'item_name':i.item_name,'total_qty':stocks["actual_qty"] - total_scrap_qty +total_reserved_qty ,'reserved_qty':total_reserved_qty or 0,'free_qty':stocks["actual_qty"] - total_scrap_qty - demo_qty['actual_qty']-mrb_qty['actual_qty'],'non_sale_qty':mrb_qty['actual_qty'] or 0,'po_qty':ppoc_total or 0,'so_qty':psoc_total or 0,'unit':i.stock_uom,'demo_qty':demo_qty['actual_qty']}
			else:
				row = {'company':filters.company,'item':i.name,'item_name':i.item_name,'total_qty':0+total_reserved_qty ,'reserved_qty':total_reserved_qty or 0,'free_qty':0,'non_sale_qty':mrb_qty['actual_qty'] or 0,'po_qty':ppoc_total or 0,'so_qty':psoc_total or 0,'unit':i.stock_uom,'demo_qty':demo_qty['actual_qty']}
			data.append(row)
		return data