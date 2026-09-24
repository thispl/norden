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
	columns = [
		_("Sales Order") + ":Link/Sales Order:200",
		_("Sales Person")+":Link/Sales Person:110",
		_("Status") + ":Data:200",
		_("Customer Name") + ":Link/Customer:200",
		_("Customer Purchase Order Number") + ":Data:200",
        _("Date") + ":Date:200",
		_("Item Code") + ":Link/Item:200",
		_("Item Description") + ":Data:300",
		_("Qty") + ":Float:100",
		_("Delivered Qty") + ":Float:100",
		_("Qty to Deliver") + ":Float:100",
		_("Allocated Qty") + ":Float:100",

		_("Rate") + ":Float:100",
		_("Amount") + ":Float:100",
		_("Amount to Deliver") + ":Float:100",
		_("Available Qty") + ":Float:100",
		_("Projected Qty") + ":Float:100",
		_("Item Delivery Date") + ":Date:100",
		_("Delay Days") + ":Int:100",
		_("Item Group") + ":Link/Item Group:200",
		_("Warehouse") + ":Link/Warehouse:200",
	]
	return columns

def get_data(filters):
	conditions = ""
	if filters.company:
		conditions += " and `tabSales Order`.company = %(company)s"
	if filters.customer:
		conditions += " and `tabSales Order`.customer = %(customer)s"
	if filters.get("sales_person_user"):
		conditions += " and `tabSales Order`.sales_person_user = %(sales_person_user)s"
	if filters.sales_order:
		conditions += " and `tabSales Order`.name = %(sales_order)s"
	if filters.from_date and filters.to_date:
		conditions += " and `tabSales Order`.transaction_date between %(from_date)s and %(to_date)s"
	data = []
	
	sale = frappe.db.sql(""" select name from `tabSales Order` where `tabSales Order`.docstatus = 1 and `tabSales Order`.status not in ("Stopped", "Closed") and `tabSales Order`.per_delivered != 100 %s """%conditions,filters,as_dict=1)
	for s in sale:
		sa = frappe.db.sql("""select
		`tabSales Order`.`name`,
		`tabSales Order`.`sales_person_user`,			 
		`tabSales Order`.`status`,
		`tabSales Order`.`customer_name`,
		`tabSales Order`.`po_no`,
		`tabSales Order`.`transaction_date`, 
		`tabSales Order`.`project`, 
		`tabSales Order Item`.item_code, 
		`tabSales Order Item`.item_name, 
		`tabSales Order Item`.qty, 
		`tabSales Order Item`.delivered_qty, 
		(`tabSales Order Item`.qty - ifnull(`tabSales Order Item`.delivered_qty, 0)) as qty_to_deliver, 
		`tabSales Order Item`.base_rate, `tabSales Order Item`.base_amount, 
		((`tabSales Order Item`.qty - ifnull(`tabSales Order Item`.delivered_qty, 0))*`tabSales Order Item`.base_rate) as amount_to_deliver, 
		`tabBin`.actual_qty, 
		`tabBin`.projected_qty, 
		`tabSales Order Item`.`delivery_date`,  
		DATEDIFF(CURDATE(),`tabSales Order Item`.`delivery_date`) as diffdate, 
		`tabSales Order Item`.item_group, 
		`tabSales Order Item`.warehouse 
		from 
		`tabSales Order` 
		JOIN `tabSales Order Item`  LEFT JOIN `tabBin` ON (`tabBin`.item_code = `tabSales Order Item`.item_code and `tabBin`.warehouse = `tabSales Order Item`.warehouse) 
		where 
		`tabSales Order Item`.`parent` = `tabSales Order`.`name` 
		and 
		`tabSales Order`.docstatus = 1
		and 
		`tabSales Order`.status not in ("Stopped", "Closed") and `tabSales Order`.name = '%s'
		and ifnull(`tabSales Order Item`.delivered_qty,0) < ifnull(`tabSales Order Item`.qty,0)order by `tabSales Order`.transaction_date
		asc"""%(s.name),as_dict=1)
		sb = frappe.db.sql("""select
		`tabSales Order`.`name`,
		`tabSales Order`.`sales_person_user`,
		`tabSales Order`.`status`, 
		`tabSales Order`.`customer_name`, 
		`tabSales Order`.`po_no`,
		`tabSales Order`.`transaction_date`, 
		`tabSales Order`.`project`, 
		`tabSales Order Item`.item_code, 
		`tabSales Order Item`.item_name,
		sum(`tabSales Order Item`.qty) as qty, 
		sum(`tabSales Order Item`.delivered_qty) as delivered_qty, 
		sum((`tabSales Order Item`.qty - ifnull(`tabSales Order Item`.delivered_qty, 0))) as qty_to_deliver, 
		`tabSales Order Item`.base_rate, sum(`tabSales Order Item`.base_amount) as base_amount, 
		sum(((`tabSales Order Item`.qty - ifnull(`tabSales Order Item`.delivered_qty, 0))*`tabSales Order Item`.base_rate)) as amount_to_deliver, 
		`tabBin`.actual_qty, 
		`tabBin`.projected_qty, 
		`tabSales Order Item`.`delivery_date`,  
		DATEDIFF(CURDATE(),`tabSales Order Item`.`delivery_date`) as diffdate, 
		`tabSales Order Item`.item_group, 
		`tabSales Order Item`.warehouse 
		from 
		`tabSales Order` 
		JOIN `tabSales Order Item`  LEFT JOIN `tabBin` ON (`tabBin`.item_code = `tabSales Order Item`.item_code and `tabBin`.warehouse = `tabSales Order Item`.warehouse) 
		where 
		`tabSales Order Item`.`parent` = `tabSales Order`.`name` 
		and 
		`tabSales Order`.docstatus = 1 
		and 
		`tabSales Order`.status not in ("Stopped", "Closed") and `tabSales Order`.name = '%s'
		and ifnull(`tabSales Order Item`.delivered_qty,0) < ifnull(`tabSales Order Item`.qty,0)order by `tabSales Order`.transaction_date
		asc"""%(s.name),as_dict=1)[0]
		reserved_qty =0
		stock_entry = frappe.get_all("Stock Reservation Entry", {"voucher_no":s.name,"status": ["in", ["Reserved", "Partially Reserved"]]}, ['reserved_qty'])      
		prq = frappe.db.sql("""select (reserved_qty - delivered_qty) as partially_delivered from `tabStock Reservation Entry`
								where status = 'Partially Delivered' and voucher_no = '%s' """ % (s.name), as_dict=True)
			
		for reser in stock_entry:
			reserved_qty += reser.reserved_qty
		for prq_ in prq:
			reserved_qty += flt(prq_['partially_delivered']) or 0
		raw = {'sales_order':s.name,'sales_person':sb['sales_person_user'],'status':sb['status'],'customer_name':sb["customer_name"],'customer_purchase_order_number':sb["po_no"],'date':sb["transaction_date"],'qty':sb["qty"],'delivered_qty':sb["delivered_qty"],'qty_to_deliver':sb["qty_to_deliver"],'allocated_qty':reserved_qty,'amount':sb["base_amount"],'amount_to_deliver':sb["amount_to_deliver"],'item_delivery_date':sb["delivery_date"],'delay_days':sb["diffdate"],'indent':0}
		data.append(raw)
		for i in sa:
			total_reserved_qty =0
			stock_entry = frappe.get_all("Stock Reservation Entry", {"item_code":i.item_code,"voucher_no":s.name,"status": ["in", ["Reserved", "Partially Reserved"]]}, ['reserved_qty'])      
			prq = frappe.db.sql("""select (reserved_qty - delivered_qty) as partially_delivered from `tabStock Reservation Entry`
									where item_code = '%s' and status = 'Partially Delivered' and voucher_no = '%s' """ % (i.item_code,s.name), as_dict=True)
				
			for reser in stock_entry:
				total_reserved_qty += reser.reserved_qty
			for prq_ in prq:
				total_reserved_qty += flt(prq_['partially_delivered']) or 0
			row = {'item_code':i.item_code,'item_description':i.item_name,'qty':i.qty,'delivered_qty':i.delivered_qty,'qty_to_deliver':i.qty_to_deliver,'allocated_qty':total_reserved_qty,'rate':i.base_rate,'amount':i.base_amount,'amount_to_deliver':i.amount_to_deliver,'available_qty':i.actual_qty,'projected_qty':i.projected_qty,'item_delivery_date':i.delivery_date,'delay_days':i.diffdate,'item_group':i.item_group,'warehouse':i.warehouse,'indent':1}
			data.append(row)
		
	return data
