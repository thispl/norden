# Copyright (c) 2022, Teampro and contributors
# For license information, please see license.txt

from email import message
import frappe
from frappe import _
from frappe.model.document import Document

class CustomerEntertainmentExpenseClaim(Document):
	
	def validate(self):
		for customer in self.customer_expense_claim:
			if len(str(customer.contact_number)) < 10:
				frappe.throw(_('Contact Number should be 10 digits'))
			elif len(str(customer.contact_number)) > 10:
				frappe.throw(_('Contact Number should be 10 digits'))
			else:
				message = ('Contact Number should be 10 digits')	
				frappe.log_error('Customer Entertaiment',message)




