import frappe

@frappe.whitelist()
def fetch_file_number(order_no):
    po = frappe.get_value("Purchase Order",{"name":order_no},["delivery_term"])
    return po
