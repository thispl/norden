# Copyright (c) 2025, Teampro and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe


class PDICompletionDetails(Document):
    def validate(self):
        # Get the PO and aggregate item quantities
        purchase = frappe.get_doc("Purchase Order", self.po)
        po_qty_map = {}
        for item in purchase.items:
            po_qty_map[item.item_code] = po_qty_map.get(item.item_code, 0) + item.qty

        # Aggregate the PDI quantities per item code
        pdi_qty_map = {}
        for row in self.pdi_completion:
            pdi_qty_map[row.item_code] = pdi_qty_map.get(row.item_code, 0) + row.qty

        # Check for excess quantity
        for item_code, pdi_qty in pdi_qty_map.items():
            po_qty = po_qty_map.get(item_code, 0)
            if pdi_qty > po_qty:
                frappe.throw(f"PDI quantity for item {item_code} ({pdi_qty}) exceeds the PO quantity ({po_qty}).")

        # Check for duplicate PDI creation
        if self.is_new():
            if frappe.db.exists("PDI Completion Details", {"po": self.po}):
                frappe.throw(f"PDI for PO {self.po} has already been created.")

        # Fill missing item quantities
        item_qty_tracker = {}
        for row in self.pdi_completion:
            item_qty_tracker[row.item_code] = item_qty_tracker.get(row.item_code, 0) + row.qty

        for item_code, po_qty in po_qty_map.items():
            current_qty = item_qty_tracker.get(item_code, 0)
            if current_qty < po_qty:
                remaining_qty = po_qty - current_qty
                self.append("pdi_completion", {
                    "item_code": item_code,
                    "qty": remaining_qty,
                    "pdi_completion": 0
                })
