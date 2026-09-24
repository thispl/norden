import frappe
@frappe.whitelist()
def pay_entry(type):
    if type=="Payable":
        pay= frappe.db.get_list("Payment Entry",{"pdc_i":1,"pdc_completed":0},["name","reference_date","reference_no","paid_amount","posting_date","paid_from"])
    else:
        pay= frappe.db.get_list("Payment Entry",{"pdc_r":1,"pdc_completed":0},["name","reference_date","reference_no","paid_amount","posting_date","paid_to"])
    return pay