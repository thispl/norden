from curses import is_term_resized
import email
import frappe
import requests
from frappe.utils.data import format_date, today 
from frappe import _
import json
from frappe.utils.background_jobs import enqueue
from norden.custom import employee
from frappe.utils import flt
from dateutil import relativedelta
from datetime import date, datetime
from frappe.utils.csvutils import read_csv_content
from frappe.utils.file_manager import get_file
from erpnext.setup.utils import get_exchange_rate
from frappe.utils import (
    add_days,
    add_months,
    add_years,
    cint,
    cstr,
    date_diff,
    flt,
    formatdate,
    get_last_day,
    get_timestamp,
    getdate,
    nowdate,
)
import openpyxl
from openpyxl import Workbook
import openpyxl
import xlrd
import re
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import GradientFill, PatternFill
from six import BytesIO, string_types
from datetime import datetime, date, timedelta



@frappe.whitelist()
def update_company_currency(account_currency,company_currency):
    return get_exchange_rate(account_currency,company_currency)

@frappe.whitelist()
def update_unit_price_document_currency():
    qi = frappe.db.sql("""select unit_price,unit_price_document_currency from `tabQuotation Item`  """)
    print(qi)
    
# @frappe.whitelist()
# def getstock_detail(item_details,company):
# 	item_details = json.loads(item_details)
# 	frappe.errprint(item_details)
# 	data = ''
# 	data += '<h4><center><b>STOCK DETAILS</b></center></h4>'
# 	data += '</table>'
# 	for j in item_details:
# 		country = frappe.get_value("Company",{"name":company},["country"])

# 		warehouse_stock = frappe.db.sql("""
# 		select sum(b.actual_qty) as qty from `tabBin` b join `tabWarehouse` wh on wh.name = b.warehouse join `tabCompany` c on c.name = wh.company where c.country = '%s' and b.item_code = '%s'
# 		""" % (country,j["item_code"]),as_dict=True)[0]

# 		if not warehouse_stock["qty"]:
# 			warehouse_stock["qty"] = 0
# 		purchase_order = frappe.db.sql("""select sum(`tabPurchase Order Item`.qty) as qty from `tabPurchase Order`
# 				left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
# 				where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 """%(j["item_code"]),as_dict=True)[0] or 0 
# 		if not purchase_order["qty"]:
# 			purchase_order["qty"] = 0
# 		purchase_receipt = frappe.db.sql("""select sum(`tabPurchase Receipt Item`.qty) as qty from `tabPurchase Receipt`
# 				left join `tabPurchase Receipt Item` on `tabPurchase Receipt`.name = `tabPurchase Receipt Item`.parent
# 				where `tabPurchase Receipt Item`.item_code = '%s' and `tabPurchase Receipt`.docstatus = 1 """%(j["item_code"]),as_dict=True)[0] or 0 
# 		if not purchase_receipt["qty"]:
# 			purchase_receipt["qty"] = 0
# 		in_transit = purchase_order["qty"] - purchase_receipt["qty"]
# 		total = warehouse_stock["qty"] + in_transit

# 		stocks = frappe.db.sql("""select actual_qty,warehouse,stock_uom,stock_value from tabBin
# 		where item_code = '%s' """%(j["item_code"]),as_dict=True)

# 		pos = frappe.db.sql("""select `tabPurchase Order Item`.item_code as item_code,`tabPurchase Order Item`.item_name as item_name,`tabPurchase Order`.supplier as supplier,sum(`tabPurchase Order Item`.qty) as qty,`tabPurchase Order Item`.rate as rate,`tabPurchase Order`.transaction_date as date,`tabPurchase Order`.name as po from `tabPurchase Order`
# 		left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
# 		where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 order by rate asc limit 1""" % (j["item_code"]), as_dict=True)
    
# 		sale = frappe.db.sql("""select `tabSales Order Item`.item_code as item_code,`tabSales Order Item`.item_name as item_name,sum(`tabSales Order Item`.qty) as qty,`tabSales Order Item`.rate as rate,`tabSales Order`.name as so from `tabSales Order`
# 		left join `tabSales Order Item` on `tabSales Order`.name = `tabSales Order Item`.parent
# 		where `tabSales Order Item`.item_code = '%s' and `tabSales Order`.docstatus = 0 order by rate asc limit 1""" % (j["item_code"]), as_dict=True)
        
# 		i = 0
# 		for po in pos:
# 			for so in sale:
                
# 				if pos:
# 					frappe.errprint(po.qty)
# 					data += '<table class="table table-bordered">'
# 					data += '<tr>'
# 					data += '<td colspan=1 style="width:13%;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>ITEM CODE</b><center></td>'
# 					data += '<td colspan=1 style="width:33%;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>ITEM NAME</b><center></td>'
# 					data += '<td colspan=1 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>STOCK</b><center></td>'

# 					for stock in stocks:
# 						if stock.actual_qty > 0:
# 							wh = stock.warehouse
# 							x = wh.split('- ')
# 							data += '<td colspan=1 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>%s</b><center></td>'%(x[-1])
# 					data += '<td colspan=1 style="padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>PENDING TO RECEIVE</b><center></td>'
# 					# data += '<td colspan=1 style="padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>AGAINST PO</b><center></td>'
# 					data += '<td colspan=1 style="padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>PENDING TO SELL</b><center></td>'
# 					data += '</tr>'
                    
                    
                    
# 					data +='<tr>'
# 					data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>'%(j["item_code"])
# 					data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>'%(j["item_name"])
# 					data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>'%(warehouse_stock['qty'] or 0)
# 					for stock in stocks:
# 						if stock.actual_qty > 0:
# 							data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>'%(stock.actual_qty)
# 					data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>'%(in_transit or 0)
# 					# data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>'%(po.qty or 0)
# 					data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>'%(so.qty or 0)
# 					data += '</tr>'
# 				i += 1
# 			data += '</table>'
            
# 		#     data+='<tr><td colspan=1 style="border: 1px solid black;font-size:12px;"><center>%s<center><center></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><center>%s<center><center></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><center>%s<center><center></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><center>%s</center></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><center>%s</center></td></tr>'%(j["item_code"],j["item_name"],warehouse_stock["qty"], in_transit,total)
        
# 		# data += '</table>'
# 	return data

@frappe.whitelist()
def getstock_detail(item_details, company):
    item_details = json.loads(item_details)
    
    data = ''
    data += '<h4><center><b>STOCK DETAILS</b></center></h4>'
    data += '<table class="table table-bordered">'
    data += '<tr>'
    data += '<td colspan=1 style="width:13%;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>ITEM CODE</b></center></td>'
    data += '<td colspan=1 style="width:33%;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>ITEM NAME</b></center></td>'
    data += '<td colspan=1 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>STOCK</b></center></td>'
    data += '<td colspan=1 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>NSPL</b></center></td>'
    data += '<td colspan=1 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>NCME</b></center></td>'
    data += '<td colspan=1 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>NCUL</b></center></td>'
    data += '<td colspan=1 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>SNTL</b></center></td>'
    data += '<td colspan=1 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>NCPL</b></center></td>'
    data += '<td colspan=1 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>NRIC</b></center></td>'
    # data += '<td colspan=1 style="padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>IN TRANSIT</b></center></td>'
    # data += '<td colspan=1 style="padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>PENDING TO SELL</b></center></td>'
    warehouses = []  # Create a list to store warehouse names

    for j in item_details:
        country = frappe.get_value("Company", {"name": company}, ["country"])
        warehouse_stock = frappe.db.sql("""
            SELECT SUM(b.actual_qty - b.reserved_stock) AS qty
            FROM `tabBin` AS b
            JOIN `tabWarehouse` AS wh ON wh.name = b.warehouse
            JOIN `tabCompany` AS c ON c.name = wh.company
            WHERE c.country = %s AND b.item_code = %s and wh.custom_stock_is_shown_only_in_product_search = 0
        """, (country, j["item_code"]), as_dict=True)[0]
        # warehouse_stock = frappe.db.sql("""
        # select (sum(`tabBin`.actual_qty) - sum(b.reserved_stock)) as qty from `tabBin` b join `tabWarehouse` wh on wh.name = b.warehouse join `tabCompany` c on c.name = wh.company where c.country = '%s' and b.item_code = '%s'
        # """ % (country, j["item_code"]), as_dict=True)[0]

        if not warehouse_stock["qty"]:
            warehouse_stock["qty"] = 0
        purchase_order = frappe.db.sql("""select sum(`tabPurchase Order Item`.qty) as qty from `tabPurchase Order`
                left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
                where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 """ % (
            j["item_code"]), as_dict=True)[0] or 0
        if not purchase_order["qty"]:
            purchase_order["qty"] = 0
        purchase_receipt = frappe.db.sql("""select sum(`tabPurchase Receipt Item`.qty) as qty from `tabPurchase Receipt`
                left join `tabPurchase Receipt Item` on `tabPurchase Receipt`.name = `tabPurchase Receipt Item`.parent
                where `tabPurchase Receipt Item`.item_code = '%s' and `tabPurchase Receipt`.docstatus = 1 """ % (
            j["item_code"]), as_dict=True)[0] or 0
        if not purchase_receipt["qty"]:
            purchase_receipt["qty"] = 0
        in_transit = purchase_order["qty"] - purchase_receipt["qty"]
        total = warehouse_stock["qty"] + in_transit

        

        stocks = frappe.db.sql("""select (sum(`tabBin`.actual_qty) - sum(reserved_stock)) as actual_qty,warehouse,stock_uom,stock_value from tabBin
        where item_code = '%s' """ % (j["item_code"]), as_dict=True)

        pos = frappe.db.sql("""select `tabPurchase Order Item`.item_code as item_code,`tabPurchase Order Item`.item_name as item_name,`tabPurchase Order`.supplier as supplier,sum(`tabPurchase Order Item`.qty) as qty,`tabPurchase Order Item`.rate as rate,`tabPurchase Order`.name as po from `tabPurchase Order`
                left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
                where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 order by rate asc limit 1""" % (
            j["item_code"]), as_dict=True)

        sale = frappe.db.sql("""select `tabSales Order Item`.item_code as item_code,`tabSales Order Item`.item_name as item_name,sum(`tabSales Order Item`.qty) as qty,`tabSales Order Item`.rate as rate,`tabSales Order`.name as so from `tabSales Order`
                left join `tabSales Order Item` on `tabSales Order`.name = `tabSales Order Item`.parent
                where `tabSales Order Item`.item_code = '%s' and `tabSales Order`.docstatus = 0 order by rate asc limit 1""" % (
            j["item_code"]), as_dict=True)

        for po in pos:
            for so in sale:
                data += '<tr>'
                data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' % (j["item_code"])
                data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' % (j["item_name"])
                data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' % (warehouse_stock['qty'] or 0)
                
                compa = ["Norden Singapore PTE LTD","Norden Communication Middle East FZE","Norden Communication UK Limited","Sparcom Ningbo Telecom Ltd","Norden Communication Pvt Ltd","Norden Research and Innovation Centre (OPC) Pvt. Ltd"]

                for co in compa:
                    st = 0
                    ware = frappe.db.get_list("Warehouse",{"company":co,"custom_stock_is_shown_only_in_product_search":0},['name'])
                    for w in ware:
                        sto = frappe.db.get_value("Bin",{"item_code":j["item_code"],"warehouse":w.name},['actual_qty'])
                        if not sto:
                            sto = 0
                        st += sto
                    data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' %(st)
                # data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' 
                # data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>'
                # data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>'
                # data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>'
                # data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>'

                # for stock in stocks:
                # 	wh = stock.warehouse
                # 	x = wh.split('- ')
                # 	warehouse_name = x[-1]
                # 	if warehouse_name not in warehouses:
                # 		warehouses.append(warehouse_name)  # Add warehouse name to the list
                # 	data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' % (stock.actual_qty)
                    

                # data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' % (in_transit or 0)
                # data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' % (so.qty or 0)
                data += '</tr>'

    data += '<tr>'
    
    data += '</table>'
    return data

@frappe.whitelist()
def getstock_detail_list(name):
    company = frappe.db.get_value("Sales Order",{'name':name},['company'])
    item_details = frappe.get_all("Sales Order Item",{'parent':name},['item_code','item_name','qty','rate'])
    data = ''
    data += '<h4><center><b>STOCK DETAILS</b></center></h4>'
    data += '<table class="table table-bordered">'
    data += '<tr>'
    data += '<td colspan=1 style="width:13%;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>ITEM CODE</b></center></td>'
    data += '<td colspan=1 style="width:33%;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>ITEM NAME</b></center></td>'
    data += '<td colspan=1 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>STOCK</b></center></td>'
    data += '<td colspan=1 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>NSPL</b></center></td>'
    data += '<td colspan=1 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>NCME</b></center></td>'
    data += '<td colspan=1 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>NCUL</b></center></td>'
    data += '<td colspan=1 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>SNTL</b></center></td>'
    data += '<td colspan=1 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>NCPL</b></center></td>'
    data += '<td colspan=1 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>NRIC</b></center></td>'
    # data += '<td colspan=1 style="padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>IN TRANSIT</b></center></td>'
    # data += '<td colspan=1 style="padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>PENDING TO SELL</b></center></td>'
    warehouses = []  # Create a list to store warehouse names

    for j in item_details:
        country = frappe.get_value("Company", {"name": company}, ["country"])
        warehouse_stock = frappe.db.sql("""
        select (sum(`tabBin`.actual_qty) - sum(b.reserved_stock)) as qty from `tabBin` b join `tabWarehouse` wh on wh.name = b.warehouse join `tabCompany` c on c.name = wh.company where c.country = '%s' and b.item_code = '%s'
        """ % (country, j["item_code"]), as_dict=True)[0]

        if not warehouse_stock["qty"]:
            warehouse_stock["qty"] = 0
        purchase_order = frappe.db.sql("""select sum(`tabPurchase Order Item`.qty) as qty from `tabPurchase Order`
                left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
                where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 """ % (
            j["item_code"]), as_dict=True)[0] or 0
        if not purchase_order["qty"]:
            purchase_order["qty"] = 0
        purchase_receipt = frappe.db.sql("""select sum(`tabPurchase Receipt Item`.qty) as qty from `tabPurchase Receipt`
                left join `tabPurchase Receipt Item` on `tabPurchase Receipt`.name = `tabPurchase Receipt Item`.parent
                where `tabPurchase Receipt Item`.item_code = '%s' and `tabPurchase Receipt`.docstatus = 1 """ % (
            j["item_code"]), as_dict=True)[0] or 0
        if not purchase_receipt["qty"]:
            purchase_receipt["qty"] = 0
        in_transit = purchase_order["qty"] - purchase_receipt["qty"]
        total = warehouse_stock["qty"] + in_transit

        

        stocks = frappe.db.sql("""select actual_qty,warehouse,stock_uom,stock_value from tabBin
        where item_code = '%s' """ % (j["item_code"]), as_dict=True)

        pos = frappe.db.sql("""select `tabPurchase Order Item`.item_code as item_code,`tabPurchase Order Item`.item_name as item_name,`tabPurchase Order`.supplier as supplier,sum(`tabPurchase Order Item`.qty) as qty,`tabPurchase Order Item`.rate as rate,`tabPurchase Order`.name as po from `tabPurchase Order`
                left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
                where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 order by rate asc limit 1""" % (
            j["item_code"]), as_dict=True)

        sale = frappe.db.sql("""select `tabSales Order Item`.item_code as item_code,`tabSales Order Item`.item_name as item_name,sum(`tabSales Order Item`.qty) as qty,`tabSales Order Item`.rate as rate,`tabSales Order`.name as so from `tabSales Order`
                left join `tabSales Order Item` on `tabSales Order`.name = `tabSales Order Item`.parent
                where `tabSales Order Item`.item_code = '%s' and `tabSales Order`.docstatus = 0 order by rate asc limit 1""" % (
            j["item_code"]), as_dict=True)

        for po in pos:
            for so in sale:
                data += '<tr>'
                data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' % (j["item_code"])
                data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' % (j["item_name"])
                data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' % (warehouse_stock['qty'] or 0)
                
                compa = ["Norden Singapore PTE LTD","Norden Communication Middle East FZE","Norden Communication UK Limited","Sparcom Ningbo Telecom Ltd","Norden Communication Pvt Ltd","Norden Research and Innovation Centre (OPC) Pvt. Ltd"]

                for co in compa:
                    st = 0
                    ware = frappe.db.get_list("Warehouse",{"company":co},['name'])
                    for w in ware:
                        sto = frappe.db.get_value("Bin",{"item_code":j["item_code"],"warehouse":w.name},['actual_qty'])
                        if not sto:
                            sto = 0
                        st += sto
                    data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' %(st)
                # data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' 
                # data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>'
                # data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>'
                # data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>'
                # data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>'

                # for stock in stocks:
                # 	wh = stock.warehouse
                # 	x = wh.split('- ')
                # 	warehouse_name = x[-1]
                # 	if warehouse_name not in warehouses:
                # 		warehouses.append(warehouse_name)  # Add warehouse name to the list
                # 	data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' % (stock.actual_qty)
                    

                # data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' % (in_transit or 0)
                # data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' % (so.qty or 0)
                data += '</tr>'

    data += '<tr>'
    
    data += '</table>'
    return data


@frappe.whitelist()
def item_default_wh(doc,method):
    item_group = frappe.get_value('Item',doc.item_code,'item_group')
    general_services = ['General Service','Service','Office Stationary','Assets','Stationary']
    if item_group not in general_services:
        item_default_set = frappe.get_value('Item',doc.item_code,'item_default_set')
        if not item_default_set:
            companies = [
            {
                "company": "Norden Communication Pvt Ltd",
                "buying_cost_center": "Main - NCPL",
                "selling_cost_center": "Main - NCPL",
                "expense_account": "Cost of Goods Sold - NCPL",
                "income_account": "Sales - NCPL"
            },
            {
                "company": "Norden Communication Middle East FZE",
                "buying_cost_center": "Main - NCME",
                "selling_cost_center": "Main - NCME",
                "expense_account": "Cost of Goods Sold - NCME",
                "income_account": "Sales - NCME"
            },
            {
                "company": "Norden research and Innovation Centre  Pvt. Ltd",
                "buying_cost_center": "Main - NRIC",
                "selling_cost_center": "Main - NRIC",
                "expense_account": "Cost of Goods Sold - NRIC",
                "income_account": "Sales - NRIC"
            },
            {
                "company": "Norden Communication UK Limited",
                "buying_cost_center": "Main - NCUL",
                "selling_cost_center": "Main - NCUL",
                "expense_account": "Cost of Goods Sold - NCUL",
                "income_account": "Sales - NCUL"
            },
            {
                "company": "Sparcom Ningbo Telecom Ltd",
                "buying_cost_center": "Main - SNTL",
                "selling_cost_center": "Main - SNTL",
                "expense_account": "Cost of Goods Sold - SNTL",
                "income_account": "Sales - SNTL"
            },
            {
                "company": "Norden Singapore PTE LTD",
                "buying_cost_center": "Main - NSPL",
                "selling_cost_center": "Main - NSPL",
                "expense_account": "Cost of Goods Sold - NSPL",
                "income_account": "Sales - NSPL"
            },
            {
                "company": "Norden Communication India",
                "buying_cost_center": "Corporate - NC",
                "selling_cost_center": "Corporate - NC",
                "expense_account": "Cost of Goods Sold - NC",
                "income_account": "Sales - NC"
            }
                        ]
            for company in companies:
                item_default = frappe.db.exists('Item Default',{'parent':doc.item_code,'company':company['company']},'parent')
                if not item_default:
                    itemid = frappe.get_doc("Item",doc.item_code)
                    itemid.item_default_set = 1
                    itemid.append('item_defaults',{
                        'company':company['company'],
                        'buying_cost_center':company['buying_cost_center'],
                        'selling_cost_center':company['selling_cost_center'],
                        'expense_account':company['expense_account'],
                        'income_account':company['income_account'],
                    })
                    itemid.save(ignore_permissions=True)
                else:
                    itemid = frappe.get_doc("Item",doc.item_code)
                    frappe.db.set_value('Item Default',{'parent':itemid.name,'company':company['company']},'buying_cost_center',company['buying_cost_center'])
                    frappe.db.set_value('Item Default',{'parent':itemid.name,'company':company['company']},'selling_cost_center',company['selling_cost_center'])
                    frappe.db.set_value('Item Default',{'parent':itemid.name,'company':company['company']},'expense_account',company['expense_account'])
                    frappe.db.set_value('Item Default',{'parent':itemid.name,'company':company['company']},'income_account',company['income_account'])
            frappe.db.set_value('Item',doc.item_code,"item_default_set",1)


@frappe.whitelist()
def get_series(date,company,doctype):
    company_series = frappe.db.get_value("Company Series",{'company':company,'document_type':doctype,'with_tax':0},'series')
    return company_series

@frappe.whitelist()
def get_series_with_tax(date,company,doctype):
    company_series = frappe.db.get_value("Company Series",{'company':company,'document_type':doctype,'with_tax':1},'series')
    return company_series



# @frappe.whitelist()
# def get_series(date,company,doctype):
# 	company_series = frappe.db.get_value("Company Series",{'company':company,'document_type':doctype,'with_tax':0},'series')
# 	updated_series = company_series
# 	fy_info = frappe.db.sql(""" SELECT year, year_start_date, year_end_date FROM `tabFiscal Year` LEFT JOIN `tabFiscal Year Company` ON `tabFiscal Year`.name = `tabFiscal Year Company`.parent WHERE `tabFiscal Year`.custom_active_fy = 1 AND `tabFiscal Year Company`.company = %s """, (company), as_dict=True)
# 	if fy_info and doctype != "File Number": 
# 		if len(fy_info[0]['year']) == 4:
# 			fy_year = fy_info[0]['year']
# 			previous_year = int(fy_year)-1
# 			fy_start_date = datetime.strptime(str(fy_info[0]['year_start_date']), '%Y-%m-%d').date()
# 			fy_end_date = datetime.strptime(str(fy_info[0]['year_end_date']), '%Y-%m-%d').date()
# 			date_obj = datetime.strptime(date, '%Y-%m-%d').date()        
# 			if fy_start_date <= date_obj <= fy_end_date:
# 				updated_series = company_series
# 			else:
# 				if "YYYY" in company_series:
# 					updated_series = company_series.replace("YYYY", str(previous_year))
# 		else:
# 			fy_year = fy_info[0]['year']
# 			fyear = fy_year[0:4]
# 			f_year = str(fy_year[2:4]) + str(fy_year[-2:])
# 			prev_year = str(int(fy_year[2:4]) - 1) + str(int(fy_year[-2:]) -1)
# 			previous_year = int(fyear)-1
# 			fy_start_date = datetime.strptime(str(fy_info[0]['year_start_date']), '%Y-%m-%d').date()
# 			fy_end_date = datetime.strptime(str(fy_info[0]['year_end_date']), '%Y-%m-%d').date()
# 			date_obj = datetime.strptime(date, '%Y-%m-%d').date()        
# 			if fy_start_date <= date_obj <= fy_end_date:
# 				updated_series = company_series
# 			else:
# 				if fyear in company_series:
# 					updated_series = company_series.replace(fyear, str(previous_year))
# 				elif f_year in company_series and doctype == "Sales Invoice":
# 					updated_series = company_series.replace(f_year, str(prev_year))
# 	return updated_series

