import frappe
@frappe.whitelist()
def get_items_from_so(so):
    items=[]
    sales_order=frappe.get_doc("Sales Order",so)
    for s in sales_order.items:
        items.append({'item_code':s.item_code,
        'item_name':s.item_name,
        'qty':s.qty})
    return items