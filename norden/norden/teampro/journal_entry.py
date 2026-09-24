import frappe
@frappe.whitelist()
def validate_cheque_no(cheque_no):
    journal_entry=frappe.get_all("Journal Entry",{'cheque_no':cheque_no,"docstatus":("!=",2)},['*'])
    if journal_entry:
        i=0
        doc_name=[]
        for je in journal_entry:
            i+=1
            doc_name.append(je.name)
        return i,doc_name