# @frappe.whitelist()
# def get_series_with_tax(date,company,doctype):
# 	company_series = frappe.db.get_value("Company Series",{'company':company,'document_type':doctype,'with_tax':1},'series')
# 	updated_series = company_series
# 	fy_info = frappe.db.sql(""" SELECT year, year_start_date, year_end_date FROM `tabFiscal Year` LEFT JOIN `tabFiscal Year Company` ON `tabFiscal Year`.name = `tabFiscal Year Company`.parent WHERE `tabFiscal Year`.custom_active_fy = 1 AND `tabFiscal Year Company`.company = %s """, (company), as_dict=True)
# 	if fy_info and doctype != "File Number": 
# 		if len(fy_info[0]['year']) == 4:
# 			fy_year = fy_info[0]['year']
# 			previous_year = int(fy_year)-1
# 			fy_start_date = datetime.strptime(str(fy_info[0]['year_start_date']), '%Y-%m-%d').date()
# 			fy_end_date = datetime.strptime(str(fy_info[0]['year_end_date']), '%Y-%m-%d').date()
# 			date_obj = datetime.strptime(date, '%Y-%m-%d').date()        
# 			if fy_start_date <= date_obj <= fy_end_date:
# 				updated_series = company_series
# 			else:
# 				if "YYYY" in company_series:
# 					updated_series = company_series.replace("YYYY", str(previous_year))
# 		else:
# 			fy_year = fy_info[0]['year']
# 			fyear = fy_year[0:4]
# 			f_year = str(fy_year[2:4]) + str(fy_year[-2:])
# 			prev_year = str(int(fy_year[2:4]) - 1) + str(int(fy_year[-2:]) -1)
# 			previous_year = int(fyear)-1
# 			fy_start_date = datetime.strptime(str(fy_info[0]['year_start_date']), '%Y-%m-%d').date()
# 			fy_end_date = datetime.strptime(str(fy_info[0]['year_end_date']), '%Y-%m-%d').date()
# 			date_obj = datetime.strptime(date, '%Y-%m-%d').date()        
# 			if fy_start_date <= date_obj <= fy_end_date:
# 				updated_series = company_series
# 			else:
# 				if fyear in company_series:
# 					updated_series = company_series.replace(fyear, str(previous_year))
# 				elif f_year in company_series and doctype == "Sales Invoice":
# 					updated_series = company_series.replace(f_year, str(prev_year))
# 	return updated_series
    
@frappe.whitelist()
def email_salary_slip(from_date):
    ss = frappe.get_all("Salary Slip",{'start_date':from_date},['employee','name'])
    for s in ss:
        doc = frappe.get_doc("Salary Slip",s['name'])
        receiver = frappe.db.get_value("Employee", doc.employee, "company_email")
        payroll_settings = frappe.get_single("Payroll Settings")
        message = "Please Find the attachment"
        password = None

        if receiver:
            email_args = {
                "sender": "erp@nordencommunication.com",
                "recipients":receiver,
                "message": _(message),
                "subject": 'Salary Slip - from {0} to {1}'.format(doc.start_date, doc.end_date),
                "attachments": [frappe.attach_print(doc.doctype, doc.name, file_name=doc.name, password=password)],
                "reference_doctype": doc.doctype,
                "reference_name": doc.name
                }
            if not frappe.flags.in_test:
                print('yes')
                enqueue(method=frappe.sendmail, queue='short', timeout=300, is_async=True, **email_args)
            else:
                print('No')
                frappe.sendmail(**email_args)
        else:
            print(_("{0}: Employee email not found, hence email not sent").format(doc.employee_name))

@frappe.whitelist()
def email_notification():
    employee = frappe.db.get_all('Employee',{'status':'Active','Company':'Norden Communication Pvt Ltd'},['*'])
    for emp in employee:
        if emp.company_email:
            frappe.sendmail(
                recipients = emp.company_email,
                # 'api@groupteampro.com','hrd@nordencommunication.com','aiswarya@nordencommunication.com','jeyesh@nordencommunication.com'],
                subject = ' ERP Notification- Travel Request and Expense Claim Online',
                message = """<p style='font-size:15px'>Dear All,</p><br>
                        <p>On behalf of our Management, HRD is very pleased to introduce you to an online Travel Request and Expense Claim process through our new ERP system.</p><br>
                        <p>Effective today, all Travel requests and expense Claims can be processed online (submission and approval), the system will allow you to add all your claims online, and also allow you to upload all relevant bills to support your claims. The approvals and the payment will be processed within two weeks of submission; however, you will be able to monitor the status and the stage of your bill claim online.</p><br>
                        <p>Submit your claim through ERP access under Travel request & Expense Claim, and HR & Admin Expert- Ms. Aiswarya will be able to clarify the process in case you need support.</p><br>
                        <p>Kindly find your user id and Password, you may connect the below hyperlink for a demo of the process for self-guidelines.</p><br>
                        <table border="1">
                        <tr><td>Employee ID</td><td>%s</td></tr>
                        <tr><td>Employee Name</td><td>%s</td></tr>
                        <tr><td>User Login</td><td>%s</td></tr>
                        <tr><td>Password</td><td>Norden@1234</td></tr>
                        <tr><td>ERP WEBSITE LINK</td><td><a href="https://erp.nordencommunication.com">erp.nordencommunication.com</a></td></tr>
                        <tr><td><b>Travel Request WorkFlow<b></td><td><a href="https://screen-recorder-bucket.s3.ap-south-1.amazonaws.com/ScreenRecorder_2022-10-18_dfdd4ccb-b0e7-4bef-bb9a-2283f328c20c.mp4">Travel Request</a></td></tr>
                        <tr><td><b>Expense Claim WorkFlow<b></td><td><a href="https://watch.screencastify.com/v/WfShLegErakwNcUqJ3X8">Expense claim</a></td></tr>
                        </table><br>
                        <p>Regards,<br>
                        HRM</p><br>
                        """%(emp.employee_number,emp.first_name,emp.user_id)
            )
        else:
            message = ('Company Email Not in Employee %s'%(emp.name))   
            frappe.log_error('Email Notification',message) 
            



@frappe.whitelist()
def email_probation_emp():
    company_names = ["Norden Communication Pvt Ltd", "Norden Research and Innovation Centre (OPC) Pvt. Ltd"]
    category = ["NCPL INTERN" , "NRIC INTERN"]
    data = ''
    employee = frappe.get_all('Employee', {'status': 'Active', 'company': ['in' , company_names], 'payroll_category' : ['in' , category]}, [
                              "name", "employee_name", "department","date_of_joining"])
    data += 'Kindly Find the List of Employees going to complete their Internship<br><br><table class="table table-bordered">'
    data += '<table class="table table-bordered"><tr><th>Employee ID</th><th>Employee Name</th><th>Department</th><th>Date of Joining</th><th>Internship End Date</th></tr>'
    for emp in employee:
        intern_end_date = add_months(emp.date_of_joining, +6)
        data += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
                emp.name, emp.employee_name, emp.department, format_date(emp.date_of_joining),format_date(intern_end_date))
    data += '</table>'
    frappe.sendmail(
        # recipients=['gayathri.r@groupteampro.com'],
        subject=('Reg: Employee Intership End Related'),
        header=('Dear HR'),
        message=data
    )

#Material Request Showing Available Stock and Previous Purchase Orders
#Stock Availablity HTML Table View
@frappe.whitelist()
def stock_available(item_details):
    item_detail = json.loads(item_details)
    data =''
    data +='<table class="table table-bordered"><tr><th style="padding:1px;border: 1px solid black" colspan=17><center>Stock Available</center></th></tr>'
    data +='<tr><td style="padding:1px;border: 1px solid black"><b>Item Code</b></td><td style="padding:1px;border: 1px solid black"><b>Description</b></td><td style="padding:1px;border: 1px solid black"><b>Warehouse NCFME</b></td><td style="padding:1px;border: 1px solid black"><b>Warehouse NCUL</b></td><td style="padding:1px;border: 1px solid black"><b>Warehouse NCPL</b></td><td style="padding:1px;border: 1px solid black"><b>Warehouse NC</b></td><td style="padding:1px;border: 1px solid black"><b>Warehouse 5</b></td><td style="padding:1px;border: 1px solid black"><b>Total</b></td>'
    for s in item_detail:
        total_actual_qty = 0
        actual_qty = []
        description = frappe.get_value('Item',s['item_code'],'description')
        ware_house = ['Stores - NCFME','Stores - NCUL','Stores - NSPL','Stores - NC','Stores - NCI']
        for w in ware_house:
            stock_qty = frappe.db.sql(""" select (sum(`tabBin`.actual_qty) - sum(reserved_stock)) as actual_qty from `tabBin` where item_code = '%s' and warehouse = '%s' """%(s['item_code'],w),as_dict=1)
            if stock_qty:
                qty = stock_qty[0]['actual_qty']
                actual_qty.append(qty)
                total_actual_qty += qty
            else:
                actual_qty.append(0)
    
        data += '<tr><td style="padding: 1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td>'%(s['item_code'] or '',description or '',actual_qty[0],actual_qty[1],actual_qty[2],actual_qty[3],actual_qty[4],total_actual_qty)
    return data
# Previous Purchase Orders
# @frappe.whitelist()
# def previous_purchase_orders(item_details):
#    item_detail = json.loads(item_details)
#    data =''
#    data +='<table class="table table-bordered"><tr><th style="padding:1px;border: 1px solid black" colspan=17><center>Previous Purchase Orders</center></th></tr>'
#    data +='<tr><td style="padding:1px;border: 1px solid black"><b>Item Code</b></td><td style="padding:1px;border: 1px solid black"><b>Description</b></td><td style="padding:1px;border: 1px solid black"><b>Supplier</b></td>'
# #    <td style="padding:1px;border: 1px solid black"><b>Warehouse NCUL</b></td><td style="padding:1px;border: 1px solid black"><b>Warehouse NCPL</b></td><td style="padding:1px;border: 1px solid black"><b>Warehouse NC</b></td><td style="padding:1px;border: 1px solid black"><b>Warehouse 5</b></td><td style="padding:1px;border: 1px solid black"><b>Total</b></td>'
#    for s in item_detail:
# #        total_actual_qty = 0
# #        actual_qty = []
#        description = frappe.get_value('Item',s['item_code'],'description')
#     #    supplier = 
# #        ware_house = ['Stores - NCFME','Stores - NCUL','Stores - NSPL','Stores - NC','Stores - NCI']
# #        for w in ware_house:
# #            stock_qty = frappe.db.sql(""" select actual_qty from `tabBin` where item_code = '%s' and warehouse = '%s' """%(s['item_code'],w),as_dict=1)
# #            if stock_qty:
# #                qty = stock_qty[0]['actual_qty']
# #                actual_qty.append(qty)
# #                total_actual_qty += qty
# #            else:
# #                actual_qty.append(0)
 
# #        data += '<tr><td style="padding: 1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td>'%(s['item_code'] or '',description or '',actual_qty[0],actual_qty[1],actual_qty[2],actual_qty[3],actual_qty[4],total_actual_qty)
#    return data
 
#Quotation in Child Table Item Select will shown the stock items of the selected items 
@frappe.whitelist()
def stock_popup_table(item_code):
    item = frappe.db.get_value('Item',{'item_code':item_code},['item_code'])
    data = ''
    # stocks = frappe.db.sql(""" select actual_qty, warehouse """)
    data += '<table class="table table-bordered"><tr><th style="padding:1px;border: 1px solid black" colspan=6><center>Stock Availability</center></th></tr>'
    return data

#Purchase order to select child table to fetch the previous stock
@frappe.whitelist()
def purchase_order_items(item_code):
    item = frappe.db.get_value('Item',{'item_code':item_code},['item_code'])
    data = ''
    po = frappe.db.sql(""" select `tabPurchase Order Item` .item_code as item_code, `tabPurchase Order Item` .item_name as item_name,
                        `tabPurchase Order Item` .supplier as supplier,`tabPurchase Order Item` .qty as qty,`tabPurchase Order`.transaction_date as date,
                        `tabPurchase Order`.name as po from `tabPurchase Order` left join `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus !=2 """%(item_code),as_dict=True)
    
    data += '<table class="table table-bordered"><tr><th style="padding:1px;border: 1px solid black" colspan=6><center>Stock Availability</center></th></tr>'
    data += '<tr><td style="padding:1px;border: 1px solid black"><b>Item Code</b></td><td style="padding:1px;border: 1px solid black"><b>Item Name</b></td><td style="padding:1px;border: 1px solid black"><b>Warehouse</b></td><td style="padding:1px;border: 1px solid black"><b>QTY</b></td><td style="padding:1px;border: 1px solid black"><b>UOM</b></td></tr>'
    i = 0
    data +='</table>'
    return data

#Material Request to select table to fetch the Stock Availablity
@frappe.whitelist()
def stock_popup(item_code):
    item = frappe.get_value('Item',{'item_code':item_code},'item_code')
    data = ''
    stocks = frappe.db.sql("""select (sum(`tabBin`.actual_qty) - sum(reserved_stock)) as actual_qty,warehouse,stock_uom,stock_value from tabBin
        where item_code = '%s' """%(item),as_dict=True)
    data += '<table class="table table-bordered"><tr><th style="padding:1px;border: 1px solid black" colspan=6><center>Stock Availability</center></th></tr>'
    data += '<tr><td style="padding:1px;border: 1px solid black"><b>Item Code</b></td><td style="padding:1px;border: 1px solid black"><b>Item Name</b></td><td style="padding:1px;border: 1px solid black"><b>Warehouse</b></td><td style="padding:1px;border: 1px solid black"><b>QTY</b></td><td style="padding:1px;border: 1px solid black"><b>UOM</b></td></tr>'
    i = 0
    for stock in stocks:
        if stock.actual_qty > 0:
            data += '<tr><td style="padding:1px;border: 1px solid black">%s</td><td style="padding:1px;border: 1px solid black">%s</td><td style="padding:1px;border: 1px solid black">%s</td><td style="padding:1px;border: 1px solid black">%s</td><td style="padding:1px;border: 1px solid black">%s</td></tr>'%(item,frappe.db.get_value('Item',item,'item_name'),stock.warehouse,stock.actual_qty,stock.stock_uom)
            i += 1
    data += '</table>'
    if i > 0:
        return data

@frappe.whitelist()
def get_hsn():
    item = frappe.get_value('Item',{'item_code':item_code},'item_code')
    return "hi"

def get_exc_rate():
    from_currency ='USD'
    to_currency = 'AED'
    exc_rate = get_exchange_rate(from_currency,to_currency)
    print(exc_rate)

@frappe.whitelist()
def set_territory():
    quotation = frappe.get_all('Quotation',{"status":"Ordered"},["*"])
    for i in quotation:
        territory = frappe.get_value('Customer',{'name':i.customer_name},['territory'])
        frappe.db.set_value('Quotation',i.name,'territory',territory)


@frappe.whitelist()
def get_user_id_travel_request(reports_to):
    employee = frappe.db.get_value('Employee',{'status':'Active','employee_number':reports_to},['employee_name','user_id'])
    return employee

@frappe.whitelist()
def get_user_id():
    user_login =  frappe.db.get_value('Employee',{'user_id':frappe.session.user},['user_id'])
    return user_login



@frappe.whitelist()
def get_empl(doc,method):
    salary_slip = frappe.db.sql("""select * from `tabSalary Slip` where status = 'Draft' and start_date between '2022-10-01' and '2022-10-31' """,as_dict=1)
    for esi in salary_slip:
        get=frappe.get_doc('Salary Slip',{'name':esi.name})

@frappe.whitelist()
def get_customer_det(doc,method):
    # frappe.errprint("hi")
    if doc.first_name:
        cus = frappe.new_doc("Contact")
        cus.first_name = doc.first_name
        cus.last_name = doc.last_name
        cus.designation = doc.designation
        cus.status = doc.status
        cus.append("links", {
            "link_doctype": "Customer",
            "link_name":doc.name
            })
        cus.flags.ignore_mandatory = True    
        cus.save(ignore_permissions= True)

@frappe.whitelist()
def get_address_det(doc,method):
    # frappe.errprint("hi")
    if doc.address_title:
        addr = frappe.new_doc("Address")
        addr.address_title = doc.address_title
        addr.address_line1 = doc.address_line1
        addr.address_line2 = doc.address_line2
        addr.city = doc.city
        addr.country = doc.country
        addr.email_idl = doc.email_id
        addr.phone = doc.phone
        addr.append("links", {
            "link_doctype": "Customer",
            "link_name":doc.name
            })
        addr.flags.ignore_mandatory = True    
        addr.save(ignore_permissions= True)

@frappe.whitelist()
def create_sample_inspection(sample,item,po,pr,name):
    # s = int(sample) - 1
    it = frappe.get_value("Item",{"name":item},["inspection_template"])
    for i in range(int(sample)):
        doc = frappe.new_doc("Inspection Sample")
        doc.item = item
        doc.po_number = po
        doc.pr_number = pr
        doc.inspection_template = it
        doc.item_inspection = name
        doc.save(ignore_permissions = True)

@frappe.whitelist()
def create_sample_inspection_from_lr(sample,item,po,lr,name):
    # s = int(sample) - 1
    it = frappe.get_value("Item",{"name":item},["factory_inspection_template"])
    for i in range(int(sample)):
        doc = frappe.new_doc("Inspection Sample")
        doc.item = item
        doc.po_number = po
        doc.logistics_request_number = lr
        doc.inspection_template = it
        doc.item_inspection = name
        doc.save(ignore_permissions = True)

@frappe.whitelist()
def create_sample_inspection_from_dn(sample,item,so,dn,name):
    # s = int(sample) - 1
    it = frappe.get_value("Item",{"name":item},["inspection_template"])
    for i in range(int(sample)):
        doc = frappe.new_doc("Inspection Sample")
        doc.item = item
        doc.so_number = so
        doc.dn_number = dn
        doc.inspection_template = it
        doc.item_inspection = name
        doc.save(ignore_permissions = True)

@frappe.whitelist()
def update_quotation_cluster(import_file):
    filepath = get_file(import_file)
    pps = read_csv_content(filepath[1])
    for pp in pps:
        if frappe.db.exists('Sales Order',{'name':pp[1]}):
            so = frappe.db.sql(""" update `tabSales Order` set cluster = '%s' where name = '%s' """%(pp[6],pp[1]))
            print(pp[1])
        #     c = frappe.get_value("Sales Order",{"name":pp[2]},["docstatus"])
        #     if c == 0 or c == 1:
        #         print(pp[2])
       
        # #         doc = frappe.get_doc("Sales Order",pp[2])
        # #         doc.prepared_by =  pp[6]
        # #         doc.sale_person =  pp[7]
        # #         doc.territory =  pp[8]
        # #         doc.save(ignore_permissions=True)
        #         so = frappe.db.sql(""" update `tabSales Order` set cluster = '%s' where name = '%s' """%(pp[6],pp[2]))
        #         print(so)

       
@frappe.whitelist()
def add_specification(template):
    # frappe.errprint(template)
    it = frappe.get_doc("Inspection Template",template)
    # frappe.errprint(it.functional_aspects_table)
    return it.functional_aspects_table,it.visual_aspects_table,it.material_aspects_table,it.dimensional_aspects_table
    # frappe.errprint(it.dimensional_aspects_table)
    # for i in it.dimensional_aspects_table:
    #     frappe.errprint()
    # frappe.errprint(it.material_aspects_table)
    # frappe.errprint(it.functional_aspects_table)

# @frappe.whitelist()
# def get_sub_heading(item_detail):
#     item_detail = json.loads(item_detail)
#     l1 = []
#     l2 = []
#     l3 = []
#     l4 = []
#     l5 = []
#     l6 = []
#     for i in item_detail:
#         if i['item_heading'] not in l1:
#             l1.append(i["item_heading"])
#         else:
#             l2.append(i["item_heading"])
#         if i['item_sub_heading'] not in l3:
#             l3.append(i['item_sub_heading'])
#         else:
#             l4.append(i['item_sub_heading'])
#         if i['item_title_3'] not in l5:
#             l5.append(i['item_title_3'])
#         else:
#             l6.append(['item_title_3'])
#     return l1,l3,l5

@frappe.whitelist()
def update_company_currency_in_payments(selected_currency,account_currency):
    return get_exchange_rate(selected_currency,account_currency)


@frappe.whitelist()
def get_dimensional(doc):
    sample = frappe.get_all("Inspection Sample",{"item_inspection":doc.name},["*"])
    item = frappe.get_value("Item",{"name":doc.item_code},["inspection_template"])
    it = frappe.db.sql(""" select `tabDimensional Aspects Table`.specification from `tabInspection Template` 
    left join `tabDimensional Aspects Table` on `tabInspection Template`.name = `tabDimensional Aspects Table`.parent
    where  `tabInspection Template`.name = '%s' """ %(item),as_dict = True)
    data = ''
    data += '<tr><td colspan="18" style="border-color:#e20026"><center><b>Dimensional Aspects<b></center></td></tr><tr>'
    data += '<tr><td width = "20%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;padding-bottom :50px;" >,<center><b style = "color:white;" >Specification<b></center></td><td width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;" ><center><b style = "color:white" >Acceptance  Criteria<b></center></td><td width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;" ><center><b style = "color:white">Instrument/Ref No<b></center></td><td width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;" ><center><b style = "color:white">1<b></center></td><td  width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;"><center><b style = "color:white" >2<b></center></td><td  width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;" ><center><b style = "color:white" >3<b></center></td><td width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;" ><center><b style = "color:white" >4<b></center></td><td width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;"><center><b style = "color:white" >5<b></center></td><td width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;" ><center><b style = "color:white" >Remarks<b></center></td></tr><tr>'
    for s in it:
        data += '<tr><td style="border-color:#e20026">%s</td><td style="border-color:#e20026">''</td><td style="border-color:#e20026">''</td>'%(s.specification)
        for i in sample:
            spec = frappe.db.sql(""" select `tabDimensional Aspects Sample`.specification,`tabDimensional Aspects Sample`.acceptance_criteria ,`tabDimensional Aspects Sample`.status from `tabInspection Sample` 
            left join `tabDimensional Aspects Sample` on `tabInspection Sample`.name = `tabDimensional Aspects Sample`.parent
            where  `tabInspection Sample`.item_inspection = '%s' and `tabDimensional Aspects Sample`.specification = '%s' and `tabInspection Sample`.name = '%s' """ %(doc.name,s.specification,i.name),as_dict = True)
            
            if spec[0]['status']:
                data +='<td colspan="1" style="border-color:#e20026">%s</td>'%('&#10004')
            else:
                data +='<td colspan="1" style="border-color:#e20026"><center>%s</center></td>'%('-')
        data += '<td style="border-color:#e20026">''</td>'
        data +='</tr>'
    return data

