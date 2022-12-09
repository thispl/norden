# Copyright (c) 2022, Teampro and contributors
# For license information, please see license.txt

from itertools import count
from shutil import SpecialFileError
from tokenize import single_quoted
import frappe
from frappe.model.document import Document
from frappe.utils.background_jobs import enqueue
from frappe.utils.file_manager import get_file
import json

class MarginPriceTool(Document):
    @frappe.whitelist()
    def update_all_region(self):
        singapore_table = self.singapore
        enqueue_update_item_price_bulk(singapore_table,'Singapore')


        philippines_table = self.philippines
        enqueue_update_item_price_bulk(philippines_table,'Philippines')
        
        malaysia_table = self.malaysia
        enqueue_update_item_price_bulk(malaysia_table,'malaysia')
        
        indonesia_table = self.indonesia
        enqueue_update_item_price_bulk(indonesia_table,'indonesia')
        
        vietnam_table = self.vietnam
        enqueue_update_item_price_bulk(vietnam_table,'vietnam')

        combodia_table = self.combodia
        enqueue_update_item_price_bulk(combodia_table,'combodia')

        bangladesh_table = self.bangladesh
        enqueue_update_item_price_bulk(bangladesh_table,'bangladesh')

        srilanka_table = self.srilanka
        enqueue_update_item_price_bulk(srilanka_table,'srilanka')

        india_table = self.india
        enqueue_update_item_price_india_bulk(india_table)

        uk_table = self.uk
        enqueue_update_item_price_uk_bulk(uk_table)

        africa_table = self.africa
        enqueue_update_item_price_africa_bulk(africa_table)

        return 'Updated'

@frappe.whitelist()
def enqueue_update_item_price(table,country):
    enqueue(update_item_price, queue='default', timeout=6000, event='updating_margin_sales_price',at_front=True,table=table,country=country)

@frappe.whitelist()
def update_item_price(table,country):
    frappe.log_error(type(table))
    table = json.loads(table)
    for row in table:
        items = frappe.get_all('Item',{'item_sub_group':row["item_group"]})
        for i in items:
            factory_price = frappe.db.get_value('Item Price',{'price_list':'STANDARD BUYING-USD','item_code':i.name},'price_list_rate')
            if factory_price:
                if row["internal_cost"] and row["internal_cost"] > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':country + ' Internal Cost','item_code':i.name})
                    rate = factory_price * row["internal_cost"]
                    if not existing_ip:
                        price_list = country + " Internal Cost"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = rate
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()
                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',rate)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')

                if row["sales_price"] and row["sales_price"] > 0:
                    pps = rate/(100 - row["sales_price"])*100

                if row["freight"] and row["freight"] > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':country + ' Freight','item_code':i.name})
                    rate = pps * row["freight"]
                    # rate = rate + (rate*row["freight"])/100
                    if not existing_ip:
                        price_list = country + " Freight"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = rate
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()
                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',rate)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')

                existing_ip = frappe.db.exists('Item Price',{'price_list':country + ' Sales Price','item_code':i.name})
                # rate = rate + (rate*row["sales_price"])/100
                if not existing_ip:
                    price_list = country + " Sales Price"
                    doc = frappe.new_doc("Item Price")
                    doc.item_code = i.name
                    doc.price_list = price_list
                    doc.selling = 1
                    doc.buying = 1
                    doc.valid_from = '2022-01-01'
                    doc.price_list_rate = rate
                    doc.save(ignore_permissions=True)
                    frappe.db.commit()
                else:
                    frappe.db.set_value("Item Price",existing_ip,'price_list_rate',rate)
                    frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')

@frappe.whitelist()
def enqueue_update_item_price_bulk(table,country):
    enqueue(update_item_price_bulk, queue='default', timeout=6000, event='updating_margin_sales_price',table=table,country=country)

