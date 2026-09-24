import frappe
@frappe.whitelist()
def update_todo(doc,method):
    if doc.reference_type=="Quotation":
        document=frappe.get_doc(doc.reference_type,doc.reference_name)
        doc.customer=document.party_name
        doc.save(ignore_permissions=True)