def get_functional(doc):
    sample = frappe.get_all("Inspection Sample",{"item_inspection":doc.name},["*"])
    item = frappe.get_value("Item",{"name":doc.item_code},["inspection_template"])
    it = frappe.db.sql(""" select `tabFunctional Aspects Table`.specification from `tabInspection Template` 
    left join `tabFunctional Aspects Table` on `tabInspection Template`.name = `tabFunctional Aspects Table`.parent
    where  `tabInspection Template`.name = '%s' """ %(item),as_dict = True)
    data = ''
    data += '<tr><td colspan="18" style="border-color:#e20026"><center><b>Functional Aspects<b></center></td></tr><tr>'
    data += '<tr><td width = "20%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;padding-bottom :50px;" >,<center><b style = "color:white;" >Specification<b></center></td><td width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;" ><center><b style = "color:white" >Acceptance  Criteria<b></center></td><td width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;" ><center><b style = "color:white">Instrument/Ref No<b></center></td><td width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;" ><center><b style = "color:white">1<b></center></td><td  width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;"><center><b style = "color:white" >2<b></center></td><td  width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;" ><center><b style = "color:white" >3<b></center></td><td width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;" ><center><b style = "color:white" >4<b></center></td><td width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;"><center><b style = "color:white" >5<b></center></td><td width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;" ><center><b style = "color:white" >Remarks<b></center></td></tr><tr>'
    for s in it:
        data += '<tr><td style="border-color:#e20026">%s</td><td style="border-color:#e20026">''</td><td style="border-color:#e20026">''</td>'%(s.specification)
        for i in sample:
            spec = frappe.db.sql(""" select `tabFunctional Aspects Sample`.specification,`tabFunctional Aspects Sample`.acceptance_criteria ,`tabFunctional Aspects Sample`.status from `tabInspection Sample` 
            left join `tabFunctional Aspects Sample` on `tabInspection Sample`.name = `tabFunctional Aspects Sample`.parent
            where  `tabInspection Sample`.item_inspection = '%s' and `tabFunctional Aspects Sample`.specification = '%s' and `tabInspection Sample`.name = '%s' """ %(doc.name,s.specification,i.name),as_dict = True)
            if spec[0]['status']:
                data +='<td colspan="1" style="border-color:#e20026">%s</td>'%('&#10004')
            else:
                data +='<td colspan="1" style="border-color:#e20026"><center>%s</center></td>'%('-')
        data += '<td style="border-color:#e20026">''</td>'
        data +='</tr>'
    return data

def get_material(doc):
    sample = frappe.get_all("Inspection Sample",{"item_inspection":doc.name},["*"])
    item = frappe.get_value("Item",{"name":doc.item_code},["inspection_template"])
    it = frappe.db.sql(""" select `tabMaterial Aspects Table`.specification from `tabInspection Template` 
    left join `tabMaterial Aspects Table` on `tabInspection Template`.name = `tabMaterial Aspects Table`.parent
    where  `tabInspection Template`.name = '%s' """ %(item),as_dict = True)
    data = ''
    data += '<tr><td colspan="18" style="border-color:#e20026"><center><b>Material Aspects<b></center></td></tr><tr>'
    data += '<tr><td width = "20%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;padding-bottom :50px;" >,<center><b style = "color:white;" >Specification<b></center></td><td width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;" ><center><b style = "color:white" >Acceptance  Criteria<b></center></td><td width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;" ><center><b style = "color:white">Instrument/Ref No<b></center></td><td width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;" ><center><b style = "color:white">1<b></center></td><td  width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;"><center><b style = "color:white" >2<b></center></td><td  width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;" ><center><b style = "color:white" >3<b></center></td><td width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;" ><center><b style = "color:white" >4<b></center></td><td width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;"><center><b style = "color:white" >5<b></center></td><td width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;" ><center><b style = "color:white" >Remarks<b></center></td></tr><tr>'
    for s in it:
        data += '<tr><td style="border-color:#e20026">%s</td><td style="border-color:#e20026">''</td><td style="border-color:#e20026">''</td>'%(s.specification)
        for i in sample:
            spec = frappe.db.sql(""" select `tabMaterial Aspects Sample`.specification,`tabMaterial Aspects Sample`.acceptance_criteria ,`tabMaterial Aspects Sample`.status from `tabInspection Sample` 
            left join `tabMaterial Aspects Sample` on `tabInspection Sample`.name = `tabMaterial Aspects Sample`.parent
            where  `tabInspection Sample`.item_inspection = '%s' and `tabMaterial Aspects Sample`.specification = '%s' and `tabInspection Sample`.name = '%s' """ %(doc.name,s.specification,i.name),as_dict = True)
            if spec[0]['status']:
                data +='<td colspan="1" style="border-color:#e20026">%s</td>'%('&#10004')
            else:
                data +='<td colspan="1" style="border-color:#e20026"><center>%s</center></td>'%('-')
        data += '<td style="border-color:#e20026">''</td>'
        data +='</tr>'
    return data

def get_visual(doc):
    # s = frappe.get_all("Inspection Sample",{"item_inspection":doc.name},["*"])
    item = frappe.get_value("Item",{"name":doc.item_code},["inspection_template"])
    it = frappe.db.sql(""" select `tabVisual Aspects Table`.specification from `tabInspection Template` 
    left join `tabVisual Aspects Table` on `tabInspection Template`.name = `tabVisual Aspects Table`.parent
    where  `tabInspection Template`.name = '%s' """ %(item),as_dict = True)
    data = ''
    data += '<tr><td colspan="10"><center><b>Visual Aspects</b></center></td></tr><tr>'
    data += '<tr><td width = "20%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;padding-bottom :50px;" >,<center><b style = "color:white;" >Specification<b></center></td><td width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;" ><center><b style = "color:white" >Acceptance  Criteria<b></center></td><td width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;" ><center><b style = "color:white">Instrument/Ref No<b></center></td><td width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;" ><center><b style = "color:white">1<b></center></td><td  width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;"><center><b style = "color:white" >2<b></center></td><td  width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;" ><center><b style = "color:white" >3<b></center></td><td width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;" ><center><b style = "color:white" >4<b></center></td><td width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;"><center><b style = "color:white" >5<b></center></td><td width = "10%" style = "border-color:#e20026;border-right-color:#e20026;background-color: #e20026;color: white;" ><center><b style = "color:white" >Remarks<b></center></td></tr><tr>'
    for s in it:
        data += '<tr><td style="border-color:#e20026">%s</td><td style="border-color:#e20026">''</td><td style="border-color:#e20026">''</td>'%(s.specification)
    return data

def india_quotation(doc):
    data = ''
    data += '<tr style="height:10%;">'
    data += '<td style="border-color:#e20026;border-right-color:white;background-color: #e20026;color: white;">No</td>'
    data += '<td style="border-color:#e20026;border-right-color:white;background-color: #e20026;color: white;width:18%;">Item</td>'
    data += '<td style="border-color:#e20026;border-right-color:white;background-color: #e20026;color: white;width:40%,height:10px;">Description</td>'
    data += '<td style="border-color:#e20026;border-right-color:white;background-color: #e20026;color: white;">UOM</td>'
    data += '<td style="border-color:#e20026;border-right-color:white;background-color: #e20026;color: white;">Qty</td>'
    data += '<td style="border-color:#e20026;border-right-color:white;background-color: #e20026;color: white;">Rate </td>'
    data += '<td style="border-color:#e20026;border-right-color:white;background-color: #e20026;color: white;">Amount</td>'
    data += '<td style="border-color:#e20026;border-right-color:white;background-color: #e20026;color: white;">Datasheet Link</td>'
    data += '<td style="border-color:#e20026;border-right-color:white;background-color: #e20026;color: white;">Remarks</td> </tr>'
    for h in doc.heading: 
        data += '<tr style="height:10%;">'
        data += '<td style="border-color:#e20026;text-align:left" colspan="10"><span><b><center>%s</center></b></span></td></tr>' %(h.main_title)
        for s in doc.sub_heading:
            if h.main_title == s.heading:
                if s.title:
                    data += '<td style="border-color:#e20026;text-align:left" colspan="10"><span><b>%s</b></span></td></tr>' %(s.title)
                else:
                    pass
                for t in doc.title_3:
                    if h.main_title == t.heading and s.title == t.sub_heading:
                        if t.title_3:
                            data += '<td style="border-color:#e20026;text-align:left" colspan="10"><span><b>%s</b></span></td></tr>' %(t.title_3)
                        else:
                            pass
                        x = 1
                        for i in doc.items:
                            if i.item_heading == h.main_title and i.item_sub_heading == s.title and i.item_title_3 == t.title_3:
                                if i.optional_item == 1:
                                    data+='<tr class ="altercolor" style="font-size:10px; height:10%;">'

                                    data+='<td style="font-family:Arial;border-color:#e20026;">%s</td>' %(x)
                                    data+='<td style="border-color:#e20026;background-color: #F1EAE8;">%s</td>' %(i.item_code)
                                    data+='<td style="border-color:#e20026;background-color: #F1EAE8;">%s</td>' %(i.description)
                                    data+='<td style="border-color:#e20026;background-color: #F1EAE8;">%s</td>' %(i.uom)
                                    data+='<td style="border-color:#e20026;background-color: #F1EAE8;">%s</td>' %(i.qty)
                                    data+='<td style="border-color:#e20026;background-color: #F1EAE8;">%s</td>' %(i.rate)
                                    data+='<td style="border-color:#e20026;background-color: #F1EAE8;">%s</td>' %(i.amount)
                                    data+='<td style="border-color:#e20026;background-color: #F1EAE8;">%s</td>' %('')
                                    data+='<td style="border-color:#e20026;background-color: #F1EAE8;">%s</td></tr>' %(i.remark or '')
                                else:
                                    data+='<tr class ="altercolor" style="font-size:10px; height:10%;">'

                                    data+='<td style="font-family:Arial;border-color:#e20026;">%s</td>' %(x)
                                    data+='<td style="border-color:#e20026">%s</td>' %(i.item_code)
                                    data+='<td style="border-color:#e20026">%s</td>' %(i.description)
                                    data+='<td style="border-color:#e20026">%s</td>' %(i.uom)
                                    data+='<td style="border-color:#e20026">%s</td>' %(i.qty)
                                    data+='<td style="border-color:#e20026">%s</td>' %(i.rate)
                                    data+='<td style="border-color:#e20026">%s</td>' %(i.amount)
                                    data+='<td style="border-color:#e20026;">%s</td>' %('')
                                    data+='<td style="border-color:#e20026">%s</td></tr>' %(i.remark or '')

                            x = x + 1
    return data

#Show the print for opportunity 
def opportunity_india(doc):
    data = ''
    data += '<tr style="height:10%;">'
    data += '<td style="border-color:#e20026;border-right-color:white;background-color: #e20026;color: white;">No</td>'
    data += '<td style="border-color:#e20026;border-right-color:white;background-color: #e20026;color: white;width:18%;">Item</td>'
    data += '<td style="border-color:#e20026;border-right-color:white;background-color: #e20026;color: white;width:40%,height:10px;">Description</td>'
    data += '<td style="border-color:#e20026;border-right-color:white;background-color: #e20026;color: white;">UOM</td>'
    data += '<td style="border-color:#e20026;border-right-color:white;background-color: #e20026;color: white;">Qty</td>'
    # data += '<td style="border-color:#e20026;border-right-color:white;background-color: #e20026;color: white;">Rate </td>'
    # data += '<td style="border-color:#e20026;border-right-color:white;background-color: #e20026;color: white;">Amount</td>'
    # data += '<td style="border-color:#e20026;border-right-color:white;background-color: #e20026;color: white;">Datasheet Link</td>'
    data += '<td style="border-color:#e20026;border-right-color:white;background-color: #e20026;color: white;">Remarks</td> </tr>'
    for h in doc.heading: 
        data += '<tr style="height:10%;">'
        data += '<td style="border-color:#e20026;text-align:left" colspan="10"><span><b><center>%s</center></b></span></td></tr>' %(h.main_title)
        for s in doc.sub_heading:
            if h.main_title == s.heading:
                if s.title:
                    data += '<td style="border-color:#e20026;text-align:left" colspan="10"><span><b>%s</b></span></td></tr>' %(s.title)
                else:
                    pass
                for t in doc.title_3:
                    if h.main_title == t.heading and s.title == t.sub_heading:
                        if t.title_3:
                            data += '<td style="border-color:#e20026;text-align:left" colspan="10"><span><b>%s</b></span></td></tr>' %(t.title_3)
                        else:
                            pass
                        x = 1
                        for i in doc.items:
                            if i.item_heading == h.main_title and i.item_sub_heading == s.title and i.item_title_3 == t.title_3:
                                if i.optional == 1:
                                    data+='<tr class ="altercolor" style="font-size:10px; height:10%;">'
                                    data+='<td style="font-family:Arial;border-color:#e20026;background-color: #F1EAE8;">%s</td>' %(x)
                                    data+='<td style="border-color:#e20026;background-color: #F1EAE8;">%s</td>' %(i.item_code)
                                    data+='<td style="border-color:#e20026;background-color: #F1EAE8;">%s</td>' %(i.description)
                                    data+='<td style="border-color:#e20026;background-color: #F1EAE8;">%s</td>' %(i.uom)
                                    data+='<td style="border-color:#e20026;background-color: #F1EAE8;">%s</td>' %(i.qty)
                                    # data+='<td style="border-color:#e20026">%s</td>' %(i.rate)
                                    # data+='<td style="border-color:#e20026">%s</td>' %(i.amount)
                                    # data+='<td style="border-color:#e20026;">%s</td>' %('')
                                    data+='<td style="border-color:#e20026;background-color: #F1EAE8;">%s</td></tr>' %(i.remarks or '')
                                else:
                                    data+='<tr class ="altercolor" style="font-size:10px; height:10%;">'
                                    data+='<td style="font-family:Arial;border-color:#e20026;">%s</td>' %(x)
                                    data+='<td style="border-color:#e20026;">%s</td>' %(i.item_code)
                                    data+='<td style="border-color:#e20026">%s</td>' %(i.description)
                                    data+='<td style="border-color:#e20026">%s</td>' %(i.uom)
                                    data+='<td style="border-color:#e20026">%s</td>' %(i.qty)
                                    # data+='<td style="border-color:#e20026">%s</td>' %(i.rate)
                                    # data+='<td style="border-color:#e20026">%s</td>' %(i.amount)
                                    # data+='<td style="border-color:#e20026;">%s</td>' %('')
                                    data+='<td style="border-color:#e20026">%s</td></tr>' %(i.remarks or '')
                            x = x + 1
    return data
#Alert for every work flow status for Quotation
@frappe.whitelist()
def quotation_workflow_alert(doc,method):
    wa = frappe.get_doc("Workflow Approval","Quotation")
    for i in wa.workflow:
        if doc.cluster:
            if doc.company == "Norden Communication Middle East FZE":
                sales_role = "Sales Master Manager"
            else:
                sales_role = "Sales Manager"
            if doc.so_check == 0 and doc.cluster == i.cluster and doc.company == i.company and doc.price_list_region == i.territory and i.role == sales_role and doc.work_flow == "Pending for Sales Manager":
                frappe.sendmail(
                    recipients=[i.user ],
                    subject = 'Quotation - %s is Pending for Approval' %(doc.name),
                    message = """ Quotation - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/quotation/%s">Click here</a> to approve """ %(doc.name,doc.name)

                )  
                doc.so_check = 1
            
            if doc.op_check == 0 and doc.cluster == i.cluster and doc.company == i.company and doc.price_list_region == i.territory and i.role == "Operation Director" and doc.work_flow == "Pending for Operation Director":
                frappe.sendmail(
                    recipients=[i.user ],
                    subject = 'Quotation - %s is Pending for Approval' %(doc.name),
                    message = """ Quotation - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/quotation/%s">Click here</a> to approve """ %(doc.name,doc.name)

                )   
                doc.op_check = 1

            if doc.coo_check == 0 and doc.company == i.company and i.role == "COO" and doc.work_flow == "Pending for COO":
                frappe.sendmail(
                    recipients=[i.user ],
                    subject = 'Quotation - %s is Pending for Approval' %(doc.name),
                    message = """ Quotation - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/quotation/%s">Click here</a> to approve """ %(doc.name,doc.name)

                )
                doc.coo_check =1
        
        else:
            if doc.company == "Norden Communication Middle East FZE":
                sales_role = "Sales Master Manager"
            else:
                sales_role = "Sales Manager"
            if doc.so_check == 0 and doc.company == i.company and doc.price_list_region == i.territory and i.role == sales_role and doc.work_flow == "Pending for Sales Manager":
                frappe.sendmail(
                    recipients=[i.user ],
                    subject = 'Quotation - %s is Pending for Approval' %(doc.name),
                    message = """ Quotation - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/quotation/%s">Click here</a> to approve """ %(doc.name,doc.name)

                )   
                doc.so_check = 1
            
                if doc.op_check == 0 and doc.company == i.company and doc.price_list_region == i.territory and i.role == "Operation Director" and doc.work_flow == "Pending for Operation Director":
                    frappe.sendmail(
                        recipients=[i.user ],
                        subject = 'Quotation - %s is Pending for Approval' %(doc.name),
                        message = """ Quotation - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/quotation/%s">Click here</a> to approve """ %(doc.name,doc.name)

                    )
                doc.op_check = 1

                if doc.coo_check == 0 and doc.company == i.company and i.role == "COO" and doc.work_flow == "Pending for COO":
                    frappe.sendmail(
                        recipients=[i.user ],
                        subject = 'Quotation - %s is Pending for Approval' %(doc.name),
                        message = """ Quotation - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/quotation/%s">Click here</a> to approve """ %(doc.name,doc.name)

                    )
                doc.coo_check =1
#Alert for every work flow status for SO
@frappe.whitelist()
def so_workflow_alert(doc,method):
    wa = frappe.get_doc("Workflow Approval","Sales Order")
    for i in wa.workflow:
        if doc.cluster:
            if doc.cluster == i.cluster and doc.company == i.company and i.role == "HOD" and doc.workflow_state == "Pending for HOD":
                frappe.sendmail(
                    recipients=[i.user ],
                    subject = 'Sales Order - %s is Pending for Approval' %(doc.name),
                    message = """ Sales Order - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/sales-order/%s">Click here</a> to approve """ %(doc.name,doc.name)

                )   
            
            if doc.cluster == i.cluster and doc.company == i.company and i.role == "Accounts User" and doc.work_flow == "Pending for Accounts":
                frappe.sendmail(
                    recipients=[i.user ],
                    subject = 'Sales Order - %s is Pending for Approval' %(doc.name),
                    message = """ Sales Order - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/sales-order/%s">Click here</a> to approve """ %(doc.name,doc.name)

                )   

            # if doc.company == i.company and i.role == "COO" and doc.work_flow == "Pending for COO":
            #     frappe.sendmail(
            #         recipients=[i.user ],
            #         subject = 'Sales Order - %s is Pending for Approval' %(doc.name),
            #         message = """ Sales Order - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/sales-order/%s">Click here</a> to approve """ %(doc.name,doc.name)

            #     )
        
        else:
            if doc.company == i.company and i.role == "HOD" and doc.work_flow == "Pending for HOD":
                frappe.sendmail(
                    recipients=[i.user ],
                    subject = 'Sales Order - %s is Pending for Approval' %(doc.name),
                    message = """ Sales Order - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/sales-order/%s">Click here</a> to approve """ %(doc.name,doc.name)

                )   

            if doc.company == i.company and i.role == "Accounts User" and doc.work_flow == "Pending for Accounts":
                frappe.sendmail(
                    recipients=[i.user ],
                    subject = 'Sales order - %s is Pending for Approval' %(doc.name),
                    message = """ Sales Order - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/sales-order/%s">Click here</a> to approve """ %(doc.name,doc.name)

                )

                # if doc.company == i.company and i.role == "COO" and doc.work_flow == "Pending for COO":
                #     frappe.sendmail(
                #         recipients=[i.user ],
                #         subject = 'Sales Order - %s is Pending for Approval' %(doc.name),
                #         message = """ Sales Order - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/quotation/%s">Click here</a> to approve """ %(doc.name,doc.name)

                #     )
#Alert for every work flow status for PO
@frappe.whitelist()
def po_workflow_alert(doc,method):
    wa = frappe.get_doc("Workflow Approval","Purchase Order")
    for i in wa.workflow:
        if doc.cluster:
            if doc.cluster == i.cluster and doc.company == i.company and i.role == "Purchase Master Manager" and doc.workflow_state == "Pending for purchase manager":
                frappe.sendmail(
                    recipients=[i.user ],
                    subject = 'Purchase Order - %s is Pending for Approval' %(doc.name),
                    message = """ Purchase Order - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/purchase-order/%s">Click here</a> to approve """ %(doc.name,doc.name)

                )   
            
            if doc.cluster == i.cluster and doc.company == i.company and i.role == "Accounts User" and doc.work_flow == "Pending for Accounts":
                frappe.sendmail(
                    recipients=[i.user ],
                    subject = 'Purchase Order - %s is Pending for Approval' %(doc.name),
                    message = """ Purchase Order - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/purchase-order/%s">Click here</a> to approve """ %(doc.name,doc.name)

                )   

            # if doc.company == i.company and i.role == "COO" and doc.work_flow == "Pending for COO":
            #     frappe.sendmail(
            #         recipients=[i.user ],
            #         subject = 'Sales Order - %s is Pending for Approval' %(doc.name),
            #         message = """ Sales Order - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/sales-order/%s">Click here</a> to approve """ %(doc.name,doc.name)

            #     )
        
        else:
            if doc.company == i.company and i.role == "Purchase Master Manager" and doc.work_flow == "Pending for purchase manager":
                frappe.sendmail(
                    recipients=[i.user ],
                    subject = 'Purchase Order - %s is Pending for Approval' %(doc.name),
                    message = """ Purchase Order - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/purchase-order/%s">Click here</a> to approve """ %(doc.name,doc.name)

                )   

            if doc.company == i.company and i.role == "Accounts User" and doc.work_flow == "Pending for Accounts":
                frappe.sendmail(
                    recipients=[i.user ],
                    subject = 'Purchase Order - %s is Pending for Approval' %(doc.name),
                    message = """ Purchase Order - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/purchase-order/%s">Click here</a> to approve """ %(doc.name,doc.name)

                )

                # if doc.company == i.company and i.role == "COO" and doc.work_flow == "Pending for COO":
                #     frappe.sendmail(
                #         recipients=[i.user ],
                #         subject = 'Sales Order - %s is Pending for Approval' %(doc.name),
                #         message = """ Sales Order - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/quotation/%s">Click here</a> to approve """ %(doc.name,doc.name)

                #     )


#Throw the below message while submission of Delivery Note
@frappe.whitelist()
def check_item_inspection_dn(doc,method):
    for i in doc.items:
        if not i.skip_qc:
            item = frappe.get_value("Item",{"name":i.item_code},["request_for_quality_inspection"])
            inspection = frappe.db.exists("Item Inspection",{"item_code":i.item_code,"pr_mumber":doc.name,'docstatus':'1'})
            if item == 1:
                if not inspection:
                    frappe.throw("Please inspect the items")
            else:
                frappe.validated = True

