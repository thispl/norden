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
        _('Description') + ":Data/:200",
        _("Valuation Rate") + ":Data/:200",
        _("Unit") + ":Data/:200",


    ]
    
    return columns


def get_data(filters):
    data = []
    item = frappe.db.get_all("Item",["*"])
    if filters.item_code:
        item = frappe.db.get_all("Item",{'name':filters.item_code},["*"])

    for i in item:
        row = [i.name,i.item_name,i.valuation_rate,i.stock_uom]
        data.append(row)
    return data