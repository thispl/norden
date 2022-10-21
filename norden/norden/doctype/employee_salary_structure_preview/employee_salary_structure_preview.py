# Copyright (c) 2022, Teampro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class EmployeeSalaryStructurePreview(Document):
	pass

	def validate(self):
		total_deduction = self.esi + self.epf + self.professional_tax + self.lwf
		self.total_deduction = total_deduction
		total_employer_contribution = self.esi + self.epf + self.lwf
		self.total_employer_contribution = total_employer_contribution










	