#Sent a mail for leave application and work from home
@frappe.whitelist()
def leave_notification():
    employee = frappe.db.get_all('Employee',{'status':'Active','Company':'Norden Communication Pvt Ltd'},['*'])
    for emp in employee:
        if emp.company_email:
            frappe.sendmail(
                recipients = emp.company_email,
                # 'api@groupteampro.com','hrd@nordencommunication.com','aiswarya@nordencommunication.com','jeyesh@nordencommunication.com'],
                subject = 'ERP Notification-Leave Application & Work from home',
                message = """<p style='font-size:15px'>Dear All,</p>
                        <p align:'justify'>On behalf of NORDEN Management, HRD is very pleased to introduce you to an online <b>Leave Application & Work from Home</b> process through our new ERP system.</p>
                        <p align:'justify'>Effective 06th January 2023, all <b>Leave Application & Work from home requests</b> can be processed online (submission and approval). However you will be able to monitor the status of your leave balance & request.</p>
                        <p align:'justify'>HR & Admin Expert- Ms.Aiswarya will be able to clarify the process in case you need any support. Meanwhile please check your leave balance in ERP in the beginning itself , if you have any queries on it, please coordinate with Ms. Asha immediately</p>
                        <p align:'justify'>NB:as informed before, Hereafter there is no carry forward option available for casual & sick leave, both are fixed as 12 days for all permanent staff.</p>
                        <table border="1">
                        <tr><td>ERP WEBSITE LINK</td><td><a href="https://erp.nordencommunication.com">erp.nordencommunication.com</a></td></tr>
                        <tr><td><b>Leave Application Process Link</b></td><td><a href="https://www.awesomescreenshot.com/video/13751301?key=cf795cbc77b91c6b93a571e5b45fd477">Leave Application</a></td></tr>
                        <tr><td><b>Work from home and leave application Process Link</b></td><td><a href="https://www.awesomescreenshot.com/video/13753132?key=b67e492b31bafea03e78c30a4c2f548a">Work From Home and Attendance Request</a></td></tr>
                        </table><br>
                        <p>Thanking You</p>
                        <p>HRD</p>
                        """
            )
        else:
            message = ('Company Email Not in Employee %s'%(emp.name))   
            frappe.log_error('Email Notification',message) 
        
@frappe.whitelist()
def pr_creation(doc,method):
    if doc.logistics:
        lr = frappe.get_doc("Logistics Request",doc.logistics)
        for i in doc.receipts:
            i.purchase_receipt = lr.name
        
#Set the cluster name to match with sales person
@frappe.whitelist()
def set_cluster(sales_person):
    doc = frappe.get_value("Cluster",{"user":sales_person})
    if doc:
        return doc
   
#Get the Opportunity items values
@frappe.whitelist()
def opp_details(opp):
    doc = frappe.get_doc("Opportunity",opp)
    return doc.items
    # for i in doc.heading:
    #     frappe.errprint(i.main_title)

#Create Stock Transfer India while submission of Stock Entry	
@frappe.whitelist()
def create_sti(doc,method):
    if doc.bill_of_entry or doc.bom_out_bound:
        if doc.stock_entry_type == "Material Receipt":
            if frappe.db.exists("Stock Transfer India",doc.bill_of_entry):
                s = frappe.get_doc("Stock Transfer India",doc.bill_of_entry)
                s.boe_inbound_no = doc.bill_of_entry
                for i in doc.items:
                    x = s.append("stock_transfer")
                    x.item_code = i.item_code
                    x.target_warehouse = i.t_warehouse
                    x.bom_inbound_qty = i.qty
                    x.balance_in_qty = i.qty
                    x.bom_inbound = doc.bill_of_entry
                    x.serial_no = i.serial_no
                    x.qty = i.qty
                    x.uom = i.uom
                    x.basic_rate = i.basic_rate
                    x.additional_cost = i.additional_cost
                    x.itemwise_additional_cost = i.itemwise_additional_cost
                    x.valuation_rate = i.valuation_rate
                    x.basic_amount = i.basic_amount
                    x.amount = i.amount
                    x.batch = i.batch_no
                s.save(ignore_permissions=True)
            else:
                s = frappe.new_doc("Stock Transfer India")
                s.warehouse = doc.to_warehouse
                s.boe_inbound_no = doc.bill_of_entry
                for i in doc.items:
                    x = s.append("stock_transfer")
                    x.item_code = i.item_code
                    x.target_warehouse = i.t_warehouse
                    x.bom_inbound_qty = i.qty
                    x.balance_in_qty = i.qty
                    x.bom_inbound = doc.bill_of_entry
                    x.serial_no = i.serial_no
                    x.updated_serial_no = i.serial_no
                    x.qty = i.qty
                    x.uom = i.uom
                    x.basic_rate = i.basic_rate
                    x.additional_cost = i.additional_cost
                    x.itemwise_additional_cost = i.itemwise_additional_cost
                    x.valuation_rate = i.valuation_rate
                    x.basic_amount = i.basic_amount
                    x.amount = i.amount
                    x.batch = i.batch_no
                s.save(ignore_permissions=True)

        if doc.stock_entry_type == "Material Transfer" and doc.bom_out_bound:
            s = frappe.new_doc("Stock Transfer India")
            s.boe_outbound_no = doc.bom_out_bound
            for i in doc.items:
                x = s.append("stock_transfer")
                x.item_code = i.item_code
                x.source_warehouse = i.s_warehouse
                x.target_warehouse = i.t_warehouse
                x.bom_outbound_qty = i.qty
                x.balance_out_qty = i.qty
                x.bom_outbound = doc.bom_out_bound
                x.serial_no = i.serial_no
                x.qty = i.qty
                x.uom = i.uom
                x.basic_rate = i.basic_rate
                x.additional_cost = i.additional_cost
                x.itemwise_additional_cost = i.itemwise_additional_cost
                x.valuation_rate = i.valuation_rate
                x.basic_amount = i.basic_amount
                x.amount = i.amount
                x.batch = i.batch_no
            s.save(ignore_permissions=True)
            s = frappe.get_doc("Stock Transfer India",{"boe_inbound_no":doc.bill_of_entry})
            for i in s.stock_transfer:
                for d in doc.items:
                    if d.item_code == i.item_code and i.target_warehouse == "India Bonded Warehouse - NCPL":
                        i.balance_in_qty = i.balance_in_qty - d.qty 
                        # out_list = json.loads(doc.bom_out_bound)
                        # i.outbound_list = out_list
                        if i.updated_serial_no:
                            s_name = (i.updated_serial_no).upper() 
                            ser_name = s_name.split("\n")
                            d_name = (d.serial_no).upper() 
                            sr_name = d_name.split("\n")
                            for k in sr_name:
                                if k in ser_name:
                                    ser_name.remove(k)
                            i.updated_serial_no = ''
                            i.updated_serial_no = "\n".join(ser_name)
            s.save(ignore_permissions=True)

#Reverse the all value while cancel of Stock Entry
@frappe.whitelist()
def reversing_se(doc,method):
    if doc.bill_of_entry and doc.stock_entry_type == "Material Transfer":
        s = frappe.get_doc("Stock Transfer India",{"boe_inbound_no":doc.bill_of_entry})
        for i in s.stock_transfer:
            for d in doc.items:
                if d.item_code == i.item_code and i.target_warehouse == "India Bonded Warehouse - NCPL":
                    i.balance_in_qty = i.balance_in_qty + d.qty 
                    if i.updated_serial_no:
                        s_name = (i.updated_serial_no).upper() 
                        ser_name = s_name.split("\n")
                        d_name = (d.serial_no).upper()
                        sr_name = d_name.split("\n")
                        for k in sr_name:
                            ser_name.append(k)
                            
                        i.updated_serial_no = ''
                        i.updated_serial_no = "\n".join(ser_name)
        s.save(ignore_permissions=True)
        o = frappe.get_doc("Stock Transfer India",{"boe_outbound_no":doc.bom_out_bound})
        o.save(ignore_permissions=True)
        o.delete()
        

    if doc.bill_of_entry and doc.stock_entry_type == "Material Receipt":
        s = frappe.get_doc("Stock Transfer India",{"boe_inbound_no":doc.bill_of_entry})
        s.save(ignore_permissions=True)
        s.delete()

#Add additional cost value in stock entry
def add_itemwise_additional_cost(doc,method):
    for row in doc.items:
        if row.itemwise_additional_cost:
            row.additional_cost += row.itemwise_additional_cost

#Set the value in serial no document while submission of Stock Entry
@frappe.whitelist()
def update_sn(doc,method):
    for i in doc.items:
        if i.serial_no:
            s_name = (i.serial_no).upper() 
            ser_name = s_name.split("\n")
            for sn in ser_name:
                if frappe.db.exists("Serial No",sn):
                    frappe.db.set_value("Serial No",sn,"inbound",doc.bill_of_entry)
                    frappe.db.set_value("Serial No",sn,"outbound",doc.bom_out_bound)          

#Set the value in serial no document while submission of PR
@frappe.whitelist()
def update_sn_pr(doc,method):
    for i in doc.items:
        if i.serial_no:
            s_name = (i.serial_no).upper() 
            ser_name = s_name.split("\n")
            for sn in ser_name:
                if frappe.db.exists("Serial No",sn):
                    frappe.db.set_value("Serial No",sn,"inbound",doc.bill_of_entry)
                    # frappe.db.set_value("Serial No",sn,"outbound",doc.bom_out_bound)               

#Calculate the value ad set to on duty field of Logistics Request
@frappe.whitelist()
def currency_conversion_lg(gt,cr):
    ep = get_exchange_rate(cr,"INR")
    s = float(gt) * float(ep)
    return s

#Set the correct uom in Quotation items
@frappe.whitelist()
def check_uom(item,uom):
    s = frappe.get_doc("Item",item)
    return s.uoms
  
@frappe.whitelist()
def set_inbound(doc,method):
    if doc.bill_of_entry and doc.bom_out_bound:
        if frappe.db.exists("Bill of Entry Outbound",doc.bom_out_bound):
            s = frappe.get_doc("Bill of Entry Outbound",doc.bom_out_bound)
            s.boe_inbound = doc.bill_of_entry
            s.save(ignore_permissions=True)

#Transfer the items in the block warehouse - This method is run on daily
@frappe.whitelist()
def return_blocked_items():
    block = frappe.get_all("Block Warehouse",{"workflow_state":"Transfered"},["*"])
    for i in block:
        days =  add_days(days,15)
        if days > today():
            print(i.name)
            b = frappe.get_doc("Block Warehouse",i.name)
            b.workflow_state = "Returned"
            b.status = "Return"
            stock = frappe.new_doc("Stock Entry")
            stock.company = b.company
            stock.stock_entry_type = "Material Transfer"
            stock.from_warehouse = b.target
            stock.to_warehouse = b.source
            for s in b.items:
                stock.append("items", {
                "s_warehouse":b.target,
                "t_warehouse": b.source,
                "item_code": s.item_code,
                "qty":s.quantity,
                "allow_zero_valuation_rate":1
                })
            stock.save(ignore_permissions=True)
            stock.submit()

#Create the Stock Transfer India while submission of PR
@frappe.whitelist()
def create_stock_transfer_india(doc,method):
    if doc.bill_of_entry != "NA":
        if frappe.db.exists("Stock Transfer India",{"boe_inbound_no":doc.bill_of_entry}):
            s = frappe.get_doc("Stock Transfer India",{"boe_inbound_no":doc.bill_of_entry})
            for i in doc.items:
                x = s.append("stock_transfer")
                x.item_code = i.item_code
                x.item_name = i.item_name
                x.target_warehouse = i.warehouse
                x.bom_inbound_qty = i.received_qty
                x.balance_in_qty = i.received_qty
                x.bom_inbound = doc.bill_of_entry
                x.serial_no = i.serial_no
                x.updated_serial_no = i.serial_no
                x.qty = i.received_qty
                x.uom = i.uom
                x.basic_rate = i.rate
                # x.additional_cost = i.additional_cost
                # x.itemwise_additional_cost = i.itemwise_additional_cost
                # x.valuation_rate = i.valuation_rate
                x.basic_amount = i.amount
                x.amount = i.amount
                x.batch = i.batch_no
            s.save(ignore_permissions=True)
        else:
            s = frappe.new_doc("Stock Transfer India")
            s.boe_inbound_no = doc.bill_of_entry
            for i in doc.items:
                x = s.append("stock_transfer")
                x.item_code = i.item_code
                x.item_name = i.item_name
                x.target_warehouse = i.warehouse
                x.bom_inbound_qty = i.received_qty
                x.balance_in_qty = i.received_qty
                x.bom_inbound = doc.bill_of_entry
                x.serial_no = i.serial_no
                x.updated_serial_no = i.serial_no
                x.qty = i.received_qty
                x.uom = i.uom
                x.basic_rate = i.rate
                # x.additional_cost = i.additional_cost
                # x.itemwise_additional_cost = i.itemwise_additional_cost
                # x.valuation_rate = i.valuation_rate
                x.basic_amount = i.amount
                x.amount = i.amount
                x.batch = i.batch_no
            s.save(ignore_permissions=True)

    if doc.bill_of_entry and doc.boe_outbound:
        s = frappe.new_doc("Stock Transfer India")
        s.boe_outbound_no = doc.boe_outbound
        for i in doc.items:
            x = s.append("stock_transfer")
            x.item_code = i.item_code
            x.item_name = i.item_name
            x.target_warehouse = i.warehouse
            x.bom_inbound_qty = i.received_qty
            x.balance_in_qty = i.received_qty
            x.bom_inbound = doc.bill_of_entry
            x.serial_no = i.serial_no
            x.updated_serial_no = i.serial_no
            x.qty = i.received_qty
            x.uom = i.uom
            x.basic_rate = i.rate
            # x.additional_cost = i.additional_cost
            # x.itemwise_additional_cost = i.itemwise_additional_cost
            # x.valuation_rate = i.valuation_rate
            x.basic_amount = i.amount
            x.amount = i.amount
            x.batch = i.batch_no
        s.save(ignore_permissions=True)
        s = frappe.get_doc("Stock Transfer India",{"boe_inbound_no":doc.bill_of_entry})
        for i in s.stock_transfer:
            ob = []
            out = (i.outbound_list).upper()
            out_name = out.split("\n")
            ob.extend(out_name)
            for d in doc.items:
                if d.item_code == i.item_code and i.target_warehouse == "India Bonded Warehouse - NCPL":
                    i.balance_in_qty = i.balance_in_qty - d.qty 
                    ob.append(doc.boe_outbound)
                    out_list = ob
                    i.outbound_list = "\n".join(out_list)
                    s_name = (i.updated_serial_no).upper() 
                    ser_name = s_name.split("\n")
                    d_name = (d.serial_no).upper() 
                    sr_name = d_name.split("\n")
                    for k in sr_name:
                        if k in ser_name:
                            ser_name.remove(k)
                    i.updated_serial_no = ''
                    i.updated_serial_no = "\n".join(ser_name)
        s.save(ignore_permissions=True)

#Delete the Stock Transfer India document while cancel of the PR
@frappe.whitelist()
def reverse_sti_pr(doc,method):
    if doc.bill_of_entry and doc.bill_of_entry != "NA":
        s = frappe.get_doc("Stock Transfer India",{"boe_inbound_no":doc.bill_of_entry})
        s.save(ignore_permissions=True)
        s.delete()

#Create new stock entry while save of MRP Document only the action is scrap
@frappe.whitelist()
def transfer_to_scrap(doc,method):
    if doc.mrb_action == "Scrap":
        s = frappe.new_doc("Stock Entry")
        s.stock_entry_type = "Material Transfer"   
        s.from_warehouse = doc.warehouse     
        scrap_warehouse = frappe.get_value("Warehouse",{"company":doc.company,"is_scrap":1})
        s.to_warehouse = scrap_warehouse
        for i in s.items:
            i.item_code = doc.item_code
            i.qty = doc.rejected_qty
            i.uom = doc.uom
            i.batch_no = doc.batch_no
            i.basic_rate = doc.rate
        s.save(ignore_permissions=True)

#Show the below details in PO HTML view
@frappe.whitelist()
def po_file_summary(so,mr,supplier,currency,item_details):
    po = frappe.get_all("Purchase Order",{"sales_order_number":so},["*"])
    item_details = json.loads(item_details)
    cus = frappe.get_value("Sales Order",{"name":so},["customer"])
    gt = frappe.get_value("Sales Order",{"name":so},["grand_total"])
    pt = frappe.get_value("Sales Order",{"name":so},["Payment_terms_template"])
    icm = frappe.get_value("Sales Order",{"name":so},["internal_cost_margin"])
    outstanding = frappe.get_all("Sales Invoice",{"customer":cus},["*"])
    s_out = 0
    for i in outstanding:
        if not i.status == "Paid":
            s_out = s_out + i.outstanding_amount
    sq = frappe.db.sql(""" select `tabMaterial Request Item`.item_code as item_code,`tabMaterial Request Item`.sales_order_qty as sales_order_qty,`tabMaterial Request Item`.stock_qty as stock_qty 
    from `tabMaterial Request` left join `tabMaterial Request Item` on `tabMaterial Request`.name = `tabMaterial Request Item`.parent where `tabMaterial Request`.name = '%s' """ %(mr),as_dict=True)
    # so_total = 0
    # s_total = 0
    # for i in sq:
    #     for s in item_details:
    #         if i.item_code == s["item_code"]:
    #             so_total = so_total + i.sales_order_qty * s["rate"]
    #             s_total = s_total + i.stock_qty * s["rate"]
    data = ''
    data+='<table class="table"><style>table,tr,td { padding:5px;border: 1px solid black; font-size:11px;border-color:#e20026;} </style>'
    # data+='<tr><td style="padding:1px;border: 1px solid black;font-size:14px;" colspan=20><center><b>File Summary<b></center></td></tr>'
    data+='<tr style="background-color:lightgrey" ><td style="padding:1px;border: 1px solid black;font-size:14px;border-color:#e20026;" colspan=20><center><b>Customer Details</b></center></td></tr>'
   
    data+='<tr><td style="padding:1px;border: 1px solid black;font-size:14px;width:25%;border-color:#e20026;font-weight:bold;"><center>Name</center></td>'
    data+='<td style="padding:1px;border: 1px solid black;font-size:14px;border-color:#e20026;"><center>%s</center></td>'%(cus)
    data+='<td style="padding:1px;border: 1px solid black;font-size:14px;width:25%;border-color:#e20026;font-weight:bold;"><center>Margin</center></td>'
    data+='<td style="padding:1px;border: 1px solid black;font-size:14px;border-color:#e20026;"><center>%s</center></td>'%(round(icm,2))
    data+='</tr>'

    data+='<tr><td style="padding:1px;border: 1px solid black;font-size:14px;width:25%;border-color:#e20026;font-weight:bold;"><center>Amount</center></td>'
    data+='<td style="padding:1px;border: 1px solid black;font-size:14px;border-color:#e20026;"><center>%s</center></td>' %(gt)
    data+='<td style="padding:1px;border: 1px solid black;font-size:14px;width:25%;border-color:#e20026;font-weight:bold;"><center>Outstanding</center></td>'
    data+='<td style="padding:1px;border: 1px solid black;font-size:14px;border-color:#e20026;"><center>%s</center></td>' %(round(s_out,2))
    data+='</tr>'

    data+='<tr><td style="padding:1px;border: 1px   solid black;font-size:14px;width:25%;border-color:#e20026;font-weight:bold;"><center>Payment Terms</center></td>'
    data+='<td style="padding:1px;border: 1px solid black;font-size:14px;border-color:#e20026;"><center>%s</center></td>' %(pt or '')
    data+='<td style="padding:1px;border: 1px solid black;font-size:14px;width:25%;border-color:#e20026;"><center></center></td>'
    data+='<td style="padding:1px;border: 1px solid black;font-size:14px;width:25%;border-color:#e20026;"><center></center></td>'
    data+='</tr>'

    data+='<tr style="background-color:lightgrey" ><td style="padding:1px;border: 1px solid black;font-size:14px;border-color:#e20026;" colspan=20><center><b>Supplier Details - B2B</b></center></td></tr>'
    
    data+='<tr><td style="padding:1px;border: 1px solid black;font-size:14px;width:25%;border-color:#e20026; font-weight: bold;"><center>Supplier</center></td>'
    data+='<td style="padding:1px;border: 1px solid black;font-size:14px;width:25%;border-color:#e20026; font-weight: bold;"><center>Currency</center></td>'
    data+='<td style="padding:1px;border: 1px solid black;font-size:14px;width:25%;border-color:#e20026; font-weight: bold;"><center>Amount-B2B</center></td>'
    data+='<td style="padding:1px;border: 1px solid black;font-size:14px;width:25%;border-color:#e20026; font-weight: bold;"><center>Payment Terms</center></td>'
    data+='</tr>'

    for i in po:
        pos = frappe.db.sql(""" select `tabPurchase Order Item`.item_code as item_code,`tabPurchase Order Item`.rate as rate
        from `tabPurchase Order` left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent where `tabPurchase Order`.name = '%s' """ %(i.name),as_dict=True)
        sales_total = 0
        for s in pos:
            for r in sq:
                if s.item_code == r.item_code:
                    sales_total = sales_total + r.sales_order_qty * s.rate
        data+='<tr><td style="padding:1px;border: 1px solid black;font-size:14px;border-color:#e20026;"><center>%s</center></td>' %(i.supplier)
        data+='<td style="padding:1px;border: 1px solid black;font-size:14px;border-color:#e20026;"><center>%s</center></td>' %(i.currency)
        data+='<td style="padding:1px;border: 1px solid black;font-size:14px;border-color:#e20026;"><center>%s</center></td>' %(sales_total)
        data+='<td style="padding:1px;border: 1px solid black;font-size:14px;border-color:#e20026;"><center>%s</center></td>' %(i.payment_terms_template or '')
        data+='</tr>'

    data+='<tr style="background-color:lightgrey" ><td style="padding:1px;border: 1px solid black;font-size:14px;border-color:#e20026;" colspan=20><center><b>Supplier Details - Stock</b></center></td></tr>'
    
    data+='<tr><td style="padding:1px;border: 1px solid black;font-size:14px;width:25%;border-color:#e20026; font-weight: bold;"><center>Supplier</center></td>'
    data+='<td style="padding:1px;border: 1px solid black;font-size:14px;width:25%;border-color:#e20026; font-weight: bold;"><center>Currency</center></td>'
    data+='<td style="padding:1px;border: 1px solid black;font-size:14px;width:25%;border-color:#e20026; font-weight: bold;"><center>Amount-Stock</center></td>'
    data+='<td style="padding:1px;border: 1px solid black;font-size:14px;width:25%;border-color:#e20026; font-weight: bold;"><center>Payment Terms</center></td>'
    data+='</tr>'
    for i in po:
        pos = frappe.db.sql(""" select `tabPurchase Order Item`.item_code as item_code,`tabPurchase Order Item`.rate as rate
        from `tabPurchase Order` left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent where `tabPurchase Order`.name = '%s' """ %(i.name or ""),as_dict=True)
        
        stock_total = 0
        for r in sq:
            for s in pos:
                if s.item_code == r.item_code:
                    stock_total = stock_total + r.stock_qty * s.rate
        
        data+='<tr><td style="padding:1px;border: 1px solid black;font-size:14px;border-color:#e20026;"><center>%s</center></td>' %(i.supplier)
        data+='<td style="padding:1px;border: 1px solid black;font-size:14px;border-color:#e20026;"><center>%s</center></td>' %(i.currency)
        data+='<td style="padding:1px;border: 1px solid black;font-size:14px;border-color:#e20026;"><center>%s</center></td>' %(round(stock_total,2))
        data+='<td style="padding:1px;border: 1px solid black;font-size:14px;border-color:#e20026;"><center>%s</center></td>' %(i.payment_terms_template or '')
        data+='</tr>'
    # stock_total = 0

    data+='</table>'
    return data

