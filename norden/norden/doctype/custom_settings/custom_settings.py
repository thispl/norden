# Copyright (c) 2024, Teampro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CustomSettings(Document):
	pass



@frappe.whitelist()
def cost_rate_update(item_code):
    item_group = frappe.db.get_value("Item",item_code,'item_sub_group')
    stock = frappe.db.sql("""select (sum(b.stock_value)/sum(b.actual_qty)) as val_rate from `tabBin` b 
                join `tabWarehouse` wh on wh.name = b.warehouse
                join `tabCompany` c on c.name = wh.company
                where wh.company = '%s' and b.item_code = '%s'
                """ % ("Norden Communication Middle East FZE",item_code),as_dict=True)[0]

    stock_val  = 0
    if stock['val_rate'] and float(stock['val_rate']) > 0:
        stock_val = float(stock['val_rate'])
    if stock_val > 0:
        mp = frappe.get_doc("Margin Price Tool","Margin Price Tool")
        for row in mp.dubai:
            
            if item_group == row.item_group:
                existing_ip = frappe.db.exists('Item Price',{'price_list':'Cost Rate - NCMEF','item_code':item_code})
                if not existing_ip:
                    doc = frappe.new_doc("Item Price")
                else:
                    doc = frappe.get_doc("Item Price",existing_ip)
                price_list = "Cost Rate - NCMEF"
                doc.item_code = item_code
                doc.price_list = price_list
                doc.selling = 1
                doc.buying = 1
                doc.valid_from = '2022-01-01'
                doc.price_list_rate = stock_val
                doc.save(ignore_permissions=True)
                frappe.db.commit()

                if row.landing and row.landing > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':'Landing - NCMEF','item_code':item_code})
                    rate = stock_val * row.landing
                    if not existing_ip:
                        doc = frappe.new_doc("Item Price")
                    else:
                        doc = frappe.get_doc("Item Price",existing_ip)
                    price_list = "Landing - NCMEF"
                    doc.item_code = item_code
                    doc.price_list = price_list
                    doc.selling = 1
                    doc.buying = 1
                    doc.valid_from = '2022-01-01'
                    doc.price_list_rate = rate
                    doc.save(ignore_permissions=True)
                    frappe.db.commit()


                if row.incentive and row.incentive > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':'Incentive - NCMEF','item_code':item_code})
                    incentive = rate * row.incentive
                    if not existing_ip:
                        doc = frappe.new_doc("Item Price")
                    else:
                        doc = frappe.get_doc("Item Price",existing_ip)
                    price_list = "Incentive - NCMEF"
                    doc.item_code = item_code
                    doc.price_list = price_list
                    doc.selling = 1
                    doc.buying = 1
                    doc.valid_from = '2022-01-01'
                    doc.price_list_rate = incentive
                    doc.save(ignore_permissions=True)
                    frappe.db.commit()
                
                if row.electra and row.electra > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':'Electra Qatar - NCMEF','item_code':item_code})
                    electra = stock_val * row.electra
                    if not existing_ip:
                        doc = frappe.new_doc("Item Price")
                    else:
                        doc = frappe.get_doc("Item Price",existing_ip)
                    price_list = "Electra Qatar - NCMEF"
                    doc.item_code = item_code
                    doc.price_list = price_list
                    doc.selling = 1
                    doc.buying = 1
                    doc.valid_from = '2022-01-01'
                    doc.price_list_rate = electra
                    doc.save(ignore_permissions=True)
                    frappe.db.commit()




from frappe.utils.background_jobs import enqueue
@frappe.whitelist()
def cost_rate_update_all_item():
    enqueue(cost_rate_update_all, queue='default', timeout=6000, event='updating_cost_rate',at_front=True)


@frappe.whitelist()
def cost_rate_update_all():
    item_list = frappe.db.sql(""" select item_code from `tabItem` where disabled = 0 """,as_dict=1)
    for it in item_list:
        if it.item_code == "212-03023050":
            item_group = frappe.db.get_value("Item",it.item_code,'item_sub_group')
            stock = frappe.db.sql("""select (sum(b.stock_value)/sum(b.actual_qty)) as val_rate from `tabBin` b 
                        join `tabWarehouse` wh on wh.name = b.warehouse
                        join `tabCompany` c on c.name = wh.company
                        where wh.company = '%s' and b.item_code = '%s'
                        """ % ("Norden Communication Middle East FZE",it.item_code),as_dict=True)[0]
            stock_val  = 0
            if stock['val_rate'] and float(stock['val_rate']) > 0:
                stock_val = float(stock['val_rate'])
            if stock_val > 0:
                mp = frappe.get_doc("Margin Price Tool","Margin Price Tool")
                for row in mp.dubai:
                    if item_group == row.item_group:
                        existing_ip = frappe.db.exists('Item Price',{'price_list':'Cost Rate - NCMEF','item_code':it.item_code})
                        if not existing_ip:
                            doc = frappe.new_doc("Item Price")
                        else:
                            doc = frappe.get_doc("Item Price",existing_ip)
                        price_list = "Cost Rate - NCMEF"
                        doc.item_code = it.item_code
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = stock_val
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()

                        if row.landing and row.landing > 0:
                            existing_ip = frappe.db.exists('Item Price',{'price_list':'Landing - NCMEF','item_code':it.item_code})
                            rate = stock_val * row.landing
                            if not existing_ip:
                                doc = frappe.new_doc("Item Price")
                            else:
                                doc = frappe.get_doc("Item Price",existing_ip)
                            price_list = "Landing - NCMEF"
                            doc.item_code = it.item_code
                            doc.price_list = price_list
                            doc.selling = 1
                            doc.buying = 1
                            doc.valid_from = '2022-01-01'
                            doc.price_list_rate = rate
                            doc.save(ignore_permissions=True)
                            frappe.db.commit()


                        if row.incentive and row.incentive > 0:
                            existing_ip = frappe.db.exists('Item Price',{'price_list':'Incentive - NCMEF','item_code':it.item_code})
                            incentive = rate * row.incentive
                            if not existing_ip:
                                doc = frappe.new_doc("Item Price")
                            else:
                                doc = frappe.get_doc("Item Price",existing_ip)
                            price_list = "Incentive - NCMEF"
                            doc.item_code = it.item_code
                            doc.price_list = price_list
                            doc.selling = 1
                            doc.buying = 1
                            doc.valid_from = '2022-01-01'
                            doc.price_list_rate = incentive
                            doc.save(ignore_permissions=True)
                            frappe.db.commit()
                        
                        if row.electra and row.electra > 0:
                            existing_ip = frappe.db.exists('Item Price',{'price_list':'Electra Qatar - NCMEF','item_code':it.item_code})
                            electra = stock_val * row.electra
                            if not existing_ip:
                                doc = frappe.new_doc("Item Price")
                            else:
                                doc = frappe.get_doc("Item Price",existing_ip)
                            price_list = "Electra Qatar - NCMEF"
                            doc.item_code = it.item_code
                            doc.price_list = price_list
                            doc.selling = 1
                            doc.buying = 1
                            doc.valid_from = '2022-01-01'
                            doc.price_list_rate = electra
                            doc.save(ignore_permissions=True)
                            frappe.db.commit()
