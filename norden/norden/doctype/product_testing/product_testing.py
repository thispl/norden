# Copyright (c) 2023, Teampro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ProductTesting(Document):
    def on_update(self):
        if self.workflow_state == "Rejected":
            stock = frappe.new_doc("Stock Entry")
            stock.company = self.company
            stock.stock_entry_type = "Material Transfer"
            stock.from_warehouse = self.source
            stock.to_warehouse = self.target
            for i in self.items:
                stock.append("items", {
                "s_warehouse": self.source,
                "t_warehouse":  self.target,
                "item_code": self.item_code,
                "qty":i.qty,
                "allow_zero_valuation_rate":1
                })
            stock.save(ignore_permissions=True)
            stock.submit()