#Create new document of Item allocation 
@frappe.whitelist()
def item_allocation(item_details,name,company):
    item_details = json.loads(item_details)
    ia = frappe.new_doc("Item Allocation")
    ia.document = "Quotation"
    ia.quotation = name

    for i in item_details:
        sno = frappe.get_all("Serial No",{"item_code":i["item_code"]})
        ia.append('allocation_item',{
            'item_code':i["item_code"],
            'item_name':i["item_name"],
            'qty':i["qty"],
        
        })
            
    ia.save(ignore_permissions = True)
    ai = frappe.get_doc("Item Allocation",{"name":ia.name})
    for i in item_details:
        sno = frappe.get_all("Serial No",{"item_code":i["item_code"]})
        for s in sno:
            for d in ai.allocation_item:
                # s_name = (s.name).upper()
                # name_s = s_name.split("\n")
                frappe.errprint(s.name)
                
            # d.serial_no = "\n".join(name_s)
                
    ai.save(ignore_permissions = True)

    frappe.msgprint("Items Transfered")


    # default_warehouse = frappe.get_value("Warehouse",{"company":company,"default_for_stock_transfer":1})
    # target_warehouse = frappe.get_value("Warehouse",{"company":company,"is_block":1})
    # stock = frappe.new_doc("Stock Entry")
    # stock.company = company
    # stock.stock_entry_type = "Material Transfer"
    # stock.from_warehouse = default_warehouse
    # stock.to_warehouse = target_warehouse
    
    # for i in item_details:
        
    #     stock.append("items", {
    #     "s_warehouse": default_warehouse,
    #     "t_warehouse": target_warehouse,
    #     "item_code": i["item_code"],
    #     "qty":i["qty"],
    #     "allow_zero_valuation_rate":1
    #     })
    # stock.save(ignore_permissions=True)
    
    # stock.submit()

# @frappe.whitelist()
# def cancel_stock():
#     se = frappe.db.sql("""update `tabStock Entry` set docstatus = 1 where name = 'SE-NCMEF-2023-00001' """)

#Create the new document of product testing While save the PR
@frappe.whitelist()
def create_product_testing(doc,method):
    for i in doc.items:
        pt = frappe.new_doc("Product Testing")
        pt.purchase_receipt = i.name
        pt.item_code = i.item_code
        pt.item_name = i.item_name
        pt.qty = i.qty
        pt.serial_no = i.serial_no
        pt.batch_no = i.batch_no
        pt.warehouse = i.rejected_warehouse
        pt.cost_center = i.cost_center
        pt.save(ignore_permissions = True)

#Run this method for every month and update_previous_leave_allocation for the all employees
@frappe.whitelist()
def update_previous_leave_allocation_manually():
    employee = frappe.db.sql(""" select date_of_joining,name from `tabEmployee` where status = 'Active' and employee_number like '1-01-%' and employee_number != "1-01-100" """,as_dict=True)
    current_date = date.today()
    for i in employee:
        rdelta = relativedelta.relativedelta(current_date, i.date_of_joining)
        months = rdelta.years * 12 + rdelta.months
        if months >= 13:
            earned = frappe.db.sql(""" select name from `tabLeave Allocation` where leave_type = 'Earned Leave' and year(from_date) = year(current_date) and employee ='%s' and docstatus =1 """%(i.name),as_dict=True)
            for j in earned:
                earn = frappe.get_doc("Leave Allocation",j.name)
                earn.new_leaves_allocated = earn.new_leaves_allocated + 1
                earn.save(ignore_permissions=True)

            exist = frappe.db.exists("Leave Allocation",{"leave_type":"Earned Leave","employee":i.name,"docstatus":1})
            if not exist:
                new_all = frappe.new_doc("Leave Allocation")
                new_all.employee = i.name
                new_all.new_leaves_allocated = 12
                new_all.leave_type = "Earned Leave"
                new_all.company =frappe.db.get_value("Employee",i.name,["company"])
                new_all.from_date = date.today()
                new_all.to_date = date.today().replace(month=12, day=31)
                new_all.save(ignore_permissions=True)
                new_all.submit()
#Run the update_previous_leave_allocation_manually this mail for every month start date	


#Create leave allocation for the all employees based on below conditions 
from datetime import datetime
import calendar
@frappe.whitelist()
def create_update_leave_allocation():
    employees = frappe.get_all("Employee",{"status":"Active",'Company':'Norden Communication Middle East FZE'},["*"])
    current_date = datetime.now().date()
    for emp in employees:
        doj = emp.date_of_joining
        diff = current_date - doj
        years = diff.days / 365.25  
        print(int(years))
        if(int(years)) > 0 :
            if frappe.db.exists("Leave Allocation",{'employee':emp.employee,'leave_type':"Annual Leave"}):
                la = frappe.get_doc("Leave Allocation",{'employee':emp.employee,'leave_type':"Annual Leave"},["*"])
                la.new_leaves_allocated = la.new_leaves_allocated + 2.5
                # la.to_date = "2100-12-31"
                la.save(ignore_permissions=True)
                la.submit()   
            else:
                la = frappe.new_doc("Leave Allocation")
                la.employee = emp.name
                la.leave_type = "Annual Leave"
                la.new_leaves_allocated = 2.5
                la.from_date = current_date
                la.to_date = "2100-12-31"
                la.save(ignore_permissions=True)
                la.submit()  


  
#Get the details for expiry annual leave 
import frappe
from datetime import datetime, timedelta , date
@frappe.whitelist()
def annual_leave_expired():
    employees = frappe.get_all("Employee",{'status':"Active","company":"Norden Communication Middle East FZE"},['*'])
    for emp in employees:
        if frappe.db.exists("Leave Allocation",{'employee':emp.name,'leave_type':"Annual Leave","docstatus":1}):
            today = date.today()
            leave = frappe.get_doc("Leave Allocation",{'employee':emp.name,'leave_type':"Annual Leave","docstatus":1})
            if leave.expiry_date == today:
                application = frappe.db.sql("""select * from `tabLeave Application` where  leave_type = 'Annual leave' and docstatus = 1 and from_date = '%s' and to_date = '%s' """%(leave.leave_start_date,leave.expiry_date),as_dict=1)[0]
                total = 0
                for a in application:
                    total = a.total_leave_days
                if leave.expire_from > total :
                    el = leave.expire_from - total
                    leave.new_leaves_allocated = leave.new_leaves_allocated - el
                    leave_end_date = str(leave.leave_end_date)
                    do = datetime.strptime(leave_end_date, '%Y-%m-%d')
                    add_do = do + timedelta(days=1)
                    add_do_str = add_do.strftime("%Y-%m-%d")
                    add_date = datetime.strptime(add_do_str, '%Y-%m-%d').date()
                    leave.leave_start_date = add_date
                    leave_end_date = str(leave.leave_end_date)
                    do = datetime.strptime(leave_end_date, '%Y-%m-%d')
                    add_do = do + timedelta(months=12)
                    add_do_str = add_do.strftime("%Y-%m-%d")
                    add_date = datetime.strptime(add_do_str, '%Y-%m-%d').date()
                    leave.leave_end_date = add_date
                    leave_end_date = str(leave.leave_end_date)
                    do = datetime.strptime(leave_end_date, '%Y-%m-%d')
                    add_do = do + timedelta(year=1) + timedelta(months=6)
                    add_do_str = add_do.strftime("%Y-%m-%d")
                    add_date = datetime.strptime(add_do_str, '%Y-%m-%d').date()
                    leave.expiry_date = add_date
                    leave.expire_from = 30
                    leave.save(ignore_permissions = True)
                    frappe.db.commit


#Set the reservation status in Sales Order
@frappe.whitelist()
def empty_reserve_status():
    list = frappe.db.get_list("Sales Order",{'docstatus':1,'custom_reservation_status':"Reserved"},['name'])
    for i in list:
        reservations = frappe.db.get_list("Stock Reservation Entry",{"voucher_no":i.name,"docstatus":1},['name','status'])
        all_delivered = all(reservation["status"] == "Delivered" for reservation in reservations)
        if all_delivered:
            frappe.db.set_value("Sales Order",i.name,'custom_reservation_status',"",update_modified=False)
        else:
            frappe.db.set_value("Sales Order",i.name,'custom_reservation_status',"Reserved",update_modified=False)



#Upload the below file and set the value for Sales Order Items
@frappe.whitelist()  
def si_name(filename):
    from frappe.utils.file_manager import get_file
    _file = frappe.get_doc("File", {"file_name":filename})
    filepath = get_file(filename)
    ips = read_csv_content(filepath[1])
    for ip in ips:
        sales_invoice = ip[0]
        si_name = frappe.get_doc("Sales Invoice",sales_invoice)
        for s in si_name.items:
            sales = s.sales_order
            so_name = frappe.get_doc("Sales Order",sales)
            for si in so_name.items:
                quote = si.prevdoc_docname
        print(sales_invoice)
        print(sales)
        print(quote)
        if quote:
            quote_update = frappe.get_doc("Quotation",quote)
            for quo in quote_update.items:
                disc_amt = quo.discount_rate * quo.qty
            # 	# frappe.db.set_value("Sales Order Item", {"parent":i.parent,"item_code":k.item_code}, 'unit_price_document_currency', k.unit_price_document_currency)
            # 	# frappe.db.set_value("Sales Order Item", {"parent":i.parent,"item_code":k.item_code}, 'discount_value', k.discount_value)
                frappe.db.set_value("Quotation Item", {"parent":quote,"item_code":quo.item_code}, 'disc_amt', disc_amt)
            # 	# frappe.db.set_value("Sales Order Item", {"parent":i.parent,"item_code":k.item_code}, 'disc_amt', disc_amt)
        if sales:
            sale = frappe.get_doc("Sales Order",sales)
            for sa in sale.items:
                quot = frappe.get_doc("Quotation",sa.prevdoc_docname)
                for qu in quot.items:
                    if sa.item_code == qu.item_code:
                        frappe.db.set_value("Sales Order Item", {"parent":sales,"item_code":qu.item_code}, 'discount_value', qu.discount_value)
                        frappe.db.set_value("Sales Order Item", {"parent":sales,"item_code":qu.item_code}, 'discount', qu.discount)
                        frappe.db.set_value("Sales Order Item", {"parent":sales,"item_code":qu.item_code}, 'discount_rate', qu.discount_rate)
                        frappe.db.set_value("Sales Order Item", {"parent":sales,"item_code":qu.item_code}, 'disc_amt', qu.disc_amt)
                        if qu.unit_price_document_currency:
                            frappe.db.set_value("Sales Order Item", {"parent":sales,"item_code":qu.item_code}, 'unit_price_document_currency', qu.unit_price_document_currency)
        if sales:
            sale_in = frappe.get_doc("Sales Invoice",sales_invoice)
            for sin in sale_in.items:
                so_ord = frappe.get_doc("Sales Order",sin.sales_order)
                for sd in so_ord.items:
                    if sin.item_code == sd.item_code:
                        if sd.unit_price_document_currency:
                            frappe.db.set_value("Sales Invoice Item", {"parent":sales_invoice,"item_code":sd.item_code}, 'unit_price_document_currency', sd.unit_price_document_currency)
                        frappe.db.set_value("Sales Invoice Item", {"parent":sales_invoice,"item_code":sd.item_code}, 'discount', sd.discount)
                        frappe.db.set_value("Sales Invoice Item", {"parent":sales_invoice,"item_code":sd.item_code}, 'discount_rate', sd.discount_rate)
                        frappe.db.set_value("Sales Invoice Item", {"parent":sales_invoice,"item_code":sd.item_code}, 'discount_value', sd.discount_value)
                        frappe.db.set_value("Sales Invoice Item", {"parent":sales_invoice,"item_code":sd.item_code}, 'disc_amt', sd.disc_amt)

#Bulk upload the given file for item price
@frappe.whitelist()  
def item_price_bulk_upload_csv(filename):
    from frappe.utils.file_manager import get_file
    _file = frappe.get_doc("File", {"file_name":filename})
    filepath = get_file(filename)
    ips = read_csv_content(filepath[1])
    no_item = ["HI"]
    for ip in ips:
        if frappe.db.exists('Item Price',{'item_code':ip[0]}):
            if frappe.db.exists('Item Price',{'item_code':ip[0],'price_list':"Cost Rate - NCMEF"}):
                rate = frappe.get_doc('Item Price',{'item_code':ip[0],'price_list':"Cost Rate - NCMEF"})
                print(rate.price_list_rate)
                rate.price_list_rate = ip[2]
            
            if frappe.db.exists('Item Price',{'item_code':ip[0],'price_list':"Landing - NCMEF"}):
                rate = frappe.get_doc('Item Price',{'item_code':ip[0],'price_list':"Landing - NCMEF"})
                print(rate.price_list_rate)
                rate.price_list_rate = ip[3]
            
            if frappe.db.exists('Item Price',{'item_code':ip[0],'price_list':"Incentive - NCMEF"}):
                rate = frappe.get_doc('Item Price',{'item_code':ip[0],'price_list':"Incentive - NCMEF"})
                print(rate.price_list_rate)
                rate.price_list_rate = ip[4]
            
            if frappe.db.exists('Item Price',{'item_code':ip[0],'price_list':"Internal - NCMEF"}):
                rate = frappe.get_doc('Item Price',{'item_code':ip[0],'price_list':"Internal - NCMEF"})
                print(rate.price_list_rate)
                rate.price_list_rate = ip[5]
            
            if frappe.db.exists('Item Price',{'item_code':ip[0],'price_list':"Base Sales Price - NCMEF"}):
                rate = frappe.get_doc('Item Price',{'item_code':ip[0],'price_list':"Base Sales Price - NCMEF"})
                print(rate.price_list_rate)
                rate.price_list_rate = ip[6]
            
            if frappe.db.exists('Item Price',{'item_code':ip[0],'price_list':"Retail - NCMEF"}):
                rate = frappe.get_doc('Item Price',{'item_code':ip[0],'price_list':"Retail - NCMEF"})
                print(rate.price_list_rate)
                rate.price_list_rate = ip[7]
            
            if frappe.db.exists('Item Price',{'item_code':ip[0],'price_list':"Dist. Price - NCMEF"}):
                rate = frappe.get_doc('Item Price',{'item_code':ip[0],'price_list':"Dist. Price - NCMEF"})
                print(rate.price_list_rate)
                rate.price_list_rate = ip[8]
            
            if frappe.db.exists('Item Price',{'item_code':ip[0],'price_list':"Electra Qatar - NCMEF"}):
                rate = frappe.get_doc('Item Price',{'item_code':ip[0],'price_list':"Electra Qatar - NCMEF"})
                print(rate.price_list_rate)
                rate.price_list_rate = ip[9]
            
            if frappe.db.exists('Item Price',{'item_code':ip[0],'price_list':"Project Group - NCMEF"}):
                rate = frappe.get_doc('Item Price',{'item_code':ip[0],'price_list':"Project Group - NCMEF"})
                print(rate.price_list_rate)
                rate.price_list_rate = ip[10]
            
            if frappe.db.exists('Item Price',{'item_code':ip[0],'price_list':"Saudi Dist. - NCMEF"}):
                rate = frappe.get_doc('Item Price',{'item_code':ip[0],'price_list':"Saudi Dist. - NCMEF"})
                print(rate.price_list_rate)
                rate.price_list_rate = ip[11]
        else:
            no_item.append(lis)
    frappe.log_error(title="No Item",message=no_item)

#Get the purchase receipt and cancel it		
def cancel_po():
    doc = frappe.get_doc('Purchase Receipt',"PR-NCPLP-2023-00034")
    doc.flags.ignore_validate = True
    doc.cancel()
    frappe.db.commit()




# def create_hooks_mark_ot():
#     job = frappe.db.exists('Scheduled Job Type', 'check_se_and_send_mail_quote')
#     if not job:
#         sjt = frappe.new_doc("Scheduled Job Type")
#         sjt.update({
#             "method": 'norden.custom.check_se_and_send_mail_quote',
#             "frequency": 'Cron',
#             "cron_format": '0 2 * * *'
#         })
#         sjt.save(ignore_permissions=True)


#Get the quotation item to match with given quotation
@frappe.whitelist()
def get_detailed_quo(quotation):
    quo = frappe.get_doc("Quotation",quotation)
    return quo.items

#Get the sales order item to match with given so
@frappe.whitelist()
def get_detailed_so(sales_order):
    so = frappe.get_doc("Sales Order",sales_order)
    return so.items

#For downloading item table as excel
@frappe.whitelist()
def make_item_sheet():
    args = frappe.local.form_dict
    filename = args.name
    test = build_xlsx_response(filename)

def make_xlsx(data, sheet_name=None, wb=None, column_widths=None):
    args = frappe.local.form_dict
    column_widths = column_widths or []
    if wb is None:
        wb = openpyxl.Workbook()
    ws = wb.create_sheet(sheet_name, 0)
    doc = frappe.get_doc("Quotation",args.name)
    if doc:
        ws.append(["Item Code","Item Name","Qty","Unit Rate","Margin Percentage","Margin Rate","Margin Value","Discount","Discount Rate","Discount Value","Discount Amount","Amount"])
        for i in doc.items:
            ws.append([i.item_code,i.item_name,i.qty,i.unit_price_document_currency,i.margin_percentage,i.margin_rate,i.margin_value,i.discount,i.discount_rate,i.discount_value,i.disc_amt,i.amount])
    xlsx_file = BytesIO()
    wb.save(xlsx_file)
    return xlsx_file

def build_xlsx_response(filename):
    xlsx_file = make_xlsx(filename)
    frappe.response['filename'] = filename + '.xlsx'
    frappe.response['filecontent'] = xlsx_file.getvalue()
    frappe.response['type'] = 'binary' 	

#Get the salary structure assignment for the given employee
@frappe.whitelist()
def get_salary_structure_assignment_base(employee,docstatus):
    assignment = frappe.get_value(
        "Salary Structure Assignment",
        filters={
            "employee": employee,
            "docstatus": 1  # Consider only submitted assignments
        },
        fieldname="base",
        order_by="creation DESC",
        
    )

    return assignment or 0.0
#Show the electra items details in product search
@frappe.whitelist(allow_guest=True)
def get_electra_item(item):
    url = "http://13.234.40.9/api/method/electra.custom.get_norden_details?item=%s" % (item)
    headers = { 'Content-Type': 'application/json','Authorization': 'token 583681db58de9d7:c9fc006b5b31cef'}
    # params = {"limit_start": 0,"limit_page_length": 20000}

    try:
        response = requests.request('GET',url,headers=headers,timeout=10)
        res = json.loads(response.text)
    except Exception:
        frappe.log_error(frappe.get_traceback(),"Electra item lookup failed")
        res = {"message":"<p>Electra server is unreachable. Please try again later.</p>"}
    return res

#Show the electra items details in product search
@frappe.whitelist(allow_guest=True)
def electra_item(item):
    url = "http://13.234.40.9/api/method/electra.custom.norden_details?item=%s" % (item)
    headers = { 'Content-Type': 'application/json','Authorization': 'token 583681db58de9d7:c9fc006b5b31cef'}
    # params = {"limit_start": 0,"limit_page_length": 20000}

    try:
        response = requests.request('GET',url,headers=headers,timeout=10)
        res = json.loads(response.text)
    except Exception:
        frappe.log_error(frappe.get_traceback(),"Electra item lookup failed")
        res = {"message":"<p>Electra server is unreachable. Please try again later.</p>"}
    return res


#Get the basic details for given item details with company and show in quotation
@frappe.whitelist()
def get_basic_details(item_code,company):
    data = ''
    data+= '<br><table width = "100%"><style>td { text-align:left } table,tr,td { padding:5px;border: 1px solid black; font-size:11px;} </style>'

    data+=	'<tr><td ><b>ITEM CODE</b></td>'
    data += '<td align = "center" ><b>%s</b></td>' %(item_code)
    
    stocks = frappe.db.sql("""select sum(`tabBin`.actual_qty) as actual_qty from `tabBin`
                            join `tabWarehouse` on `tabWarehouse`.name = `tabBin`.warehouse
                            join `tabCompany` on `tabCompany`.name = `tabWarehouse`.company
                            where `tabBin`.item_code = '%s' and `tabWarehouse`.company = '%s' """ % (item_code,company), as_dict=True)[0]
 
    if not stocks['actual_qty']:
            stocks['actual_qty'] = 0
   
    if stocks["actual_qty"] > 0:
        data += '<tr><td ><b> TOTAL STOCK</b></td>'
        data += '<td align = "center" ><b>%s</b></td>' %(stocks["actual_qty"])
  
    all_qty = frappe.db.sql("""select sum(reserved_stock) as actual_qty from `tabBin`
                            join `tabWarehouse` on `tabWarehouse`.name = `tabBin`.warehouse
                            join `tabCompany` on `tabCompany`.name = `tabWarehouse`.company
                            where `tabBin`.item_code = '%s' and `tabWarehouse`.company = '%s' """ % (item_code,company), as_dict=True)[0]
    if not all_qty['actual_qty']:
            all_qty['actual_qty'] = 0


    data += '<tr><td ><b>RESERVED QTY</b></td>'
    data += '<td align = "center" ><b>%s</b></td>' %(all_qty['actual_qty'])
    
    
    free_qty = stocks["actual_qty"] - all_qty['actual_qty']
    data += '<tr><td ><b>FREE QTY</b></td>'
    data += '<td align = "center" ><b>%s</b></td>' %(free_qty)
 
    
    new_po = frappe.db.sql("""select sum(`tabPurchase Order Item`.qty) as qty,sum(`tabPurchase Order Item`.received_qty) as d_qty from `tabPurchase Order`
        left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
        where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus = 1 and `tabPurchase Order`.company = '%s' and `tabPurchase Order Item`.qty >= `tabPurchase Order Item`.received_qty """ % (item_code,company), as_dict=True)[0]
    if not new_po['qty']:
        new_po['qty'] = 0
    if not new_po['d_qty']:
        new_po['d_qty'] = 0
    ppoc_total = new_po['qty'] - new_po['d_qty']

    data += '<tr><td ><b>PURCHASE ORDER QTY</b></td>'
    data += '<td align = "center" ><b>%s</b></td>' %(ppoc_total)
 
    new_so = frappe.db.sql("""select sum(`tabSales Order Item`.qty) as qty,sum(`tabSales Order Item`.delivered_qty) as d_qty from `tabSales Order`
            left join `tabSales Order Item` on `tabSales Order`.name = `tabSales Order Item`.parent
            where `tabSales Order Item`.item_code = '%s' and company = '%s' """ % (item_code,company), as_dict=True)[0]
    if not new_so['qty']:
        new_so['qty'] = 0
    if not new_so['d_qty']:
        new_so['d_qty'] = 0
    so_qty = new_so['qty'] - new_so['d_qty']
    
    data += '<tr><td ><b>SALES ORDER QTY</b></td>'
    data += '<td align = "center" ><b>%s</b></td>' %(so_qty)
 
    data += '</table>'
    return data