@frappe.whitelist()
def update_item_price_bulk(table,country):
    for row in table:
        items = frappe.get_all('Item',{'item_sub_group':row.item_group})
        for i in items:
            factory_price = frappe.db.get_value('Item Price',{'price_list':'STANDARD BUYING-USD','item_code':i.name},'price_list_rate')
            if factory_price:
                if row.internal_cost and row.internal_cost > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':country + ' Internal Cost','item_code':i.name})
                    rate = factory_price * row.internal_cost
                    if not existing_ip:
                        price_list = country + " Internal Cost"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = rate
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()
                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',rate)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')

                if row.sales_price and row.sales_price > 0:
                    pps = rate/(100 - row.sales_price)*100

                if row.freight and row.freight > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':country + ' Freight','item_code':i.name})
                    rate = pps * row.freight
                    # rate = rate + (rate*row["freight"])/100
                    if not existing_ip:
                        price_list = country + " Freight"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = rate
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()
                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',rate)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')

                existing_ip = frappe.db.exists('Item Price',{'price_list':country + ' Sales Price','item_code':i.name})
                # rate = rate + (rate*row["sales_price"])/100
                if not existing_ip:
                    price_list = country + " Sales Price"
                    doc = frappe.new_doc("Item Price")
                    doc.item_code = i.name
                    doc.price_list = price_list
                    doc.selling = 1
                    doc.buying = 1
                    doc.valid_from = '2022-01-01'
                    doc.price_list_rate = rate
                    doc.save(ignore_permissions=True)
                    frappe.db.commit()
                else:
                    frappe.db.set_value("Item Price",existing_ip,'price_list_rate',rate)
                    frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')

@frappe.whitelist()
def enqueue_update_item_price_uk(table):
    enqueue(update_item_price_uk, queue='default', timeout=6000, event='updating_margin_sales_price',table=table)

@frappe.whitelist()
def update_item_price_uk(table):
    table = json.loads(table)
    for row in table:
        items = frappe.get_all('Item',{'item_sub_group':row["item_group"]})
        for i in items:
            factory_price = frappe.db.get_value('Item Price',{'price_list':'STANDARD BUYING-USD','item_code':i.name},'price_list_rate')
            if factory_price:
                if row["freight"] and row["freight"] > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':'UK Freight Cost','item_code':i.name})
                    freight = factory_price * row["freight"]
                    if not existing_ip:
                        price_list = "UK Freight Cost"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = freight
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()
                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',freight)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')

                if row["destination_charges"] and row["destination_charges"] > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':'UK Destination Charges','item_code':i.name})
                    destination_charges = freight * row["destination_charges"]
                    if not existing_ip:
                        price_list = "UK Destination Charges"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = destination_charges
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()
                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',destination_charges)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')

                if row["installer"] and row["installer"] > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':'UK Installer Price','item_code':i.name})
                    installer = destination_charges/(100 - row["installer"])*100
                    if not existing_ip:
                        price_list = "UK Installer Price"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = installer
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()
                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',installer)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')
                
                if row["distributor"] and row["distributor"] > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':'UK Distributor Price','item_code':i.name})
                    distributor = destination_charges/(100 - row["distributor"])*100
                    if not existing_ip:
                        price_list = "UK Distributor Price"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = distributor
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()
                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',distributor)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')

@frappe.whitelist()
def enqueue_update_item_price_uk_bulk(table):
    enqueue(update_item_price_uk_bulk, queue='default', timeout=6000, event='updating_margin_sales_price',table=table)

@frappe.whitelist()
def update_item_price_uk_bulk(table):
    for row in table:
        items = frappe.get_all('Item',{'item_sub_group':row.item_group})
        for i in items:
            factory_price = frappe.db.get_value('Item Price',{'price_list':'STANDARD BUYING-USD','item_code':i.name},'price_list_rate')
            if factory_price:
                if row.freight and row.freight > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':'UK Freight Cost','item_code':i.name})
                    freight = factory_price * row.freight
                    if not existing_ip:
                        price_list = "UK Freight Cost"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = freight
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()
                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',freight)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')

                if row.destination_charges and row.destination_charges > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':'UK Destination Charges','item_code':i.name})
                    destination_charges = freight * row.destination_charges
                    if not existing_ip:
                        price_list = "UK Destination Charges"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = destination_charges
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()
                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',destination_charges)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')

                if row.installer and row.installer > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':'UK Installer Price','item_code':i.name})
                    installer = destination_charges/(100 - row.installer)*100
                    if not existing_ip:
                        price_list = "UK Installer Price"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = installer
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()
                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',installer)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')
                
                if row.distributor and row.distributor > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':'UK Distributor Price','item_code':i.name})
                    distributor = destination_charges/(100 - row.distributor)*100
                    if not existing_ip:
                        price_list = "UK Distributor Price"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = distributor
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()
                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',distributor)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')


                
                

