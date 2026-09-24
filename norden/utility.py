import frappe
from erpnext.accounts.utils import (
	unlink_ref_doc_from_payment_entries,
    remove_ref_doc_link_from_pe

)

def get_spec():
    powers = frappe.db.sql("""select specification from `tabDS General` where title like 'power consumption%'""",as_dict=True)
    for power in powers:
        spec = "".join(power.specification.split())
        print(spec)

@frappe.whitelist()     
def pe_on_trash(doc,method):
    ple = frappe.qb.DocType("Payment Ledger Entry")
    frappe.qb.from_(ple).delete().where(
        (ple.voucher_type == doc.doctype) & (ple.voucher_no == doc.name)
    ).run()
    frappe.db.sql(
        "delete from `tabGL Entry` where voucher_type=%s and voucher_no=%s", (doc.doctype, doc.name)
    )
    frappe.db.sql(
        "delete from `tabStock Ledger Entry` where voucher_type=%s and voucher_no=%s",
        (doc.doctype, doc.name),
    )

@frappe.whitelist()
def clear_default_warehouse():
    items = frappe.get_all('Item')
    for doc in items:
        item_defaults = frappe.get_all('Item Default',{'parent':doc['name']},['name','default_warehouse'])
        for it_df in item_defaults:
            default_warehouse = frappe.db.get_value('Item Default',{'name':it_df['name']},'default_warehouse')
            if default_warehouse:
                frappe.db.set_value('Item Default',{'name':it_df['name']},'default_warehouse',None)
                frappe.db.commit()