#Show the below details in Picking List Print format in Sales order
@frappe.whitelist()
def stock_detail(doc):
    item_details = doc.items
    data = ''
    data += '<h4><center><b>NON AVAILABLE ITEMS</b></center></h4>'
    data += '<table class="table table-bordered">'
    data += '<tr>'
    data += '<td colspan=1 style="width:13%;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e20026;color:white;"><center><b>ITEM CODE</b></center></td>'
    data += '<td colspan=1 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e20026;color:white;"><center><b>ITEM NAME</b></center></td>'
    data += '<td colspan=1 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e20026;color:white;"><center><b>ORDERED QTY</b></center></td>'
    data += '<td colspan=1 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e20026;color:white;"><center><b>NON AVAILABLE QTY</b></center></td></tr>'
    for j in item_details:
        
        
        st = 0
        ware = frappe.db.get_list("Warehouse",{"company":doc.company,"custom_stock_is_shown_only_in_product_search":0},['name'])
        for w in ware:
            sto = frappe.db.get_value("Bin",{"item_code":j.item_code,"warehouse":w.name},['actual_qty'])
            if sto and sto>0:
                st+=sto
                
        if st < j.qty:
            a=j.qty-st
            data += '<tr><td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' %(j.item_code)
            data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' %(j.item_name)
            data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' %(j.qty)
        
            data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' %(a)
        
    data += '</tr>'
    data += '</table>'
    return data

#Get the available details for UAE and showing the details for Quotation
@frappe.whitelist()
def stock_uae(item_details,company):
    item_details = json.loads(item_details)
    data = ''
    data += '<h4><center><b>STOCK DETAILS - UAE</b></center></h4>'
    data += '<table class="table table-bordered">'
    data += '<tr>'
    data += '<td colspan=1 style="width:13%;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>ITEM CODE</b></center></td>'
    data += '<td colspan=1 style="width:33%;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>ITEM NAME</b></center></td>'
    data += '<td colspan=1 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>DESCRIPTION</b></center></td>'
    data += '<td colspan=1 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>UNIT</b></center></td>'
    data += '<td colspan=1 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>RESERVED QTY</b></center></td>'
    data += '<td colspan=1 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>FREE QTY</b></center></td>'
    data += '<td colspan=1 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e35310;color:white;"><center><b>PO QTY</b></center></td>'
    for j in item_details:
        stocks = frappe.db.sql("""select sum(`tabBin`.actual_qty) as actual_qty from `tabBin`
                            join `tabWarehouse` on `tabWarehouse`.name = `tabBin`.warehouse
                            join `tabCompany` on `tabCompany`.name = `tabWarehouse`.company
                            where `tabBin`.item_code = '%s' and `tabWarehouse`.company = '%s' and `tabWarehouse`.custom_stock_is_shown_only_in_product_search = 0 """ % (j["item_code"],company), as_dict=True)[0]
        
        if not stocks['actual_qty']:
            stocks['actual_qty'] = 0
            
        all_qty = frappe.db.sql("""select sum(reserved_stock) as actual_qty from `tabBin`
                            join `tabWarehouse` on `tabWarehouse`.name = `tabBin`.warehouse
                            join `tabCompany` on `tabCompany`.name = `tabWarehouse`.company
                            where `tabBin`.item_code = '%s' and `tabWarehouse`.company = '%s' and `tabWarehouse`.custom_stock_is_shown_only_in_product_search = 0 """ % (j["item_code"],company), as_dict=True)[0]
        if not all_qty['actual_qty']:
            all_qty['actual_qty'] = 0

        
        free_qty = stocks["actual_qty"]-all_qty['actual_qty']

        new_po = frappe.db.sql("""select sum(`tabPurchase Order Item`.qty) as qty,sum(`tabPurchase Order Item`.received_qty) as d_qty from `tabPurchase Order`
        left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
        where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus = 1 and `tabPurchase Order`.company = '%s' and `tabPurchase Order Item`.qty >= `tabPurchase Order Item`.received_qty """ % (j["item_code"],company), as_dict=True)[0]
        if not new_po['qty']:
            new_po['qty'] = 0
        if not new_po['d_qty']:
            new_po['d_qty'] = 0
        ppoc_total = new_po['qty'] - new_po['d_qty']
     
        data += '<tr>'
        data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' % (j["item_code"])
        data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' % (j["item_name"])
        data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' % (j["description"])
        data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' % (j["uom"])
        data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' % (all_qty['actual_qty'] or 0)
        data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' % (free_qty or 0)
        data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' % (ppoc_total or 0)
        data += '</tr>'
    data += '</table>'
    return data
#Revert the reservation entry while save the 	Stock Reservation Entry
@frappe.whitelist()
def update_reserve_status(doc,method):
    if doc.voucher_type == "Sales Order":
        frappe.db.set_value(doc.voucher_type,doc.voucher_no,'custom_reservation_status',"Reserved")

#Revert the reservation entry while cancel the 	Stock Reservation Entry
@frappe.whitelist()
def revert_reserve_status(doc,method):
    if doc.voucher_type == "Sales Order":
        frappe.db.set_value(doc.voucher_type,doc.voucher_no,'custom_reservation_status',"")
    list = frappe.db.exists("Stock Reservation Entry",{'docstatus':1,'voucher_no':doc.voucher_no})
    if list:
        frappe.db.set_value(doc.voucher_type,doc.voucher_no,'custom_reservation_status',"Reserved")

#Get the all territory and Get the target amount for the given territory
@frappe.whitelist()
def update_target():
    processed_territories = set()
    target_invoices = frappe.get_all("Sales Invoice", {'company': "Norden Singapore PTE LTD"}, ['territory'])

    for invoice in target_invoices:
        territory = invoice.get('territory')
        if territory and territory not in processed_territories:
            target_value = frappe.db.get_value("Target Detail", {'parent': territory}, 'target_amount')
            if target_value is not None:
                print(territory, target_value)
                processed_territories.add(territory)

#Get the below details from GL Entry
@frappe.whitelist()
def gross_net():
    total=0
    to_net=0
    gross = frappe.get_all("GL Entry",{'company':'Norden Communication Pvt Ltd','account':'Sales - NCPL'},['credit'])
    for i in gross:
        total +=i.credit
    print(total)
    net = frappe.get_all("GL Entry",{'company':'Norden Communication Pvt Ltd'},['credit','account'])
    for i in net:
        if i.account == 'Cost of Goods Sold - NCPL':
            to_net +=i.credit
    print(to_net)
    print(to_net-total)

#Get the below details from Stock Ledger Entry
@frappe.whitelist()
def sub_group():
    bal_qty = 0.0
    from_date = '2023-11-09'
    to_date = '2023-12-09'
    unique_item_codes = set()
    values = frappe.get_all("Stock Ledger Entry", {'is_cancelled': '0', 'company': 'Norden Communication Pvt Ltd', 'posting_date': ('between', [from_date, to_date])}, ['actual_qty', 'qty_after_transaction', 'item_code'])
    for i in values:
        item_code = i.item_code
        unique_item_codes.add(item_code)   
        if i.actual_qty <0:
            out_qty += i.actual_qty
        if i.actual_qty < 0:
            in_qty += i.actual_qty
    total_count = len(unique_item_codes)
    print(total_count)

#Get the PO No
@frappe.whitelist()
def get_pr_po_no(bill):
    pr = frappe.db.get_value("Purchase Receipt",{"bill_of_entry":bill,"docstatus":1},["name"])
    order = frappe.db.get_value("Purchase Receipt",{"bill_of_entry":bill,"docstatus":1},["purchase_order_no"])
    return pr,order

#Sent the mail for the Probation End Period Employee Details 
@frappe.whitelist()
def probation_to_confirmation():
    data = ''
    employee = frappe.get_all('Employee', {'status': 'Active', 'custom_employee_category': 'Probation', 'company': 'Norden Communication Middle East FZE'}, [
                              "name", "employee_name", "department", "date_of_joining"])
    data += 'Dear Mam,<br>Kindly Find the List of Employees going to complete their Probation With in 7 Days.<br><table class="table table-bordered">'
    data += '<table class="table table-bordered"><tr><th>Employee ID</th><th>Employee Name</th><th>Department</th><th>Date of Joining</th></tr>'
    for emp in employee:
        diff = date_diff(emp.date_end_of_joining, today())
        if (diff <= 7 and diff >= 0):
            
            data += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
                emp.name, emp.employee_name, emp.department, format_date(emp.date_of_joining))
    data += '</table>'
    frappe.sendmail(
        # recipients=["gayathri.r@groupteampro"],
        subject=('Probation Completion Remainder Mail'),
        header=('Probation End Period Employee Details'),
        message=data
    )

probation_to_confirmation()

#Sent the leave expiry  mail
@frappe.whitelist()
def annual_leave_expiry():
    employees = frappe.get_all('Employee', 
                               {'status': 'Active', 'company': 'Norden Communication Middle East FZE'}, 
                               ["name", "employee_name", "department", "date_of_joining",'company_email'])
    for emp in employees:
        diff = date_diff(add_months(emp.date_of_joining, 18), today())
        if diff == 0:
            print("hi")
            if emp.company_email:
                send_leave_expiry_mail(emp.employee_name, emp.date_of_joining, emp.company_email)

        elif diff == 30:
            print("hello")
            if emp.company_email:
                send_leave_expiry_reminder_mail(emp.employee_name, emp.date_of_joining,emp.company_email)
#Sent the leave expiry  mail
def send_leave_expiry_mail(employee_name, date_of_joining,email_id):
    subject = 'Annual Leave Expiry - Leave Expired'
    message = f'Dear {employee_name},\n\nYour annual leave has expired as of {format_date(date_of_joining)}.\n\nPlease contact HR for further assistance.'
    
    send_mail(subject, message,email_id)

#Sent the leave expiry remainder mail
def send_leave_expiry_reminder_mail(employee_name, date_of_joining,email_id):
    subject = 'Annual Leave Expiry - 1st Reminder'
    message = f'Dear {employee_name},\n\nThis is a reminder that your annual leave will expire in 1 month, on {format_date(add_months(date_of_joining, 18))}.\n\nPlease plan accordingly.'
    
    send_mail(subject, message, email_id)

def send_mail(subject, message, email_id):
    frappe.sendmail(
        recipients=[email_id],
        subject=subject,
        message=message
    )

from datetime import datetime

#Send the remainder the below format for allocate the annual leaves
@frappe.whitelist()
def annual_leave_due():
    employees = frappe.get_all('Employee', 
                               {'status': 'Active', 'company': 'Norden Communication Middle East FZE'}, 
                               ["name", "employee_name", "department", "date_of_joining"])

    for emp in employees:
        date_of_joining = frappe.utils.get_datetime(emp.date_of_joining).date()  # Convert string to date object
        today_date = frappe.utils.now_datetime().date()  # Convert today to date object
        months_since_joining = month_diff(date_of_joining, today_date)

        if months_since_joining == 10:
            # 10 months after joining date - First reminder
            send_annual_leave_due_reminder(emp.employee_name, date_of_joining, "first")

        elif months_since_joining == 11:
            # 11 months after joining date - Second reminder
            send_annual_leave_due_reminder(emp.employee_name, date_of_joining, "second")

        elif months_since_joining == 12:
            # 1 year after joining date - 3rd reminder
            send_annual_leave_due_reminder(emp.employee_name, date_of_joining, "third")

#Reminder for allocate the annual leave
def send_annual_leave_due_reminder(employee_name, date_of_joining, reminder_type):
    subject = f'Annual Leave Due Reminder - {reminder_type.capitalize()} Reminder'
    message = f'Dear {employee_name},\n\nThis is your {reminder_type} reminder to allocate your annual leave. You joined our company on {format_date(date_of_joining)}, and it is essential to plan your leave accordingly.\n\nPlease contact HR for leave allocation.'
    send_mail(subject, message)

def send_mail(subject, message):
    frappe.sendmail(
        # recipients=["gayathri.r@groupteampro.com"],
        # cc=["sobha123@gmail.com"],
        subject=subject,
        message=message
    )

#Get the month different
def month_diff(start_date, end_date):
    return (end_date.year - start_date.year) * 12 + end_date.month - start_date.month

annual_leave_due()

#This message sent to Teampro
@frappe.whitelist()
def send_mail_to_teampro(subject, message, recipients, sender):
    """
    Send an email to the specified recipients with the given subject and message.
    """
    if not frappe.db.exists("Email Account", {"email_id": sender}):
        frappe.throw(_("Sender email not configured in Email Account"))

    # Add additional content to the message body
    message_body = f"Dear Sir/Madam,<br><br>\
                    Greetings from Norden!!<br><br>\
                    Hope this mail finds you well!!<br><br>\
                    {message}<br><br>\
                    Thanks & Regards,<br>\
                    Norden Support"

    try:
        frappe.sendmail(
            recipients=recipients,
            sender=sender,
            subject=subject,
            message=message_body,
            now=True
        )
        return "Email sent successfully"
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Email Sending Failed')
        return "Failed to send email"

#Get the Bin name to match with below conditions
@frappe.whitelist()
def bin_value():
    bin = frappe.db.get_value("Bin",{"item_code":"1335-M201BK","warehouse":"Main Stores - NCME"},["name"])
    print(bin)

#Get the manufacture serial no 
@frappe.whitelist()
def serial_manufacture():
    sabb = frappe.db.get_list("Serial and Batch Bundle",{'has_serial_no':1},['name','voucher_type','voucher_no'])
    for i in sabb:
        if i.voucher_type == "Stock Entry":
            typ = frappe.db.get_value("Stock Entry",i.voucher_no,'stock_entry_type')
            if typ =="Manufacture":
                print(i.name)


#Sent the remainder for Work Anniversary
@frappe.whitelist()
def work_anniversary_remainder():
    data = ''
    employees = frappe.get_all('Employee', {'status': 'Active', 'company': 'Norden Communication Middle East FZE'}, [
                              "name", "employee_name", "department", "date_of_joining"])
    data += _(" Dear Mam,<br>A friendly reminder of important dates for our team.")
    data += "<br>"
    data += _("Let’s congratulate them on their work anniversary!")
    data += '<table class="table table-bordered"><tr><th>Employee ID</th><th>Employee Name</th><th>Department</th><th>Date of Joining</th><th>Work Anniversary Completed</th></tr>'

    for emp in employees:
        anniversary_completed_year = calculate_anniversary_years(emp.date_of_joining)
        if anniversary_completed_year in [5, 10, 15, 20]:
            row_data = send_notification_before_anniversary(emp, anniversary_completed_year)
            if row_data:
                data += row_data

    data += '</table>'

    if data != '':
        frappe.sendmail(
            # recipients=["gayathri.r@groupteampro.com"],
            subject=("Work Anniversary Reminder"),
            header=('Anniversary Wishes!!'),
            message=data
        )

# calculate the work anniversary years
def calculate_anniversary_years(joining_date):
    today_date = date.today()
    diff_years = today_date.year - joining_date.year
    return diff_years

#Sent the notification for work anniversary mail
def send_notification_before_anniversary(emp, anniversary_completed_year):
    return '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
        emp.name, emp.employee_name, emp.department, format_date(emp.date_of_joining), anniversary_completed_year)

work_anniversary_remainder()

#Update the Price rate for STANDARD BUYING-USD Item price for the LME Items
@frappe.whitelist()
def update_lme(per_change):
    sub_groups = frappe.get_all("Item Sub Group", {'has_lme': 1}, ['name'])
    for sub_group in sub_groups:
        price_list = frappe.get_all("Item Price",{"item_sub_group": sub_group.name, "price_list": "STANDARD BUYING-USD"},['name', 'price_list_rate'])
        for entry in price_list:
            new_price = entry.price_list_rate + ( entry.price_list_rate * float(per_change)) / 100
            frappe.db.set_value("Item Price", entry.name, "price_list_rate", new_price)

#This is Enqueue job for LME Percentage Calculation
@frappe.whitelist()    
def enqueue_update_lme(per_change):
    frappe.enqueue(
        update_lme, 
        queue="long", 
        timeout=80000, 
        is_async=True,
        now=False,
        job_name='LME Percentage Calculation',
        per_change=per_change,
    ) 
    return "Prices updated successfully"


# @frappe.whitelist()
# def getval():
# 	frappe.errprint(frappe.db.get_value("Journal Entry","JE-NSPL-2024-00005","naming_series"))


# @frappe.whitelist()
# def update_previous_leave_allocation():
# 	employee = frappe.db.sql(""" select date_of_joining,name from `tabEmployee` where status = 'Active' and employee_number like '1-01-%' and employee_number != "1-01-100" """,as_dict=True)
# 	current_date = datetime.strptime("2024-04-01", "%Y-%m-%d").date()
    
# 	for i in employee:
# 		rdelta = relativedelta.relativedelta(current_date, i.date_of_joining)
# 		months = rdelta.years * 12 + rdelta.months
# 		if months >= 13:
# 			earned = frappe.db.sql(""" select name from `tabLeave Allocation` where leave_type = 'Earned Leave' and year(from_date) = year(current_date) and employee ='%s'  """%(i.name),as_dict=True)
# 			for j in earned:
                
# 				earn = frappe.get_doc("Leave Allocation",j.name)
# 				earn.new_leaves_allocated = earn.new_leaves_allocated + 1
# 				earn.save(ignore_permissions=True)
# 				frappe.db.commit()

# 			# exist = frappe.db.exists("Leave Allocation",{"leave_type":"Earned Leave","employee":i.name,"docstatus":1})
# 			# if not exist:
# 			# 	new_all = frappe.new_doc("Leave Allocation")
# 			# 	new_all.employee = i.name
# 			# 	new_all.new_leaves_allocated = 1
# 			# 	new_all.leave_type = "Earned Leave"
# 			# 	new_all.company =frappe.db.get_value("Employee",i.name,["company"])
# 			# 	new_all.from_date = date.today()
# 			# 	new_all.to_date = date.today().replace(month=12, day=31)
# 			# 	new_all.save(ignore_permissions=True)
# 			# 	new_all.submit()

#Set the Sales Person details for Sales Order
@frappe.whitelist()
def set_sp():
    list = ['SO-NCMEF-2022-00150','SO-NCMEF-2022-00153','SO-NCMEF-2022-00157','SO-NSPL-2022-00108','SO-NCPLP-2023-00868','SO-NSPL-2024-00008-1','SO-NSPL-2024-00016','SO-NCPLP-2024-00041','SO-NCMEF-2023-00214','SO-NSPL-2023-00147','SO-NSPL-2023-00144','SO-NCPLP-2023-00560','SO-NCPLP-2023-00534','SO-NCPLP-2023-00505-1','SO-NCMEF-2023-00071','SO-NCMEFT-2023-00970','SO-NCPLP-2023-00392','SO-NCPLP-2023-00465','SO-NCPLP-2023-00468','SO-NSPL-2023-00113-1','SO-NCPLP-2023-00506-1','SO-NCPLP-2023-00507']
    sl = frappe.db.get_list("Sales Order",{'transaction_date':['between', ['2022-04-01', '2022-06-01']]},["name","sales_person_user"])
    # sl = frappe.db.sql(""" select name from `tabSales Order`""")
    for sale in sl:
        if sale.sales_person_user and sale.name not in list:
            sp = frappe.get_doc("Sales Order",sale.name)
            print(sale.name)
            # name = frappe.db.get_value("Employee",{'user_id':sp.sale_person},['name'])
            # sale_person = frappe.db.get_value("Sales Person",{'employee':name},['name'])
            if sp.sales_person_user:
                sp.set('sales_team', [])
                sp.append("sales_team",{
                    'sales_person': sp.sales_person_user,
                    'allocated_percentage': 100,
                    'allocated_amount':sp.net_total,
                })
                sp.flags.ignore_mandatory = True
                sp.flags.ignore_validate_update_after_submit = True
                sp.save(ignore_permissions = True)

#Sent the mail for WFH request while submission of WFH Request
@frappe.whitelist()
def wfh_approval_mail(doc,method):
    if doc.company=="Norden Communication Middle East FZE":
        frappe.sendmail(
        recipients=["sobha@nordenco.ae","rajeesh@nordenco.ae"],
        subject=_("Work From Home Request Approved"),
        message="""     
            Dear Sir/Madam,<br>Work From Home Request for the employee {}:{} is approved from {} to {} for the reason <b>{}</b><br><br>
            Thanks & Regards,<br>TEAM ERP<br>"This email has been automatically generated. Please do not reply"
            """.format(doc.employee,doc.employee_name,formatdate(doc.work_from_date),formatdate(doc.work_to_date), doc.reason)      
    )

#Get the Passport expiry details
@frappe.whitelist()
def passport_expire():
    visa = frappe.db.sql(""" select name,custom_job_loss_insurance_date,custom_valid_upto,custom_visa_valid_upto from `tabEmployee` where company='Norden Communication Middle East FZE' """,as_dict = 1)
    data = ''
    data += '<table border=1 width=100%><tr border-color:black><td width=30% colspan=2>Expired Visa</td><td width=40% colspan=2>Expired Passport</td><td width=30% colspan=2>Expired Insurance</td></tr>'
    data += '<tr border-color:black><td width=20%>Expiry Date</td><td width=20%>Employee</td><td width=20%>Expiry Date</td><td width=20%>Employee</td><td width=10%>Expiry Date</td><td width=10%>Employee</td></tr>'
    for date in visa:
        Visa_date = date.custom_visa_valid_upto
        passport = date.custom_valid_upto
        insurance=date.custom_job_loss_insurance_date
        if Visa_date:
            different = date_diff(Visa_date,today())
            if 31 > different >0:
                data += '<tr border-color:black><td>%s</td><td>%s</td>'%(Visa_date,date.name)
        if passport:
            differ= date_diff(passport,today())
            if 31>differ >0:
                data += '<td>%s</td><td>%s</td>'%(passport,date.name)
        if insurance:
            diff= date_diff(insurance,today())
            if 31>diff >0:
                data += '<td>%s</td><td>%s</td>'%(insurance,date.name)
    data+='</tr>'
    data += '</table>'
    frappe.sendmail(
            recipients=['jenisha.p@groupteampro.com'],
            subject=('Expiry Details'),
            header=('Visa,Passport and Job Loss Insurance Expiry List'),
            message="""
                    Dear Mam,<br><br>
                    %s
                    """ % (data)
        )
    