@frappe.whitelist()
def enqueue_update_item_price_india(table):
    enqueue(update_item_price_india, queue='default', timeout=6000, event='updating_margin_sales_price',table=table)

@frappe.whitelist()
def update_item_price_india(table):
    table = json.loads(table)
    for row in table:
        items = frappe.get_all('Item',{'item_sub_group':row["item_group"]})
        for i in items:
            factory_price = frappe.db.get_value('Item Price',{'price_list':'STANDARD BUYING-USD','item_code':i.name},'price_list_rate')
            if factory_price:
                from erpnext.setup.utils import get_exchange_rate
                fp_conversion = get_exchange_rate("USD","INR")
                factory_price = fp_conversion * factory_price
                if row["landing"] and row["landing"] > 0:
                    landing = factory_price * row["landing"]
                    existing_ip = frappe.db.exists('Item Price',{'price_list': 'India Landing','item_code':i.name})
                    if not existing_ip:
                        price_list = "India Landing"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.currency = "INR"
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = landing
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()
                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',landing)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')
                        frappe.db.set_value("Item Price",existing_ip,'currency',"INR")
                        
                if row["spc"] and row["spc"] > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list': 'India SPC','item_code':i.name})
                    spc =  landing / row["spc"]
                    if not existing_ip:
                        price_list = "India SPC"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.currency = "INR"
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = spc
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()
                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',spc)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')
                        frappe.db.set_value("Item Price",existing_ip,'currency',"INR")

                if row["ltp"] and row["ltp"] > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list': 'India LTP','item_code':i.name})
                    ltp = spc / row["ltp"]
                    if not existing_ip:
                        price_list = "India LTP"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.currency = "INR"
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = ltp
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()
                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',ltp)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')
                        frappe.db.set_value("Item Price",existing_ip,'currency',"INR")

                if row["dtp"] and row["dtp"] > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list': 'India DTP','item_code':i.name})
                    dtp = ltp / row["dtp"]
                    if not existing_ip:
                        price_list = "India DTP"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.currency = "INR"
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = dtp
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()
                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',dtp)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')
                        frappe.db.set_value("Item Price",existing_ip,'currency',"INR")

                if row["stp"] and row["stp"] > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list': 'India STP','item_code':i.name})
                    stp = dtp / row["stp"]
                    if not existing_ip:
                        price_list = "India STP"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.currency = "INR"
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = stp
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()
                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',stp)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')
                        frappe.db.set_value("Item Price",existing_ip,'currency',"INR")

                if row["mop"] and row["mop"] > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list': 'India MOP','item_code':i.name})
                    mop = stp / row["mop"]
                    if not existing_ip:
                        price_list = "India MOP"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.currency = "INR"
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = mop
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()
                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',mop)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')
                        frappe.db.set_value("Item Price",existing_ip,'currency',"INR")

                if row["mrp"] and row["mrp"] > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list': 'India MRP','item_code':i.name})
                    mrp = mop / row["mrp"]
                    if not existing_ip:
                        price_list = "India MRP"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.currency = "INR"
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = mrp
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()
                    else:
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',mrp)
                        frappe.db.set_value("Item Price",existing_ip,'currency',"INR")


@frappe.whitelist()
def enqueue_update_item_price_india_bulk(table):
    enqueue(update_item_price_india_bulk, queue='default', timeout=6000, event='updating_margin_sales_price',table=table)

