# Copyright (c) 2024, Teampro and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    columns = [
        _('Item') + ":Link/Item:200",
        _("Item Name") + ":Data/:250",
        _("Item Group") + ":Link/Item Group:190",
        _("Company") + ":Link/Company:190",
        _("Total Qty") + ":Data/:100",
        _("Reserved Qty") + ":Data/:100",
        _("Free Qty") + ":Data/:100",
        _("Non Sale Qty") + ":Data/:100",
        _("PO Qty") + ":Data/:100",
        _("Unit") + ":Data/:100",
    ]
    return columns

def get_data(filters):
    data = []
    item_filters = {}
    if filters.item:
        item_filters["name"] = filters.item
    if filters.like:
        item_filters["name"] = ["like", "%" + filters.like + "%"]
    if filters.item_group:
        item_filters["item_sub_group"] = filters.item_group
    
    items = frappe.get_all("Item", filters=item_filters, fields=["name", "item_name", "item_sub_group", "stock_uom"])
    
    for item in items:
        stocks = get_stock_quantity(item.name, filters.company)
        reserved_qty = get_reserved_quantity(item.name, filters.company)
        free_qty = stocks - reserved_qty
        non_sale_qty = get_non_sale_quantity(item.name, filters.company)
        po_qty = get_purchase_order_quantity(item.name, filters.company)
        
        row = [
            item.name,
            item.item_name,
            item.item_sub_group,
            filters.company,
            stocks,
            reserved_qty,
            free_qty,
            non_sale_qty,
            po_qty,
            item.stock_uom
        ]
        if filters.non_zero == "With Zero" or stocks != 0:
            data.append(row)
    
    return data

def get_stock_quantity(item_code, company):
    return frappe.db.sql("""
        SELECT SUM(actual_qty) AS stock_quantity
        FROM `tabBin`
        WHERE item_code = %s AND warehouse IN (
            SELECT name FROM `tabWarehouse` WHERE company = %s
        )
    """, (item_code, company), as_dict=True)[0].get('stock_quantity', 0) or 0

def get_reserved_quantity(item_code, company):
    return frappe.db.sql("""
        SELECT SUM(reserved_stock) AS reserved_quantity
        FROM `tabBin`
        WHERE item_code = %s AND warehouse IN (
            SELECT name FROM `tabWarehouse` WHERE company = %s
        )
    """, (item_code, company), as_dict=True)[0].get('reserved_quantity', 0) or 0

def get_non_sale_quantity(item_code, company):
    mrb_qty = frappe.db.sql("""
        SELECT IFNULL(SUM(b.actual_qty), 0) AS actual_qty
        FROM `tabBin` b
        JOIN `tabWarehouse` w ON b.warehouse = w.name
        WHERE b.item_code = %s
        AND w.company = %s
        AND w.is_mrb = 1
    """, (item_code, company), as_dict=True)[0]
    return mrb_qty['actual_qty'] or 0


def get_purchase_order_quantity(item_code, company):
    po_qty = frappe.db.sql("""
        SELECT SUM(`tabPurchase Order Item`.qty) AS qty, SUM(`tabPurchase Order Item`.received_qty) AS d_qty
        FROM `tabPurchase Order Item`
        INNER JOIN `tabPurchase Order` ON `tabPurchase Order`.name = `tabPurchase Order Item`.parent
        WHERE `tabPurchase Order Item`.item_code = %s 
            AND `tabPurchase Order`.docstatus = 1 
            AND `tabPurchase Order`.company = %s
    """, (item_code, company), as_dict=True)[0]
    return max(0, (po_qty.qty or 0) - (po_qty.d_qty or 0))
