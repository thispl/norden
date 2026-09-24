# Copyright (c) 2024, Teampro and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    data = get_data(filters)
    columns = get_columns()
    return columns, data

def get_columns():
    return [
        _("Team") + ":Link/Stock Team:65",
        _("Product") + ":Link/Item:190",
        _("Description") + ":Link/Company:540",
        _("Rack") + ":Link/Rack: 140",
        _("Physical Stock") + ":Int:130",
        _("Analysis Date & Time") + ":Datetime:170",
    ]
    
def get_data(filters):
    data = []
    conditions = {"docstatus": ["!=", 2]}
    if filters:
        if filters.get("team"):
            conditions["team"] = filters["team"]
        if filters.get("item"):
            conditions["item"] = filters["item"]
        if filters.get("rack"):
            conditions["rack"] = filters["rack"]
        if filters.get("stock_analysis"):
            conditions["stock_analysis"] = filters["stock_analysis"]
        
    tool = frappe.get_all("ERP Stock Reconciliation Tool",
        fields=["rack", "team", "item", "physical_qty", "creation"],
        filters=conditions,
    )
    for t in tool:
        data.append([t.team, t.item, fetch_item_name(t.item), t.rack, t.physical_qty, t.creation])
    return data

frappe.whitelist()
def fetch_item_name(item):
    doc = frappe.get_doc("Item", {"name":item})
    return doc.item_name