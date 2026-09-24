import frappe
@frappe.whitelist()
def get_rtv_warehouse(company):
    like_filter = "%"+"RTV"+"%"
    store_warehouse = frappe.db.get_value('Warehouse', filters={"company":company,'name': ['like', like_filter]})
    return store_warehouse


@frappe.whitelist()
def get_rework_warehouse(company):
    like_filter = "%"+"Rework"+"%"
    store_warehouse = frappe.db.get_value('Warehouse', filters={"company":company,'name': ['like', like_filter]})
    return store_warehouse