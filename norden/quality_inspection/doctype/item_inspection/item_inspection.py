# Copyright (c) 2022, Teampro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ItemInspection(Document):
	def before_submit(self):
		if self.received_quantity:
			rec_qty = self.received_quantity
			# split_qty = self.sample_reference + self.accepted_quantity + self.rejected_quantity
			split_qty = self.sample_qty + self.accepted_quantity + self.rejected_quantity
			if rec_qty != split_qty:
				frappe.validated = False
				frappe.throw("Received Qty Does Not Matched with Inspection Qty")
		
				
	def on_submit(self):
		if self.delivery_qc ==1:
			pick_list=frappe.get_doc("Pick List",{"sales_order":self.so_number})
			for i in pick_list.locations:
				if i.item_code==self.item_code and i.stock_qty==self.received_quantity:
					i.qty=self.accepted_quantity * i.conversion_factor
					i.stock_qty=self.accepted_quantity * i.conversion_factor

					i.custom_accepted_quantity=self.accepted_quantity
					i.custom_rejected_quantity=self.rejected_quantity
					i.custom_inspection_completed = 1
			pick_list.save(ignore_permissions=True)
			frappe.db.commit()
		# if self.pdi == 0:
		# 	if self.pr_number:
		# 		pr = frappe.get_doc("Purchase Receipt",self.pr_number)
		# 		for i in pr.items:
		# 			# frappe.errprint(row)
		# 			if self.item_code == i.item_code and self.id == i.name:
		# 				i.qty = (self.accepted_quantity / i.conversion_factor)
		# 				i.rejected_qty = (self.rejected_quantity / i.conversion_factor)
		# 				i.stock_qty = self.accepted_quantity
		# 				mrb = frappe.get_value("Warehouse",{"company":self.company_name,"is_mrb":1})
		# 				i.rejected_warehouse = mrb
		# 				i.rejected_serial_no = self.rejected_serial
		# 				i.custom_inspection_completed = 1
		# 		pr.save(ignore_permissions = True)
		
		
		if self.stock_entry:
			pr = frappe.get_doc("Stock Entry",self.stock_entry)
			for i in pr.items:
				if self.item_code == i.item_code and self.row == i.name:
					i.custom_inspection_completed = 1
			
			pr.save(ignore_permissions = True)
				
			

		# if self.dn_number:
		# 	if self.pr_number:
		# 		pr = frappe.get_doc("Purchase Receipt",self.pr_number)
		# 		for i in pr.items:
		# 			if self.item_code == i.item_code and self.id == i.name:
		# 				i.qty = (self.accepted_quantity / i.conversion_factor)
		# 				i.rejected_qty = (self.rejected_quantity / i.conversion_factor)
		# 				mrb = frappe.get_value("Warehouse",{"company":self.company_name,"is_mrb":1})
		# 				i.rejected_warehouse = mrb
		# 				i.rejected_serial_no = self.rejected_serial
		# 		pr.save(ignore_permissions = True)
			
		# if self.rejected_qty > 0:
		#     new_doc = frappe.new_doc('MRB')  
		#     new_doc.purchase_receipt = self.pr_number
		#     new_doc.item_inspection = self.name
		#     new_doc.item_code = self.item_code
		#     new_doc.description = self.description
		#     new_doc.qty = self.rejected_qty
		#     new_doc.purchase_order = self. po_number
		#     new_doc.save(ignore_permissions=True)

		#     new_docu = frappe.new_doc('SCAR')  
		#     new_docu.purchase_receipt_number = self.pr_number
		#     new_docu.item_inspection = self.name
		#     new_docu.item_code = self.item_code
		#     new_docu.item_name = self.description
		#     new_docu.rejected_qty = self.rejected_qty
		#     new_docu.purchase_order_number = self. po_number
		#     new_docu.save(ignore_permissions=True)
			
		if (self.sample_qty) > 0:
			if self.delivery_qc !=1:
				s = frappe.new_doc("Stock Entry")
				s.stock_entry_type = "Material Transfer"
				s.posting_date = self.custom_submission_date
				s.set_posting_time = 1
				s.from_warehouse = self.warehouse    
				s.company = self.company_name
				like_filter = "%"+"Destructive"+"%"
				store_warehouse = frappe.db.get_value('Warehouse', filters={"company":self.company_name,'name': ['like', like_filter]})
				s.custom_item_inspection = self.name
				cc = frappe.get_value("Cost Center",{"company":self.company_name,"is_default":1})
				s.to_warehouse = store_warehouse
				s.append("items", {
				"s_warehouse":self.warehouse,
				"t_warehouse":store_warehouse,
				"item_code":self.item_code,
				"qty":self.sample_qty,
				"cost_center":cc
				})
				s.save(ignore_permissions=True)
				s.submit()

		if self.accepted_quantity > 0:
			if self.delivery_qc !=1:
				se = frappe.new_doc("Stock Entry")
				se.stock_entry_type = "Material Transfer"
				se.posting_date = self.custom_submission_date
				se.set_posting_time = 1
				se.from_warehouse = self.warehouse
				se.company = self.company_name
				se.custom_item_inspection = self.name
				store_warehouse = frappe.get_value("Warehouse",{"company":self.company_name,"default_for_stock_transfer":1})
				
				cc = frappe.get_value("Cost Center",{"company":self.company_name,"is_default":1})
				se.to_warehouse = self.accepted_warehouse
				se.append("items", {
				"s_warehouse":self.warehouse,
				"t_warehouse":self.accepted_warehouse,
				"item_code":self.item_code,
				"qty":self.accepted_quantity,
				# "serial_and_batch_bundle":self.serial_and_batch_bundle,
				# "serial_no":self.serial,
				# "batch_no":self.batch_number_new,
				# "batch_no":self.batch_number,
				"cost_center":cc
				})
				se.save(ignore_permissions=True)
				se.submit()
			
		if self.rejected_quantity > 0:
			if self.delivery_qc !=1:
				se = frappe.new_doc("Stock Entry")
				se.stock_entry_type = "Material Transfer"
				se.posting_date = self.custom_submission_date
				se.set_posting_time = 1
				se.from_warehouse = self.warehouse
				se.company = self.company_name
				se.custom_item_inspection = self.name
				store_warehouse = frappe.get_value("Warehouse",{"company":self.company_name,"is_mrb":1})
				cc = frappe.get_value("Cost Center",{"company":self.company_name,"is_default":1})
				se.to_warehouse = store_warehouse
				se.append("items",{
					"s_warehouse":self.warehouse,
					"t_warehouse":store_warehouse,
					"item_code":self.item_code,
					"qty":self.rejected_quantity,
					"cost_center":cc
				})
				se.save(ignore_permissions=True)
				se.submit()
				# rejected_serial_and_batch_bundle=frappe.db.get_value("Stock Entry Detail",{'parent':se.name},['serial_and_batch_bundle'])
				# pur_rec=frappe.get_doc("Purchase Receipt",self.pr_number)
				# for pr in pur_rec.items:
				# 	if (pr.item_code==self.item_code) and (pr.serial_and_batch_bundle==self.serial_and_batch_bundle):
				# 		pr.rejected_serial_and_batch_bundle=rejected_serial_and_batch_bundle
				# pur_rec.submit()
			
			
		if self.rejected_quantity > 0:
			new_doc = frappe.new_doc('MRB')  
			new_doc.purchase_receipt = self.pr_number
			new_doc.item_code = self.item_code
			new_doc.description = self.description
			new_doc.qty = self.rejected_quantity
			new_doc.company = self.company_name
			store_warehouse = frappe.get_value("Warehouse",{"company":self.company_name,"is_mrb":1})
			new_doc.warehouse = store_warehouse
			new_doc.rejected_qty_serial_no = self.rejected_serial

			new_doc.item_inspection = self.name
			new_doc.id = self.id
			new_doc.supplier = self.supplier_name
			new_doc.ncmr_no = self.ncmr_no
			new_doc.reason_for_rejection = self.reason_for_rejection
			new_doc.purchase_order = self. po_number
			new_doc.save(ignore_permissions=True)
			if self.delivery_qc !=1:
				new_docu = frappe.new_doc('SCAR')  
				new_docu.purchase_receipt_number = self.pr_number
				new_docu.item_code = self.item_code
				new_docu.item_name = self.description
				new_docu.rejected_qty = self.rejected_quantity
				new_docu.company = self.company_name
				new_docu.purchase_order_number = self. po_number
				new_docu.save(ignore_permissions=True)
	
	
	def on_cancel(self):
		if self.delivery_qc==0:
			# if self.pr_number:
			# 	pr = frappe.get_doc("Purchase Receipt",self.pr_number)
			# 	for i in pr.items:
			# 		if self.item_code == i.item_code and self.id == i.name:
			# 			i.qty = float(self.received_quantity / i.conversion_factor)
			# 			i.stock_qty = self.received_quantity
			# 			i.rejected_qty = 0
			# 			i.serial_and_batch_bundle = self.serial_and_batch_bundle
			# 			i.rejected_serial_and_batch_bundle = ''
			# 			i.warehouse = self.warehouse
			# 			i.rejected_warehouse = ''
			# 			i.custom_inspection_completed = 0
			# 	pr.save(ignore_permissions = True)
				
			if self.stock_entry:
				pr = frappe.get_doc("Stock Entry",self.stock_entry)
				for i in pr.items:
					if self.item_code == i.item_code and self.row == i.name:
						i.custom_inspection_completed = 0
				
				pr.save(ignore_permissions = True)
		# if self.delivery_qc==1:
		#     pick_list=frappe.get_doc("Pick List",{"sales_order":self.so_number})
		#     for i in pick_list.locations:
		#         if i.item_code==self.item_code and i.stock_qty==self.received_quantity:
		#             i.qty = i.stock_qty
		#             i.custom_accepted_quantity=0
		#             i.custom_rejected_quantity=0
		#             i.custom_inspection_completed = 0
		#     pick_list.save(ignore_permissions=True)
		#     frappe.db.commit()
			












