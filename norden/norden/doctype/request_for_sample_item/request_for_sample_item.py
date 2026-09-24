# Copyright (c) 2022, Teampro and contributors
# For license information, please see license.txt
import frappe
import erpnext
from frappe.model.document import Document
from frappe.utils import date_diff, add_months, today, add_days, nowdate
from frappe.utils.csvutils import read_csv_content
from frappe.utils.file_manager import get_file
import json

class RequestforSampleItem(Document):
	@frappe.whitelist()
	def get_rate(self):
		for i in self.items:
			country = frappe.get_value("Company",{"name":self.company},["country"])
			frappe.errprint(country)
			if country == "India" :
				item_price = frappe.get_value("Item Price",{"item_code":i.item,"price_list":"India MRP"},["price_list_rate"])
			if country == "Singapore" :
				item_price = frappe.get_value("Item Price",{"item_code":i.item,"price_list":"Singapore Sales Price"},["price_list_rate"])
			if country == "United Arab Emirates" :
				item_price = frappe.get_value("Item Price",{"item_code":i.item,"price_list":"Base Sales Price - NCMEF"},["price_list_rate"])
			if country == "United Kingdom" :
				item_price = frappe.get_value("Item Price",{"item_code":i.item,"price_list":"UK Distributor Price"},["price_list_rate"])
			return item_price

	def on_update(self):
		if self.workflow_state == 'Issued' and self.custom_is_stock_issued==0:
			stock = frappe.new_doc("Stock Entry")
			stock.company = self.company
			stock.stock_entry_type = "Material Transfer"
			stock.customer = self.customer
			stock.from_warehouse = self.source_warehouse
			stock.to_warehouse = self.target_warehouse
			for i in self.items:
				stock.append("items", {
				"s_warehouse": self.source_warehouse,
				"t_warehouse": self.target_warehouse,
				"item_code": i.item,
				"qty": i.quantity,
				"allow_zero_valuation_rate":1
			})
			stock.save(ignore_permissions=True)
			stock.submit()
			self.db_set("stock_issued", stock.name, update_modified=False)
			self.db_set("custom_is_stock_issued", 1, update_modified=False)

			# frappe.errprint(stock.name)
			# self.stock_issued= stock.name
			# self.save(ignore_permissions=True)
			# frappe.db.commit()


		if self.workflow_state == "Returned" and self.is_stock_returned==0:
			s = frappe.new_doc("Stock Entry")
			s.company = self.company
			s.stock_entry_type = "Material Transfer"
			s.customer = self.customer
			s.from_warehouse = self.target_warehouse
			s.to_warehouse = self.source_warehouse,
			for i in self.items:
				s.append("items", {
				"s_warehouse": self.target_warehouse,
				"t_warehouse": self.source_warehouse,
				"item_code": i.item,
				"qty":i.quantity,
				"allow_zero_valuation_rate":1
			})
			s.save(ignore_permissions=True)
			s.submit()
			self.db_set("stock_returned", s.name, update_modified=False)
			self.db_set("is_stock_returned", 1, update_modified=False)

	# @frappe.whitelist()
	# def transfer_item(self):
	# 	outward_name = ''
	# 	for i in self.items:
	# 		if i.serial_no:
	# 			inward = frappe.new_doc("Serial and Batch Bundle")
	# 			inward.company = self.company
	# 			inward.item_code = i.item
	# 			inward.warehouse = self.target_warehouse
	# 			inward.type_of_transaction = "Inward"
	# 			inward.total_qty = i.quantity
	# 			inward.total_amount = i.quantity * i.rate
	# 			split_codes = i.serial_no.split('\n')
	# 			inward.voucher_type = 'Stock Entry'
	# 			for code in split_codes:
	# 				inward.append('entries',{
	# 					'serial_no': code,
	# 					'batch_no': frappe.db.get_value("Serial No",code,'batch_no'),
	# 					'warehouse': self.target_warehouse,
	# 					'qty': 1
	# 				})
	# 			inward.insert()

	# 			outward = frappe.new_doc("Serial and Batch Bundle")
	# 			outward.company = self.company
	# 			outward.item_code = i.item
	# 			outward.warehouse = self.source_warehouse
	# 			outward.type_of_transaction = "Outward"
	# 			outward.total_qty = -i.quantity
	# 			outward.total_amount = -i.quantity * i.rate
	# 			split_codes = i.serial_no.split('\n')
	# 			outward.voucher_type = 'Stock Entry'
	# 			for code in split_codes:
	# 				outward.append('entries',{
	# 					'serial_no': code,
	# 					'batch_no': frappe.db.get_value("Serial No",code,'batch_no'),
	# 					'warehouse': self.source_warehouse,
	# 					'qty': -1
	# 				})
	# 			outward.insert()
	# 			outward_name = outward.name

	# 	stock = frappe.new_doc("Stock Entry")
	# 	stock.company = self.company
	# 	stock.stock_entry_type = "Material Transfer"
	# 	stock.customer = self.customer
	# 	stock.from_warehouse = self.source_warehouse
	# 	stock.to_warehouse = self.target_warehouse
	# 	for i in self.items:
	# 		stock.append("items", {
	# 		"s_warehouse": self.source_warehouse,
	# 		"t_warehouse": self.target_warehouse,
	# 		"item_code": i.item,
	# 		"qty": i.quantity,
	# 		"allow_zero_valuation_rate":1,
	# 		"serial_and_batch_bundle":outward_name
	# 	})
	# 	stock.save(ignore_permissions=True)
	# 	frappe.db.set_value("Request for Sample Item",self.name,"stock_issued", stock.name, update_modified=False)
	# 	for i in self.items:
	# 		if i.serial_no:
	# 			frappe.db.set_value("Serial and Batch Bundle",outward.name,'voucher_no',stock.name, update_modified=False)
	# 			frappe.db.set_value("Serial and Batch Bundle",inward.name,'voucher_no',stock.name, update_modified=False)			
	# 	stock.submit()
		
	# @frappe.whitelist()
	# def return_item(self):
	# 	outward_name = ''
	# 	for i in self.items:
	# 		if i.serial_no:
	# 			inward = frappe.new_doc("Serial and Batch Bundle")
	# 			inward.company = self.company
	# 			inward.item_code = i.item
	# 			inward.warehouse = self.source_warehouse
	# 			inward.type_of_transaction = "Inward"
	# 			inward.total_qty = i.quantity
	# 			inward.total_amount = i.quantity * i.rate
	# 			split_codes = i.serial_no.split('\n')
	# 			inward.voucher_type = 'Stock Entry'
	# 			for code in split_codes:
	# 				inward.append('entries',{
	# 					'serial_no': code,
	# 					'batch_no': frappe.db.get_value("Serial No",code,'batch_no'),
	# 					'warehouse': self.source_warehouse,
	# 					'qty': 1
	# 				})
	# 			inward.insert()

	# 			outward = frappe.new_doc("Serial and Batch Bundle")
	# 			outward.company = self.company
	# 			outward.item_code = i.item
	# 			outward.warehouse = self.target_warehouse
	# 			outward.type_of_transaction = "Outward"
	# 			outward.total_qty = -i.quantity
	# 			outward.total_amount = -i.quantity * i.rate
	# 			split_codes = i.serial_no.split('\n')
	# 			outward.voucher_type = 'Stock Entry'
	# 			for code in split_codes:
	# 				outward.append('entries',{
	# 					'serial_no': code,
	# 					'batch_no': frappe.db.get_value("Serial No",code,'batch_no'),
	# 					'warehouse': self.target_warehouse,
	# 					'qty': -1
	# 				})
	# 			outward.insert()
	# 			outward_name = outward.name

	# 	s = frappe.new_doc("Stock Entry")
	# 	s.company = self.company
	# 	s.stock_entry_type = "Material Transfer"
	# 	s.customer = self.customer
	# 	s.from_warehouse = self.target_warehouse
	# 	s.to_warehouse = self.source_warehouse,
	# 	for i in self.items:
	# 		s.append("items", {
	# 		"s_warehouse": self.target_warehouse,
	# 		"t_warehouse": self.source_warehouse,
	# 		"item_code": i.item,
	# 		"qty":i.quantity,
	# 		"allow_zero_valuation_rate":1,
	# 		"serial_and_batch_bundle":outward_name
	# 	})
	# 	s.save(ignore_permissions=True)
	# 	s.submit()
	# 	frappe.db.set_value("Request for Sample Item",self.name,"stock_returned", s.name, update_modified=False)
	# 	for i in self.items:
	# 		if i.serial_no:
	# 			frappe.db.set_value("Serial and Batch Bundle",outward.name,'voucher_no',s.name, update_modified=False)
	# 			frappe.db.set_value("Serial and Batch Bundle",inward.name,'voucher_no',s.name, update_modified=False)

	@frappe.whitelist()
	def get_rate(self):
		for i in self.items:
			country = frappe.get_value("Company",{"name":self.company},["country"])
			if country == "India" :
				item_price = frappe.get_value("Item Price",{"item_code":i.item,"price_list":"India MRP"},["price_list_rate"])
				currency = frappe.get_value("Item Price",{"item_code":i.item,"price_list":"India MRP"},["currency"])
			if country == "Singapore" :
				item_price = frappe.get_value("Item Price",{"item_code":i.item,"price_list":"Singapore Sales Price"},["price_list_rate"])
				currency = frappe.get_value("Item Price",{"item_code":i.item,"price_list":"Singapore Sales Price"},["currency"])
			if country == "United Arab Emirates" :
				item_price = frappe.get_value("Item Price",{"item_code":i.item,"price_list":"Retail - NCMEF"},["price_list_rate"])
				currency = frappe.get_value("Item Price",{"item_code":i.item,"price_list":"Retail - NCMEF"},["currency"])
			if country == "United Kingdom" :
				item_price = frappe.get_value("Item Price",{"item_code":i.item,"price_list":"UK Distributor Price"},["price_list_rate"])
				currency = frappe.get_value("Item Price",{"item_code":i.item,"price_list":"UK Distributor Price"},["currency"])
			return item_price,currency

