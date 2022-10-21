# Copyright (c) 2022, Teampro and contributors
# For license information, please see license.txt

import frappe
import erpnext
from frappe.model.document import Document
from frappe.utils import date_diff, add_months, today, add_days, nowdate
from frappe.utils.csvutils import read_csv_content
from frappe.utils.file_manager import get_file
import json

class BlockWarehouse(Document):
    def validate(self):
        if self.workflow_state == "Transfered":
            # warehouse = frappe.get_value("Warehouse",{"company":self.company,"warehouse_name":self.source},[])
            # target = frappe.get_value("Warehouse",{"company":self.company,"warehouse_name":self.target})
            stock = frappe.new_doc("Stock Entry")
            stock.company = self.company
            stock.stock_entry_type = "Material Transfer"
            stock.from_warehouse = self.source
            stock.to_warehouse = self.target
            for i in self.items:
                stock.append("items", {
                "s_warehouse": self.source,
                "t_warehouse":  self.target,
                "item_code": i.item_code,
                "qty":i.quantity,
                "allow_zero_valuation_rate":1
                })
            stock.save(ignore_permissions=True)
            stock.submit()

        if self.workflow_state == "Returned":
            # warehouse = frappe.get_value("Warehouse",{"company":self.company,"warehouse_name":self.target})
            # target = frappe.get_value("Warehouse",{"company":self.company,"warehouse_name":self.source})
            stock = frappe.new_doc("Stock Entry")
            stock.company = self.company
            stock.stock_entry_type = "Material Transfer"
            stock.from_warehouse = self.target
            stock.to_warehouse = self.source
            for i in self.items:
                stock.append("items", {
                "s_warehouse":self.target,
                "t_warehouse": self.source,
                "item_code": i.item_code,
                "qty":i.quantity,
                "allow_zero_valuation_rate":1
                })
            stock.save(ignore_permissions=True)
            stock.submit()

    @frappe.whitelist()
    def get_rate(self):
        for i in self.items:
            country = frappe.get_value("Company",{"name":self.company},["country"])
            frappe.errprint(country)
            if country == "India" :
                item_price = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"India STP"},["price_list_rate"])
            if country == "Singapore" :
                item_price = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Singapore Sales Price"},["price_list_rate"])
            if country == "United Arab Emirates" :
                item_price = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Base Sales Price - NCMEF"},["price_list_rate"])
            if country == "United Kingdom" :
                item_price = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"UK Destination Charges"},["price_list_rate"])
            return item_price