@frappe.whitelist()
def update_item_price_india_bulk(table):
    for row in table:
        items = frappe.get_all('Item',{'item_sub_group':row.item_group})
        for i in items:
            factory_price = frappe.db.get_value('Item Price',{'price_list':'STANDARD BUYING-USD','item_code':i.name},'price_list_rate')
            if factory_price:
                if row.landing and row.landing > 0:
                    landing = factory_price * row.landing
                    existing_ip = frappe.db.exists('Item Price',{'price_list': 'India Landing','item_code':i.name})
                    if not existing_ip:
                        price_list = "India Landing"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = landing
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()
                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',landing)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')
                        
                if row.spc and row.spc > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list': 'India SPC','item_code':i.name})
                    spc =  landing / row.spc
                    if not existing_ip:
                        price_list = "India SPC"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = spc
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()
                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',spc)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')

                if row.ltp and row.ltp > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list': 'India LTP','item_code':i.name})
                    ltp = spc / row.ltp
                    if not existing_ip:
                        price_list = "India LTP"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = ltp
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()
                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',ltp)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')

                if row["dtp"] and row["dtp"] > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list': 'India DTP','item_code':i.name})
                    dtp = ltp / row["dtp"]
                    if not existing_ip:
                        price_list = "India DTP"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = dtp
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()
                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',dtp)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')

                if row.stp and row.stp > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list': 'India STP','item_code':i.name})
                    stp = dtp / row.stp
                    if not existing_ip:
                        price_list = "India STP"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = stp
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()
                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',stp)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')

                if row.mop and row.mop > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list': 'India MOP','item_code':i.name})
                    mop = stp / row.mop
                    if not existing_ip:
                        price_list = "India MOP"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = mop
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()
                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',mop)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')

                if row.mrp and row.mrp > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list': 'India MRP','item_code':i.name})
                    mrp = mop / row.mrp
                    if not existing_ip:
                        price_list = "India MRP"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = mrp
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()
                    else:
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',mrp)



@frappe.whitelist()
def enqueue_update_item_price_africa(table):
    enqueue(update_item_price_africa, queue='default', timeout=6000, event='updating_margin_sales_price',table=table)

@frappe.whitelist()
def update_item_price_africa(table):
    table = json.loads(table)
    for row in table:
        items = frappe.get_all('Item',{'item_sub_group':row["item_group"]})
        for i in items:
            factory_price = frappe.db.get_value('Item Price',{'price_list':'STANDARD BUYING-USD','item_code':i.name},'price_list_rate')
            if factory_price:
                if row["landing"] and row["landing"] > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':'Africa Landing Cost','item_code':i.name})
                    rate = factory_price * row["landing"]
                    if not existing_ip:
                        price_list = "Africa Landing Cost"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = rate
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()

                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',rate)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')

                if row["margin"] and row["margin"] > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':'Africa Sales Price','item_code':i.name})
                    sales_price = rate * row["margin"]
                    if not existing_ip:
                        price_list = "Africa Sales Price"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = sales_price
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()

                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',sales_price)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')

                if row["dealer_price"] and row["dealer_price"] > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':'Africa Dealer Price','item_code':i.name})
                    dp = rate * row["dealer_price"]
                    if not existing_ip:
                        price_list = "Africa Dealer Price"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = dp
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()

                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',dp)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')

                if row["customer_price"] and row["customer_price"] > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':'Africa Customer Price','item_code':i.name})
                    cp = rate * row["customer_price"]
                    if not existing_ip:
                        price_list = "Africa Customer Price"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = cp
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()

                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',cp)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')


@frappe.whitelist()
def enqueue_update_item_price_africa_bulk(table):
    enqueue(enqueue_update_item_price_africa_bulk, queue='default', timeout=6000, event='updating_margin_sales_price',table=table)

