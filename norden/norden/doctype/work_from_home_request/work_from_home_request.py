# Copyright (c) 2022, Teampro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cstr, cint, getdate, get_last_day, get_first_day, add_days,date_diff


class WorkFromHomeRequest(Document):

	# def before_update_after_submit(self):
	# 	if self.workflow_state == 'Attendance Marked':
	# 		frappe.log_error('wfh',self.name)
			# dates = self.get_dates(self.work_from_date,self.work_to_date)
			# for date in dates:
			# 	attendance = frappe.db.exists('Attendance',{'employee':self.employee,'attendance_date':date,'wfh_marked':'1'})
			# 	if attendance:
			# 		frappe.db.set_value('Attedance',attendance,'work_from_home',self.name)
	
	def on_submit(self):
		if self.workflow_state == 'Attendance Marked':
			company = frappe.get_value('Employee', self.employee, 'company')  # Get the company associated with the employee

			dates = self.get_dates(self.work_from_date, self.work_to_date)
			for date in dates:
				attendance = frappe.db.exists('Attendance', {'employee': self.employee, 'attendance_date': date, 'docstatus': ('!=', '2')})
				if not attendance:
					if self.half_day == 1:
						att = frappe.new_doc('Attendance')
						att.employee = self.employee
						att.company = company  # Set the Company field
						att.status = 'Present'
						att.remarks_state = 'Work From Home/HD'
						att.attendance_date = date
						att.wfh_marked = 1
					else:
						att = frappe.new_doc('Attendance')
						att.employee = self.employee
						att.company = company  # Set the Company field
						att.status = 'Work From Home'
						att.attendance_date = date
						att.wfh_marked = 1
					att.save(ignore_permissions=True)
					att.submit()
					frappe.db.commit()
					frappe.msgprint('Attendance Marked as Work From Home')
				else:
					frappe.throw(frappe._('Attendance Already Marked for that %s' % (date)))
	

	def on_cancel(self):
		if self.docstatus == 2:		
			attendance = frappe.db.exists('Attendance',{'employee':self.employee,'attendance_date':('between',(self.work_from_date,self.work_to_date)),'wfh_marked':'1'})
			if attendance:
				attend = frappe.db.get_all('Attendance',{'employee':self.employee,'attendance_date':('between',(self.work_from_date,self.work_to_date)),'wfh_marked':'1'})
				for att in attend:
					frappe.db.sql(""" update `tabAttendance` set docstatus = 2 where name = '%s'"""%(att.name))

	def get_dates(self,from_date,to_date):
		no_of_days = date_diff(add_days(to_date, 1), from_date)
		dates = [add_days(from_date, i) for i in range(0, no_of_days)]
		return dates			

