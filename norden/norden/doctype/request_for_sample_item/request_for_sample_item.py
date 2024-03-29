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
    def on_update(self):
        if self.workflow_state == 'Issued':
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

            # frappe.errprint(stock.name)
            # self.stock_issued= stock.name
            # self.save(ignore_permissions=True)
            # frappe.db.commit()


        if self.workflow_state == "Returned":
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



    # def after_insert(self):
    #     if self.workflow_state == 'Issued':
    #         se = frappe.get_doc("Stock Entry",{})
        
            

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