#Set the file number for manually to the given quotation
@frappe.whitelist()
def update_old_file_numbers():
    frappe.db.set_value("Quotation","F-Q-NCMET-2024-01726","file_number","NCME000361")

# @frappe.whitelist()
# def modify_file_number():
# 	att = frappe.db.sql(""" update  `tabQuotation`  set file_number = 'NCME000378' where name='F-Q-NCMET-2024-01724'  """)
# 	att = frappe.db.sql(""" update  `tabQuotation`  set file_number = 'NCME000379' where name='F-Q-NCME-2024-01170'  """)
# 	att = frappe.db.sql(""" update  `tabQuotation`  set file_number = 'NCPL000086' where name='F-Q-NCPLP-2024-00156'  """)
    # att = frappe.db.sql(""" update  `tabQuotation`  set file_number = 'NCME000368' where name='F-Q-NCMET-2024-01710'  """)
    # att = frappe.db.sql(""" update  `tabQuotation`  set file_number = 'NCME000369' where name='F-Q-NCMET-2024-01711'  """)
    # att = frappe.db.sql(""" update  `tabQuotation`  set file_number = 'NCME000370' where name='F-Q-NCMET-2024-01709-1'  """)
    # att = frappe.db.sql(""" update  `tabQuotation`  set file_number = 'NCME000371' where name='F-Q-NCMET-2024-01715'  """)
    # att = frappe.db.sql(""" update  `tabQuotation`  set file_number = 'NCME000372' where name='F-Q-NCME-2024-01165'  """)
    # att = frappe.db.sql(""" update  `tabQuotation`  set file_number = 'NCME000373' where name='F-Q-NCMET-2024-01718'  """)
    # att = frappe.db.sql(""" update  `tabQuotation`  set file_number = 'NCME000374' where name='F-Q-NCMET-2024-01719'  """)
    # att = frappe.db.sql(""" update  `tabQuotation`  set file_number = 'NCME000375' where name='F-Q-NCMET-2024-01720'  """)
    # att = frappe.db.sql(""" update  `tabQuotation`  set file_number = 'NCME000376' where name='F-Q-NCMET-2024-01721'  """)
    # att = frappe.db.sql(""" update  `tabQuotation`  set file_number = 'NCME000377' where name='F-Q-NCME-2024-01160-1'  """)
    # att = frappe.db.sql(""" update  `tabQuotation`  set file_number = 'NCME000305' where name='F-Q-NCMET-2024-01684'  """)
    # att = frappe.db.sql(""" update  `tabQuotation`  set file_number = 'NCME000306' where name='F-Q-NCMET-2024-01687'  """)
    # att = frappe.db.sql(""" update  `tabQuotation`  set file_number = 'NCME000307' where name='F-Q-NCMET-2024-01688'  """)
    # print(att)

#Update the qty for the below bin
def update_bin():
    bin = frappe.get_doc('Bin','MAT-BIN-2022-02219')
    bin.db_set('actual_qty',6.4772,update_modified=True)

#Set the file number for manually
@frappe.whitelist()
def set_file_number():
    att = frappe.db.sql(""" update  `tabSales Order`  set file_number = 'NCME001318' where name='SO-NCMEFT-2024-00797'  """)
    att = frappe.db.sql(""" update  `tabSales Order`  set file_number = 'NSPL000110' where name='SO-NSPL-2024-00124'  """)
    att = frappe.db.sql(""" update  `tabSales Order`  set file_number = 'NCME001268' where name='SO-NCMEF-2024-00368'  """)
    # att = frappe.db.sql(""" update  `tabSales Order`  set file_number = 'NCME001268' where name='SO-NSPL-2024-00121-1'  """)
    # att = frappe.db.sql(""" update  `tabSales Order`  set file_number = 'NSA000006' where name='F-Q-NSA-2022-00305'  """)
    # att = frappe.db.sql(""" update  `tabSales Order`  set file_number = 'NCUL000015' where name='F-Q-NCUL-2024-00031'  """)
    # att = frappe.db.sql(""" update  `tabSales Order`  set file_number = 'NSPL000116' where name='F-Q-NSPL-2024-00212-2'  """)
    # att = frappe.db.sql(""" update  `tabSales Order`  set file_number = 'NCUL000016' where name='F-Q-NCUL-2024-00030-3'  """)
    # att = frappe.db.sql(""" update  `tabSales Order`  set file_number = 'SNTL000006' where name='F-Q-SNTL-2024-00002'  """)
    # att = frappe.db.sql(""" update  `tabSales Order`  set file_number = 'NSA000007' where name='F-Q-NSA-2022-00304-1'  """)
    # att = frappe.db.sql(""" update  `tabSales Order`  set file_number = 'NSPL000117' where name='F-Q-NSPL-2024-00197'  """)
    # att = frappe.db.sql(""" update  `tabSales Order`  set file_number = 'NSPL000118' where name='F-Q-NSPL-2024-00192'  """)
    # att = frappe.db.sql(""" update  `tabSales Order`  set file_number = 'NSPL000114' where name='F-Q-NSPL-2024-00219'  """)
    # att = frappe.db.sql(""" update  `tabSales Order`  set file_number = 'NSPL000114' where name='F-Q-NSPL-2024-00219'  """)

# @frappe.whitelist()
# def modify_file_number_so():
# 	att = frappe.db.sql(""" update  `tabSales Order`  set file_number = 'NCUL000137' where name='SO-NCUL-2024-00016'  """)
# 	print(att)

# @frappe.whitelist()
# def modify_file_number_q():
# 	att = frappe.db.sql(""" update  `tabQuotation`  set file_number = 'NSPL000156' where name='F-Q-NSPL-2024-00225'  """)
# 	print(att)

# @frappe.whitelist()
# def modify_file_number_si():
# 	att = frappe.db.sql(""" update  `tabSales Invoice`  set file_number = 'SNTL000014' where name='SI-SNTL-2024-00014'  """)
    # att = frappe.db.sql(""" update  `tabSales Invoice`  set file_number = 'NSPL000149' where name='NID2425-00402'  """)
    # att = frappe.db.sql(""" update  `tabSales Invoice`  set file_number = 'NCME001317' where name='SI-NCMEFT-2024-00178'  """)
    # print(att)

# @frappe.whitelist()
# def modify_file_number_dn():
# 	att = frappe.db.sql(""" update  `tabDelivery Note`  set file_number = 'SNTL000014' where name='DN-SNTL-2024-00017' """)
# 	# att = frappe.db.sql(""" update  `tabDelivery Note`  set file_number = 'NCME001317' where name='DN-NCPLP-2023-00997'  """)
# 	# att = frappe.db.sql(""" update  `tabDelivery Note`  set file_number = 'NCME001317' where name='DN-NCMEFT-2024-00180'  """)
# 	print(att)
# @frappe.whitelist()
# def modify_file_number_si():
# 	att = frappe.db.sql(""" update  `tabSales Invoice`  set file_number = 'NCPL000240' where name='SI-NCI-23-00611'  """)
# 	print(att)

# @frappe.whitelist()
# def modify_file_number_dn():
# 	att = frappe.db.sql(""" update  `tabDelivery Note`  set file_number = 'F-Q-NCPLP-00772' where name='DN-NCPLP-2024-00033'  """)
# 	print(att)

#Create new user permission while change the report to in Employee
@frappe.whitelist()
def change_user_permission(reports, name, user_id):
    
    value = frappe.db.get_value("Employee", {"name": reports}, ["user_id"])
    user = frappe.db.sql("""
        SELECT `tabUser`.name as name
        FROM `tabUser`
        LEFT JOIN `tabHas Role` ON `tabHas Role`.parent = `tabUser`.name
        WHERE `tabHas Role`.role = %s AND `tabUser`.enabled = 1 AND `tabUser`.name = %s
    """, ("HR Manager", value), as_dict=True)

    if not user:
        document = frappe.get_all("User Permission", {"user": ("!=", user_id), "allow": "Employee", "for_value": name}, ["name"])
        if document:
            for i in document:
                permission = frappe.get_doc("User Permission", i.name)
                permission.delete()
        new = frappe.new_doc("User Permission")
        new.user = value
        new.allow = "Employee"
        new.for_value = name
        new.hide_descendants = 1
        new.save(ignore_permissions=True)

#Get the available qty in warehouse wise for the given company and given item details In Sales Order
@frappe.whitelist()
def getstock_detail_warehouse(item_details, company):
    item_details = json.loads(item_details)
    
    
    # Get all the warehouses for the company
    warehouses = frappe.get_all("Warehouse", {"company": company, "disabled": 0,"name":('!=', 'Stores - NCPL')}, ["name"])

    # This will store the warehouses to be displayed (where any item has stock)
    display_warehouses = set()

    # First pass: Find which warehouses have stock for any item
    for j in item_details:
        for ware in warehouses:
            warehouse_stock = frappe.db.sql("""
                select sum(b.actual_qty) as qty 
                from `tabBin` b 
                join `tabWarehouse` wh on wh.name = b.warehouse 
                where wh.name = %s and b.item_code = %s and wh.name != 'Stores - NCPL'
            """, (ware.name, j["item_code"]), as_dict=True)
            
            qty = warehouse_stock[0]["qty"] if warehouse_stock and warehouse_stock[0]["qty"] is not None else 0
            if qty > 0:
                display_warehouses.add(ware.name)

    # Begin the HTML table structure
    data = ''
    data += '<h4><center><b>STOCK DETAILS</b></center></h4>'
    data += '<table class="table table-bordered">'

    # Table headers: Item Code, Item Name, then each warehouse name in columns
    data += '<tr>'
    data += '<td style="width:13%;padding:1px;border:1px solid black;font-size:12px;background-color:#e35310;color:white;"><center><b>ITEM CODE</b></center></td>'
    data += '<td style="width:33%;padding:1px;border:1px solid black;font-size:12px;background-color:#e35310;color:white;"><center><b>ITEM NAME</b></center></td>'
    
    # Add only warehouses where any item has stock
    for ware in warehouses:
        if ware.name in display_warehouses:
            data += '<td style="width:70px;padding:1px;border:1px solid black;font-size:12px;background-color:#e35310;color:white;"><center><b>%s</b></center></td>' % (ware.name)
    
    # Add the 'In Transit' and 'Pending to Sell' columns
    data += '<td style="padding:1px;border:1px solid black;font-size:12px;background-color:#e35310;color:white;"><center><b>IN TRANSIT</b></center></td>'
    data += '<td style="padding:1px;border:1px solid black;font-size:12px;background-color:#e35310;color:white;"><center><b>PENDING TO SELL</b></center></td>'
    data += '</tr>'

    # Second pass: Populate the rows for each item
    for j in item_details:
        data += '<tr>'
        data += '<td style="text-align:center;border: 1px solid black">%s</td>' % (j["item_code"])
        data += '<td style="text-align:center;border: 1px solid black">%s</td>' % (j["item_name"])

        # Loop through each warehouse and get the stock for this item, but only for the selected display_warehouses
        for ware in warehouses:
            if ware.name in display_warehouses:
                warehouse_stock = frappe.db.sql("""
                    select sum(b.actual_qty) as qty 
                    from `tabBin` b 
                    join `tabWarehouse` wh on wh.name = b.warehouse 
                    where wh.name = %s and b.item_code = %s
                """, (ware.name, j["item_code"]), as_dict=True)
                
                qty = warehouse_stock[0]["qty"] if warehouse_stock and warehouse_stock[0]["qty"] is not None else 0
                data += '<td style="text-align:center;border: 1px solid black">%s</td>' % (qty)

        # Fetch in-transit and pending to sell values
        purchase_order = frappe.db.sql("""
            select sum(`tabPurchase Order Item`.qty) as qty 
            from `tabPurchase Order`
            left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
            where `tabPurchase Order Item`.item_code = %s and `tabPurchase Order`.docstatus != 2 and `tabPurchase Order`.company = %s
        """, (j["item_code"],company), as_dict=True)[0]
        
        purchase_receipt = frappe.db.sql("""
            select sum(`tabPurchase Receipt Item`.qty) as qty 
            from `tabPurchase Receipt`
            left join `tabPurchase Receipt Item` on `tabPurchase Receipt`.name = `tabPurchase Receipt Item`.parent
            where `tabPurchase Receipt Item`.item_code = %s and `tabPurchase Receipt`.docstatus = 1 and `tabPurchase Receipt`.company = %s
        """, (j["item_code"],company), as_dict=True)[0]

        in_transit = (purchase_order["qty"] or 0) - (purchase_receipt["qty"] or 0)

        # Fetch pending to sell
        sale = frappe.db.sql("""
            select sum(`tabSales Order Item`.qty) as qty 
            from `tabSales Order`
            left join `tabSales Order Item` on `tabSales Order`.name = `tabSales Order Item`.parent
            where `tabSales Order Item`.item_code = %s and `tabSales Order`.docstatus = 0 and `tabSales Order`.company = %s
        """, (j["item_code"],company), as_dict=True)[0]

        pending_to_sell = sale["qty"] or 0

        # Add in-transit and pending to sell columns
        data += '<td style="text-align:center;border: 1px solid black">%s</td>' % (in_transit)
        data += '<td style="text-align:center;border: 1px solid black">%s</td>' % (pending_to_sell)
        data += '</tr>'

    data += '</table>'
    return data

@frappe.whitelist()
def update_dn_status(dn):
    
    frappe.db.set_value("Delivery Note",dn,"status","Completed")
    frappe.db.set_value("Delivery Note",dn,"per_billed","100")


from frappe.utils.user import get_users_with_role
from frappe.utils import cint, cstr, flt, get_formatted_email, today

@frappe.whitelist()
def check_credit_limit(doc, method):
    if not doc.customer:
        return

    credit_limit = frappe.db.get_value("Customer Credit Limit", {
        "parent": doc.customer,
        "company": doc.company
    }, "credit_limit") or 0

    # Initialize condition for cost center
    cond = ""

    if doc.cost_center:
        lft, rgt = frappe.get_cached_value("Cost Center", doc.cost_center, ["lft", "rgt"])
        cond = """ and cost_center in (select name from `tabCost Center` where
            lft >= {0} and rgt <= {1})""".format(lft, rgt)

    # Get outstanding balance
    outstanding = frappe.db.sql("""
        SELECT IFNULL(SUM(debit), 0) - IFNULL(SUM(credit), 0)
        FROM `tabGL Entry`
        WHERE party_type = 'Customer'
        AND is_cancelled = 0
        AND party = %s
        AND company = %s
        {0}
    """.format(cond), (doc.customer, doc.company))[0][0] or 0

    new_total = outstanding + doc.base_grand_total
    credit_controller_role = frappe.db.get_single_value("Accounts Settings", "credit_controller")
    if credit_limit >0:
        if new_total > credit_limit:
            message = _("Credit limit has been crossed for customer {0} ({1}/{2})").format(
                doc.customer, new_total, credit_limit
            )

            message += "<br><br>"
            credit_controller_users = get_users_with_role(credit_controller_role or "Sales Master Manager")
            credit_controller_users_formatted = [
                get_formatted_email(user).replace("<", "(").replace(">", ")")
                for user in credit_controller_users
            ]
            if not credit_controller_users_formatted:
                frappe.throw(
                    _("Please contact your administrator to extend the credit limits for {0}.").format(doc.customer)
                )

            user_list = "<br><br><ul><li>{0}</li></ul>".format(
                "<li>".join(credit_controller_users_formatted)
            )

            message += _(
                "Please contact any of the following users to extend the credit limits for {0}: {1}"
            ).format(doc.customer, user_list)
            frappe.msgprint(
                    message,
                    title=_("Credit Limit Crossed"),
                    raise_exception=1,
                    primary_action={
                        "label": "Send Email",
                        "server_action": "erpnext.selling.doctype.customer.customer.send_emails",
                        "hide_on_success": True,
                        "args": {
                            "customer": doc.customer,
                            "customer_outstanding": new_total,
                            "credit_limit": credit_limit,
                            "credit_controller_users_list": credit_controller_users,
                        },
                    },
                )


# @frappe.whitelist()
# def so_closed():
#     # filename = 'Sales Order.csv'
#     filename = 'Sales Order (2).csv'
#     from frappe.utils.file_manager import get_file
#     filepath = get_file(filename)
#     pps = read_csv_content(filepath[1])
#     ind=0
#     for pp in pps:
#         if pp[1] != "Sales Order":
#             # frappe.db.set_value("Sales Order",{"name":pp[1]},"status","Closed")
#             ind+=1
#             print(pp[0])
#             print(pp[1])
    # print(ind)

import frappe
from frappe.utils import today, formatdate, fmt_money, nowdate, get_first_day, get_last_day

def send_mail_for_so_summary():
    
    current_date = nowdate()
    start_date = get_first_day(current_date)
    end_date = get_last_day(current_date)
    if nowdate() != get_last_day(nowdate()):
        return
    so_list_submitted = frappe.get_all(
        "Sales Order",
        filters={
            "transaction_date": ["between", [start_date, end_date]],
            "docstatus": 1,
            "company":"Norden Communication Middle East FZE"
        },
        fields=["base_grand_total"]
    )
    total_count_submitted = len(so_list_submitted)
    total_value_submitted = sum(so.base_grand_total for so in so_list_submitted)
    total_value_submitted_fmt = total_value_submitted
    
    so_list = frappe.db.sql("""
        SELECT 
            so.transaction_date AS date,
            sp.sales_person AS sales_person,
            COUNT(so.name) AS so_count,
            SUM(so.base_grand_total) AS total_value
        FROM `tabSales Order` so
        LEFT JOIN `tabSales Team` sp ON sp.parent = so.name
        WHERE so.transaction_date BETWEEN %s AND %s
          AND so.docstatus = 1
          AND so.company='Norden Communication Middle East FZE'
        GROUP BY sp.sales_person
        ORDER BY sp.sales_person
    """,(start_date, end_date), as_dict=True)

    grand_total_count = sum(row.so_count for row in so_list)
    grand_total_value = sum(row.total_value for row in so_list)
    
    so_list_cancelled_sp = frappe.db.sql("""
        SELECT
            so.transaction_date AS date,
            sp.sales_person AS sales_person,
            COUNT(so.name) AS so_count,
            SUM(so.base_grand_total) AS total_value
        FROM `tabSales Order` so
        LEFT JOIN `tabSales Team` sp ON sp.parent = so.name
        WHERE so.transaction_date BETWEEN %s AND %s
          AND so.docstatus = 2
          AND so.company='Norden Communication Middle East FZE'
        GROUP BY sp.sales_person
        ORDER BY sp.sales_person
    """, (start_date, end_date), as_dict=True)

    grand_total_count_cancel_sp = sum(row.get("so_count", 0) for row in so_list_cancelled_sp)
    grand_total_value_cancel_sp = sum(row.get("total_value", 0) for row in so_list_cancelled_sp)


    #Cancelled Orders
    so_list_cancelled = frappe.get_all(
        "Sales Order",
        filters={
            "transaction_date": ["between", [start_date, end_date]],
            "docstatus": 2,
            "company":"Norden Communication Middle East FZE"
        },
        fields=["base_grand_total"]
    )
    total_count_cancelled = len(so_list_cancelled)
    total_value_cancelled = sum(so.base_grand_total for so in so_list_cancelled)
    total_value_cancelled_fmt = total_value_cancelled

  
    html_content = ""
    html_content = f"""
        <p>Dear Team,</p>

    <p>Please find below the details of <b>Sales Orders</b> (Month Wise Status):</p>
    """

    if total_count_submitted > 0:
        html_content += f"""
        <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
        <tr>
        <td colspan="2" style="background-color:#a7d3e0;font-weight:bold;">Incoming SO Value</td>
        </tr>
        <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>No Of SO's Processed</td>
        <td>Total SO Value</td>
        </tr>
        <tr>
        <td>{total_count_submitted}</td>
        <td style="text-align:right;">{fmt_money(total_value_submitted_fmt,2)}</td>
        </tr>
        </table>
        """
    else:
        html_content += f"""
    <table border="1" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
    <tr>
    <td colspan="2" style="background-color:#a7d3e0;font-weight:bold;">
        Incoming SO Value
    </td>
    </tr>
     <tr style="background-color:#dee9ec; font-weight:bold;padding:10px;">
    <td>No Of SO's Processed</td>
    <td>Total SO Value</td>
    </tr>
    <tr>
    <td colspan="2" style="padding:10px; color:red; font-weight:bold;">
        No Sales Orders for {formatdate(today())}
    </td>
    </tr>
    </table>
"""

    if so_list:
        html_content += f"""
    <br><br><br>
    <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
    <tr>
        <td colspan="3" style="background-color:#a7d3e0;font-weight:bold;">
            Incoming SO Value<br>
            Sales Person wise Status
        </td>
    </tr>
    <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>Sales Person</td>
        <td>No Of SO's</td>
        <td>Total SO Value</td>
    </tr>
    """

        for row in so_list:
            html_content += f"""
    <tr>
    <td style="text-align:left;">{row.sales_person or ''}</td>
    <td>{row.so_count or 0}</td>
    <td style="text-align:right;">{fmt_money(row.total_value,2) or 0}</td>
    </tr>
    """

        html_content += f"""
    <tr style="background-color:#a7d3e0; font-weight:bold;">
    <td colspan="1">Grand Total</td>
    <td>{grand_total_count or 0}</td>
    <td style="text-align:right;">{fmt_money(grand_total_value,2) or 0}</td>
    </tr>
    </table>
    """
    else:
        html_content += f"""
     <br><br><br>
    <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
    <tr>
        <td colspan="3" style="background-color:#a7d3e0;font-weight:bold;">
        Incoming SO Value
        </td>
    </tr>
    <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>Sales Person</td>
        <td>No Of SO's</td>
        <td>Total SO Value</td>
    </tr>
    <tr>
    <td colspan="3" style="padding:10px; color:red; font-weight:bold;">
        No Submitted Sales Oredr In Sales Person  {formatdate(today())}
    </td>
    </tr>
    </table>
    """

    if total_count_cancelled > 0 :
        html_content += f""" 
    <br><br><br>
    <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
    <tr>
        <td colspan="2" style="background-color:#a7d3e0;font-weight:bold;">Cancelled SO Value</td>
    </tr>
    <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>No Of SO's Processed</td>
        <td>Total SO Value</td>
    </tr>
    <tr>
        <td>{total_count_cancelled}</td>
        <td style="text-align:right;">{fmt_money(total_value_cancelled_fmt,2)}</td>
    </tr>
    
    </table>
    """
    else :
        html_content += f"""
    <br><br><br>
    <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
    <tr>
        <td colspan="2" style="background-color:#a7d3e0;font-weight:bold;">
        Cancelled SO Value
        </td>
    </tr>
    <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>No Of SO's Processed</td>
        <td>Total SO Value</td>
    </tr>
    <tr>
        <td colspan="2" style="padding:10px; color:red; font-weight:bold;">
        No Cancel Sales Orders for {formatdate(today())}
    </td>
    </tr>
    </table>
    """

    html_content += """
    <br><br>
    <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
    <tr>
        <td colspan="3" style="background-color:#a7d3e0;font-weight:bold;">Cancelled SO Value<br>Sales Person wise Status</td>
    </tr>
    <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>Sales Person</td>
        <td>No Of SO's</td>
        <td>Total SO Value</td>
    </tr>
    """
    if so_list_cancelled_sp:
        for row in so_list_cancelled_sp:
            html_content += f"""
        <tr>
            <td>{row.get('sales_person') or ''}</td>
            <td>{row.get('so_count') or 0}</td>
            <td style="text-align:right;">{fmt_money(row.get('total_value'),2) or 0}</td>
        </tr>
        """
        html_content += f"""
        <tr style="background-color:#a7d3e0; font-weight:bold;">
        <td>Grand Total</td>
        <td>{grand_total_count_cancel_sp or 0}</td>
        <td style="text-align:right;">{fmt_money(grand_total_value_cancel_sp,2) or 0}</td>
        </tr>
        """
    else:
        html_content += f"""
        <tr>
        <td colspan="3" style="padding:10px; color:red; font-weight:bold;">
            No  Cancel Sales Order in Sales Person  {formatdate(today())}
        </td>
        </tr>
        """

    html_content += "</table>"
        

    frappe.sendmail(
        # recipients='divya.p@groupteampro.com',
        recipients=["divya.p@groupteampro.com","asif@norden.co.uk","sujith@nordenco.ae","anoop@nordencommunication.com","zackeria@nordenco.ae","deepak@nordenco.ae"],
        subject=f"Monthly Sales Order Summary - {formatdate(today())}",
        message=html_content
    )

    print("Email sent successfully!")


