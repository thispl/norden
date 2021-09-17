# -*- coding: utf-8 -*-
# Copyright (c) 2021, Teampro and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class NACDatasheet(Document):
	pass

@frappe.whitelist()
def get_technical_parameter(doc):
	data = ''
	data += '<tr><td><b style="color:#505050">Part Number</p></b></td><td colspan="1"><b style="color:#505050">Description</b></td> <td style="white-space: nowrap;"><b style="color:#505050">Standard Quantity</b></td></tr><tr>'
	for d in doc.technical_parameters:
		if d.part_number == "br":
			data += '</tr></table><br><table><tr>'
		else:
			data += '<td>%s</td></tr>'%(d.part_number,d.description,d.standard_quantity)
	return data