# Copyright (c) 2024, Teampro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ERPStockReconciliationTool(Document):
	def on_submit(self):
		if float(self.qty_addedremoved)<0.0:
			se=frappe.new_doc("Stock Entry")
			se.company=self.company
			se.stock_entry_type='Material Issue'
			se.append('items',{
				's_warehouse':self.warehouse,
				'item_code':self.item,
				'qty':self.qty_addedremoved
			})
			se.save(ignore_permissions=True)
			# se.submit()
			frappe.msgprint(str(self.qty_addedremoved)+" has been outwared from the warehouse : "+str(self.warehouse) +" for the Item: "+str(self.item))
		elif float(self.qty_addedremoved)>0.0:
			se=frappe.new_doc("Stock Entry")
			se.company=self.company
			se.stock_entry_type='Material Receipt'
			se.append('items',{
				't_warehouse':self.warehouse,
				'item_code':self.item,
				'qty':-(self.qty_addedremoved)
			})
			se.save(ignore_permissions=True)
			# se.submit()
			frappe.msgprint(str(-(self.qty_addedremoved))+" has been inwarded to the warehouse : "+str(self.warehouse) +" for the Item: "+str(self.item))