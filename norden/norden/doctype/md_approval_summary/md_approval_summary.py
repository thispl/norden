# Copyright (c) 2022, Teampro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class MDApprovalSummary(Document):

    @frappe.whitelist()
    def get_expence_claim(self):
        expense = frappe.get_list("Expense Claim",{"workflow_state":"Pending for HOD"},["name","employee","employee_name","expense_approver","total_claimed_amount"])
        return expense

    @frappe.whitelist()
    def get_leave_app(self):
        leave_app = frappe.get_list("Leave Application",{"workflow_state":"Pending for HOD"},["name","employee","employee_name","from_date","to_date","leave_type","total_leave_days"])
        return leave_app

    @frappe.whitelist()
    def submit_doc(self,doctype,name,workflow_state):
        doc = frappe.get_doc(doctype,name)
        doc.workflow_state = workflow_state
        # doc.insert()
        doc.submit()
        return "ok"

    @frappe.whitelist()
    def submit_all_doc_after_approval(self,doctype,name,workflow_state):
        frappe.errprint("hi")
        frappe.db.set_value(doctype,name,"workflow_state",workflow_state)
        return "ok"