@frappe.whitelist()
def update_item_price_africa_bulk(table):
    for row in table:
        items = frappe.get_all('Item',{'item_sub_group':row.item_group})
        for i in items:
            factory_price = frappe.db.get_value('Item Price',{'price_list':'STANDARD BUYING-USD','item_code':i.name},'price_list_rate')
            if factory_price:
                if row.landing and row.landing > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':'Africa Landing Cost','item_code':i.name})
                    rate = factory_price * row.landing
                    if not existing_ip:
                        price_list = "Africa Landing Cost"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = rate
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()

                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',rate)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')

                if row.margin and row.margin > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':'Africa Sales Price','item_code':i.name})
                    sales_price = rate * row.margin
                    if not existing_ip:
                        price_list = "Africa Sales Price"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = sales_price
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()

                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',sales_price)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')

                if row["dealer_price"] and row["dealer_price"] > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':'Africa Dealer Price','item_code':i.name})
                    dp = sales_price * row["dealer_price"]
                    if not existing_ip:
                        price_list = "Africa Dealer Price"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = dp
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()

                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',dp)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')

                if row["customer_price"] and row["customer_price"] > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':'Africa Customer Price','item_code':i.name})
                    cp = dp * row["customer_price"]
                    if not existing_ip:
                        price_list = "Africa Customer Price"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = cp
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()

                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',cp)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')



@frappe.whitelist()
def enqueue_update_item_price_dubai(table):
    enqueue(update_item_price_dubai, queue='default', timeout=6000, event='updating_margin_sales_price',table=table)

@frappe.whitelist()
def update_item_price_dubai(table):
    table = json.loads(table)
    for row in table:
        items = frappe.get_all('Item',{'item_sub_group':row["item_group"]})
        for i in items:
            factory_price = frappe.db.get_value('Item Price',{'price_list':'STANDARD BUYING-USD','item_code':i.name},'price_list_rate')
            if factory_price:
                from erpnext.setup.utils import get_exchange_rate
                fp_conversion = get_exchange_rate("USD","AED")
                if row["landing"] and row["landing"] > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':'Dubai Landing Cost','item_code':i.name})
                    rate = factory_price * row["landing"]
                    if not existing_ip:
                        price_list = "Dubai Landing Cost"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = rate
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()

                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',rate)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')

                if row["incentive"] and row["incentive"] > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':'Dubai Incentive','item_code':i.name})
                    incentive = rate * row["incentive"]
                    if not existing_ip:
                        price_list = "Dubai Incentive"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = incentive
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()

                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',incentive)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')

                if row["internal"] and row["internal"] > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':'Dubai Internal Cost','item_code':i.name})
                    internal = rate * row["incentive"]
                    if not existing_ip:
                        price_list = "Dubai Internal Cost"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = internal
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()

                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',internal)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')

                if row["distributor"] and row["distributor"] > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':'Dubai Distributor Price','item_code':i.name})
                    distributor = rate * row["distributor"]
                    if not existing_ip:
                        price_list = "Dubai Distributor Price"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = distributor
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()

                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',distributor)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')

                if row["saudi"] and row["saudi"] > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':'Saudi dist','item_code':i.name})
                    saudi = rate * row["saudi"]
                    if not existing_ip:
                        price_list = "Saudi dist"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = saudi
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()

                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',saudi)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')

                if row["project"] and row["project"] > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':'Dubai Project','item_code':i.name})
                    project = rate * row["project"]
                    if not existing_ip:
                        price_list = "Dubai Project"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = Project
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()

                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',project)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')

                if row["retail"] and row["retail"] > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':'Dubai Retail','item_code':i.name})
                    retail = rate * row["retail"]
                    if not existing_ip:
                        price_list = "Dubai Retail"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = retail
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()

                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',retail)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')

                if row["electra"] and row["electra"] > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':'Electra Dubai','item_code':i.name})
                    electra = factory_price * row["electra"]
                    if not existing_ip:
                        price_list = "Electra Dubai"
                        doc = frappe.new_doc("Item Price")
                        doc.item_code = i.name
                        doc.price_list = price_list
                        doc.selling = 1
                        doc.buying = 1
                        doc.valid_from = '2022-01-01'
                        doc.price_list_rate = electra
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()

                    else:
                        frappe.db.set_value("Item Price",existing_ip,'price_list_rate',electra)
                        frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')


    