import frappe
from frappe.utils import today, formatdate, fmt_money, nowdate, get_first_day, get_last_day

def send_mail_for_si_summary():
    current_date = nowdate()
    start_date = get_first_day(current_date)
    end_date = get_last_day(current_date)
    if nowdate() != get_last_day(nowdate()):
        return
    so_list_submitted = frappe.get_all(
        "Sales Invoice",
        filters={
            "posting_date": ["between", [start_date, end_date]],
            "docstatus": 1,
            "company":"Norden Communication Middle East FZE"
        },
        fields=["base_grand_total"]
    )
    total_count_submitted = len(so_list_submitted)
    total_value_submitted = sum(so.base_grand_total for so in so_list_submitted)
    total_value_submitted_fmt = total_value_submitted
    
    so_list = frappe.db.sql("""
        SELECT 
            so.posting_date AS date,
            sp.sales_person AS sales_person,
            COUNT(so.name) AS so_count,
            SUM(so.base_grand_total) AS total_value
        FROM `tabSales Invoice` so
        LEFT JOIN `tabSales Team` sp ON sp.parent = so.name
        WHERE so.posting_date BETWEEN %s AND %s
          AND so.docstatus = 1
          AND so.company='Norden Communication Middle East FZE'
        GROUP BY sp.sales_person
        ORDER BY sp.sales_person
    """,(start_date, end_date), as_dict=True)

    grand_total_count = sum(row.so_count for row in so_list)
    grand_total_value = sum(row.total_value for row in so_list)
    
    so_list_cancelled_sp = frappe.db.sql("""
        SELECT
            so.posting_date AS date,
            sp.sales_person AS sales_person,
            COUNT(so.name) AS so_count,
            SUM(so.base_grand_total) AS total_value
        FROM `tabSales Invoice` so
        LEFT JOIN `tabSales Team` sp ON sp.parent = so.name
        WHERE so.posting_date BETWEEN %s AND %s
          AND so.docstatus = 2
          AND so.company='Norden Communication Middle East FZE'
        GROUP BY sp.sales_person
        ORDER BY sp.sales_person
    """, (start_date, end_date), as_dict=True)

    grand_total_count_cancel_sp = sum(row.get("so_count", 0) for row in so_list_cancelled_sp)
    grand_total_value_cancel_sp = sum(row.get("total_value", 0) for row in so_list_cancelled_sp)


    #Cancelled Orders
    so_list_cancelled = frappe.get_all(
        "Sales Invoice",
        filters={
            "posting_date": ["between", [start_date, end_date]],
            "docstatus": 2,
            "company":"Norden Communication Middle East FZE"
        },
        fields=["base_grand_total"]
    )
    total_count_cancelled = len(so_list_cancelled)
    total_value_cancelled = sum(so.base_grand_total for so in so_list_cancelled)
    total_value_cancelled_fmt = total_value_cancelled

  
    html_content = ""
    html_content = f"""
        <p>Dear Team,</p>

    <p>Please find below the details of <b>Sales Invoices</b> (Month Wise Status):</p>
    """

    if total_count_submitted > 0:
        html_content += f"""
        <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
        <tr>
        <td colspan="2" style="background-color:#a7d3e0;font-weight:bold;">Incoming SI Value</td>
        </tr>
        <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>No Of SI's Processed</td>
        <td>Total SI Value</td>
        </tr>
        <tr>
        <td>{total_count_submitted}</td>
        <td style="text-align:right;">{fmt_money(total_value_submitted_fmt,2)}</td>
        </tr>
        </table>
        """
    else:
        html_content += f"""
    <table border="1" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
    <tr>
    <td colspan="2" style="background-color:#a7d3e0;font-weight:bold;">
        Incoming SI Value
    </td>
    </tr>
     <tr style="background-color:#dee9ec; font-weight:bold;padding:10px;">
    <td>No Of SI's Processed</td>
    <td>Total SI Value</td>
    </tr>
    <tr>
    <td colspan="2" style="padding:10px; color:red; font-weight:bold;">
        No Sales Invoices for {formatdate(today())}
    </td>
    </tr>
    </table>
"""

    if so_list:
        html_content += f"""
    <br><br><br>
    <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
    <tr>
        <td colspan="3" style="background-color:#a7d3e0;font-weight:bold;">
            Incoming SI Value<br>
            Sales Person wise Status
        </td>
    </tr>
    <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>Sales Person</td>
        <td>No Of SI's</td>
        <td>Total SI Value</td>
    </tr>
    """

        for row in so_list:
            html_content += f"""
    <tr>
    <td style="text-align:left;">{row.sales_person or ''}</td>
    <td>{row.so_count or 0}</td>
    <td style="text-align:right;">{fmt_money(row.total_value,2) or 0}</td>
    </tr>
    """

        html_content += f"""
    <tr style="background-color:#a7d3e0; font-weight:bold;">
    <td colspan="1">Grand Total</td>
    <td>{grand_total_count or 0}</td>
    <td style="text-align:right;">{fmt_money(grand_total_value,2) or 0}</td>
    </tr>
    </table>
    """
    else:
        html_content += f"""
     <br><br><br>
    <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
    <tr>
        <td colspan="3" style="background-color:#a7d3e0;font-weight:bold;">
        Incoming SI Value
        </td>
    </tr>
    <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>Sales Person</td>
        <td>No Of SI's</td>
        <td>Total SI Value</td>
    </tr>
    <tr>
    <td colspan="3" style="padding:10px; color:red; font-weight:bold;">
        No Submitted Sales Invoices In Sales Person  {formatdate(today())}
    </td>
    </tr>
    </table>
    """

    if total_count_cancelled > 0 :
        html_content += f""" 
    <br><br><br>
    <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
    <tr>
        <td colspan="2" style="background-color:#a7d3e0;font-weight:bold;">Cancelled SI Value</td>
    </tr>
    <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>No Of SI's Processed</td>
        <td>Total SI Value</td>
    </tr>
    <tr>
        <td>{total_count_cancelled}</td>
        <td style="text-align:right;">{fmt_money(total_value_cancelled_fmt,2)}</td>
    </tr>
    
    </table>
    """
    else :
        html_content += f"""
    <br><br><br>
    <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
    <tr>
        <td colspan="2" style="background-color:#a7d3e0;font-weight:bold;">
        Cancelled SI Value
        </td>
    </tr>
    <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>No Of SI's Processed</td>
        <td>Total SI Value</td>
    </tr>
    <tr>
        <td colspan="2" style="padding:10px; color:red; font-weight:bold;">
        No Cancel Sales Invoices for {formatdate(today())}
    </td>
    </tr>
    </table>
    """

    html_content += """
    <br><br>
    <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
    <tr>
        <td colspan="3" style="background-color:#a7d3e0;font-weight:bold;">Cancelled SI Value<br>Sales Person wise Status</td>
    </tr>
    <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>Sales Person</td>
        <td>No Of SI's</td>
        <td>Total SI Value</td>
    </tr>
    """
    if so_list_cancelled_sp:
        for row in so_list_cancelled_sp:
            html_content += f"""
        <tr>
            <td>{row.get('sales_person') or ''}</td>
            <td>{row.get('so_count') or 0}</td>
            <td style="text-align:right;">{fmt_money(row.get('total_value'),2) or 0}</td>
        </tr>
        """
        html_content += f"""
        <tr style="background-color:#a7d3e0; font-weight:bold;">
        <td>Grand Total</td>
        <td>{grand_total_count_cancel_sp or 0}</td>
        <td style="text-align:right;">{fmt_money(grand_total_value_cancel_sp,2) or 0}</td>
        </tr>
        """
    else:
        html_content += f"""
        <tr>
        <td colspan="3" style="padding:10px; color:red; font-weight:bold;">
            No  Cancel Sales Invoices in Sales Person  {formatdate(today())}
        </td>
        </tr>
        """

    html_content += "</table>"
        

    frappe.sendmail(
        # recipients='divya.p@groupteampro.com',
        recipients=["divya.p@groupteampro.com","asif@norden.co.uk","sujith@nordenco.ae","anoop@nordencommunication.com","zackeria@nordenco.ae","deepak@nordenco.ae"],
        subject=f"Monthly Sales Invoice Summary - {formatdate(today())}",
        message=html_content
    )

    print("Email sent successfully!")

@frappe.whitelist()
def get_non_avl_qty():
    item_details = frappe.db.sql(""" select item_code,description, sum(qty)as qty,sum(delivered_qty)as delivered_qty from `tabSales Order Item` where parent = 'SO-NCMEF-2025-00721' group by item_code order by idx """,as_dict = 1)
    for j in item_details:
        qty = 0
        av_qty = j.qty - j.delivered_qty
        if av_qty > 0:
            qty = av_qty
        available_qty = 0
        warehouse=[]
        ware = frappe.db.get_list("Warehouse",{"company":"Norden Communication Middle East FZE","custom_is_pick_list":0},['name'])
        for w in ware:
            bin = frappe.get_all("Bin",{"item_code":j.item_code,"warehouse":w.name},['actual_qty','reserved_stock'])
            sto = sum([value.get("actual_qty", 0) for value in bin])
            if sto and sto>0:
                warehouse.append(w.name)
                reserve = frappe.db.sql("""
                    SELECT (sum(reserved_qty) - sum(delivered_qty)) as reserved_qty 
                    FROM `tabStock Reservation Entry` 
                    WHERE voucher_no = %s 
                    AND item_code = %s 
                    AND docstatus != 2
                """, ("SO-NCMEF-2025-00721",j.item_code), as_dict=1)
                stock = sum([value.get("actual_qty", 0) for value in bin]) - sum([value.get("reserved_stock", 0) for value in bin])
                if reserve:
                    reser_qty = reserve[0]['reserved_qty']
                else:
                    reser_qty = 0
                if reser_qty and reser_qty > 0:
                    available_qty = reser_qty
                else:
                    if stock and qty >= stock:
                        available_qty = stock
                    elif stock and qty < stock:
                        available_qty = qty
                print(available_qty)
    # ware = frappe.db.get_list("Warehouse", {"company":"Norden Communication Middle East FZE"}, ['name'])
    # for j in item_details:
    #     if j.item_code=="ENC-HBU8M-100R-69":
    #         del_note = frappe.db.get_all("Delivery Note", {"file_number": "NCME079924","docstatus":("!=",2)}, ['*'])
    #         if del_note:
    #             del_qty = 0
    #             for i in del_note:
    #                 deli_note = frappe.get_doc("Delivery Note", i.name)
    #                 if deli_note.items:
    #                     for item in deli_note.items:
    #                         if j.item_code == item.item_code:
    #                             del_qty += item.qty
    #             available_qty = 0
    #             nonavailable_qty = 0
    #             warehouse = []
    #             for w in ware:
    #                 bin = frappe.get_all("Bin",{"item_code":"ENC-HBU8M-100R-69","warehouse":w.name},['actual_qty','reserved_stock'])
    #                 sto = sum([value.get("actual_qty", 0) for value in bin])
    #                 if sto and sto>0:
    #                     warehouse.append(w.name)
    #                     reserve = frappe.db.sql("""
    #                         SELECT (sum(reserved_qty) - sum(delivered_qty)) as reserved_qty
    #                         FROM `tabStock Reservation Entry` 
    #                         WHERE voucher_no = %s 
    #                         AND item_code = %s 
    #                         AND docstatus != 2
    #                     """, ("SO-NCMEF-2025-00721","ENC-HBU8M-100R-69"), as_dict=1)
    #                     stock = sum([value.get("actual_qty", 0) for value in bin]) - sum([value.get("reserved_stock", 0) for value in bin])
    #                     print("stock")
    #                     print(stock)
    #                     if reserve:
    #                         reser_qty = reserve[0]['reserved_qty']
    #                     else:
    #                         reser_qty = 0

    #                     if reser_qty and reser_qty > 0:
    #                         available_qty = reser_qty
    #                     else:
    #                         if stock and j.qty >= stock:
    #                             available_qty = stock
    #                         elif stock and j.qty < stock:
    #                             available_qty = j.qty
    #             print("Available")
    #             print(available_qty)
    #             nonavailable_qty = (j.qty - del_qty) - available_qty
    #             print("Non Available")
    #             print(nonavailable_qty)
    #             print(warehouse)

frappe.whitelist()
def update_si_naming_series(doc, method):
    from frappe.utils import getdate

    if doc.company != "Norden Singapore PTE LTD":
        return

    posting_date = getdate(doc.posting_date)
    year = posting_date.year
    month = posting_date.month
    if month < 4:
        series_year = year - 1
    else:
        series_year = year
    naming=f"SI-NSPL-.{series_year}.-"
    if doc.is_return:
        doc.naming_series = f"SR-NSPL-.{series_year}.-"
    else:
        doc.naming_series = f"SI-NSPL-.{series_year}.-"



def create_hooks_report():
    job = frappe.db.exists('Scheduled Job Type', 'send_mail_for_so_summary_yearly')
    if not job:
        emc = frappe.new_doc("Scheduled Job Type")  
        emc.update({
            "method": 'norden.utils.send_mail_for_so_summary_yearly',
            "frequency": 'Cron',
            "cron_format": '0 0 1 12 *'
        })
        emc.save(ignore_permissions=True)

import frappe
from frappe.utils import today, formatdate, fmt_money, nowdate, get_first_day, get_last_day

def send_mail_for_so_summary_yearly():
    
    today_date = getdate(nowdate())
    # today_date = getdate("2025-12-12")
    start_date = today_date.replace(month=1, day=1)
    end_date = today_date.replace(month=12, day=31)
    
    if today_date != end_date:
        return
    so_list_submitted = frappe.get_all(
        "Sales Order",
        filters={
            "transaction_date": ["between", [start_date, end_date]],
            "docstatus": 1,
            "company":"Norden Communication Middle East FZE"
        },
        fields=["base_grand_total"]
    )
    total_count_submitted = len(so_list_submitted)
    total_value_submitted = sum(so.base_grand_total for so in so_list_submitted)
    total_value_submitted_fmt = total_value_submitted
    
    so_list = frappe.db.sql("""
        SELECT 
            so.transaction_date AS date,
            sp.sales_person AS sales_person,
            COUNT(so.name) AS so_count,
            SUM(so.base_grand_total) AS total_value
        FROM `tabSales Order` so
        LEFT JOIN `tabSales Team` sp ON sp.parent = so.name
        WHERE so.transaction_date BETWEEN %s AND %s
          AND so.docstatus = 1
          AND so.company='Norden Communication Middle East FZE'
        GROUP BY sp.sales_person
        ORDER BY sp.sales_person
    """,(start_date, end_date), as_dict=True)

    grand_total_count = sum(row.so_count for row in so_list)
    grand_total_value = sum(row.total_value for row in so_list)
    
    so_list_cancelled_sp = frappe.db.sql("""
        SELECT
            so.transaction_date AS date,
            sp.sales_person AS sales_person,
            COUNT(so.name) AS so_count,
            SUM(so.base_grand_total) AS total_value
        FROM `tabSales Order` so
        LEFT JOIN `tabSales Team` sp ON sp.parent = so.name
        WHERE so.transaction_date BETWEEN %s AND %s
          AND so.docstatus = 2
          AND so.company='Norden Communication Middle East FZE'
        GROUP BY sp.sales_person
        ORDER BY sp.sales_person
    """, (start_date, end_date), as_dict=True)

    grand_total_count_cancel_sp = sum(row.get("so_count", 0) for row in so_list_cancelled_sp)
    grand_total_value_cancel_sp = sum(row.get("total_value", 0) for row in so_list_cancelled_sp)


    #Cancelled Orders
    so_list_cancelled = frappe.get_all(
        "Sales Order",
        filters={
            "transaction_date": ["between", [start_date, end_date]],
            "docstatus": 2,
            "company":"Norden Communication Middle East FZE"
        },
        fields=["base_grand_total"]
    )
    total_count_cancelled = len(so_list_cancelled)
    total_value_cancelled = sum(so.base_grand_total for so in so_list_cancelled)
    total_value_cancelled_fmt = total_value_cancelled

  
    html_content = ""
    html_content = f"""
        <p>Dear Team,</p>

    <p>Please find below the details of <b>Sales Orders</b> (Year Wise Status):</p>
    """

    if total_count_submitted > 0:
        html_content += f"""
        <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
        <tr>
        <td colspan="2" style="background-color:#a7d3e0;font-weight:bold;">Incoming SO Value</td>
        </tr>
        <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>No Of SO's Processed</td>
        <td>Total SO Value</td>
        </tr>
        <tr>
        <td>{total_count_submitted}</td>
        <td style="text-align:right;">{fmt_money(total_value_submitted_fmt,2)}</td>
        </tr>
        </table>
        """
    else:
        html_content += f"""
    <table border="1" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
    <tr>
    <td colspan="2" style="background-color:#a7d3e0;font-weight:bold;">
        Incoming SO Value
    </td>
    </tr>
     <tr style="background-color:#dee9ec; font-weight:bold;padding:10px;">
    <td>No Of SO's Processed</td>
    <td>Total SO Value</td>
    </tr>
    <tr>
    <td colspan="2" style="padding:10px; color:red; font-weight:bold;">
        No Sales Orders for {formatdate(today())}
    </td>
    </tr>
    </table>
"""

    if so_list:
        html_content += f"""
    <br><br><br>
    <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
    <tr>
        <td colspan="3" style="background-color:#a7d3e0;font-weight:bold;">
            Incoming SO Value<br>
            Sales Person wise Status
        </td>
    </tr>
    <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>Sales Person</td>
        <td>No Of SO's</td>
        <td>Total SO Value</td>
    </tr>
    """

        for row in so_list:
            html_content += f"""
    <tr>
    <td style="text-align:left;">{row.sales_person or ''}</td>
    <td>{row.so_count or 0}</td>
    <td style="text-align:right;">{fmt_money(row.total_value,2) or 0}</td>
    </tr>
    """

        html_content += f"""
    <tr style="background-color:#a7d3e0; font-weight:bold;">
    <td colspan="1">Grand Total</td>
    <td>{grand_total_count or 0}</td>
    <td style="text-align:right;">{fmt_money(grand_total_value,2) or 0}</td>
    </tr>
    </table>
    """
    else:
        html_content += f"""
     <br><br><br>
    <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
    <tr>
        <td colspan="3" style="background-color:#a7d3e0;font-weight:bold;">
        Incoming SO Value
        </td>
    </tr>
    <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>Sales Person</td>
        <td>No Of SO's</td>
        <td>Total SO Value</td>
    </tr>
    <tr>
    <td colspan="3" style="padding:10px; color:red; font-weight:bold;">
        No Submitted Sales Oredr In Sales Person  {formatdate(today())}
    </td>
    </tr>
    </table>
    """

    if total_count_cancelled > 0 :
        html_content += f""" 
    <br><br><br>
    <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
    <tr>
        <td colspan="2" style="background-color:#a7d3e0;font-weight:bold;">Cancelled SO Value</td>
    </tr>
    <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>No Of SO's Processed</td>
        <td>Total SO Value</td>
    </tr>
    <tr>
        <td>{total_count_cancelled}</td>
        <td style="text-align:right;">{fmt_money(total_value_cancelled_fmt,2)}</td>
    </tr>
    
    </table>
    """
    else :
        html_content += f"""
    <br><br><br>
    <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
    <tr>
        <td colspan="2" style="background-color:#a7d3e0;font-weight:bold;">
        Cancelled SO Value
        </td>
    </tr>
    <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>No Of SO's Processed</td>
        <td>Total SO Value</td>
    </tr>
    <tr>
        <td colspan="2" style="padding:10px; color:red; font-weight:bold;">
        No Cancel Sales Orders for {formatdate(today())}
    </td>
    </tr>
    </table>
    """

    html_content += """
    <br><br>
    <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
    <tr>
        <td colspan="3" style="background-color:#a7d3e0;font-weight:bold;">Cancelled SO Value<br>Sales Person wise Status</td>
    </tr>
    <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>Sales Person</td>
        <td>No Of SO's</td>
        <td>Total SO Value</td>
    </tr>
    """
    if so_list_cancelled_sp:
        for row in so_list_cancelled_sp:
            html_content += f"""
        <tr>
            <td>{row.get('sales_person') or ''}</td>
            <td>{row.get('so_count') or 0}</td>
            <td style="text-align:right;">{fmt_money(row.get('total_value'),2) or 0}</td>
        </tr>
        """
        html_content += f"""
        <tr style="background-color:#a7d3e0; font-weight:bold;">
        <td>Grand Total</td>
        <td>{grand_total_count_cancel_sp or 0}</td>
        <td style="text-align:right;">{fmt_money(grand_total_value_cancel_sp,2) or 0}</td>
        </tr>
        """
    else:
        html_content += f"""
        <tr>
        <td colspan="3" style="padding:10px; color:red; font-weight:bold;">
            No  Cancel Sales Order in Sales Person  {formatdate(today())}
        </td>
        </tr>
        """

    html_content += "</table>"
        

    frappe.sendmail(
        # recipients='divya.p@groupteampro.com',
        recipients=["asif@norden.co.uk","sujith@nordenco.ae","anoop@nordencommunication.com","zackeria@nordenco.ae","deepak@nordenco.ae"],
        subject=f"Yearly Sales Order Summary - {formatdate(start_date)}- {formatdate(end_date)}",
        message=html_content
    )