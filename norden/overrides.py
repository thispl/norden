from email import message
import frappe
from hrms.hr.doctype.leave_application.leave_application import LeaveApplication
from hrms.hr.doctype.expense_claim.expense_claim import ExpenseClaim
from hrms.hr.doctype.attendance_request.attendance_request import AttendanceRequest
from frappe import _
import frappe

class CustomLeaveApplication(LeaveApplication):
	def before_save(self):
		self.status = 'Approved'

		year_first = "2023-01-01"
		year_end = "2023-12-31"
		
		result = frappe.db.sql("""SELECT sum(total_leave_days) as count  FROM `tabLeave Application` WHERE leave_type='Sick Leave'  and from_date  between '%s' and '%s' and employee = '%s' """%(year_first,year_end,self.employee), as_dict=True)[0]
		res_count = result['count'] or 0
		
		if res_count > 15:
			frappe.throw(_('Sick Leave application limit is reached'))
		
	   
			 

class CustomExpenseClaim(ExpenseClaim):
	def before_save(self):
		self.approval_status = 'Approved'

class CustomAttendanceRequest(AttendanceRequest):
	def before_save(self):
		wfh = frappe.db.get_value('Work From Home Request',{'employee':self.employee,'work_from_date':self.from_date},['workflow_state'])
		if wfh != 'Approved':
			frappe.throw(_(' Employee %s Work From Home Request is Not Approved by %s'%(self.employee,self.from_date)))
		else:
			message = ('Employee Work From Home Request is Approved')
			frappe.log_error('Attendance Request',message)
