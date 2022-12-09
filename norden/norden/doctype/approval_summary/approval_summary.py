# Copyright (c) 2022, Teampro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ApprovalSummary(Document):
    @frappe.whitelist()
    def get_sales_order(self):
        data = frappe.get_list("Sales Order",{"workflow_state":"Pending for COO"},["name","customer","transaction_date","sales_person_name"])
        return data

    @frappe.whitelist()
    def get_quote(self):
        q_data = frappe.get_list("Quotation",{"work_flow":"Pending for COO","docstatus":0},["name","party_name","transaction_date","sales_person_name"])
        return q_data

    @frappe.whitelist()
    def get_po(self):
        po_data = frappe.get_list("Purchase Order",{"workflow_state":"Pending for COO"},["name","supplier","transaction_date"])
        return po_data


    @frappe.whitelist()
    def get_expence_claim(self):
        expense = frappe.get_list("Expense Claim",{"workflow_state":"Pending for HOD"},["employee","employee_name","expense_approver","total_claimed_amount"])
        return expense

    @frappe.whitelist()
    def get_expence_claim_1(self):
        expense_1 = frappe.get_list("Expense Claim",{"workflow_state":"Pending for CFO"},["employee","employee_name","expense_approver","total_claimed_amount"])
        return expense_1

    @frappe.whitelist()
    def get_leave_app(self):
        leave_app = frappe.get_list("Leave Application",{"workflow_state":"Pending for HOD"},["employee","employee_name","from_date","to_date","leave_type","total_leave_days"])
        return leave_app

    # @frappe.whitelist()
    # def get_att_req(self):
    #     att_req = frappe.get_list("Attandance Request",{"workflow_state":"Pending for HOD"},["employee","employee_name","from_date","to_date","reason"])
    #     return att_req


    @frappe.whitelist()
    def get_sales_order_hod(self):
        data_hod = frappe.get_list("Sales Order",{"workflow_state":"Pending for HOD"},["name","customer","transaction_date","sales_person_name"])
        return data_hod

    @frappe.whitelist()
    def get_sales_order_cfo(self):
        data_cfo = frappe.get_list("Sales Order",{"workflow_state":"Pending for CFO"},["name","customer","transaction_date","sales_person_name"])
        return data_cfo


    @frappe.whitelist()
    def get_po_cfo(self):
        po_data_cfo = frappe.get_list("Purchase Order",{"workflow_state":"Pending for CFO"},["name","supplier","transaction_date"])
        return po_data_cfo

    @frappe.whitelist()
    def submit_doc(self,doctype,name,workflow_state):
        doc = frappe.get_doc(doctype,name)
        doc.workflow_state = workflow_state
        doc.save(ignore_permissions=True)
        # doc.submit()
        return "ok"

    @frappe.whitelist()
    def submit_quote(self,doctype,name,work_flow):
        frappe.db.set_value(doctype,name,"workflow",work_flow)
        # doc = frappe.get_doc(doctype,name)
        # doc.work_flow = work_flow
        # doc.save(ignore_permissions=True)
        # doc.submit()
        return "ok"

