# Copyright (c) 2022, Teampro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ItemInspection(Document):

    def on_submit(self):
        if self.pdi == 0:
            pr = frappe.get_doc("Purchase Receipt",self.pr_number)
            for i in pr.items:
                # frappe.errprint(row)
                if self.item_code == i.item_code and self.id == i.name:
                    i.qty = self.accepted_qty
                    i.rejected_qty = self.rejected_qty	
                    mrb = frappe.get_value("Warehouse",{"company":self.company_name,"is_mrb":1})
                    i.rejected_warehouse = mrb
                    i.rejected_serial_no = self.rejected_serial_no
            pr.save(ignore_permissions = True)

        if self.dn_number:
            pr = frappe.get_doc("Purchase Receipt",self.pr_number)
            for i in pr.items:
                if self.item_code == i.item_code and self.id == i.name:
                    i.qty = self.accepted_qty
                    i.rejected_qty = self.rejected_qty
                    mrb = frappe.get_value("Warehouse",{"company":self.company_name,"is_mrb":1})
                    i.rejected_warehouse = mrb
                    i.rejected_serial_no = self.rejected_serial_no
            pr.save(ignore_permissions = True)
            
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
            
        if int(self.sample_reference) > 0:
            s = frappe.new_doc("Stock Entry")
            s.stock_entry_type = "Material Transfer"   
            s.from_warehouse = self.warehouse    
            s.company = self.company_name
            like_filter = "%"+"Sample"+"%"
            store_warehouse = frappe.db.get_value('Warehouse', filters={"company":self.company_name,'name': ['like', like_filter]})
            frappe.errprint(store_warehouse)
            cc = frappe.get_value("Cost Center",{"company":self.company_name,"is_default":1})
            s.to_warehouse = store_warehouse
            s.append("items", {
            "s_warehouse":self.warehouse,
            "t_warehouse":store_warehouse,
            "item_code":self.item_code,
            "qty":self.sample_reference,
            "cost_center":cc
            })
            s.save(ignore_permissions=True)
            s.submit()

        if self.accepted_qty > 0:
            se = frappe.new_doc("Stock Entry")
            se.stock_entry_type = "Material Transfer"
            se.from_warehouse = self.warehouse
            se.company = self.company_name
            store_warehouse = frappe.get_value("Warehouse",{"company":self.company_name,"default_for_stock_transfer":1})
            
            cc = frappe.get_value("Cost Center",{"company":self.company_name,"is_default":1})
            se.to_warehouse = self.accepted_warehouse
            se.append("items", {
            "s_warehouse":self.warehouse,
            "t_warehouse":self.accepted_warehouse,
            "item_code":self.item_code,
            "qty":self.accepted_qty,
            "serial_no":self.serial,
            "batch_no":self.batch_number_new,
            # "batch_no":self.batch_number,
            "cost_center":cc
            })
            se.save(ignore_permissions=True)
            se.submit()
            
        if self.rejected_qty > 0:
            se = frappe.new_doc("Stock Entry")
            se.stock_entry_type = "Material Transfer"
            se.from_warehouse = self.warehouse
            se.company = self.company_name
            store_warehouse = frappe.get_value("Warehouse",{"company":self.company_name,"is_mrb":1})
            cc = frappe.get_value("Cost Center",{"company":self.company_name,"is_default":1})
            se.to_warehouse = store_warehouse
            se.append("items",{
                "s_warehouse":self.warehouse,
                "t_warehouse":store_warehouse,
                "item_code":self.item_code,
                "qty":self.rejected_qty,
                "cost_center":cc
            })
            se.save(ignore_permissions=True)
            se.submit()
            
            
        if self.rejected_qty > 0:
            new_doc = frappe.new_doc('MRB')  
            new_doc.purchase_receipt = self.pr_number
            new_doc.item_code = self.item_code
            new_doc.description = self.description
            new_doc.qty = self.rejected_qty
            new_doc.company = self.company_name
            store_warehouse = frappe.get_value("Warehouse",{"company":self.company_name,"is_mrb":1})
            new_doc.warehouse = store_warehouse
            new_doc.purchase_order = self. po_number
            new_doc.save(ignore_permissions=True)

            new_docu = frappe.new_doc('SCAR')  
            new_docu.purchase_receipt_number = self.pr_number
            new_docu.item_code = self.item_code
            new_docu.item_name = self.description
            new_docu.rejected_qty = self.rejected_qty
            new_doc.company = self.company_name
            # store_warehouse = frappe.get_value("Warehouse",{"company":self.company_name,"is_mrb":1})
            # new_doc.warehouse = store_warehouse
            new_docu.purchase_order_number = self. po_number
            new_docu.save(ignore_permissions=True)
    
            







