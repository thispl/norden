# # Copyright (c) 2023, Teampro and contributors
# # For license information, please see license.txt

# import frappe
# import erpnext
# from frappe.model.document import Document
# from frappe.utils import date_diff, add_months, today, add_days, nowdate
# from frappe.utils.csvutils import read_csv_content
# from frappe.utils.file_manager import get_file
# import json

# class MRB(Document):
# 	def on_submit(self):
# 		if self.mrb_action == "Scrap":
# 			s = frappe.new_doc("Stock Entry")
# 			s.stock_entry_type = "Material Transfer"   
# 			s.from_warehouse = self.warehouse    
# 			s.company = self.company 
# 			scrap_warehouse = frappe.get_value("Warehouse",{"company":self.company,"is_scrap":1})
# 			cc = frappe.get_value("Cost Center",{"company":self.company,"is_default":1})
# 			s.to_warehouse = scrap_warehouse
# 			s.append("items", {
# 			"s_warehouse":self.warehouse,
# 			"t_warehouse":scrap_warehouse,
# 			"item_code":self.item_code,
# 			"qty":self.qty,
# 			"uom":self.uom,
# 			"serial_no":self.serial_no,
# 			"batch_no":self.batch_no,
# 			"basic_rate":self.rate,
# 			"cost_center":cc
# 			})
# 			s.save(ignore_permissions=True)
# 			s.submit()

# 		if self.mrb_action == "RTV": 
# 			pr = frappe.get_doc("Purchase Receipt",self.purchase_receipt)
# 			s = frappe.new_doc("Purchase Receipt")
# 			s.purchase_order_no = self.purchase_order
# 			s.return_against = self.purchase_receipt
# 			s.supplier = pr.supplier
# 			s.company = pr.company
# 			s.is_return = 1
# 			s.currency = pr.currency
# 			s.buying_price_list = pr.buying_price_list
# 			s.price_list_currency = pr.price_list_currency
# 			s.plc_conversion_rate = pr.plc_conversion_rate
# 			for i in pr.items:
# 				s.append("items", {
# 				"item_code":i.item_code,
# 				"item_name":i.item_name,
# 				"description":i.description,
# 				"received_qty":-i.received_qty,
# 				"rejected_qty":-i.rejected_qty,
# 				"qty":-i.qty,
# 				"uom":i.uom,
# 				"serial_no":i.serial_no,
# 				"batch_no":i.batch_no,
# 				"rate":i.rate,
# 				"cost_center":i.cost_center,
# 				"conversion_factor":i.conversion_factor,
# 				"warehouse":i.warehouse,
# 				"expense_account":i.expense_account,
# 				"rejected_warehouse":i.rejected_warehouse,
# 				"skip_qc":1,
# 				})
# 			s.save(ignore_permissions=True)
# 			s.submit()

# 		if self.mrb_action == "Purchase Return": 
# 			pr = frappe.get_doc("Purchase Receipt",self.purchase_receipt)
# 			s = frappe.new_doc("Purchase Receipt")
# 			s.purchase_order_no = self.purchase_order
# 			s.return_against = self.purchase_receipt
# 			s.supplier = pr.supplier
# 			s.company = pr.company
# 			s.is_return = 1
# 			s.currency = pr.currency
# 			s.buying_price_list = pr.buying_price_list
# 			s.price_list_currency = pr.price_list_currency
# 			s.plc_conversion_rate = pr.plc_conversion_rate
# 			for i in pr.items:
# 				s.append("items", {
# 				"item_code":i.item_code,
# 				"item_name":i.item_name,
# 				"description":i.description,
# 				"received_qty":-i.received_qty,
# 				"rejected_qty":-i.rejected_qty,
# 				"qty":-i.qty,
# 				"uom":i.uom,
# 				"serial_no":i.serial_no,
# 				"batch_no":i.batch_no,
# 				"rate":i.rate,
# 				"cost_center":i.cost_center,
# 				"conversion_factor":i.conversion_factor,
# 				"warehouse":i.warehouse,
# 				"expense_account":i.expense_account,
# 				"rejected_warehouse":i.rejected_warehouse,
# 				"skip_qc":1,
# 				})
# 			s.save(ignore_permissions=True)
# 			s.submit()

# 		if self.mrb_action == "Repair / Rework" or self.mrb_action == "Deviation" or self.mrb_action == "Use as it is" :
# 			s = frappe.new_doc("Stock Entry")
# 			s.stock_entry_type = "Material Transfer"   
# 			s.from_warehouse = self.warehouse    
# 			s.company = self.company 
# 			store_warehouse = frappe.get_value("Warehouse",{"company":self.company,"default_for_stock_transfer":1})
# 			cc = frappe.get_value("Cost Center",{"company":self.company,"is_default":1})
# 			s.to_warehouse = store_warehouse
# 			s.append("items", {
# 			"s_warehouse":self.warehouse,
# 			"t_warehouse":store_warehouse,
# 			"item_code":self.item_code,
# 			"qty":self.qty,
# 			"uom":self.uom,
# 			"serial_no":self.serial_no,
# 			"batch_no":self.batch_no,
# 			"basic_rate":self.rate,
# 			"cost_center":cc
# 			})
# 			s.save(ignore_permissions=True)
# 			s.submit()


