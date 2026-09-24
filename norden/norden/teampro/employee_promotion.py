import frappe
@frappe.whitelist()
def get_appraisal_kra(employee):
    emp = frappe.get_doc("Appraisal Template",{'employee':employee})
    
    return emp.goals