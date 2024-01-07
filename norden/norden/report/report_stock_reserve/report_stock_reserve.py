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
        _("Item") + ":Link/Item:200",
        _("Qty") + ":Float:100",
        _("Reserved Qty") + ":Float:100",
        _("Unreserved Qty") + ":Float:100",
        _("Warehouse") + ":Link/Warehouse:200",
    ]
    return columns

def get_data(filters):
    conditions = ""
    if filters.company:
        conditions += " and `tabSales Order`.company = %(company)s"
    if filters.custom_reservation_status:
        conditions += " and `tabSales Order`.custom_reservation_status = %(custom_reservation_status)s"
    data = []
    sale = frappe.db.sql("""select name from `tabSales Order` where docstatus =1 %s """%conditions,filters,as_dict=1)
    for s in sale:
        sa = frappe.db.sql("""select
        `tabSales Order`.`name`,
        `tabSales Order`.`sales_person_user`,			 
        `tabSales Order`.`status`, `tabSales Order`.`customer`, 
        `tabSales Order`.`customer_name`, 
        `tabSales Order`.`transaction_date`, 
        `tabSales Order`.`project`, 
        `tabSales Order Item`.item_code, 
        `tabSales Order Item`.qty, 
        `tabSales Order Item`.delivered_qty, 
        (`tabSales Order Item`.qty - ifnull(`tabSales Order Item`.delivered_qty, 0)) as qty_to_deliver, 
        `tabSales Order Item`.base_rate, `tabSales Order Item`.base_amount, 
        ((`tabSales Order Item`.qty - ifnull(`tabSales Order Item`.delivered_qty, 0))*`tabSales Order Item`.base_rate) as amount_to_deliver, 
        `tabBin`.actual_qty, 
        `tabBin`.projected_qty, 
        `tabSales Order Item`.`delivery_date`,  
        DATEDIFF(CURDATE(),`tabSales Order Item`.`delivery_date`) as diffdate, 
        `tabSales Order Item`.item_name, 
        `tabSales Order Item`.description, 
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
        `tabSales Order`.`status`, `tabSales Order`.`customer`, 
        `tabSales Order`.`customer_name`, 
        `tabSales Order`.`transaction_date`, 
        `tabSales Order`.`project`, 
        `tabSales Order Item`.item_code, 
        sum(`tabSales Order Item`.qty) as qty, 
        sum(`tabSales Order Item`.delivered_qty) as delivered_qty, 
        sum((`tabSales Order Item`.qty - ifnull(`tabSales Order Item`.delivered_qty, 0))) as qty_to_deliver, 
        `tabSales Order Item`.base_rate, sum(`tabSales Order Item`.base_amount) as base_amount, 
        sum(((`tabSales Order Item`.qty - ifnull(`tabSales Order Item`.delivered_qty, 0))*`tabSales Order Item`.base_rate)) as amount_to_deliver, 
        `tabBin`.actual_qty, 
        `tabBin`.projected_qty, 
        `tabSales Order Item`.`delivery_date`,  
        DATEDIFF(CURDATE(),`tabSales Order Item`.`delivery_date`) as diffdate, 
        `tabSales Order Item`.item_name, 
        `tabSales Order Item`.description, 
        `tabSales Order Item`.item_group, 
        `tabSales Order Item`.warehouse 
        from 
        `tabSales Order` 
        JOIN `tabSales Order Item`  LEFT JOIN `tabBin` ON (`tabBin`.item_code = `tabSales Order Item`.item_code and `tabBin`.warehouse = `tabSales Order Item`.warehouse) 
        where 
        `tabSales Order Item`.`parent` = `tabSales Order`.`name` 
        and 
        `tabSales Order`.docstatus =1
        and 
        `tabSales Order`.status not in ("Stopped", "Closed") and `tabSales Order`.name = '%s'
        and ifnull(`tabSales Order Item`.delivered_qty,0) < ifnull(`tabSales Order Item`.qty,0)order by `tabSales Order`.transaction_date
        asc"""%(s.name),as_dict=1)[0]
        raw = {'sales_order':s.name,'qty':sb["qty"],'indent':0}
        data.append(raw)
        frappe.errprint(raw)
        for i in sa:
            reserve = frappe.db.get_value("Stock Reservation Entry",{"item_code":i.item_code,"voucher_no":s.name,"warehouse":i.warehouse},["reserved_qty"])
            row = {'item':i.item_code,'qty':i.qty,'reserved_qty':reserve or 0,'unreserved_qty':float(i.qty - (reserve or 0)),'warehouse':i.warehouse,'indent':1}
            data.append(row)
    return data

