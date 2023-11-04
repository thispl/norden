# Copyright (c) 2023, Teampro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class LeaveSalary(Document):
	@frappe.whitelist()
	def get_leave_application(self):
		leave_application = frappe.db.get_all('Leave Application', {'employee': self.employee}, ['*'])
		if leave_application:
			for lap in leave_application:
				return lap.from_date, lap.to_date, lap.total_leave_days, lap.leave_balance, lap.leave_type
