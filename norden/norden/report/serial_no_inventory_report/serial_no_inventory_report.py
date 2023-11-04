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
        _('Item') + ":Link/Item:250",
        _('Serial Number') + ":Link/Serial No:250",
        _("Creation Document Type") + ":Data/:250",
        _("Creation Document Number") + ":Data/:250",

    ]
    
    return columns


def get_data(filters):
    data = []
    if filters.serial_no:
        serial = frappe.db.get_all("Serial No",{'name':filters.serial_no,'status':'Active'},["*"])
    elif filters.item_code:
        serial = frappe.db.get_all("Serial No",{'item_code':filters.item_code,'status':'Active'},["*"])
    else:
        serial = frappe.db.get_all("Serial No",{'status':'Active'},["*"])

    for i in serial:
        row = [i.item_code,i.name,i.purchase_document_type,i.purchase_document_no]
        data.append(row)
    return data