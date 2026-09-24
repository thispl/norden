import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
    data = get_data(filters)
    columns = get_columns()
    return columns, data

def get_columns():
    return [
        _("Product") + ":Link/Item:190",
        _("Description") + ":Data:660",
        _("Stock Qty") + ":Int:120",
        _("Physical Qty") + ":Int:120",
        _("Difference") + ":Int:120",
    ]
    
def get_data(filters):
    conditions = "WHERE docstatus < 2 AND warehouse = 'Main Stores - NCME'"
    if filters and filters.get("item"):
        conditions += " AND item = '%s'" % filters.get("item")
    
    tool = frappe.db.sql("""SELECT item, SUM(physical_qty) as physical_qty 
                            FROM `tabERP Stock Reconciliation Tool` 
                            {conditions} 
                            GROUP BY item""".format(conditions=conditions), as_dict=True)
    
    data = []
    for t in tool:
        if t:
            stock_qty = fetch_stock_qty(t.item)
            data.append([t.item, fetch_item_name(t.item), stock_qty, t.physical_qty, stock_qty - t.physical_qty])
    return data

frappe.whitelist()
def fetch_item_name(item):
    doc = frappe.get_doc("Item", item)
    return doc.item_name

frappe.whitelist()
def fetch_stock_qty(item):
    stock_qty = frappe.db.get_value("Bin", {"item_code": item, "warehouse": "Main Stores - NCME"}, "actual_qty")
    return flt(stock_qty) if stock_qty else 0