import frappe
import erpnext
from frappe.model.document import Document
from frappe.utils import date_diff, add_months, today, add_days, nowdate
from frappe.utils.csvutils import read_csv_content
from frappe.utils.file_manager import get_file
import json

class MRB(Document):
    def before_submit(self):
        if (self.qty):
            rec_qty = self.qty
            split_qty = self.use_as_is + self.scrap + self.rework + self.return_to_vendor
            if rec_qty != split_qty:
                frappe.validated = False
                frappe.throw("Rejected Qty Does Not Matched with Mrb Actions Qty")
    
    
    def on_submit(self):
        if self.purchase_receipt:
            pr = frappe.get_doc("Purchase Receipt",self.purchase_receipt)
            for i in pr.items:
                if self.item_code == i.item_code and self.id == i.name:
                    i.rejected_qty = (self.return_to_vendor	/ i.conversion_factor)
                    like_filter = "%"+"RTV"+"%"
                    re_tv = frappe.db.get_value('Warehouse', filters={"company":self.company,'name': ['like', like_filter]})
                    i.rejected_warehouse = re_tv
                    # i.rejected_serial_no = self.rejected_serial_no
            pr.save(ignore_permissions = True)
                
                
        if self.use_as_is > 0:
            s = frappe.new_doc("Stock Entry")
            s.stock_entry_type = "Material Transfer"   
            s.from_warehouse = self.warehouse    
            s.company = self.company 
            s.custom_mrb = self.name
            store_warehouse = frappe.get_value("Warehouse",{"company":self.company,"custom_stores":1})
            cc = frappe.get_value("Cost Center",{"company":self.company,"is_default":1})
            s.to_warehouse = store_warehouse
            s.append("items", {
            "s_warehouse":self.warehouse,
            "t_warehouse":store_warehouse,
            "item_code":self.item_code,
            "qty":self.use_as_is,
            "uom":self.uom,
            "serial_no":self.serial_no,
            "batch_no":self.batch_no,
            "allow_zero_valuation_rate":1,
            # "basic_rate":self.rate,
            "cost_center":cc
            })
            s.save(ignore_permissions=True)
            s.submit()


        if self.scrap > 0:
            s = frappe.new_doc("Stock Entry")
            s.stock_entry_type = "Material Transfer"   
            s.from_warehouse = self.warehouse    
            s.company = self.company 
            s.custom_mrb = self.name
            scrap_warehouse = frappe.get_value("Warehouse",{"company":self.company,"is_scrap":1})
            cc = frappe.get_value("Cost Center",{"company":self.company,"is_default":1})
            s.to_warehouse = scrap_warehouse
            s.append("items", {
            "s_warehouse":self.warehouse,
            "t_warehouse":scrap_warehouse,
            "item_code":self.item_code,
            "qty":self.scrap,
            "uom":self.uom,
            "serial_no":self.serial_no,
            "batch_no":self.batch_no,
            "allow_zero_valuation_rate":1,
            # "basic_rate":self.rate,
            "cost_center":cc
            })
            s.save(ignore_permissions=True)
            s.submit()
   
   
        if self.rework > 0:
            s = frappe.new_doc("Stock Entry")
            s.stock_entry_type = "Material Transfer"   
            s.from_warehouse = self.warehouse    
            s.company = self.company 
            s.custom_mrb = self.name
            like_filter = "%"+"Rework"+"%"
            store_warehouse = frappe.db.get_value('Warehouse', filters={"company":self.company,'name': ['like', like_filter]})
            cc = frappe.get_value("Cost Center",{"company":self.company,"is_default":1})
            s.to_warehouse = self.rework_warehouse
            s.append("items", {
            "s_warehouse":self.warehouse,
            "t_warehouse": self.rework_warehouse,
            "item_code":self.item_code,
            "qty":self.rework,
            "uom":self.uom,
            "serial_no":self.serial_no,
            "batch_no":self.batch_no,
            # "basic_rate":self.rate,
            "cost_center":cc
            })
            s.save(ignore_permissions=True)
            s.submit()


        if self.return_to_vendor > 0:
            s = frappe.new_doc("Stock Entry")
            s.stock_entry_type = "Material Transfer"   
            s.from_warehouse = self.warehouse    
            s.company = self.company
            s.custom_mrb = self.name
            like_filter = "%"+"RTV"+"%"
            store_warehouse = frappe.db.get_value('Warehouse', filters={"company":self.company,'name': ['like', like_filter]})
            cc = frappe.get_value("Cost Center",{"company":self.company,"is_default":1})
            s.to_warehouse = store_warehouse
            s.append("items", {
            "s_warehouse":self.warehouse,
            "t_warehouse":store_warehouse,
            "item_code":self.item_code,
            "qty":self.return_to_vendor,
            "uom":self.uom,
            "serial_no":self.serial_no,
            "batch_no":self.batch_no,
            # "basic_rate":self.rate,
            "cost_center":cc
            })
            s.save(ignore_permissions=True)
            s.submit()




