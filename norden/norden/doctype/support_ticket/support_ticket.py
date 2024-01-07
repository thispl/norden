# Copyright (c) 2023, Teampro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class SupportTicket(Document):
    
    def validate(self):
        # Check if it's a new document
        if not self.get("__islocal"):
            return

        # Create new Issue document
        isu = frappe.new_doc("Issue")
        isu.subject = self.subject
        isu.status = self.status
        isu.description = self.description
        isu.resolution_details = self.resolution_details
        isu.opening_date = self.opening_date
        isu.opening_time = self.opening_time
        isu.flags.ignore_mandatory = True
        isu.save(ignore_permissions=True)





	