from email import message
import frappe
from erpnext.hr.doctype.leave_application.leave_application import LeaveApplication
from erpnext.hr.doctype.expense_claim.expense_claim import ExpenseClaim
from erpnext.hr.doctype.attendance_request.attendance_request import AttendanceRequest
from frappe import _


class CustomLeaveApplication(LeaveApplication):
    def validate(self):
        self.status = 'Approved'

class CustomExpenseClaim(ExpenseClaim):
    def validate(self):
        self.approval_status = 'Approved'

class CustomAttendanceRequest(AttendanceRequest):
    def validate(self):
        wfh = frappe.db.get_value('Work From Home Request',{'employee':self.employee,'work_from_date':self.from_date},['workflow_state'])
        if wfh != 'Approved':
            frappe.throw(_(' Employee %s Work From Home Request is Not Approved by %s'%(self.employee,self.from_date)))
        else:
            message = ('Employee Work From Home Request is Approved')
            frappe.log_error('Attendance Request',message)

    