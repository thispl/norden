from datetime import datetime
from lib2to3.pytree import convert
import frappe
from frappe.utils import get_url
from datetime import datetime, timedelta
import requests
from datetime import date
from calendar import monthrange
import erpnext
from frappe.utils import date_diff, add_months, today, add_days, nowdate,formatdate,format_date,getdate
from frappe.utils.csvutils import read_csv_content
from frappe.utils.file_manager import get_file
import json
from frappe import _
from forex_python.converter import CurrencyRates
from frappe.model.document import Document
from frappe.utils import time_diff
import pandas as pd
from frappe.model.rename_doc import rename_doc
from frappe.model.naming import make_autoname
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions
from erpnext.setup.utils import get_exchange_rate
# from erpnext.accounts.doctype.gl_entry.gl_entry import rename_gle_sle_docs


@frappe.whitelist()
def create_material_request(item_table, company):
    item_table = json.loads(item_table)
    for item in item_table:
        stocks = frappe.db.sql("""select (sum(`tabBin`.actual_qty) - sum(reserved_stock)) as actual_qty,warehouse,stock_uom,stock_value from tabBin
            where item_code = '%s' """ % (item["item_code"]), as_dict=True)
        req_qty = 0
        for stock in stocks:
            if stock.warehouse == item['warehouse']:
                if item['qty'] - stock.actual_qty:
                    req_qty = item['qty'] - stock.actual_qty
        if req_qty > 0:
            mr = frappe.new_doc("Material Request")
            mr.material_request_type = "Purchase"
            mr.requester_name = frappe.session.user
            mr.company = company
            mr.append('items', {
                'item_code': item['item_code'],
                'schedule_date': item['delivery_date'],
                'qty': req_qty,
                'warehouse': item['warehouse'],
            })
            mr.save(ignore_permissions=True)
            frappe.db.commit()


@frappe.whitelist()
def get_stock_balance(item_table):
    item_table = json.loads(item_table)
    data = []
    for item in item_table:
        stocks = frappe.db.sql("""select (sum(`tabBin`.actual_qty) - sum(reserved_stock)) as actual_qty,warehouse,stock_uom,stock_value from tabBin
            where item_code = '%s' """ % (item["item_code"]), as_dict=True)
        item_name = frappe.db.get_value('Item',{'item_code':item['item_code']},['item_name'])
        for stock in stocks:
            if stock.actual_qty and stock.actual_qty > 0:
                data.append([item['item_code'],item_name, stock.warehouse,
                            stock.actual_qty, stock.stock_uom, stock.stock_value])
    return data


@frappe.whitelist()
def get_previous_po(item_table):
    item_table = json.loads(item_table)
    data = []
    for item in item_table:
        pos = frappe.db.sql("""select `tabPurchase Order Item`.item_code as item_code,`tabPurchase Order Item`.item_name as item_name,`tabPurchase Order`.supplier as supplier,`tabPurchase Order Item`.qty as qty,`tabPurchase Order Item`.amount as amount,`tabPurchase Order`.transaction_date as date,`tabPurchase Order`.name as po from `tabPurchase Order`
        left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
        where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 """ % (item["item_code"]), as_dict=True)
        item_name = frappe.db.get_value('Item',{'item_code':item['item_code']},['item_name'])
        for po in pos:
            data.append([item['item_code'],item_name,
                        po.supplier, po.qty, po.date, po.amount, po.po])
    return data

@frappe.whitelist()
def return_dn_date():
    pos = frappe.db.sql("""select `tabDelivery Note Item`.item_code as item_code,`tabDelivery Note Item`.qty as qty from `tabDelivery Note`
    left join `tabDelivery Note Item` on `tabDelivery Note`.name = `tabDelivery Note Item`.parent
    where `tabDelivery Note Item`.item_code = '%s' """%("ADC221104GY"),as_dict = 1)[0]
    print(pos)

@frappe.whitelist()
def get_out_qty(item_table):
    item_table = json.loads(item_table)
    data = []
    for item in item_table:
        sles = frappe.db.sql("""select * from `tabStock Ledger Entry` 
        left join `tabStock Entry` on `tabStock Ledger Entry`.voucher_no = `tabStock Entry`.name where `tabStock Ledger Entry`.posting_date between '%s' and '%s' and `tabStock Ledger Entry`.item_code = '%s' and `tabStock Ledger Entry`.actual_qty < 0 and `tabStock Ledger Entry`.voucher_type = 'Stock Entry' and `tabStock Entry`.stock_entry_type = 'Material Issue' """ % (add_months(today(), -6), today(), item['item_code']), as_dict=True)
        for sl in sles:
            data.append([item['item_code'], sl.warehouse, abs(
                sl.actual_qty), sl.posting_date, sl.voucher_type])
    return data


@frappe.whitelist()
def stock_popup(item_code):
    item = frappe.get_value('Item',{'item_name':item_code},'item_code')
    data = ''
    stocks = frappe.db.sql("""select (sum(`tabBin`.actual_qty) - sum(reserved_stock)) as actual_qty,warehouse,stock_uom,stock_value from tabBin
        where item_code = '%s' """%(item),as_dict=True)
    data += '<table class="table table-bordered"><tr><th style="padding:1px;border: 1px solid Red" colspan=6><center>Stock Availability</center></th></tr>'
    data += '<tr><td style="padding:1px;border: 1px solid black"><b>Item Code</b></td><td style="padding:1px;border: 1px solid black"><b>Item Name</b></td><td style="padding:1px;border: 1px solid black"><b>Warehouse</b></td><td style="padding:1px;border: 1px solid black"><b>QTY</b></td><td style="padding:1px;border: 1px solid black"><b>UOM</b></td><td style="padding:1px;border: 1px solid black"><b>Value</b></td></tr>'
    i = 0
    for stock in stocks:
        if stock.actual_qty > 0:
            data += '<tr><td style="padding:1px;border: 1px solid black">%s</td><td style="padding:1px;border: 1px solid black">%s</td><td style="padding:1px;border: 1px solid black">%s</td><td style="padding:1px;border: 1px solid black">%s</td><td style="padding:1px;border: 1px solid black">%s</td><td style="padding:1px;border: 1px solid black">%s</td></tr>'%(item,frappe.db.get_value('Item',item,'item_name'),stock.warehouse,stock.actual_qty,stock.stock_uom,stock.stock_value)
            i += 1
    data += '</table>'
    if i > 0:
        return data


@frappe.whitelist()
def po_popup(item_code,company,name):
    item = frappe.get_value('Item',{'item_code':item_code},["item_code"])
    data = ''
    data_1 = ''
    pos = frappe.db.sql("""select `tabPurchase Order Item`.item_code as item_code,`tabPurchase Order Item`.item_name as item_name,`tabPurchase Order`.supplier as supplier,`tabPurchase Order Item`.qty as qty,`tabPurchase Order Item`.amount as amount,`tabPurchase Order`.transaction_date as date,`tabPurchase Order`.name as po,`tabPurchase Order`.company as company from `tabPurchase Order`
    left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
    where `tabPurchase Order`.company = '%s' and `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.name != '%s' and `tabPurchase Order`.docstatus != 2 order by date desc """ % (company,item,name), as_dict=True)
    data += '<table class="table table-bordered"><tr><th style="padding:1px;border: 1px solid black" colspan=6><center>Previous Purchase Order</center></th></tr>'
    data += '<tr><td style="padding:1px;border: 1px solid black"><b>Item Code</b></td><td style="padding:1px;border: 1px solid black"><b>PO Number</b></td><td style="padding:1px;border: 1px solid black"><b>Supplier</b></td><td style="padding:1px;border: 1px solid black"><b>QTY</b></td><td style="padding:1px;border: 1px solid black"><b>PO Date</b></td><td style="padding:1px;border: 1px solid black"><b>Amount</b></td></tr>'
    for po in pos[:3]:
        data += '<tr><td style="padding:1px;border: 1px solid black">%s</td><td style="padding:1px;border: 1px solid black"><a href="https://erp.nordencommunication.com/app/purchase-order/%s">%s</td><td style="padding:1px;border: 1px solid black">%s</td><td style="padding:1px;border: 1px solid black">%s</td><td style="padding:1px;border: 1px solid black">%s</td><td style="padding:1px;border: 1px solid black">%s</td></tr>' %(po.item_code, po.po,po.po, po.supplier, po.qty,formatdate(str(po.date)), po.amount/po.qty)
    data += '</table>'
    if not pos == []:
        return data
    else:
        data_1 += '<table class="table table-bordered"><tr><th style="padding:1px;border: 1px solid black;color:#FF3131;" colspan=6><center>Previous Purchase Order Not Found</center></th></tr>'
        return data_1

@frappe.whitelist()
def out_qty_popup(item):
    data = ''
    sles = frappe.db.sql("""select * from `tabStock Ledger Entry` 
    left join `tabStock Entry` on `tabStock Ledger Entry`.voucher_no = `tabStock Entry`.name where `tabStock Ledger Entry`.posting_date between '%s' and '%s' and `tabStock Ledger Entry`.item_code = '%s' and `tabStock Ledger Entry`.actual_qty < 0 and `tabStock Ledger Entry`.voucher_type = 'Stock Entry' and `tabStock Entry`.stock_entry_type = 'Material Issue' """ % (add_months(today(), -6), today(), item), as_dict=True)
    data += '<table class="table table-bordered"><tr><th style="padding:1px;border: 1px solid black" colspan=6><center>6 Months Stock Out Qty</center></th></tr>'
    data += '<tr><td style="padding:1px;border: 1px solid black"><b>Item Code</b></td><td style="padding:1px;border: 1px solid black"><b>Warehouse</b></td><td style="padding:1px;border: 1px solid black"><b>QTY</b></td><td style="padding:1px;border: 1px solid black"><b>Date</b></td><td style="padding:1px;border: 1px solid black"><b>Out Type</b></td></tr>'
    for sl in sles:
        data += '<tr><td style="padding:1px;border: 1px solid black">%s</td><td style="padding:1px;border: 1px solid black">%s</td><td style="padding:1px;border: 1px solid black">%s</td><td style="padding:1px;border: 1px solid black">%s</td><td style="padding:1px;border: 1px solid black">%s</td></tr>' % (
            sl.item_code, sl.warehouse, abs(sl.actual_qty), sl.posting_date, sl.voucher_type)
    data += '</table>'
    if sles:
        return data


@frappe.whitelist()
def check_discount_percent(doc,method):
    user_roles = frappe.get_roles(frappe.session.user)
    max_discount = 0
    for role in user_roles:
        d = frappe.db.get_value("Quotation Discount", {'role':role, 'parent': 'Sales Settings'}, ['role', 'max_dis'])
        if d:
            if max_discount < d[1]:
                max_discount = d[1]
    
    if max_discount == 0:
        return 'invalid'
    elif float(doc.additional_discount_percentage) > max_discount:
        frappe.throw("Maximum discount percentage allowed for you is %s "%(int(max_discount)))
        frappe.set_value("Quotation",doc.name,"additional_discount_percentage","")

# @frappe.whitelist()
# def create_logistics_request(name):
#     po = frappe.get_doc("Purchase Order",name)
#     lg = frappe.new_doc("Logistics Request")
#     lg.logistic_type = 'Import'
#     lg.po_so = 'Purchase Order'
#     lg.order_no = name
#     lg.consignment_type = po.consignment_types
#     lg.cargo_type = po.mode_of_dispatch
#     lg.supplier = po.supplier
#     lg.project_name = po.project_name
#     lg.grand_total = po.grand_total
#     lg.freight_rate = po.grand_total
#     lg.requester_name = po.requester_name
#     lg.append('product_description',[{'item_code':'001'}])
#     for i in po.items:
#         lg.append('product_description',{
#             'item_code':i.item_code
#         })
#     lg.flags.ignore_mandatory = True
#     lg.save(ignore_permissions=True)
#     frappe.db.commit()

@frappe.whitelist()
def create_landed_cost_voucher(doc,method):
    lcv = frappe.new_doc("Landed Cost Voucher")

@frappe.whitelist()
def create_sales_person(emp):
    if not frappe.db.exists("Sales Person", {'employee': emp}):
        employee = frappe.get_doc('Employee', emp)
        if employee.department in ('Sales - NC', 'Sales - NCMEFD', 'Sales - NCPLB', 'Sales - NCPLP', 'Sales - NCUL', 'Sales - NSPL', 'Sales - SNTL'):
            doc = frappe.new_doc("Sales Person")
            doc.employee = emp
            doc.sales_person_name = employee.employee_name
            doc.parent_sales_person = 'Sales Team'
            if employee.reports_to:
                parent = frappe.db.get_value(
                    'Sales Person', {'is_group': 1, 'employee': employee.reports_to})
                if parent:
                    doc.parent_sales_person = parent
                else:
                    frappe.db.set_value(
                        'Sales Person', {'employee': employee.reports_to}, 'is_group', 1)
                    parent = frappe.db.get_value(
                        'Sales Person', {'is_group': 1, 'employee': employee.reports_to})
                    doc.parent_sales_person = parent
            doc.save(ignore_permissions=True)
            frappe.db.commit()


@frappe.whitelist()
def get_html_version():
    a = "hi"
    print(a)
    return a


@frappe.whitelist()
def create_lcv_je(doc, method):
    tnc = doc.taxes
    for tn in tnc:
        if tn.supplier:
            jv = frappe.new_doc("Journal Entry")
            jv.voucher_type = "Journal Entry"
            jv.company = doc.company
            jv.posting_date = nowdate()
            jv.bill_no = tn.bill_no
            jv.append("accounts", {
                "account": tn.expense_account,
                "debit": tn.base_amount,
                "cost_center": erpnext.get_default_cost_center(doc.company),
                "debit_in_account_currency": tn.amount
            })

            jv.append("accounts", {

                "account": frappe.get_cached_value('Company', doc.company, 'default_payable_account'),
                "party_type": "Supplier",
                "party": tn.supplier,
                "cost_center": erpnext.get_default_cost_center(doc.company),
                "credit": tn.base_amount,
                "credit_in_account_currency": tn.amount
            })
            jv.insert()
            jv.submit()


@frappe.whitelist()
def create_lcv(doc, method):
    lcv = frappe.new_doc('Landed Cost Voucher')
    lcv.company = doc.company
    lcv.append('purchase_receipts', {
        'receipt_document_type': 'Purchase Receipt',
        'receipt_document': doc.name,
    })
    lcv.items = doc.items
    lcv.taxes = doc.landed_taxes
    lcv.save(ignore_permissions=True)
    frappe.db.commit()


@frappe.whitelist()
def get_sales_person(converted_by):
    if converted_by:
        sp = frappe.db.exists('Sales Person', {'user_id': converted_by})
        r = frappe.get_value('Sales Person', sp, [
                                'name', 'commission_rate'])
        return r

# @frappe.whitelist()
# def bulk_upload_item_price(file_name):
#     from frappe.utils.file_manager import get_file
#     file_path =  get_file(file_name)
#     pps = read_csv_content(file_path[1])
#     item_not_exists = []
#     for pp in pps:
#         if frappe.db.exists('Item',{'item_code':pp[0]}):
#                 up_doc = frappe.new_doc('Item Price')
#                 up_doc.item_code = pp[0]
#                 up_doc.price_list = pp[1]
#                 up_doc.price_list_rate = pp[2]
#                 up_doc.save(ignore_permissions = True)
#         else:
#             item_not_exists.append(pp[0])

    # print(doc)
    # for pp in pss:


# @frappe.whitelist()
# def bulk_upload_stock_entry(file_name):
#     from frappe.utils.file_manager import get_file
#     file_path = get_file(file_name)
#     pps = read_csv_content(file_path[1])
#     for pp in pps:
#         up_doc = frappe.new_doc('Stock Entry')
#         up_doc.stock_entry_type = pp[0]
#         up_doc.company = pp[1]
#         up_doc.append("items", {
#             "item_code": pp[2],
#             "qty": pp[3],
#             "transfer_qty": pp[4],
#             "uom": pp[5],
#             "stock_uom": pp[6],
#             "t_warehouse": pp[7],
#             "valuation_rate": pp[8],
          

#         })
#         up_doc.save()
#         up_doc.submit()


@frappe.whitelist()
def get_leave_balance(doc):
    from erpnext.hr.doctype.leave_application.leave_application import get_leave_details
    leave_balance = get_leave_details(doc.employee, doc.end_date)
    leave_types = frappe.get_all('Leave Type', {'is_lwp': 0})
    html = "<tr>"
    for leave in leave_types:
        try:
            html += "<td>%s</td><td>%s</td>" % (
                leave['name'], leave_balance['leave_allocation'][leave['name']]['remaining_leaves'])
        except:
            pass
    return html
@frappe.whitelist()
def get_qtn(code):
    qtn = frappe.db.get_value('Quotation',)

@frappe.whitelist()
def get_emp_code(code):
    emps = frappe.get_all('Employee', {'name': ('like', code+'%')}, ['name'])
    print(emps)
    emp_list = []
    for emp in emps:
        emp_list.append(emp["name"].replace(code, ''))
    if not emp_list:    
        emp_code = str(code) + "101"
    else:
        emp_code = str(code) + str(int(max(emp_list))+1)
    return emp_code

@frappe.whitelist()
def mat_req(item_details,company):
    item_details = json.loads(item_details)
    data =''
    for item in item_details:
        stocks = frappe.db.sql("""select (sum(`tabBin`.actual_qty) - sum(reserved_stock)) as actual_qty from tabBin
            where item_code = '%s' """ % (item["item_code"]), as_dict=True)
        pos = frappe.db.sql("""select `tabPurchase Order Item`.item_code as item_code,`tabPurchase Order Item`.item_name as item_name,`tabPurchase Order`.supplier as supplier,`tabPurchase Order Item`.qty as qty,`tabPurchase Order Item`.rate as rate,`tabPurchase Order Item`.amount as amount,`tabPurchase Order`.transaction_date as date,`tabPurchase Order`.name as po from `tabPurchase Order`
            left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
            where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 """ % (item["item_code"]), as_dict=True)    
        sal = frappe.db.sql("""select `tabSales Order Item`.item_code as item_code,`tabSales Order Item`.item_name as item_name,`tabSales Order`.customer as customer,`tabSales Order Item`.qty as qty,`tabSales Order Item`.amount as amount,`tabSales Order`.transaction_date as date,`tabSales Order`.name as po from `tabSales Order`
            left join `tabSales Order Item` on `tabSales Order`.name = `tabSales Order Item`.parent
            where `tabSales Order Item`.item_code = '%s' and `tabSales Order`.docstatus != 2 """ % (item["item_code"]), as_dict=True)        
        data +='<table class="table table-bordered"><tr><th style="padding:1px;border: 1px solid black" colspan=17><center>Approval</center></th></tr>'
        data +='<tr><td colspan="2" style="padding:1px;border: 1px solid black"><b></b></td><td colspan="3" style="padding:1px;border: 1px solid black"><b>Ordering QTY</b></td><td Colspan="2" style="padding:1px;border: 1px solid black"><b>Sales Order</b></td><td colspan="2" style="padding:1px;border: 1px solid black"><b>Purchase Order</b></td><td colpsan="1" style="padding:1px;border: 1px solid black"><b></b></td><td colspan="3" style="padding:1px;border: 1px solid black"><b>Stock Available Now</b></td><td colspan="3" style="padding:1px;border: 1px solid black"><b></b></td></tr>'
        data +='<tr><td style="padding:1px;border: 1px solid black"><b>item Code</b></td><td style="padding:1px;border: 1px solid black"><b>description</b></td><td style="padding:1px;border: 1px solid black"><b>B2B</b></td><td style="padding:1px;border: 1px solid black"><b>For Stock</b></td><td style="padding:1px;border: 1px solid black"><b>FOC</b></td><td style="padding:1px;border: 1px solid black"><b>Rate</b></td><td style="padding:1px;border: 1px solid black"><b>Amount</b></td><td style="padding:1px;border: 1px solid black"><b>Rate</b></td><td style="padding:1px;border: 1px solid black"><b>Amount</b></td><td style="padding:1px;border: 1px solid black"><b>Margin%</b></td><td style="padding:1px;border: 1px solid black"><b>STOCK</b></td><td style="padding:1px;border: 1px solid black"><b>PO</b></td><td style="padding:1px;border: 1px solid black"><b>Total</b></td><td style="padding:1px;border: 1px solid black"><b>Last 3month transaction</b></td><td style="padding:1px;border: 1px solid black"><b>Last Unit Purchase</b></td><td style="padding:1px;border: 1px solid black"><b>Remark</b></td></tr>'
        i = 0
        for s in item_details:
            if s["type"] == 'STOCK':
                res1 = s["qty"]
                stocks = frappe.db.sql("""select (sum(`tabBin`.actual_qty) - sum(reserved_stock)) as actual_qty,warehouse from tabBin
                where item_code = '%s' """%(s["item_code"]),as_dict=True)
                
                pos = frappe.db.sql("""select `tabPurchase Order Item`.rate as rate from `tabPurchase Order`
                left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
                where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 """%(s["item_code"]),as_dict=True)[0] or 0 
                
                sos = frappe.db.sql("""select `tabSales Order Item`.rate as rate from `tabSales Order`
                left join `tabSales Order Item` on `tabSales Order`.name = `tabSales Order Item`.parent
                where `tabSales Order Item`.item_code = '%s' and `tabSales Order`.docstatus != 2 """%(s["item_code"]),as_dict=True) or 0   
                
                stock = frappe.db.sql("""select sum(b.actual_qty) as qty from `tabBin` b 
                join `tabWarehouse` wh on wh.name = b.warehouse
                join `tabCompany` c on c.name = wh.company
                where wh.company = '%s' and b.item_code = '%s'
                """ % (company,s["item_code"]),as_dict=True)[0]
                
                sum_of_po = frappe.db.sql("""select sum(`tabPurchase Order Item`.amount) as amount from `tabPurchase Order`
                left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
                where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 and `tabPurchase Order`.transaction_date between %s and %s """%(s["item_code"],today(),add_months(today(),-3)),as_dict=True)[0] or 0 
                if not sum_of_po["amount"]:
                    sum_of_po["amount"] = 0
                data +='<tr><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td></tr>'%(s["item_code"],s["item_name"],'',res1 or '','',sos[0]["rate"],sos[0]["rate"]*s["qty"],pos["rate"],pos["rate"]*s["qty"],sos[0]["rate"]*s["qty"]-pos["rate"]*s["qty"],stock["qty"],'','',sum_of_po["amount"],'','')
            elif s["type"] == 'FOC':
                res2 = s["qty"]
                stocks = frappe.db.sql("""select (sum(`tabBin`.actual_qty) - sum(reserved_stock)) as actual_qty,warehouse from tabBin
                where item_code = '%s' """%(s["item_code"]),as_dict=True)
                
                pos = frappe.db.sql("""select `tabPurchase Order Item`.rate as rate from `tabPurchase Order`
                left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
                where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 """%(s["item_code"]),as_dict=True)[0] or 0 
                
                sos = frappe.db.sql("""select `tabSales Order Item`.rate as rate from `tabSales Order`
                left join `tabSales Order Item` on `tabSales Order`.name = `tabSales Order Item`.parent
                where `tabSales Order Item`.item_code = '%s' and `tabSales Order`.docstatus != 2 """%(s["item_code"]),as_dict=True) or 0   
                
                stock = frappe.db.sql("""select sum(b.actual_qty) as qty from `tabBin` b 
                join `tabWarehouse` wh on wh.name = b.warehouse
                join `tabCompany` c on c.name = wh.company
                where wh.company = '%s' and b.item_code = '%s'
                """ % (company,s["item_code"]),as_dict=True)[0]
                
                sum_of_po = frappe.db.sql("""select sum(`tabPurchase Order Item`.amount) as amount from `tabPurchase Order`
                left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
                where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 and `tabPurchase Order`.transaction_date between %s and %s """%(s["item_code"],today(),add_months(today(),-3)),as_dict=True)[0] or 0 
                if not sum_of_po["amount"]:
                    sum_of_po["amount"] = 0
                data +='<tr><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td></tr>'%(s["item_code"],s["item_name"],'','',res2 or '',sos[0]["rate"],sos[0]["rate"]*s["qty"],pos["rate"],pos["rate"]*s["qty"],sos[0]["rate"]*s["qty"]-pos["rate"]*s["qty"],stock["qty"],'','',sum_of_po["amount"],'','')

            #     res2 = s["qty"]
            #     data +='<tr><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td></tr>'%(s.item_code,s.description,'','',res2 or '')
            # elif s["type"] == 'B2B':
            #     res3 = s["qty"]
            #     data +='<tr><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td><td style="padding:1px;border: 1px solid black"><b>%s</b></td></tr>'%(s.item_code,s.description,res3 or '','','')

        data +='</table>'
    return data

    
@frappe.whitelist()
def stock_popup(item_code,company):
    item = frappe.get_value('Item', {'item_code': item_code}, 'item_code')
    data = ''
    stock = 0
    stock_value = 0
    stocks = frappe.db.sql("""select (sum(`tabBin`.actual_qty) - sum(reserved_stock)) as actual_qty,`tabBin`.warehouse as warehouse,`tabBin`.stock_uom as stock_uom,`tabBin`.stock_value as stock_value from `tabBin`
                            join `tabWarehouse` on `tabWarehouse`.name = `tabBin`.warehouse
                            join `tabCompany` on `tabCompany`.name = `tabWarehouse`.company
                            where `tabBin`.item_code = '%s' and `tabWarehouse`.company = '%s' """ % (item,company), as_dict=True)
    
    data += '<table class="table table-bordered"><tr><th style="padding:1px;border: 1px solid black" colspan=6><center>Stock Availability</center></th></tr>'
    data += '<tr><td style="padding:1px;border: 1px solid black"><b>Item Code</b></td><td style="padding:1px;border: 1px solid black"><b>Item Name</b></td><td style="padding:1px;border: 1px solid black"><b>Warehouse</b></td><td style="padding:1px;border: 1px solid black"><b>QTY</b></td><td style="padding:1px;border: 1px solid black"><b>UOM</b></td></tr>'
    if stocks:
        for stock in stocks:
            if stock["actual_qty"] and stock["actual_qty"] > 0:
                data += '<tr><td style="padding:1px;border: 1px solid black">%s</td><td style="padding:1px;border: 1px solid black">%s</td><td style="padding:1px;border: 1px solid black">%s</td><td style="padding:1px;border: 1px solid black">%s</td><td style="padding:1px;border: 1px solid black">%s</td></tr>' % (
                    item, frappe.db.get_value('Item', item, 'item_name'), stock["warehouse"], stock["actual_qty"], stock["stock_uom"])
    else:
        data += '<tr><td style="padding:1px;border: 1px solid black">%s</td><td style="padding:1px;border: 1px solid black">%s</td><td style="padding:1px;border: 1px solid black;text-align:center" colspan="3">%s</td></tr>' % (
                    item, frappe.db.get_value('Item', item, 'item_name'), 'No Stock Available')
    data += '</table>'
    return data


@frappe.whitelist()
def employee():
    # emp = frappe.db.sql(""" select count(*) from `tabAttendance` where attendance_date between  '2022-04-01' and '2022-04-31'  """)
    # print(emp)
    att = frappe.db.sql(""" update  `tabGL Entry`  set posting_date = '2025-04-21' where name ='ACC-GLE-2025-32564'  """)
    print(att)



@frappe.whitelist()
def sales_order():
    sales = frappe.get_all("Sales Order",{"name":"SAL-ORD-2022-00010"},['*'])
    print(sales)


@frappe.whitelist()
def leave():
    emp = frappe.db.get('Quotation',{"name":"SAL-QTN-NC-2022-00005-1"},['*'])
    print(emp)



@frappe.whitelist()
def get_sales_price(company):
    company = frappe.db.get_value("Company",{'name':company},['country'])
    for pl in frappe.get_all('Price List'):
        if company in pl['name'] and 'Sales' in pl['name']:
            return pl['name']
    # sales_price = frappe.db.sql(""" select name from `tabPrice List`"""),as_dict=True)
    # if sales_price["name"]:
    #     return sales_price["name"]

@frappe.whitelist()
def mark_att():
    # att = frappe.db.sql(""" select count(*) from `tabAttendance` where attendance_date between '2022-05-01' and '2022-05-31'  """)
    # print(att)
    # att = frappe.db.sql(""" update `tabAttendance` set docstatus = 1 where attendance_date between '2022-05-01' and '2022-05-31'  """)
    # print(att)
    att = frappe.db.sql(""" delete from `tabAdditional Salary` where payroll_date between '2022-05-01' and '2022-05-31' """)
    print(att)

@frappe.whitelist()
def item_transfer(company,customer,item,quantity):
    warehouse = frappe.get_value("Warehouse",{"company":company,"warehouse_name":"Store A"})
    target = frappe.get_value("Warehouse",{"company":company,"warehouse_name":"Store T"})
    if warehouse:
        stock = frappe.new_doc("Stock Entry")
        stock.company = company
        stock.stock_entry_type = "Material Transfer"
        stock.customer = customer
        stock.from_warehouse = warehouse
        stock.to_warehouse = target
        stock.append("items", {
            "s_warehouse": warehouse,
            "t_warehouse": target,
            "item_code": item,
            "qty":quantity,
            "allow_zero_valuation_rate":1
        })
        stock.save(ignore_permissions=True)
        stock.submit()
        return warehouse,target

@frappe.whitelist()
def sample_warehouse(company,customer,item,quantity):
    warehouse = frappe.get_value("Warehouse",{"company":company,"warehouse_name":"Store A"})
    target = frappe.get_value("Warehouse",{"company":company,"warehouse_name":"Store T"})
    if warehouse:
        stock = frappe.new_doc("Stock Entry")
        stock.company = company
        stock.stock_entry_type = "Material Transfer"
        stock.customer = customer
        stock.from_warehouse = target
        stock.to_warehouse = warehouse
        stock.append("items", {
            "s_warehouse": target,
            "t_warehouse": warehouse,
            "item_code": item,
            "qty":quantity,
            "allow_zero_valuation_rate":1
        })
        stock.save(ignore_permissions=True)
        # stock.submit()
        return warehouse,target

@frappe.whitelist()
def generate_series(po_no):
    pr = frappe.get_doc("Purchase Receipt",{"purchase_order_no":po_no})
    for i in pr.items:
        i.starting_s_po
    return pr.items.qty

@frappe.whitelist()
def fetch_customer(file):
    customer = frappe.get_value("Sales Order", {"file_number": file}, ["customer", "prepared_by"])
    return customer


@frappe.whitelist()
def get_margin_details(item_details,company,exchange_rate,currency,name):
    item_details = json.loads(item_details)
    data_4 = ''
    if "Sales Manager" in frappe.get_roles(frappe.session.user):
        data_4 += '<table class="table"><tr><th style="padding:1px;border: 1px solid black;font-size:14px;background-color:lightgrey;color:white;" colspan=20><center><b>STOCK STATUS  &  INTERNAL COST</b></center></th></tr>'
    
        data_4+='<tr><td colspan=5 style="border: 0.5px solid black;font-size:11px;"><b>ITEM</b></td><td colspan=2 style="border: 0.5px solid black;font-size:11px;width:50%;"><b>ITEM NAME</b><td colspan=3 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=3 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=3 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td></td><td colspan=3 style="border: 0.5px solid black;font-size:11px;"><b><center>QTY</center></b></td><td colspan=3 style="border: 0.5px solid black;font-size:11px;"><b><center>INTERNAL COST</center></b></td></tr>'
    total_internal_cost = 0
    total_qty = 0
    total_selling_price = 0
    total_warehouse = 0
    total_in_transit = 0
    sum_of_total_stock = 0
    for i in item_details:
        total_qty = total_qty + i["qty"]
        country = frappe.get_value("Company",{"name":company},["country"])
        warehouse_stock = frappe.db.sql("""
            select (sum(`tabBin`.actual_qty) - sum(b.reserved_stock)) as qty from `tabBin` b 
            join `tabWarehouse` wh on wh.name = b.warehouse
            join `tabCompany` c on c.name = wh.company
            where c.country = '%s' and b.item_code = '%s' and wh.company = '%s'
            """ % (country,i["item_code"],company),as_dict=True)[0]
        if not warehouse_stock["qty"]:
            warehouse_stock["qty"] = 0
        total_warehouse = total_warehouse + warehouse_stock["qty"]

        purchase_order = frappe.db.sql("""select sum(`tabPurchase Order Item`.qty) as qty from `tabPurchase Order`
                left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
                where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 and `tabPurchase Order`.company = '%s' """%(i["item_code"],company),as_dict=True)[0] or 0 
        if not purchase_order["qty"]:
            purchase_order["qty"] = 0
        purchase_receipt = frappe.db.sql("""select sum(`tabPurchase Receipt Item`.qty) as qty from `tabPurchase Receipt`
                left join `tabPurchase Receipt Item` on `tabPurchase Receipt`.name = `tabPurchase Receipt Item`.parent
                where `tabPurchase Receipt Item`.item_code = '%s' and `tabPurchase Receipt`.docstatus = 1 and `tabPurchase Receipt`.company = '%s' """%(i["item_code"],company),as_dict=True)[0] or 0 
        if not purchase_receipt["qty"]:
            purchase_receipt["qty"] = 0
        in_transit = purchase_order["qty"] - purchase_receipt["qty"]

        total_stock = warehouse_stock["qty"] + in_transit
        total_in_transit = in_transit + total_in_transit 
        sum_of_total_stock = total_stock + sum_of_total_stock 
        # if not currency == "USD":
        #     if not company == "Norden Communication Middle East FZE":
        #         ep = get_exchange_rate('USD',currency)
        #         i["rate"] = round(i["rate"]/ep,1)

        total_selling_price =  (i["rate"] * i["qty"]) + total_selling_price
        valuation_rate = frappe.get_value("Item",{"name":i["item_code"]},["valuation_rate"])
        if not valuation_rate:
            valuation_rate = 0
        standard_buying_usd = frappe.get_value("Item Price",{"item_code":i["item_code"],"price_list":"STANDARD BUYING-USD"},["price_list_rate"])
        if not standard_buying_usd:
            standard_buying_usd = 0
        country = frappe.get_value("Company",{"name":company},["country"])
        if country == "Singapore":
            internal = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"Singapore Internal Cost"},['price_list_rate'])
            if not internal:
                internal = 0
        if country == "United Arab Emirates":
            internal = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"Internal - NCMEF"},['price_list_rate'])
            if not internal:
                internal = 0 
        if country == "India":
            internal = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"India Landing"},['price_list_rate'])
            if not internal:
                internal = 0
        if country == "United Kingdom":
            internal = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"UK Destination Charges"},['price_list_rate'])
            if not internal:
                internal = 0
        total_internal_cost = internal*i["qty"] + total_internal_cost
        if "Sales Manager" in frappe.get_roles(frappe.session.user):
            data_4+='<tr style="height:5px;"><td colspan=3 style="border: 1px solid black;font-size:11px;padding-top:10px; margin:0px;"><center>%s</center></td><td colspan=3 style="border: 1px solid black;font-size:11px;">%s</td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=3 align = "right"style="border: 1px solid black;font-size:11px;">%s</td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round((internal*i["qty"]),2))      
    if total_internal_cost == 0:
        total_margin_internal = (total_selling_price - total_internal_cost)/100
        # total_margin_internal = ((total_selling_price - total_internal_cost )/ total_internal_cost)*100
    else:
        total_margin_internal = ((total_selling_price - total_internal_cost )/total_selling_price)*100

    if "Sales Manager" in frappe.get_roles(frappe.session.user):
        data_4 += '<tr style="line-height:0.4;"><th style="padding-top:12px;border: 1px solid black;font-size:12px" colspan=6><center><b>TOTAL MARGIN BASED ON INTERNAL COST :  %s</b></center></th><td colspan=9 align = "right" style="border: 1px solid black;font-size:12px;"><b>%s</b></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:12px;"><b>%s</b></td><td colspan=9 align = "right" style="border: 1px solid black;font-size:12px;"><b>%s</b></td></tr>'%(round(total_margin_internal,2),'',total_qty,round(total_internal_cost,2))
    data_4+='</table>'


    data_5 = ''
    if "CFO" in frappe.get_roles(frappe.session.user) or "COO" in frappe.get_roles(frappe.session.user) or "HOD" in frappe.get_roles(frappe.session.user) or "Accounts User" in frappe.get_roles(frappe.session.user):
        data_5 += '<table class="table"><tr><th style="padding:1px;border: 1px solid black;font-size:14px;background-color:#32CD32;color:white;" colspan=16><center><b>MARGIN BY VALUE & MARGIN BY PERCENTAGE</b></center></th></tr>'
        spl = 0
        for i in item_details:
            if i["special_cost"] > 0:
                spl = spl + 1
        if spl == 0:
            data_5+='<tr><td colspan=4 style="border:1px solid black;font-size:11px;"><b>ITEM</b></td><td colspan=2 style="border: 1px solid black;font-size:11px;width:40%;"><b>ITEM NAME</b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SELLING PRICE</b></td></tr>'
        else:
            data_5+='<tr><td colspan=4 style="border:1px solid black;font-size:11px;"><b>ITEM</b></td><td colspan=2 style="border: 1px solid black;font-size:11px;width:40%;"><b>ITEM NAME</b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SPECIAL PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SELLING PRICE</b></td></tr>'

    total_internal_cost = 0
    total_qty = 0
    total_special_price = 0
    total_selling_price = 0
    cost_total = 0
    total_valuation_rate = 0
    spcl = 0
    total_warehouse = 0
    total_in_transit = 0
    sum_of_total_stock = 0
    for i in item_details:
        total_qty = total_qty + i["qty"]
        country = frappe.get_value("Company",{"name":company},["country"])
        warehouse_stock = frappe.db.sql("""
            select (sum(`tabBin`.actual_qty) - sum(b.reserved_stock)) as qty from `tabBin` b 
            join `tabWarehouse` wh on wh.name = b.warehouse
            join `tabCompany` c on c.name = wh.company
            where c.country = '%s' and b.item_code = '%s' and wh.company = '%s'
            """ % (country,i["item_code"],company),as_dict=True)[0]
        if not warehouse_stock["qty"]:
            warehouse_stock["qty"] = 0
        total_warehouse = total_warehouse + warehouse_stock["qty"]

        purchase_order = frappe.db.sql("""select sum(`tabPurchase Order Item`.qty) as qty from `tabPurchase Order`
                left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
                where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 and `tabPurchase Order`.company = '%s' """%(i["item_code"],company),as_dict=True)[0] or 0 
        if not purchase_order["qty"]:
            purchase_order["qty"] = 0
        purchase_receipt = frappe.db.sql("""select sum(`tabPurchase Receipt Item`.qty) as qty from `tabPurchase Receipt`
                left join `tabPurchase Receipt Item` on `tabPurchase Receipt`.name = `tabPurchase Receipt Item`.parent
                where `tabPurchase Receipt Item`.item_code = '%s' and `tabPurchase Receipt`.docstatus = 1 and `tabPurchase Receipt`.company = '%s'"""%(i["item_code"],company),as_dict=True)[0] or 0 
        if not purchase_receipt["qty"]:
            purchase_receipt["qty"] = 0
        in_transit = purchase_order["qty"] - purchase_receipt["qty"]
        total_in_transit = in_transit + total_in_transit 
        sum_of_total_stock = total_stock + sum_of_total_stock 
        if i["special_cost"] > 0:
            spcl = spcl + 1
        # if not currency == "USD":
        #     ep = get_exchange_rate('USD',currency)
        #     i["rate"] = round(i["rate"]/ep,1)
        country = frappe.get_value("Company",{"name":company},["country"])
        if country == "Singapore":
            internal = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"Singapore Internal Cost"},['price_list_rate'])
            if not internal:
                internal = 0
        if country == "United Arab Emirates":
            internal = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"Internal - NCMEF"},['price_list_rate'])
            if not internal:
                internal = 0 
        if country == "India":
            internal = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"India Landing"},['price_list_rate'])
            if not internal:
                internal = 0
        if country == "United Kingdom":
            internal = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"UK Destination Charges"},['price_list_rate'])
            if not internal:
                internal = 0
        if internal== 0:
            i_margin = 0
        if internal > 0:
            i_margin = (((i["rate"] * i["qty"]) - (internal*i["qty"]))/(i["rate"] * i["qty"]))*100
        buying_cost = frappe.get_value("Item Price",{"item_code":i["item_code"],"price_list":"STANDARD BUYING-USD"},["price_list_rate"])
        if not buying_cost:
            bc_margin = 0
        if buying_cost:
            buying_cost_conversion = get_exchange_rate("USD",currency)
            buying_cost = buying_cost * buying_cost_conversion
            bc_margin = (i["rate"] - buying_cost)/i["rate"]*100
        stock_price = frappe.get_value("Item",{"name":i["item_code"]},["valuation_rate"])
        if not stock_price:
            stock_margin = 0
        if stock_price:
            stock_margin = (((i["rate"] * i["qty"]) - (stock_price * i["qty"]))/(i["rate"] * i["qty"]))*100

        total_selling_price =  (i["rate"] * i["qty"]) + total_selling_price
        valuation_rate = frappe.get_value("Item",{"name":i["item_code"]},["valuation_rate"])
        if not valuation_rate:
            valuation_rate = 0
        total_valuation_rate = (valuation_rate * i["qty"]) + total_valuation_rate
        standard_buying_usd = frappe.get_value("Item Price",{"item_code":i["item_code"],"price_list":"STANDARD BUYING-USD"},["price_list_rate"])
        base_cost_conversion = get_exchange_rate("USD",currency)
        if not standard_buying_usd:
            standard_buying_usd = 0
        else:
            standard_buying_usd =  base_cost_conversion * standard_buying_usd
        cost_total = (standard_buying_usd * i["qty"]) + cost_total
        country = frappe.get_value("Company",{"name":company},["country"])
        
        total_internal_cost = internal*i["qty"] + total_internal_cost
        total_special_price =(i["special_cost"] * i["qty"]) + total_special_price

        if "CFO" in frappe.get_roles(frappe.session.user) or "COO" in frappe.get_roles(frappe.session.user) or "HOD" in frappe.get_roles(frappe.session.user) or "Accounts User" in frappe.get_roles(frappe.session.user):
            if i["special_cost"] > 0:
                data_5+='<tr><td colspan=4 style="border: 1px solid black;font-size:11px;">%s</td><td colspan=2 style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],standard_buying_usd,"{:.2f}".format(bc_margin),round(internal,2),round(i_margin,2),round(i["special_cost"],2),round((i["rate"]*i["qty"]),2))
            else:
                data_5+='<tr><td colspan=4 style="border: 1px solid black;font-size:11px;">%s</td><td colspan=2 style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round((standard_buying_usd*i["qty"]),2),round(bc_margin,2),round((internal*i["qty"]),2),round(i_margin,2),round((i["rate"]*i["qty"]),2))
    if cost_total == 0:
        total_margin_cost = (total_selling_price - cost_total)/100
    else:
        total_margin_cost = (total_selling_price - cost_total)/total_selling_price*100
    
    if total_valuation_rate == 0:
        total_margin_valuation= (total_selling_price - total_valuation_rate)/100
    else:
        total_margin_valuation = ((total_selling_price - total_valuation_rate )/total_selling_price)*100
    if total_internal_cost == 0:
        total_margin_internal = (total_selling_price - total_internal_cost)/100
        # total_margin_internal = ((total_selling_price - total_internal_cost )/ total_internal_cost)*100
    else:
        total_margin_internal = ((total_selling_price - total_internal_cost )/total_selling_price)*100
    
    if total_special_price == 0:
        total_margin_special = (total_selling_price - total_special_price)/100
    else:
        total_margin_special = ((total_selling_price - total_special_price)/total_selling_price)*100
    if "CFO" in frappe.get_roles(frappe.session.user) or "COO" in frappe.get_roles(frappe.session.user) or "HOD" in frappe.get_roles(frappe.session.user) or "Accounts User" in frappe.get_roles(frappe.session.user):
        if spcl == 0:
            data_5 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON INTERNAL COST : %s </b></center></th><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(round(total_margin_internal,2),'',total_qty,round(cost_total,2),round(total_margin_cost,2),round(total_internal_cost,2),round(total_margin_internal,2),round(total_selling_price,2))
        else:
            data_5 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON INTERNAL COST : %s </b></center></th><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(round(total_margin_internal,2),'',total_qty,round(cost_total,2),round(total_internal_cost,2),round(total_margin_internal,2),round(total_margin_special,2),'',round(total_selling_price,2))
    data_5+='</table>'


    # data = ''
    # data += '<table class="table"><tr><th style="padding:1px;border: 1px solid black;font-size:14px;background-color:#32CD32;" colspan=9><center><b>COST</b></center></th></tr>'
    # data+='<tr><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>ITEM</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>ITEM NAME</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>STOCK PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>SPECIAL PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>SELLING PRICE</b></td></tr>'
    # total_cost = 0
    # total_stock_price = 0
    # total_internal_cost = 0
    # total_special_price = 0
    # total_selling_price = 0
    # cost_total = 0
    # total_valuation_rate = 0
    # total_internal_cost = 0
    # total_special_price = 0
    # total_selling_price = 0
    # for i in item_details:
    #     if not currency == "USD":
    #         if not company == "Norden Communication Middle East FZE":
    #             ep = get_exchange_rate('USD',currency)
    #             i["rate"] = round(i["rate"]/ep,1)
    #     # c = CurrencyRates()
    #     # if not currency == "USD":
    #     #     ep = c.get_rate('USD','%s'%(currency))
    #     #     i["rate"] = round(i["rate"]/ep,1)
    #     total_selling_price =  (i["rate"] * i["qty"]) + total_selling_price
    #     valuation_rate = frappe.get_value("Item",{"name":i["item_code"]},["valuation_rate"])
    #     if not valuation_rate:
    #         valuation_rate = 0
    #     total_valuation_rate = (valuation_rate * i["qty"]) + total_valuation_rate
    #     standard_buying_usd = frappe.get_value("Item Price",{"item_code":i["item_code"],"price_list":"STANDARD BUYING-USD"},["price_list_rate"])
    #     if not standard_buying_usd:
    #         standard_buying_usd = 0
    #     cost_total = (standard_buying_usd * i["qty"]) + cost_total
    #     country = frappe.get_value("Company",{"name":company},["country"])
    #     if country == "Singapore":
    #         internal = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"Singapore Internal Cost"},['price_list_rate'])
    #         # internal = frappe.db.sql(""" select price_list_rate from `tabItem Price` where item_code = '%s'  and price_list = '%s' """%(i["item_code"],"Singapore Internal Cost"), as_dict=True)
    #         if not internal:
    #             internal = 0
    #     if country == "United Arab Emirates":
    #         internal = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"Internal - NCMEF"},['price_list_rate'])
    #         # internal = frappe.db.sql(""" select price_list_rate from `tabItem Price` where item_code = '%s'  and price_list = '%s' """%(i["item_code"],"Internal - NCMEF"), as_dict=True)
    #         if not internal:
    #             internal = 0 
    #     if country == "India":
    #         internal = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"India Landing"},['price_list_rate'])
    #         # internal = frappe.db.sql(""" select price_list_rate from `tabItem Price` where item_code = '%s'  and price_list = '%s' """%(i["item_code"],"STANDARD BUYING-USD"), as_dict=True)
    #         if not internal:
    #             internal = 0

    #     if country == "United Kingdom":
    #         internal = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"UK Destination Charges"},['price_list_rate'])
    #         # internal = frappe.db.sql(""" select price_list_rate from `tabItem Price` where item_code = '%s'  and price_list = '%s' """%(item["item_code"],"STANDARD BUYING-USD"), as_dict=True)
    #         if not internal:
    #             internal = 0
    #     total_internal_cost = (internal * i["qty"]) + total_internal_cost
    #     total_special_price =(i["special_cost"] * i["qty"]) + total_special_price
    #     total_cost = standard_buying_usd + total_cost
    #     total_stock_price  = valuation_rate + total_stock_price
    #     total_internal_cost = internal + total_internal_cost
    #     total_special_price = i["special_cost"] + total_special_price
    #     total_selling_price = i["rate"] + total_selling_price
    #     data+='<tr><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s</b></td></tr>'%(i["item_code"],i["description"],standard_buying_usd,valuation_rate,round(internal,2),i["special_cost"],i["rate"])
    # if cost_total == 0:
    #     total_margin_cost = (total_selling_price - cost_total)/100
    # else:
    #     total_margin_cost = ((total_selling_price - cost_total)/cost_total)*100
    # # total_margin_cost = ((total_selling_price - cost_total)/cost_total)*100
    # if total_valuation_rate == 0:
    #     total_margin_valuation= (total_selling_price - total_valuation_rate)/100
    # else:
    #     total_margin_valuation = ((total_selling_price - total_valuation_rate )/total_valuation_rate)*100
    # # total_margin_valuation = ((total_selling_price - total_valuation_rate )/total_valuation_rate)*100

    # if total_internal_cost == 0:
    #     total_margin_internal = (total_selling_price - total_internal_cost)/100
    # else:
    #     total_margin_internal = ((total_selling_price - total_internal_cost )/ total_internal_cost)*100

    # # total_margin_internal = ((total_selling_price - total_internal_cost )/ total_internal_cost)*100
    # if i["special_cost"] == 0:
    #     total_margin_special = (total_selling_price - total_special_price)/100
    # else:
    #     total_margin_special = ((total_selling_price - total_special_price)/total_special_price)*100
    # data += '<tr><th style="padding:1px;border: 1px solid black;font-size:14px" colspan=2><center><b>TOTAL MARGIN</b></center></th><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s</b><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s</b></td></tr>'%(round(total_margin_cost,2),round(total_margin_valuation,2),round(total_margin_internal,2),round(total_margin_special,2),'')
    # data+='</table>'

    # data_1 = '' 
    # data_1 += '<table class="table table-bordered"><tr><th style="padding:1px;border: 1px solid black;font-size:14px;background-color:#32CD32;" colspan=9><center><b>MARGIN</b></center></th></tr>'
    # data_1+='<tr><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>ITEM</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>ITEM NAME</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>STOCK PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>SPECIAL PRICE</b></td></tr>'
    # for item in item_details:
    #     # c = CurrencyRates()
    #     # if not currency == "USD":
    #     #     ep = c.get_rate('USD','%s'%(currency))
    #     #     item["rate"] = round(item["rate"]/ep,1)
    #     country = frappe.get_value("Company",{"name":company},["country"])
    #     if country == "Singapore":
    #         internal = frappe.get_value("Item Price",{'item_code':item["item_code"],'price_list':"Singapore Internal Cost"},['price_list_rate'])
    #         if not internal:
    #             internal = 0

    #     if country == "United Arab Emirates":
    #         internal = frappe.get_value("Item Price",{'item_code':item["item_code"],'price_list':"Internal - NCMEF"},['price_list_rate'])
    #         if not internal:
    #             internal = 0

    #     if country == "India":
    #         internal = frappe.get_value("Item Price",{'item_code':item["item_code"],'price_list':"India Landing"},['price_list_rate'])
    #         if not internal:
    #             internal = 0

    #     if country == "United Kingdom":
    #         internal = frappe.get_value("Item Price",{'item_code':item["item_code"],'price_list':"UK Destination Charges"},['price_list_rate'])
    #         # internal = frappe.db.sql(""" select price_list_rate from `tabItem Price` where item_code = '%s'  and price_list = '%s' """%(item["item_code"],"STANDARD BUYING-USD"), as_dict=True)
    #         if not internal:
    #             internal = 0

    #     if internal == 0:
    #         i_margin = (item["rate"] - internal)/100
    #     if not internal == 0:
    #         i_margin = ((item["rate"] - internal)/internal)*100
        
    #     standard_buying_usd = frappe.get_value("Item Price",{"item_code":item["item_code"],"price_list":"STANDARD BUYING-USD"},["price_list_rate"])
       
    #     if not standard_buying_usd:  
    #         standard_buying_usd = 0
    #         c_margin = (item["rate"] - standard_buying_usd)/100
    #     elif standard_buying_usd:
    #         c_margin = ((item["rate"] - standard_buying_usd)/standard_buying_usd)*100
       

    #     valuation_rate = frappe.get_value("Item",{"name":item["item_code"]},["valuation_rate"])
    #     if not valuation_rate:  
    #         valuation_rate = 0
    #         v_margin = (item["rate"] - valuation_rate)/100
    #     elif valuation_rate:
    #         v_margin = ((item["rate"] - valuation_rate)/valuation_rate)*100
        
        
    #     if not item["special_cost"]: 
    #         item["special_cost"] = 0 
    #         s_margin = (item["rate"] - item["special_cost"])/100
    #     elif item["special_cost"]:
    #         s_margin = ((item["rate"] - item["special_cost"])/item["special_cost"])*100
       

    #     data_1+='<tr><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s</b></td></tr>'%(item["item_code"],item["description"],round(c_margin,2),round(v_margin,2),round(i_margin,2),round(s_margin,2),)
    # # data_1+= '<tr><th style="padding:1px;border: 1px solid black;font-size:14px" colspan=2><center><b>TOTAL</b></center></th><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s</b></td></tr>'%(round(total_c_margin,2),round(total_v_margin,2),round(total_i_margin,2),round(total_s_margin,2),)
    # data_1+='</table>'




    
    # data_2 = ''
    # data_2 += '<table class="table table-bordered"><tr><th style="padding:1px;border: 1px solid black;font-size:14px;background-color:#32CD32;" colspan=8><center><b>STOCK STATUS</b></center></th></tr>'
    # data_2+='<tr><td colspan=1 style="border: 1px solid black;font-size:12px;"><center><b>STOCK</b><center></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><center><b>PO</b><center></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><center><b>TOTAL</b><center></td></tr>'
    # for j in item_details:
    #     country = frappe.get_value("Company",{"name":company},["country"])
    #     warehouse_stock = frappe.db.sql("""
    #     select sum(b.actual_qty) as qty from `tabBin` b 
    #     join `tabWarehouse` wh on wh.name = b.warehouse
    #     join `tabCompany` c on c.name = wh.company
    #     where c.country = '%s' and b.item_code = '%s'
    #     """ % (country,j["item_code"]),as_dict=True)[0]
    #     if not warehouse_stock["qty"]:
    #         warehouse_stock["qty"] = 0
    #     purchase_order = frappe.db.sql("""select sum(`tabPurchase Order Item`.qty) as qty from `tabPurchase Order`
    #             left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
    #             where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 """%(j["item_code"]),as_dict=True)[0] or 0 
    #     if not purchase_order["qty"]:
    #         purchase_order["qty"] = 0
    #     purchase_receipt = frappe.db.sql("""select sum(`tabPurchase Receipt Item`.qty) as qty from `tabPurchase Receipt`
    #             left join `tabPurchase Receipt Item` on `tabPurchase Receipt`.name = `tabPurchase Receipt Item`.parent
    #             where `tabPurchase Receipt Item`.item_code = '%s' and `tabPurchase Receipt`.docstatus = 1 """%(j["item_code"]),as_dict=True)[0] or 0 
    #     if not purchase_receipt["qty"]:
    #         purchase_receipt["qty"] = 0
    #     in_transit = purchase_order["qty"] - purchase_receipt["qty"]
    #     total = warehouse_stock["qty"] + in_transit
    #     data_2+='<tr><td colspan=1 style="border: 1px solid black;font-size:12px;"><center><b>%s</b><center><center></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><center><b>%s</b></center></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><center><b>%s</b></center></td></tr>'%(warehouse_stock["qty"], in_transit,total)
    # data_2+='</table>'
        # country = frappe.get_value("Company",{"name":company},["country"])
        # if country == "Singapore":
        #     internal = frappe.db.sql(""" select price_list_rate from `tabItem Price` where item_code = '%s'  and price_list = '%s' """%(i["item_code"],"Singapore Internal Cost"), as_dict=True)[0]
        # if country == "United Arab Emirates":
        #     internal = frappe.db.sql(""" select price_list_rate from `tabItem Price` where item_code = '%s'  and price_list = '%s' """%(i["item_code"],"Internal - NCMEF"), as_dict=True)[0]
        # if country == "India":
        #     internal = frappe.db.sql(""" select price_list_rate from `tabItem Price` where item_code = '%s'  and price_list = '%s' """%(i["item_code"],"STANDARD BUYING-USD"), as_dict=True)[0]
    
       
    
    return data_4,data_5


@frappe.whitelist()
def fetch_file_number(order_no):
    po = frappe.get_value("Purchase Order",{"name":order_no},["delivery_term"])
    return po



@frappe.whitelist()
def inco_terms(order_no):
    material = frappe.db.sql("""select `tabPurchase Order Item`.material_request as material_request  
                            from `tabPurchase Order` left join `tabPurchase Order Item`
                            on `tabPurchase Order`.name = `tabPurchase Order Item`.parent 
                            where `tabPurchase Order`.docstatus !=2 and `tabPurchase Order`.name = '%s' """%(order_no),as_dict=True)[0]
    mat_no = material['material_request']
    sale = frappe.db.sql("""select `tabPurchase Order Item`.sales_order as sales_order  
                            from `tabPurchase Order` left join `tabPurchase Order Item`
                            on `tabPurchase Order`.name = `tabPurchase Order Item`.parent 
                            where `tabPurchase Order`.docstatus !=2 and `tabPurchase Order`.name = '%s' """%(order_no),as_dict=True)[0]
    sale_no = sale['sales_order']
    if sale_no:
        so_no = frappe.get_value("Sales Order",{"name":sale_no},["delivery"])
        return so_no
    elif mat_no: 
        so = frappe.get_value("Material Request",{"name":mat_no},["sales_order_number"])
        if so:
            po = frappe.get_value("Sales Order",{"name":so},["delivery"])


            return po

       

@frappe.whitelist()
def create_altair(supplier,requester,series,company,date,required,consignment_type,country,cargo_type,items,name,set_warehouse,tax_category,taxes_and_charges):
    po = frappe.new_doc("Purchase Order")
    po.supplier = "Altair"
    po.altair = name +"-"+"1"
    po.requester_name = requester
    po.naming_series = series
    po.company = company
    po.transaction_date = date
    po.schedule_date = required
    po.consignment_type = consignment_type
    po.mode_of_dispatch = cargo_type
    # po.our_trn = trn
    po.original_purchase_order = name
    # po.batch = batch
    # po.supplier_address = supplier_address
    # po.billing_address = billing_address
    po.set_warehouse = set_warehouse
    po.tax_category = tax_category
    po.taxes_and_charges = taxes_and_charges
    # po.payment_terms_template = payment_terms
    item_details = json.loads(items)
    for i in item_details:
        po.append("items", {
        "item_code": i["item_code"],
        "schedule_date": i["schedule_date"],
        "qty": i["qty"],
        "warehouse": i["warehouse"]
        })
    po.save(ignore_permissions=True)
    # rename_doc("Purchase Order", po.name,str(po.name) + "-" + "1",ignore_permissions=True)
    # po.rename_doc("Account", name, new_name, force=1)

    return "Purchase order for Altair is created"

@frappe.whitelist()
def check_po(original,name):
    po = frappe.get_doc("Purchase Order",original)
    po.processed_by_altair = 1
    po.altair_purchase_order_number = name
    po.save(ignore_permissions=True)

@frappe.whitelist()
def check_uom(item_code):
    uom = frappe.get_value("Item",{"name":item_code},["stock_uom"])
    return uom

@frappe.whitelist()
def check_tax(name):
    tax = frappe.get_value("Sales Order",{"name":name},["taxes_and_charges"])
    return tax

@frappe.whitelist()
def set_workflow(name):
    workflow = frappe.get_doc("Quotation",{"name":name}) 
    workflow.workflow_state = "Pending for HOD"
    workflow.save(ignore_permissions=True)
    workflow.reload()

@frappe.whitelist()
def get_item_margin(item_details,company,currency,exchange_rate,user):
    # role = frappe.db.sql(""" select `tabHas Role`.role as role from tabUser left join `tabHas Role` on `tabUser`.name = `tabHas Role`.parent where `tabUser`.name ='%s' """%(user),as_dict=True)
    # for i in role:
    #     
    # role = frappe.get_doc("Has Role",{"parent":user})
    # role = frappe.get_value("User",{"name":user},["roles"])
    
    item_details = json.loads(item_details)
    # data = ''
    # data += '<table class="table"><tr><th style="padding:1px;border: 1px solid black;font-size:14px;background-color:#FF4500;color:white;" colspan=9><center><b>MARGIN</b></center></th></tr>'
    # if "Sales Manager" in frappe.get_roles(frappe.session.user):
    #     data+='<tr><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>ITEM</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>ITEM NAME</b></td><td colspan=5 style="border: 1px solid black;font-size:12px;"><b><center>INTERNAL COST</center></b></td></tr>'
    # if "CFO" in frappe.get_roles(frappe.session.user) or "COO" in frappe.get_roles(frappe.session.user) or "HOD" in frappe.get_roles(frappe.session.user):
    #     data+='<tr><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>ITEM</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>ITEM NAME</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>STOCK PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>SPECIAL PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>SELLING PRICE</b></td></tr>'
    # # data+='<tr><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>ITEM</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>ITEM NAME</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>STOCK PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>SPECIAL PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>SELLING PRICE</b></td></tr>'
    # total_cost = 0
    # total_stock_price = 0
    # total_internal_cost = 0
    # total_special_price = 0
    # total_selling_price = 0
    # cost_total = 0
    # total_valuation_rate = 0
    # total_internal_cost = 0
    # total_special_price = 0
    # total_selling_price = 0
    # for i in item_details:
    #     c = CurrencyRates()
    #     if not currency == "USD":
    #         ep = c.get_rate('USD','%s'%(currency))
    #         i["rate"] = round(i["rate"]/ep,1)

    #     total_selling_price =  (i["rate"] * i["qty"]) + total_selling_price
    #     valuation_rate = frappe.get_value("Item",{"name":i["item_code"]},["valuation_rate"])
    #     if not valuation_rate:
    #         valuation_rate = 0
    #     total_valuation_rate = (valuation_rate * i["qty"]) + total_valuation_rate
    #     standard_buying_usd = frappe.get_value("Item Price",{"item_code":i["item_code"],"price_list":"STANDARD BUYING-USD"},["price_list_rate"])
    #     if not standard_buying_usd:
    #         standard_buying_usd = 0
    #     cost_total = (standard_buying_usd * i["qty"]) + cost_total
    #     country = frappe.get_value("Company",{"name":company},["country"])
    #     if country == "Singapore":
    #         internal = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"Singapore Internal Cost"},['price_list_rate'])
    #         # internal = frappe.db.sql(""" select price_list_rate from `tabItem Price` where item_code = '%s'  and price_list = '%s' """%(i["item_code"],"Singapore Internal Cost"), as_dict=True)
    #         if not internal:
    #             internal = 0
    #     if country == "United Arab Emirates":
    #         internal = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"Internal - NCMEF"},['price_list_rate'])
    #         # internal = frappe.db.sql(""" select price_list_rate from `tabItem Price` where item_code = '%s'  and price_list = '%s' """%(i["item_code"],"Internal - NCMEF"), as_dict=True)
    #         if not internal:
    #             internal = 0 
    #     if country == "India":
    #         internal = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"India Landing"},['price_list_rate'])
    #         # internal = frappe.db.sql(""" select price_list_rate from `tabItem Price` where item_code = '%s'  and price_list = '%s' """%(i["item_code"],"STANDARD BUYING-USD"), as_dict=True)
    #         if not internal:
    #             internal = 0

    #     if country == "United Kingdom":
    #         internal = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"UK Destination Charges"},['price_list_rate'])
    #         # internal = frappe.db.sql(""" select price_list_rate from `tabItem Price` where item_code = '%s'  and price_list = '%s' """%(item["item_code"],"STANDARD BUYING-USD"), as_dict=True)
    #         if not internal:
    #             internal = 0
    #    
    #     total_internal_cost = (internal * i["qty"]) + total_internal_cost
    #     total_special_price =(i["special_cost"] * i["qty"]) + total_special_price
    #     total_cost = standard_buying_usd + total_cost
    #     total_stock_price  = valuation_rate + total_stock_price
    #     total_internal_cost = internal + total_internal_cost
    #     total_special_price = i["special_cost"] + total_special_price
    #     total_selling_price = i["rate"] + total_selling_price
    #     if "Sales Manager" in frappe.get_roles(frappe.session.user):
    #         data+='<tr><td colspan=1 style="border: 1px solid black;font-size:12px;">%s</td><td colspan=1 style="border: 1px solid black;font-size:12px;">%s</td><td colspan=5 style="border: 1px solid black;font-size:12px;"><center>%s</center></td></tr>'%(i["item_code"],i["description"],round(internal,2))
    #     if "CFO" in frappe.get_roles(frappe.session.user) or "COO" in frappe.get_roles(frappe.session.user) or "HOD" in frappe.get_roles(frappe.session.user):
    #         data+='<tr><td colspan=1 style="border: 1px solid black;font-size:12px;">%s</td><td colspan=1 style="border: 1px solid black;font-size:12px;">%s</td><td colspan=1 style="border: 1px solid black;font-size:12px;">%s</td><td colspan=1 style="border: 1px solid black;font-size:12px;">%s</td><td colspan=1 style="border: 1px solid black;font-size:12px;">%s</td><td colspan=1 style="border: 1px solid black;font-size:12px;">%s</td><td colspan=1 style="border: 1px solid black;font-size:12px;">%s</td></tr>'%(i["item_code"],i["description"],standard_buying_usd,valuation_rate,round(internal,2),i["special_cost"],i["rate"])
    # if cost_total == 0:
    #     total_margin_cost = (total_selling_price - cost_total)/100
    # else:
    #     total_margin_cost = ((total_selling_price - cost_total)/cost_total)*100
    # # total_margin_cost = ((total_selling_price - cost_total)/cost_total)*100
    # if total_valuation_rate == 0:
    #     total_margin_valuation= (total_selling_price - total_valuation_rate)/100
    # else:
    #     total_margin_valuation = ((total_selling_price - total_valuation_rate )/total_valuation_rate)*100
    # # total_margin_valuation = ((total_selling_price - total_valuation_rate )/total_valuation_rate)*100

    # if total_internal_cost == 0:
    #     total_margin_internal = (total_selling_price - total_internal_cost)/100
    # else:
    #     total_margin_internal = ((total_selling_price - total_internal_cost )/ total_internal_cost)*100

    # # total_margin_internal = ((total_selling_price - total_internal_cost )/ total_internal_cost)*100
    # if i["special_cost"] == 0:
    #     total_margin_special = (total_selling_price - total_special_price)/100
    # else:
    #     total_margin_special = ((total_selling_price - total_special_price)/total_special_price)*100
    # if "Sales Manager" in frappe.get_roles(frappe.session.user):
    #     data += '<tr><th style="padding:1px;border: 1px solid black;font-size:12px" colspan=3><center><b>TOTAL MARGIN</b></center></th><td colspan=4 style="border: 1px solid black;font-size:12px;"><b><center>%s</center></b></td></tr>'%(round(total_margin_internal,2))
    # if "CFO" in frappe.get_roles(frappe.session.user) or "COO" in frappe.get_roles(frappe.session.user) or "HOD" in frappe.get_roles(frappe.session.user):
    #     data += '<tr><th style="padding:1px;border: 1px solid black;font-size:12px" colspan=2><center><b>TOTAL MARGIN</b></center></th><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s %% </b><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s %% </b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s %% </b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s %% </b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s</b></td></tr>'%(round(total_margin_cost,2),round(total_margin_valuation,2),round(total_margin_internal,2),round(total_margin_special,2),'')
    # data+='</table>'



    data_4 = ''
    if "Sales Manager" in frappe.get_roles(frappe.session.user):
        data_4 += '<table class="table"><tr><th style="padding:1px;border: 1px solid black;font-size:14px;background-color:#FF4500;color:white;" colspan=20><center><b>STOCK STATUS  &  INTERNAL COST</b></center></th></tr>'
    
        data_4+='<tr><td colspan=3 style="border: 0.5px solid black;font-size:11px;"><b>ITEM</b></td><td colspan=3 style="border: 0.5px solid black;font-size:11px;width:30%;"><b>ITEM NAME</b><td colspan=3 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=3 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=3 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td></td><td colspan=3 style="border: 0.5px solid black;font-size:11px;"><b><center>QTY</center></b></td><td colspan=3 style="border: 0.5px solid black;font-size:11px;"><b><center>INTERNAL COST</center></b></td></tr>'
    total_internal_cost = 0
    total_selling_price = 0
    total_warehouse = 0
    total_in_transit = 0
    total_qty = 0
    sum_of_total_stock = 0
    for i in item_details:
        total_qty = total_qty + i["qty"]
        country = frappe.get_value("Company",{"name":company},["country"])
        warehouse_stock = frappe.db.sql("""
            select sum(b.actual_qty) as qty from `tabBin` b 
            join `tabWarehouse` wh on wh.name = b.warehouse
            join `tabCompany` c on c.name = wh.company
            where c.country = '%s' and b.item_code = '%s' and wh.company = '%s'
            """ % (country,i["item_code"],company),as_dict=True)[0]
        if not warehouse_stock["qty"]:
            warehouse_stock["qty"] = 0
        total_warehouse = total_warehouse + warehouse_stock["qty"]

        purchase_order = frappe.db.sql("""select sum(`tabPurchase Order Item`.qty) as qty from `tabPurchase Order`
                left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
                where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2  and `tabPurchase Order`.company = '%s' """%(i["item_code"],company),as_dict=True)[0] or 0 
        if not purchase_order["qty"]:
            purchase_order["qty"] = 0
        purchase_receipt = frappe.db.sql("""select sum(`tabPurchase Receipt Item`.qty) as qty from `tabPurchase Receipt`
                left join `tabPurchase Receipt Item` on `tabPurchase Receipt`.name = `tabPurchase Receipt Item`.parent
                where `tabPurchase Receipt Item`.item_code = '%s' and `tabPurchase Receipt`.docstatus = 1 and `tabPurchase Receipt`.company = '%s' """%(i["item_code"],company),as_dict=True)[0] or 0 
        if not purchase_receipt["qty"]:
            purchase_receipt["qty"] = 0
        in_transit = purchase_order["qty"] - purchase_receipt["qty"]

        total_stock = warehouse_stock["qty"] + in_transit
        total_in_transit = in_transit + total_in_transit 
        sum_of_total_stock = total_stock + sum_of_total_stock 
        # if not currency == "USD":
        #     if not company == "Norden Communication Middle East FZE":
        #         ep = get_exchange_rate('USD',currency)
        #         i["rate"] = round(i["rate"]/ep,1)
        total_selling_price =  (i["rate"]*i["qty"]) + total_selling_price
        valuation_rate = frappe.get_value("Item",{"name":i["item_code"]},["valuation_rate"])
        if not valuation_rate:
            valuation_rate = 0
        standard_buying_usd = frappe.get_value("Item Price",{"item_code":i["item_code"],"price_list":"STANDARD BUYING-USD"},["price_list_rate"])
        if not standard_buying_usd:
            standard_buying_usd = 0
        country = frappe.get_value("Company",{"name":company},["country"])
        total_internal_cost = (i["internal_cost"]*i["qty"]) + total_internal_cost
        if "Sales Manager" in frappe.get_roles(frappe.session.user):
            data_4+='<tr style="height:5px;"><td colspan=3 style="border: 1px solid black;font-size:11px;padding:0px; margin:0px;"><center>%s</center></td><td colspan=3 style="border: 1px solid black;font-size:11px;">%s</td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=3 align = "right"style="border: 1px solid black;font-size:11px;">%s</td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round((i["internal_cost"]*i["qty"]),2))      
    if total_internal_cost == 0:
        total_margin_internal = (total_selling_price - total_internal_cost)/100
        # total_margin_internal = ((total_selling_price - total_internal_cost )/ total_internal_cost)*100
    else:
        total_margin_internal = (total_selling_price - total_internal_cost )/(total_selling_price)*100

    if "Sales Manager" in frappe.get_roles(frappe.session.user):
        data_4 += '<tr style="line-height:0.4;"><th style="padding-top:12px;border: 1px solid black;font-size:12px" colspan=6><center><b>TOTAL MARGIN BASED ON INTERNAL COST: %s </b></center></th><td align = "right" colspan=7 style="border: 1px solid black;font-size:12px;"><b>%s</b></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:12px;"><b>%s</b></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:12px;"><b>%s</b></td></tr>'%(round(total_margin_internal,2),'',total_qty,round(total_internal_cost,2))
    data_4+='</table>'

    data_5 = ''
    if "CFO" in frappe.get_roles(frappe.session.user) or "COO" in frappe.get_roles(frappe.session.user) or "HOD" in frappe.get_roles(frappe.session.user) or "Accounts User" in frappe.get_roles(frappe.session.user) or "Operation Director" in frappe.get_roles(frappe.session.user):
        data_5 += '<table class="table"><tr><th style="padding:1px;border: 1px solid black;font-size:14px;background-color:#FF4500;color:white;" colspan=18><center><b>MARGIN BY VALUE & MARGIN BY PERCENTAGE</b></center></th></tr>'
        spl = 0
        for i in item_details:
            if i["special_cost"] > 0:
                spl = spl + 1
        if spl == 0:
            data_5+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=2 style="border: 1px solid black;font-size:11px;width:30%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SELLING PRICE</b></td></tr>'
        else:
            data_5+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=2 style="border: 1px solid black;font-size:11px;width:30%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SPECIAL PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SELLING PRICE</b></td></tr>'

    total_internal_cost = 0
    total_special_price = 0
    total_selling_price = 0
    cost_total = 0
    total_valuation_rate = 0
    spcl = 0
    total_warehouse = 0
    total_in_transit = 0
    total_stock = 0
    sum_of_total_stock = 0
    for i in item_details:
        country = frappe.get_value("Company",{"name":company},["country"])
        warehouse_stock = frappe.db.sql("""
            select sum(b.actual_qty) as qty from `tabBin` b 
            join `tabWarehouse` wh on wh.name = b.warehouse
            join `tabCompany` c on c.name = wh.company
            where c.country = '%s' and b.item_code = '%s' and wh.company = '%s'
            """ % (country,i["item_code"],company),as_dict=True)[0]
        if not warehouse_stock["qty"]:
            warehouse_stock["qty"] = 0
        total_warehouse = total_warehouse + warehouse_stock["qty"]

        purchase_order = frappe.db.sql("""select sum(`tabPurchase Order Item`.qty) as qty from `tabPurchase Order`
                left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
                where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 and `tabPurchase Order`.company = '%s'  """%(i["item_code"],company),as_dict=True)[0] or 0 
        if not purchase_order["qty"]:
            purchase_order["qty"] = 0
        purchase_receipt = frappe.db.sql("""select sum(`tabPurchase Receipt Item`.qty) as qty from `tabPurchase Receipt`
                left join `tabPurchase Receipt Item` on `tabPurchase Receipt`.name = `tabPurchase Receipt Item`.parent
                where `tabPurchase Receipt Item`.item_code = '%s' and `tabPurchase Receipt`.docstatus = 1 and  `tabPurchase Receipt`.company = '%s' """%(i["item_code"],company),as_dict=True)[0] or 0 
        if not purchase_receipt["qty"]:
            purchase_receipt["qty"] = 0
        in_transit = purchase_order["qty"] - purchase_receipt["qty"]
        total_in_transit = in_transit + total_in_transit 
        total_stock =  warehouse_stock["qty"] + in_transit
        sum_of_total_stock = total_stock + sum_of_total_stock 
        if i["special_cost"] > 0:
            spcl = spcl + 1
        # if not currency == "USD":
        #     ep = get_exchange_rate('USD',currency)
        #     i["rate"] = round(i["rate"]/ep,1)
        if i["internal_cost"] == 0:
            i_margin = 0
        if i["internal_cost"] > 0:
            i_margin = (i["rate"]*i["qty"] - i["internal_cost"]*i["qty"])/(i["rate"]*i["qty"])*100
        buying_cost = frappe.get_value("Item Price",{"item_code":i["item_code"],"price_list":"STANDARD BUYING-USD"},["price_list_rate"])
        if not buying_cost:
            bc_margin = 0
        if buying_cost:
            buying_cost_conversion = get_exchange_rate("USD",currency)
            buying_cost =  buying_cost *  buying_cost_conversion
            bc_margin = (i["rate"]*i["qty"] - buying_cost*i["qty"])/(i["rate"]*i["qty"])*100
            
        stock_price = frappe.get_value("Item",{"name":i["item_code"]},["valuation_rate"])
        if not stock_price:
            stock_margin = 0
        if stock_price:
            stock_margin = (((i["rate"] * i["qty"]) - (stock_price * i["qty"]))/(i["rate"]*i["qty"]))*100

        total_selling_price =  i["rate"]*i["qty"] + total_selling_price
        valuation_rate = frappe.get_value("Item",{"name":i["item_code"]},["valuation_rate"])
        if not valuation_rate:
            valuation_rate = 0
        total_valuation_rate = (valuation_rate * i["qty"]) + total_valuation_rate
        standard_buying_usd = frappe.get_value("Item Price",{"item_code":i["item_code"],"price_list":"STANDARD BUYING-USD"},["price_list_rate"])
        base_cost_conversion = get_exchange_rate("USD",currency)
        if not standard_buying_usd:
            standard_buying_usd = 0
        else:
            standard_buying_usd =  base_cost_conversion * standard_buying_usd
        cost_total = standard_buying_usd*i["qty"] + cost_total
        country = frappe.get_value("Company",{"name":company},["country"])
        
        total_internal_cost = i["internal_cost"]*i["qty"] + total_internal_cost
        total_special_price =(i["special_cost"] * i["qty"]) + total_special_price

        if "CFO" in frappe.get_roles(frappe.session.user) or "COO" in frappe.get_roles(frappe.session.user) or "HOD" in frappe.get_roles(frappe.session.user) or "Accounts User" in frappe.get_roles(frappe.session.user) or "Operation Director" in frappe.get_roles(frappe.session.user):
            if i["special_cost"] > 0:
                data_5+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=2 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,i["qty"],total_stock,round((standard_buying_usd*i["qty"]),2),"{:.2f}".format(bc_margin),round(i["internal_cost"],2),round(i_margin,2),round(i["special_cost"],2),round((i["rate"]*i["qty"]),2))
            else:
                data_5+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=2 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round((standard_buying_usd*i["qty"]),2),round(bc_margin,2),round((i["internal_cost"]*i["qty"]),2),round(i_margin,2),round((i["rate"]*i["qty"]),2))
    if cost_total == 0:
        total_margin_cost = (total_selling_price - cost_total)/100
    else:
        total_margin_cost = (total_selling_price - cost_total)/ total_selling_price*100
    
    if total_valuation_rate == 0:
        total_margin_valuation= (total_selling_price - total_valuation_rate)/100
    else:
        total_margin_valuation = ((total_selling_price - total_valuation_rate )/total_selling_price)*100
    if total_internal_cost == 0:
        total_margin_internal = (total_selling_price - total_internal_cost)/100
        # total_margin_internal = ((total_selling_price - total_internal_cost )/ total_internal_cost)*100
    else:
        total_margin_internal = (total_selling_price - total_internal_cost )/total_selling_price*100
    
    if total_special_price == 0:
        total_margin_special = (total_selling_price - total_special_price)/100
    else:
        total_margin_special = ((total_selling_price - total_special_price)/total_selling_price)*100
    if "CFO" in frappe.get_roles(frappe.session.user) or "COO" in frappe.get_roles(frappe.session.user) or "HOD" in frappe.get_roles(frappe.session.user) or "Accounts User" in frappe.get_roles(frappe.session.user) or "Operation Director" in frappe.get_roles(frappe.session.user):
        if spcl == 0:
            data_5 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=5><center><b>TOTAL MARGIN BASED ON INTERNAL COST : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(round(total_margin_internal,2),'',round(cost_total,2),round(total_margin_cost,2),round(total_internal_cost,2),round(total_margin_internal,2),round(total_selling_price,2))
        else:
            data_5 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=5><center><b>TOTAL MARGIN BASED ON INTERNAL COST : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(round(total_margin_internal,2),'',round(cost_total,2),round(total_margin_cost,2),round(total_internal_cost,2),round(total_margin_special,2),'',round(total_selling_price,2))
    data_5+='</table>'



    data_1 = '' 
    if "CFO" in frappe.get_roles(frappe.session.user) or "COO" in frappe.get_roles(frappe.session.user) or "HOD" in frappe.get_roles(frappe.session.user):
        data_1 += '<table class="table table-bordered"><tr><th style="padding:1px;border: 1px solid black;font-size:14px;background-color:#FF4500;color:white;" colspan=9><center><b>MARGIN BY PERCENTAGE</b></center></th></tr>'
        data_1+='<tr><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>ITEM</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;width:50%"><b>ITEM NAME</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>STOCK PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SPECIAL PRICE</b></td></tr>'
    internal = 0
    for item in item_details:
        # c = CurrencyRates()
        # if not currency == "USD":
        #     ep = c.get_rate('USD','%s'%(currency))
        #     item["rate"] = round(item["rate"]/ep,1)
        country = frappe.get_value("Company",{"name":company},["country"])
        if country == "Singapore":
            internal = frappe.get_value("Item Price",{'item_code':item["item_code"],'price_list':"Singapore Internal Cost"},['price_list_rate'])
            if not internal:
                internal = 0

        if country == "United Arab Emirates":
            internal = frappe.get_value("Item Price",{'item_code':item["item_code"],'price_list':"Internal - NCMEF"},['price_list_rate'])
            if not internal:
                internal = 0

        if country == "India":
            internal = frappe.get_value("Item Price",{'item_code':item["item_code"],'price_list':"India Landing"},['price_list_rate'])
            if not internal:
                internal = 0

        if country == "United Kingdom":
            internal = frappe.get_value("Item Price",{'item_code':item["item_code"],'price_list':"UK Destination Charges"},['price_list_rate'])
            # internal = frappe.db.sql(""" select price_list_rate from `tabItem Price` where item_code = '%s'  and price_list = '%s' """%(item["item_code"],"STANDARD BUYING-USD"), as_dict=True)
            if not internal:
                internal = 0

       
        if internal == 0:
            i_margin = (item["rate"] - internal)/100
        if not internal == 0:
            i_margin = ((item["rate"] - internal)/internal)*100
        
        standard_buying_usd = frappe.get_value("Item Price",{"item_code":item["item_code"],"price_list":"STANDARD BUYING-USD"},["price_list_rate"])
       
        if not standard_buying_usd:  
            standard_buying_usd = 0
            c_margin = (item["rate"] - standard_buying_usd)/100
        elif standard_buying_usd:
            c_margin = ((item["rate"] - standard_buying_usd)/standard_buying_usd)*100
       

        valuation_rate = frappe.get_value("Item",{"name":item["item_code"]},["valuation_rate"])
        if not valuation_rate:  
            valuation_rate = 0
            v_margin = (item["rate"] - valuation_rate)/100
        elif valuation_rate:
            v_margin = ((item["rate"] - valuation_rate)/valuation_rate)*100
        
        
        if not item["special_cost"]: 
            item["special_cost"] = 0 
            s_margin = (item["rate"] - item["special_cost"])/100
        elif item["special_cost"]:
            s_margin = ((item["rate"] - item["special_cost"])/item["special_cost"])*100
       
        
        if "CFO" in frappe.get_roles(frappe.session.user) or "COO" in frappe.get_roles(frappe.session.user) or "HOD" in frappe.get_roles(frappe.session.user):
            data_1+='<tr><td colspan=1 style="border: 1px solid black;font-size:12px;">%s</td><td colspan=1 style="border: 1px solid black;font-size:12px;">%s</td><td colspan=1 style="border: 1px solid black;font-size:12px;">%s</td><td colspan=1 style="border: 1px solid black;font-size:12px;">%s %% </td><td colspan=1 style="border: 1px solid black;font-size:12px;">%s %% </td><td colspan=1 style="border: 1px solid black;font-size:12px;">%s %% </td></tr>'%(item["item_code"],item["description"],round(c_margin,2),round(v_margin,2),round(i_margin,2),round(s_margin,2),)
    # data_1+= '<tr><th style="padding:1px;border: 1px solid black;font-size:14px" colspan=2><center><b>TOTAL</b></center></th><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s</b></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><b>%s</b></td></tr>'%(round(total_c_margin,2),round(total_v_margin,2),round(total_i_margin,2),round(total_s_margin,2),)
    data_1+='</table>'

    # data_2 = ''
    # data_2 += '<table class="table table-bordered"><tr><th style="padding:1px;border:1px solid black;font-size:14px;background-color:#FF4500;color:white;" colspan=8><center><b>STOCK STATUS</b></center></th></tr>'
    # data_2+='<tr><td colspan=1 style="border: 1px solid black;font-size:11px;"><center><b>ITEM</b><center></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><center><b>STOCK</b><center></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><center><b>PO</b><center></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><center><b>TOTAL</b><center></td></tr>'
    # for j in item_details:
    #     country = frappe.get_value("Company",{"name":company},["country"])
    #     warehouse_stock = frappe.db.sql("""
    #     select sum(b.actual_qty) as qty from `tabBin` b 
    #     join `tabWarehouse` wh on wh.name = b.warehouse
    #     join `tabCompany` c on c.name = wh.company
    #     where c.country = '%s' and b.item_code = '%s'
    #     """ % (country,j["item_code"]),as_dict=True)[0]
    #     if not warehouse_stock["qty"]:
    #         warehouse_stock["qty"] = 0
    #     purchase_order = frappe.db.sql("""select sum(`tabPurchase Order Item`.qty) as qty from `tabPurchase Order`
    #             left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
    #             where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 """%(j["item_code"]),as_dict=True)[0] or 0 
    #     if not purchase_order["qty"]:
    #         purchase_order["qty"] = 0
    #     purchase_receipt = frappe.db.sql("""select sum(`tabPurchase Receipt Item`.qty) as qty from `tabPurchase Receipt`
    #             left join `tabPurchase Receipt Item` on `tabPurchase Receipt`.name = `tabPurchase Receipt Item`.parent
    #             where `tabPurchase Receipt Item`.item_code = '%s' and `tabPurchase Receipt`.docstatus = 1 """%(j["item_code"]),as_dict=True)[0] or 0 
    #     if not purchase_receipt["qty"]:
    #         purchase_receipt["qty"] = 0
    #     in_transit = purchase_order["qty"] - purchase_receipt["qty"]
    #     total = warehouse_stock["qty"] + in_transit
    #     data_2+='<tr style="height:5px;"><td colspan=1 style="border: 1px solid black;font-size:11px;"><center>%s<center><center></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><center>%s<center><center></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><center>%s</center></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><center>%s</center></td></tr>'%(j["item_code"],warehouse_stock["qty"], in_transit,total)
    # data_2+='</table>'
    
    return data_4,data_5

@frappe.whitelist()
def get_internal_cost(company,item_code):
    country = frappe.get_value("Company",{"name":company},["country"])
    internal = 0
    if country == "Singapore":
        internal = frappe.get_value("Item Price",{'item_code':item_code,'price_list':"Singapore Internal Cost"},['price_list_rate'])
        if not internal:
            internal = 0
    if country == "United Arab Emirates":
        internal = frappe.get_value("Item Price",{'item_code':item_code,'price_list':"Internal - NCMEF"},['price_list_rate'])
        if not internal:
            internal = 0 

    if country == "India":
        internal = frappe.get_value("Item Price",{'item_code':item_code,'price_list':"India Landing"},['price_list_rate'])
        if not internal:
            internal = 0

    if country == "United Kingdom":
        internal = frappe.get_value("Item Price",{'item_code':item_code,'price_list':"UK Destination Charges"},['price_list_rate'])
        if not internal:
            internal = 0

    return internal

@frappe.whitelist()
def check_user_roles(doc,method):
    if not doc.company == "Norden Communication Pvt Ltd":
        if not doc.company == "Sparcom Ningbo Telecom Ltd":
            if doc.work_flow == "Pending for CFO":
                if "CFO" in frappe.get_roles(frappe.session.user):
                    frappe.validated = True
                else:
                    frappe.validated = False
                    frappe.throw("CFO can only submit this document")

            if doc.work_flow == "Pending for COO":
                if "COO" in frappe.get_roles(frappe.session.user):
                    frappe.validated = True
                else:
                    frappe.validated = False
                    frappe.throw("COO can only submit this document")
                
            if doc.work_flow == "Pending for HOD":
                if "HOD" in frappe.get_roles(frappe.session.user):
                    frappe.validated = True
                else:
                    frappe.validated = False
                    frappe.throw("HOD can only submit this document")
                
            # if doc.work_flow == "Pending for Sales Manager":
            #     if "Sales Manager" in frappe.get_roles(frappe.session.user):
            #         frappe.validated = True
            #     else:
            #         frappe.validated = False
            #         frappe.throw("Sales Manager can only submit this document")

            if doc.work_flow == "Pending for Sales Manager":
                if doc.company == "Norden Communication Middle East FZE":
                    if "Sales Master Manager" in frappe.get_roles(frappe.session.user):
                        frappe.validated = True
                    else:
                        frappe.validated = False
                        frappe.throw("Sales Master Manager can only submit this document")
                else:
                    if "Sales Manager" in frappe.get_roles(frappe.session.user):
                        frappe.validated = True
                    else:
                        frappe.validated = False
                        frappe.throw("Sales Manager can only submit this document")



@frappe.whitelist()
def check_internal_cost(doc,method):
    if not doc.company == "Norden Communication Pvt Ltd":
        if not doc.company == "Sparcom Ningbo Telecom Ltd":
            if doc.company == "Norden Singapore PTE LTD":
                if doc.internal_cost_margin < 20:
                    if doc.internal_cost_margin < 20 and doc.work_flow == "Draft" and "Sales User" in frappe.get_roles(frappe.session.user):
                        frappe.validated = False
                        frappe.throw("Not allowed to submit, Send to HOD")
                        
                    if doc.internal_cost_margin < 20 and doc.work_flow == "Pending for HOD" and "HOD" in frappe.get_roles(frappe.session.user):
                        frappe.validated = False
                        frappe.throw("Not allowed to submit, Send to COO")

                    if doc.internal_cost_margin < 20 and doc.work_flow == "Pending for COO" and "COO" in frappe.get_roles(frappe.session.user):
                        frappe.validated = True
                    else:
                        frappe.validated = False
                        frappe.throw("Not allowed to submit")

                if doc.internal_cost_margin > 20 and doc.internal_cost_margin < 30:
                    if doc.internal_cost_margin < 30 and doc.work_flow == "Draft" and "Sales User" in frappe.get_roles(frappe.session.user):
                        frappe.validated = False
                        frappe.throw("Not allowed to submit, Send to HOD")
                        
                    if doc.internal_cost_margin < 30 and doc.work_flow == "Pending for HOD" and "HOD" in frappe.get_roles(frappe.session.user):
                        frappe.validated = True
                    else:
                        frappe.validated = False
                        frappe.throw("Not allowed to submit")
                
            else:
                if not doc.company == "Norden Communication UK Limited":
                    if not doc.company == "Norden Africa":
                        if not doc.internal_cost_margin:
                            doc.internal_cost_margin = 0

                        if not doc.currency == "INR" and doc.grand_total >= 250000 and doc.work_flow == 'Draft':
                            frappe.validated = False
                            frappe.throw("Not allowed to submit,Grand total exceed the limit,Please click the button Send to CFO")

                        if doc.currency == "INR" and doc.grand_total >= 10000000 and doc.work_flow == 'Draft':
                            frappe.validated = False
                            frappe.throw("Not allowed to submit,Grand total exceed the limit,Please click the button Send to CFO")

                        
                        if doc.internal_cost_margin < 40 and doc.work_flow == 'Draft':
                            frappe.validated = False
                            frappe.throw("Not allowed to submit ,the profit percentage is less than the allowed limit to submit. Click the Button Send to Sales Manager")

                        if not doc.company == "Norden Communication Middle East FZE" and doc.internal_cost_margin < 30  and doc.work_flow == "Pending for Sales Manager" and "Sales Manager" in frappe.get_roles(frappe.session.user):
                            frappe.validated = False
                            frappe.throw("Not allowed to submit ,the profit percentage is less than the allowed limit to submit. Click the Button Send to HOD")
                        
                        if doc.internal_cost_margin < 25  and doc.work_flow == "Pending for HOD" and "HOD" in frappe.get_roles(frappe.session.user):
                            frappe.validated = False
                            frappe.throw("Not allowed to submit ,the profit percentage is less than the allowed limit to submit. Click the Button Send to COO")

                        if doc.internal_cost_margin < 10 and doc.work_flow == "Pending for COO" and "COO" in frappe.get_roles(frappe.session.user):
                            frappe.validated = False
                            frappe.throw("Not allowed to submit ,the profit percentage is less than the allowed limit to submit. Click the Button Send to CFO")
                        
                        if doc.internal_cost_margin < 10 and doc.work_flow == "Pending for COO" and "HOD" in frappe.get_roles(frappe.session.user):
                            frappe.validated = False
                            frappe.throw("Not allowed to submit")
                        
                        if doc.internal_cost_margin < 10 and doc.work_flow == "Pending for COO" and "Sales Manager" in frappe.get_roles(frappe.session.user):
                            frappe.validated = False
                            frappe.throw("Not allowed to submit")

                        if doc.grand_total >= 10000000 and doc.work_flow == "Pending for CFO" and "CFO" in frappe.get_roles(frappe.session.user):
                            frappe.validated = False
                            frappe.throw("Not allowed to submit")

                        if doc.grand_total >= 10000000 and doc.work_flow == "Pending for CFO" and "COO" in frappe.get_roles(frappe.session.user):
                            frappe.validated = False
                            frappe.throw("Not allowed to submit")
                        
                        if doc.grand_total >= 10000000 and doc.work_flow == "Pending for CFO" and "Sales Manager" in frappe.get_roles(frappe.session.user):
                            frappe.validated = False
                            frappe.throw("Not allowed to submit")

                        if doc.grand_total >= 10000000 and doc.work_flow == "Pending for CFO" and "HOD" in frappe.get_roles(frappe.session.user):
                            frappe.validated = False
                            frappe.throw("Not allowed to submit")

                        if doc.work_flow == "Pending for Sales Manager" and "Sales User" in frappe.get_roles(frappe.session.user):
                            if not "Sales Manager" in frappe.get_roles(frappe.session.user):
                                frappe.validated = False
                                frappe.throw("Not allowed to submit")

                        # if doc.work_flow == "Pending for Operation Director" and "Sales Manager" in frappe.get_roles(frappe.session.user):
                        if doc.work_flow == "Pending for Operation Director":
                            if not "Operation Director" in frappe.get_roles(frappe.session.user):
                                frappe.validated = False
                                frappe.throw("Not allowed to submit")

                        # if not doc.currency == "INR" and doc.grand_total >= 100000 and doc.work_flow == "Pending for CFO" and "Sales Manager" in frappe.get_roles(frappe.session.user):
                        #     frappe.validated = False
                        #     frappe.throw("Not allowed to submit")

                        # if doc.grand_total >= 10000000 and doc.work_flow == "Pending for CFO" and "HOD" in frappe.get_roles(frappe.session.user):
                        #     frappe.validated = False
                        #     frappe.throw("Not allowed to submit")

                        # if not doc.currency == "INR" and doc.grand_total >= 100000 and doc.work_flow == "Pending for CFO" and "HOD" in frappe.get_roles(frappe.session.user):
                        #     frappe.validated = False
                        #     frappe.throw("Not allowed to submit")

                        # if doc.grand_total >= 10000000 and doc.work_flow == "Pending for CFO" and "COO" in frappe.get_roles(frappe.session.user):
                        #     frappe.validated = False
                        #     frappe.throw("Not allowed to submit")

                        # if not doc.currency == "INR" and doc.grand_total >= 100000 and doc.work_flow == "Pending for CFO" and "COO" in frappe.get_roles(frappe.session.user):
                        #     frappe.validated = False
                        #     frappe.throw("Not allowed to submit")

                        if doc.internal_cost_margin < 10 and doc.grand_total <= 1000000 and doc.company == "Norden Communication Middle East FZE" and doc.work_flow == "Pending for Sales Manager" and "Sales Manager" in frappe.get_roles(frappe.session.user) and doc.currency == "AED" and doc.currency == "SAR":
                            frappe.validated = False
                            frappe.throw("Not allowed to submit ,the profit percentage is less than the allowed limit to submit. Click the Button Send to Operation Director")

                        if doc.grand_total > 1000000 and doc.company == "Norden Communication Middle East FZE" and doc.work_flow == "Pending for Sales Manager" and "Sales Manager" in frappe.get_roles(frappe.session.user) and doc.currency == "AED" and doc.currency == "SAR":
                            frappe.validated = False
                            frappe.throw("Not allowed to submit ,the grand total is greater than the allowed limit to submit. Click the Button Send to Operation Director")

                        if doc.internal_cost_margin < 10 and doc.company == "Norden Communication Middle East FZE" and doc.work_flow == "Pending for Sales Manager" and "Sales Manager" in frappe.get_roles(frappe.session.user) and doc.currency == "AED" and doc.currency == "SAR":
                            frappe.validated = False
                            frappe.throw("Not allowed to submit ,the profit percentage is less than the allowed limit to submit. Click the Button Send to Operation Director")

            



@frappe.whitelist()
def currency_conversion(currency,price):
    
    selling_price = float(price)
    # c = CurrencyRates()
    if not currency == "USD":
        ep = get_exchange_rate('USD',currency)
        # ep = c.get_rate('USD','%s'%(currency))
        selling_price = round(selling_price/ep,1)
        return selling_price
    else:
        return selling_price

@frappe.whitelist()
def get_item_rate(item_code,price_list,doc_currency):
    uom = frappe.db.get_value("Item",item_code,'stock_uom')
    unit_price = frappe.get_value("Item Price",{"item_code":item_code,"price_list":price_list},["price_list_rate"])
    unit_price_document_currency = 0
    if unit_price:
        unit_price_document_currency = unit_price / get_exchange_rate(doc_currency,frappe.get_value("Item Price",{"item_code":item_code,"price_list":price_list},["currency"]))
    return unit_price,unit_price_document_currency,uom


@frappe.whitelist()
def internal_margin_calculation(doc,method):
    if doc.total_selling_price_in_usd:
        if doc.internal_cost == 0:
            doc.internal_cost_margin = doc.internal_cost
        else:
            margin = ((doc.total_selling_price_in_usd - doc.discount_amount - doc.internal_cost)/(doc.total_selling_price_in_usd - doc.discount_amount))*100
            doc.internal_cost_margin = margin
    # internal = 0
    # for i in doc.items:
    #     country = frappe.get_value("Company",{"name":doc.company},["country"])
    #     if country == "Singapore":
    #         if doc.selling_price_list == "Indonesia Sales Price":
    #             internal = frappe.get_value("Item Price",{'item_code':i.item_code,'price_list':"Indonesia Internal Cost"},['price_list_rate'])
    #         if doc.selling_price_list == "Singapore Sales Price":
    #             internal = frappe.get_value("Item Price",{'item_code':i.item_code,'price_list':"Singapore Internal Cost"},['price_list_rate'])
    #         if doc.selling_price_list == "Vietnam Internal Cost":
    #             internal = frappe.get_value("Item Price",{'item_code':i.item_code,'price_list':"Vietnam Internal Cost"},['price_list_rate'])
    #         if not internal:
    #             internal = 0

    #     if country == "United Arab Emirates":
    #         internal = frappe.get_value("Item Price",{'item_code':i.item_code,'price_list':"Internal - NCMEF"},['price_list_rate'])
    #         if not internal:
    #             internal = 0 
    #     if country == "India":
    #         internal = frappe.get_value("Item Price",{'item_code':i.item_code,'price_list':"India Landing"},['price_list_rate'])
    #         if not internal:
    #             internal = 0

    #     if country == "United Kingdom":
    #         internal = frappe.get_value("Item Price",{'item_code':i.item_code,'price_list':"UK Destination Charges"},['price_list_rate'])
    #         if not internal:
    #             internal = 0
    #     # total_internal = total_internal + (internal*i.qty)
    #     # doc.internal_cost = total_internal
        
                

@frappe.whitelist()
def get_supplier_part(item_code):
    # part_no = frappe.db.sql(""" select `tabItem Supplier`.supplier_part_no as supplier from `tabItem` left join `tabItem Supplier` on `tabItem`.name =`tabItem Supplier`.parent where `tabItem`.name = '%s' """%(item_code),as_dict = True)[0]
    part = frappe.get_doc("Item",item_code)
    return part.supplier_items

@frappe.whitelist()
def check_altair(name):
    altair = frappe.db.exists("Purchase Order",{"original_po_number":name})
    if altair:
        return "Yes"
    else:
        return "No"

@frappe.whitelist()
def batch_number(doc,method):
    # frappe.db.set_value("Purchase Order",doc.name,"batch",doc.name)
    doc.batch = doc.abbr +"-"+ doc.name[-10:]
    if doc.amended_from:
        doc.batch = doc.abbr +"-"+ doc.name[-12:]

    
        

@frappe.whitelist()
def create_item_price(item_code,rate):
    check_price = frappe.db.exists("Item Price",{"item_code":item_code,"price_list":"Standard Selling"},["price_list_rate"])
    if check_price:
        return "Yes"
    else:
        doc = frappe.new_doc("Item Price")
        doc.item_code = item_code
        doc.price_list = "Standard Selling"
        doc.selling = 1
        doc.buying = 0
        doc.valid_from = '2022-01-01'
        doc.price_list_rate = rate
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return rate

@frappe.whitelist()
def fetch_consultant(file_no):
    c = frappe.get_value("Quotation",{"file_number":file_no},["consultant_company","consultant_name"])
    return c

@frappe.whitelist()
def so_status(doc,method):
    frappe.log_error(title = doc.status)
    frappe.log_error(title = doc.workflow_state)

@frappe.whitelist()
def dn_status(doc,method):
    pr = frappe.get_doc("Project Reference",{"Sales_order":doc.so_no})
    if pr:
        dn_status = frappe.get_value("Sales Order",{"name":doc.so_no},["status"])
        pr.so_status_live = dn_status
        pr.save(ignore_permissions=True)

# @frappe.whitelist()
# def create_file_number(doc,method):
# 	if not doc.file_number:
# 		if doc.company == "Norden Communication Middle East FZE" or doc.company == "Norden Communication UK Limited":
# 			code = 'F-Q-' + doc.name.split('-')[2] +'-'+doc.name.split('-')[3][-2:]
# 		else:
# 			code = 'F-Q-' + doc.name.split('-')[2]
# 		doc_no = doc.name[-5:]
# 		file_no = code + '-' + doc_no
# 		doc.file_number = file_no

# @frappe.whitelist()
# def create_opp_file_number(doc,method):    
# 	code = 'F-O-' + doc.abbr
# 	doc_no = doc.name[-5:]
# 	file_no = code + '-' + doc_no
# 	doc.file_number = file_no

@frappe.whitelist()
def si_status(doc,method):
    pr = frappe.get_doc("Project Reference",{"Sales_order":doc.so_no})
    if pr:
        so_status = frappe.get_value("Sales Order",{"name":doc.so_no},["status"])
        pr.so_status_live = so_status
        pr.save(ignore_permissions=True)

@frappe.whitelist()
def get_warehouse(company):
    store_a = frappe.get_value("Warehouse",{"company":company,"warehouse_name":"Store A"})
    store_t= frappe.get_value("Warehouse",{"company":company,"warehouse_name":"Store T"})
    return store_a,store_t

@frappe.whitelist()
def rename_altair(doc,method):
    if doc.supplier == "Altair":
        frappe.rename_doc("Purchase Order", doc.name, str(doc.name) + "-" + "1", force=1)
    # altair = frappe.get_value("Purchase Order",{"supplier":"Altair"})
    # if altair:
    #     frappe.rename_doc("Purchase Order", altair, str(altair) + "-" + "1", force=1)

@frappe.whitelist()
def fetch_tax_and_charges(pr_no):
    tax = frappe.get_value("Purchase Receipt",{"name":pr_no},["tax_and_charges"])
    if tax:
        return tax

@frappe.whitelist()
def get_item_price(item_code,price_list):
    price = frappe.get_value("Item Price",{"name":item_code,"price_list":price_list},["price_list_rate"])

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_address(supplier):
    supplier_address = frappe.get_value("Address",{"address_title":supplier})
    return supplier_address

@frappe.whitelist()
def get_po_no(doc,method):
    if frappe.db.exists("Sales Order",{"name":doc.sales_order_number}):
        so= frappe.get_doc("Sales Order",{"name":doc.sales_order_number})
        so.purchase_order_number = doc.name
        so.po_completion_date = doc.completion_date
        so.save(ignore_permissions=True)

@frappe.whitelist()
def get_hsn(item_details):
    item_details = json.loads(item_details)
    l1 = []
    l2 = []
    for i in item_details:
        if i['gst_hsn_code'] not in l1:
            l1.append(i["gst_hsn_code"])
            frappe.msgprint("----")
        else:
            l2.append(i["gst_hsn_code"])
    return l1

@frappe.whitelist()
def get_cost(item_code):
    cost = frappe.get_value("Item Price",{"item_code":item_code,"price_list":"STANDARD BUYING-USD"},["price_list_rate"])
    if cost:
        return cost

@frappe.whitelist()
def get_approver(user):
    approver = frappe.get_value("Employee",{"user_id":user},["employee_name"])
    if approver:
        return approver

@frappe.whitelist()
def update_sales_team():
    so = frappe.get_all("Sales Order",["*"])
    for i in so[:5]:
        if i.sales_person_name:
            print(i.name)
            s = frappe.get_doc('Sales Order',i.name)
            s.ignore_pricing_rule = 0
            s.append("sales_team", {
                "sales_person": i.sales_person_name,
                "allocated_percentage": 100.0
                })
            s.save(ignore_permissions=True)

@frappe.whitelist()
def create_pr(company,supplier,product_description,logistic):
    pr = frappe.new_doc("Purchase Receipt")
    pr.company = company
    pr.supplier = supplier
    pr.posting_date = today()
    pr.logistics = logistic
    product = json.loads(product_description)
    for i in product:
        pr.append("items", {
        "item_code": i["item_code"],
        "schedule_date": i["schedule_date"],
        "qty": i["qty"],
        "warehouse": i["warehouse"],
        })
    pr.save(ignore_permissions = True)
    return pr.name

@frappe.whitelist()
def check_pr(doc,method):
    pr = frappe.get_doc("Logistics Request",doc.logistics)
    pr.append("receipts", {
        "purchase_receipt":doc.name,
        })
    pr.save(ignore_permissions = True)

# @frappe.whitelist()
# def delete_item_price():
#     ip = frappe.db.sql(""" delete from `tabItem Price` where price_list = "Africa Customer Price" """)

# @frappe.whitelist()
# def create_file_number_mr(doc,method):
# 	if not doc.sales_order_number:
# 		code = 'F-MR-' + doc.abbr
# 		doc_no = doc.name[-5:]
# 		file_no = code + '-' + doc_no
# 		doc.file_number = file_no

@frappe.whitelist()
def get_sub_heading(item_head):
    item_detail = json.loads(item_head)
    l1 = []
    l2 = []
    for i in item_detail:
        if i not in l1:
            l1.append(i)
        else:
            l2.append(i)
    return l1

@frappe.whitelist()
def get_item_titles(item_title):
    item_detail = json.loads(item_title)
    l1 = []
    l2 = []
    for i in item_detail:
        if i not in l1:
            l1.append(i)
        else:
            l2.append(i)
    return l1

@frappe.whitelist()
def get_item_heading(item_details):
    item_details = json.loads(item_details)
    l1 = []
    l2 = []
    for i in item_details:
        if i["item_heading"]:
            if i["item_heading"] not in l1:
                l1.append(i["item_heading"] or "")
            else:
                l2.append(i["item_heading"] or "")
    return l1


@frappe.whitelist()
def get_duplicate_item(item_details):
    item_details = json.loads(item_details)
    l1 = []
    l2 = []
    for i in item_details:
        if i['item_code'] not in l1:
            l1.append(i["item_code"])
        else:
            l2.append(i["item_code"])
    return l1

@frappe.whitelist()
def get_item_details(company,name,currency,so_no,item_details,supplier):
    item_details = json.loads(item_details)
    so_currency = frappe.get_value("Sales Order",{"name":so_no},["currency"])
    data = ''
    data+='<table><style>td { text-align:left } table,tr,td,th{ padding:5px;border: 1px solid black; font-size:13px;} </style>' 
    data += '<tr rowspan = 2 ><th style="background-color:lightgrey" colspan=14><center><b>Item Details</b></center></th></tr>'
    so_cust = frappe.get_value("Sales Order",{"name":so_no},["customer_name"])
    so_pt = frappe.get_value("Sales Order",{"name":so_no},["payment_terms_template"])
    po_pt = frappe.get_value("Purchase Order",{"name":name},["payment_terms_template"])
    data += '<tr><td  colspan = 1><b>Customer</b></td><td colspan = 2"">%s</td><td colspan = 2"><b>Supplier</b></td><td colspan = 2">%s</td><td colspan = 2" ><b>Currency</b></td><td colspan = 2">%s</td></tr>'%(so_cust,supplier,so_currency)
    data += '<tr><td  colspan = 1"><b>Payment Terms</b></td><td colspan = 2">%s</td><td colspan = 2><b>Payment Terms</b></td><td colspan=2 >%s</td></tr>'%(so_pt,po_pt or '')
    data += '<tr><td style="background-color:lightgrey" width="150px"><b>ITEM CODE</b></td><td style="background-color:lightgrey" width="300px"><b>DESCRIPTION</b></td><td style="background-color:lightgrey" width="80px" ><b>QTY</b></td><td style="background-color:lightgrey" width="80px"><b>PRV PO</b></td><td style="background-color:lightgrey" width="80px"><b>RATE</b></td><td style="background-color:lightgrey" width="80px"><b>TOTAL PO</b></td><td style="background-color:lightgrey" width="120px"><b>SELLING RATE</b></td><td style="background-color:lightgrey" width="120px"><b>TOTAL SELLING RATE</b></td><td style="background-color:lightgrey" width="80px"><b>Margin%</b></td><td style="background-color:lightgrey" width="80px" ><b>Stock</b></td><td style="background-color:lightgrey"  width="80px" ><b>PO</b></td></tr>'
        
    # data += '<tr><td width="500px ><b>Customer</b></td><td style="padding:1px;border: 1px solid black;" colspan=4>%s</td><td style="padding:1px;border: 1px solid black;" colspan = 3><b>Supplier</b></td><td style="padding:1px;border: 1px solid black;" colspan=5 >%s</td></tr>'%(so_cust,supplier)
    # data += '<tr><td <b>Payment Terms</b></td><td style="padding:1px;border: 1px solid black;" colspan=4>%s</td><td style="padding:1px;border: 1px solid black;" colspan = 3><b>Payment Terms</b></td><td style="padding:1px;border: 1px solid black;" colspan=5 >%s</td></tr>'%(so_pt,po_pt or '')
    # data += '<tr><td>Item Code</b></td><td style="padding:1px;border: 1px solid black;" colspan=2><b>Description</b></td><td style="padding:1px;border: 1px solid black;" colspan=1><b>Qty</b></td><td style="padding:1px;border: 1px solid black;" colspan=1><b>Rate</b></td><td style="padding:1px;border: 1px solid black;" colspan=1><b>Prv PO</b></td><td style="padding:1px;border: 1px solid black;" colspan=1><b>Selling Rate</b></td><td style="padding:1px;border: 1px solid black;" colspan=2><b>Margin%</b></td><td style="padding:1px;border: 1px solid black;" colspan=2><b>Stock</b></td><td style="padding:1px;border: 1px solid black;" colspan=2><b>PO</b></td><td style="padding:1px;border: 1px solid black;" colspan=2><b>Currency</b></td></tr>'
    total_po = 0
    total_selling_rate = 0
    total_margin = 0
    margin_percent = 0
    ppo = 0
    for i in item_details:
        mr_ex = get_exchange_rate(currency,so_currency)
        i["rate"] = mr_ex * i["rate"] 
        i["rate"] = round( i["rate"],3)
        s_rate = frappe.db.sql(""" select `tabSales Order Item`.rate as rate from `tabSales Order`
            left join `tabSales Order Item` on `tabSales Order`.name = `tabSales Order Item`.parent 
            where `tabSales Order`.name = '%s' and `tabSales Order Item`.item_code = '%s' """ %(so_no,i["item_code"]),as_dict = True)
        if s_rate:
            if i["rate"] == 0:
                margin = (s_rate[0]["rate"] - i["rate"])*100
            else:
                margin = (s_rate[0]["rate"] - i["rate"])/i["rate"]*100
        pos = frappe.db.sql(""" select `tabPurchase Order Item`.item_code as item_code,
        `tabPurchase Order Item`.item_name as item_name,
        `tabPurchase Order`.supplier as supplier,`tabPurchase Order Item`.qty as qty,
        `tabPurchase Order Item`.amount as amount,
         `tabPurchase Order Item`.rate as rate,
        `tabPurchase Order`.transaction_date as date,
        `tabPurchase Order`.name as po,
        `tabPurchase Order`.company as company,
        `tabPurchase Order`.currency as currency from 
        `tabPurchase Order`
        left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
        where `tabPurchase Order`.company = '%s' and 
        `tabPurchase Order Item`.item_code = '%s' and
        `tabPurchase Order`.name != '%s' and  
        `tabPurchase Order`.docstatus != 2 order by date desc """ % (company,i["item_code"],name), as_dict=True) 
        # ppo = 0
        # total_po = 0
        # total_selling_rate = 0
        if pos:
            pos_ex = get_exchange_rate(pos[0]["currency"],so_currency)
            pos[0]["rate"] = pos_ex * pos[0]["rate"]
            pos[0]["rate"] = round(pos[0]["rate"],3)
            ppo = pos[0]["rate"]
        # if not pos:
        # if not pos:
        #     pos[""] = 0
        purchase_order = frappe.db.sql("""select sum(`tabPurchase Order Item`.qty) as qty from `tabPurchase Order`
            left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
            where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 and `tabPurchase Order`.company = '%s' """%(i["item_code"],company),as_dict=True)[0] or 0 
        if not purchase_order["qty"]:
            purchase_order["qty"] = 0
        purchase_receipt = frappe.db.sql("""select sum(`tabPurchase Receipt Item`.qty) as qty from `tabPurchase Receipt`
                left join `tabPurchase Receipt Item` on `tabPurchase Receipt`.name = `tabPurchase Receipt Item`.parent
                where `tabPurchase Receipt Item`.item_code = '%s' and `tabPurchase Receipt`.docstatus = 1 and `tabPurchase Receipt`.company = '%s' """%(i["item_code"],company),as_dict=True)[0] or 0 
        if not purchase_receipt["qty"]:
            purchase_receipt["qty"] = 0
        in_transit = purchase_order["qty"] - purchase_receipt["qty"]
        country = frappe.get_value("Company",{"name":company},["country"])
        warehouse_stock = frappe.db.sql("""
            select (sum(`tabBin`.actual_qty) - sum(b.reserved_stock)) as qty from `tabBin` b 
            join `tabWarehouse` wh on wh.name = b.warehouse
            join `tabCompany` c on c.name = wh.company
            where c.country = '%s' and b.item_code = '%s' and wh.company = '%s'
            """ % (country,i["item_code"],company),as_dict=True)[0]
        
        if not warehouse_stock["qty"]:
            warehouse_stock["qty"] = 0
        total_po = total_po + (i["rate"]*i["qty"])
        total_selling_rate = total_selling_rate + s_rate[0]["rate"]*i['qty']
        total_margin = total_margin + margin
        margin_percent = ((total_selling_rate - total_po)/total_selling_rate)*100
        # if pos:
        #     data += '<tr rowspan = 2 ><td style="padding:1px;border: 1px solid black;" colspan=1>%s</td><td style="padding:1px;border: 1px solid black;" colspan=3>%s</td><td style="padding:1px;border: 1px solid black;" colspan=1>%s</td><td style="padding:1px;border: 1px solid black;" colspan=1>%s</td><td style="padding:1px;border: 1px solid black;" colspan=1 >%s</td><td style="padding:1px;border: 1px solid black;" colspan=1 >%s</td><td style="padding:1px;border: 1px solid black;" colspan=2 >%s</td><td style="padding:1px;border: 1px solid black;" colspan=2 >%s</td><td style="padding:1px;border: 1px solid black;" colspan=2 >%s</td><td style="padding:1px;border: 1px solid black;" colspan=2 >%s</td></tr>'%(i["item_code"],i["description"],i["qty"],i["rate"],pos["amount"]/pos["qty"],s_rate["rate"],round(margin,2),warehouse_stock["qty"],in_transit,currency)
        # else:
        data += '<tr rowspan = 2 ><td style="padding:1px;border: 1px solid black;width:150px;">%s</td><td style="padding:1px;border: 1px solid black;width:150px;">%s</td><td style="padding:1px;text-align:right;border: 1px solid black;">%s</td><td style="padding:1px;text-align:right;border:1px solid black;width:80px;" colspan=1>%s</td><td style="padding:1px;text-align:right;border: 1px solid black;" colspan=1>%s</td><td style="padding:1px;text-align:right;border: 1px solid black;" colspan=1 >%s</td><td style="padding:1px;text-align:right;border: 1px solid black;" colspan=1 >%s</td><td style="padding:1px;text-align:right;border: 1px solid black;" colspan=1 >%s</td><td style="padding:1px;text-align:right;border: 1px solid black;" colspan=1 >%s</td><td style="padding:1px;text-align:right;border: 1px solid black;" colspan=1 >%s</td><td style="padding:1px;text-align:right;border: 1px solid black;" colspan=2 >%s</td></tr>'%(i["item_code"],i["description"],i["qty"],ppo,round(i["rate"],2),round((i["rate"]*i["qty"]),2),s_rate[0]["rate"],(s_rate[0]["rate"]*i['qty']),round(margin,2),warehouse_stock["qty"],in_transit)
    data+= '<tr><td style="background-color:lightgrey" colspan = "5" ><b><center>Total</center><b></td><td style="text-align:right;background-color:lightgrey" width = "80px" >%s</td><td style="background-color:lightgrey" width = "80px" ></td></td><td style="text-align:right;background-color:lightgrey" width = "80px" >%s</td></td><td style="text-align:right;background-color:lightgrey" width = "80px" >%s</td></td><td style="background-color:lightgrey" width = "80px" ></td></td><td style="background-color:lightgrey" width = "80px" ></td></td></tr>' %(round(total_po,2),round(total_selling_rate,2),round(margin_percent,4))
    data+='</table>'
    return data


@frappe.whitelist()
def get_item_details_frm_mr(mat_rq,company,name,currency,item_details,supplier):
    if mat_rq:
        item_details = json.loads(item_details)
        # mr = frappe.get_doc("Material Request",mat_rq)
        mr_currency = frappe.get_value("Material Request",{"name":mat_rq},["project_currency"])
        data = ''
        data+='<table><style>td { text-align:left } table,tr,td,th{ padding:5px;border: 1px solid black; font-size:13px;} </style>' 
        data += '<tr rowspan = 2 ><th style="background-color:lightgrey" colspan=14><center><b>Item Details</b></center></th></tr>'
        mr_cust = frappe.get_value("Material Request",{"name":mat_rq},["customers"])
        po_pt = frappe.get_value("Purchase Order",{"name":name},["payment_terms_template"])
        data += '<tr><td  colspan = 1><b>Customer</b></td><td colspan = 2"">%s</td><td colspan = 2"><b>Supplier</b></td><td colspan = 2">%s</td><td colspan = 2" ><b>Currency</b></td><td colspan = 2">%s</td></tr>'%(mr_cust,supplier,mr_currency)
        data += '<tr><td  colspan = 1"><b>Payment Terms</b></td><td colspan = 2">%s</td><td colspan = 2><b>Payment Terms</b></td><td colspan=2 >%s</td></tr>'%('',po_pt or '')
        data += '<tr><td style="background-color:lightgrey" width="150px"><b>ITEM CODE</b></td><td style="background-color:lightgrey" width="300px"><b>DESCRIPTION</b></td><td style="background-color:lightgrey" width="80px" ><b>QTY</b></td><td style="background-color:lightgrey" width="80px"><b>PRV PO</b></td><td style="background-color:lightgrey" width="80px"><b>RATE</b></td><td style="background-color:lightgrey" width="80px"><b>TOTAL PO</b></td><td style="background-color:lightgrey" width="120px"><b>SELLING RATE</b></td><td style="background-color:lightgrey" width="120px"><b>TOTAL SELLING RATE</b></td><td style="background-color:lightgrey" width="80px"><b>Margin%</b></td><td style="background-color:lightgrey" width="80px" ><b>Stock</b></td><td style="background-color:lightgrey"  width="80px" ><b>PO</b></td></tr>'
        total_po = 0
        total_selling_rate = 0
        margin_percent = 0
        for i in item_details:
            mr_ex = get_exchange_rate(currency,mr_currency)
            i["rate"] = mr_ex * i["rate"] 
            i["rate"] = round(i["rate"],3)
            m_rate = frappe.db.sql(""" select `tabMaterial Request Item`.Sales_price as sales_price ,`tabMaterial Request`.currency as currency from `tabMaterial Request`
                left join `tabMaterial Request Item` on `tabMaterial Request`.name = `tabMaterial Request Item`.parent 
                where `tabMaterial Request`.name = '%s' and `tabMaterial Request Item`.item_code = '%s' """ %(mat_rq,i["item_code"]),as_dict = True)[0]
            if i["rate"] == 0:
                margin = (m_rate["sales_price"] - i["rate"])*100
            else:
                margin = (m_rate["sales_price"] - i["rate"])/i["rate"]*100
            pos = frappe.db.sql("""select `tabPurchase Order Item`.item_code as item_code,
            `tabPurchase Order Item`.item_name as item_name,
            `tabPurchase Order`.supplier as supplier,
            `tabPurchase Order Item`.qty as qty,
            `tabPurchase Order Item`.amount as amount,
            `tabPurchase Order Item`.rate as rate,
            `tabPurchase Order`.transaction_date as date,
            `tabPurchase Order`.name as po,
            `tabPurchase Order`.company as company,
            `tabPurchase Order`.currency as currency from `tabPurchase Order`
            left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
            where `tabPurchase Order`.company = '%s' and 
            `tabPurchase Order Item`.item_code = '%s' and 
            `tabPurchase Order`.name != '%s' and 
            `tabPurchase Order`.docstatus != 2 order by date desc """ % (company,i["item_code"],name), as_dict=True)
            ppo = 0
            if pos:
                pos_ex = get_exchange_rate(pos[0]["currency"],mr_currency)
                pos[0]["rate"] = pos_ex * pos[0]["rate"]
                pos[0]["rate"] = round(pos[0]["rate"],3)
                ppo = pos[0]["rate"]
            # if not pos:
            #     pos = 123
            # if pos:
                # pos_ex = get_exchange_rate(pos["currency"],mr_currency)
                # pos["amount"] = pos_ex * pos["amount"]
                # pos["amount"] = round(pos["amount"],3)
            
            purchase_order = frappe.db.sql("""select sum(`tabPurchase Order Item`.qty) as qty from `tabPurchase Order`
                left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
                where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 and `tabPurchase Order`.company = '%s' and `tabPurchase Order`.name != '%s' """%(i["item_code"],company,name),as_dict=True)[0] or 0 
            if not purchase_order["qty"]:
                purchase_order["qty"] = 0
            purchase_receipt = frappe.db.sql("""select sum(`tabPurchase Receipt Item`.qty) as qty from `tabPurchase Receipt`
                    left join `tabPurchase Receipt Item` on `tabPurchase Receipt`.name = `tabPurchase Receipt Item`.parent
                    where `tabPurchase Receipt Item`.item_code = '%s' and `tabPurchase Receipt`.docstatus = 1 and `tabPurchase Receipt`.company = '%s' """%(i["item_code"],company),as_dict=True)[0] or 0 
            if not purchase_receipt["qty"]:
                purchase_receipt["qty"] = 0
            in_transit = purchase_order["qty"] - purchase_receipt["qty"]
            country = frappe.get_value("Company",{"name":company},["country"])
            warehouse_stock = frappe.db.sql("""
                select sum(b.actual_qty) as qty from `tabBin` b 
                join `tabWarehouse` wh on wh.name = b.warehouse
                join `tabCompany` c on c.name = wh.company
                where c.country = '%s' and b.item_code = '%s' and wh.company = '%s'
                """ % (country,i["item_code"],company),as_dict=True)[0]
            if not warehouse_stock["qty"]:
                warehouse_stock["qty"] = 0
            total_po = total_po + (i["rate"]*i["qty"])
            total_selling_rate = total_selling_rate + (m_rate["sales_price"]*i["qty"])
            # margin = ((total_selling_rate - total_po)/total_selling_rate)/100
            if total_selling_rate == 0:
                margin_percent = 0
            else:
                margin_percent = ((total_selling_rate - total_po)/total_selling_rate)*100
            data += '<tr rowspan = 2 ><td width="150px">%s</td><td width="300px" >%s</td><td align = "right" width="150px" >%s</td><td align = "right" style="padding:1px;border: 1px solid black;" colspan=1>%s</td><td align = "right" style="padding:1px;border: 1px solid black;" colspan=1 >%s</td><td align = "right" width = "120px">%s</td><td align = "right" width = "80px" >%s</td><td width = "80px" >%s</td><td align = "right" width="80px">%s</td>><td align = "right" width = "80px" >%s</td><td align = "right" width = "80px" >%s</td></tr>'%(i["item_code"],i["description"],i["qty"],ppo,round(i["rate"],2),round((i["rate"]*i["qty"]),2),m_rate["sales_price"],round((m_rate["sales_price"]*i["qty"]),2),round(margin,2),warehouse_stock["qty"],in_transit)
        data+= '<tr><td style="background-color:lightgrey" colspan = "5" ><b><center>Total</center><b></td><td style="background-color:lightgrey" width = "80px" >%s</td><td style="background-color:lightgrey" width = "80px" >%s</td></td><td style="background-color:lightgrey" width = "80px" >%s</td></td><td style="background-color:lightgrey" width = "80px" >%s</td></td><td style="background-color:lightgrey" width = "80px" >%s</td></td><td style="background-color:lightgrey" width = "80px" ></td>%s</td></tr>' %(round(total_po,2),'',round(total_selling_rate,2),margin_percent,'','')
        data+='</table>'
        return data

    else:
        data_1 = ''
        data_1+='<table class = table table-bordered >' 
        data_1+= '<table class="table table-bordered"><tr rowspan = 2 ><th style="padding:1px;border: 1px solid black;width:100%;" colspan=16><center><b>No Data Found</b></center></th></tr>'
        data_1+='</table>'
        return data_1


# @frappe.whitelist()
# def update_sales_order(import_file):
#     filepath = get_file(import_file)
#     pps = read_csv_content(filepath[1])
#     for pp in pps:
#         if frappe.db.exists('Sales Order',{'name':pp[2]}):
#             c = frappe.get_value("Sales Order",{"name":pp[2]},["docstatus"])
#             if c == 0 or c == 1:
#                 print(pp[2])
#                 doc = frappe.get_doc("Sales Order",pp[2])
#                 doc.prepared_by =  pp[6]
#                 doc.sale_person =  pp[7]
#                 doc.territory =  pp[8]
#                 doc.save(ignore_permissions=True)
#                 # frappe.db.set_value("Sales Order", pp[2], "prepared_by", pp[6])
#                 # frappe.db.set_value("Sales Order", pp[2], "sale_person", pp[7])
#                 # frappe.db.set_value("Sales Order", pp[2], "territory", pp[8])
#                 so = frappe.db.sql(""" update `tabSales Order` set territory = '%s',sale_person = '%s',prepared_by = '%s' where name = '%s' """%(pp[8],pp[7],pp[6],pp[2]))
#                 print(so)
        # if frappe.db.exists('Salary Structure Assignment',{'employee':pp[0]}):
        #     if pp[0] != "Employee":
        #         doj = frappe.db.get_value('Employee',{'employee':pp[0]},['date_of_joining'])
        #         if doj:
        #             if pd.to_datetime(pp[3]).date() > doj: 
        #                 company = frappe.db.get_value("Employee",{'employee':pp[0]},['company'])
        #                 print(company)
        #                 if company:
        #                     doc = frappe.new_doc("Additional Salary")
        #                     doc.employee = pp[0]
        #                     doc.company = company
        #                     doc.salary_component = pp[1]
        #                     doc.amount = int(str(pp[2]).replace(',',''))
        #                     doc.payroll_date = '2022-02-16'
        #                     doc.save(ignore_permissions = True)
        #                     doc.submit


# @frappe.whitelist()
# def check_so_items(so_no):
#     item = frappe.db.sql(""" select sum(`tabMaterial Request Item`.qty) as qty,sum(`tabaterial Request Item`.amount) as amount from `tabMaterial Request` where `tabMaterial Request`.sales_order_number = %s """%(so_no),as_dict = True)
#     return "hi"

# @frappe.whitelist()
# def so_update():
#     so = frappe.db.sql(""" update `tabSales Order` set territory = '%s',sale_person = '%s',prepared_by = '%s' where name = '%s' """%("Vietnam","leminhthe@norden.com.sg","deepa@nordencommunication.com","SO-NSPL-2022-00055"))


@frappe.whitelist()
def get_credit_days(supplier,self):
    sup_name = frappe.get_value("Supplier",{"name":supplier},["payment_terms"])
    if sup_name:
        crd_days = frappe.db.sql("""select `tabPayment Terms Template Detail`.credit_days as credit_days
                             from `tabPayment Terms Template` left join `tabPayment Terms Template Detail` on `tabPayment Terms Template`.name = `tabPayment Terms Template Detail`.parent 
                             where `tabPayment Terms Template`.docstatus !=2 """,as_dict= 1)[0]
        
        return crd_days['credit_days']

    # url = get_url_to_form("Logistics Request", self.name)
    # 	frappe.sendmail(
    # 		recipients='karthikeyan.s@groupteampro.com',
    # 		subject=_("Logistics OPS Request"),
    # 		header=_("Logistics OPS Request"),
    # 		message = """<p style='font-size:18px'>Logistics OPS Request has been raised for Purchase Order - (<b>%s</b>).</p><br><br>
    # 		<form action="%s">
    # 		<input type="submit" value="Open Logistics Request" />
    # 		</form>
    # 		"""%(self.order_no,url)
    # 	)




@frappe.whitelist()
def change_territory(customer,territory):
    quotation = frappe.get_all("Quotation",{"customer_name":customer,"docstatus":"draft"})
    sale_order = frappe.get_all("Sales Order",{"customer":customer,"docstatus":"draft"})
    sale_invoice = frappe.get_all("Sales Invoice",{"customer":customer,"docstatus":"draft"})
    delivery_note = frappe.get_all("Delivery Note",{"customer":customer,"docstatus":"draft"})
    for q in quotation:
        frappe.db.set_value("Quotation",q.name,"territory",territory)
    for s in sale_order:
        frappe.db.set_value("Sales Order",s.name,"territory",territory)
    for si in sale_invoice:
        frappe.db.set_value("Sales Invoice",si.name,"territory",territory)
    for d in delivery_note:
        frappe.db.set_value("Delivery Note",d.name,"territory",territory)


@frappe.whitelist()
def margin(item_details,company,currency,exchange_rate,user,price_list,territory):
    item_details = json.loads(item_details)
    data = ''
    if "CFO" in frappe.get_roles(frappe.session.user) or "COO" in frappe.get_roles(frappe.session.user) or "HOD" in frappe.get_roles(frappe.session.user) or "Accounts User" in frappe.get_roles(frappe.session.user):
        data+= '<table class="table"><tr><th style="padding:1px;border: 1px solid black;font-size:14px;background-color:#e20026;color:white;" colspan=18><center><b>MARGIN BY VALUE & MARGIN BY PERCENTAGE</b></center></th></tr>'
        spl = 0
        for i in item_details:
            if i["special_cost"] > 0:
                spl = spl + 1
        if spl == 0:
            if price_list == "Singapore Internal Cost":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;background-color:#A9A9A9;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;background-color:#A9A9A9;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>INTERNAL COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>SP</b></td></tr>'
            if price_list == "Singapore Freight":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;background-color:#A9A9A9;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;background-color:#A9A9A9;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>FREIGHT</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>FREIGHT %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>SP</b></td></tr>'
            if price_list == "Singapore Sales Price":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;background-color:#A9A9A9;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;background-color:#A9A9A9;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>SALES PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>SALES PRICE %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>SP</b></td></tr>'
            
            if price_list == "Bangladesh Internal Cost":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;background-color:#A9A9A9;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;background-color:#A9A9A9;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>INTERNAL COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>SP</b></td></tr>'
            if price_list == "Bangladesh Freight":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;background-color:#A9A9A9;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;background-color:#A9A9A9;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>FREIGHT</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>FREIGHT %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>SP</b></td></tr>'
            if price_list == "Bangladesh Sales Price":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;background-color:#A9A9A9;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;background-color:#A9A9A9;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>SALES PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>SALES PRICE %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;background-color:#A9A9A9;"><b>SP</b></td></tr>'

            if price_list == "Philippines Internal Cost":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;background-color:#A9A9A9;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Philippines Freight":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;background-color:#A9A9A9;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Philippines Sales Price":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;background-color:#A9A9A9;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'

            if price_list == "Malaysia Internal Cost":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Malaysia Freight":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Malaysia Sales Price":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            
            if price_list == "Indonesia Internal Cost":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Indonesia Freight":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Indonesia Sales Price":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'

            if price_list == "Vietnam Internal Cost":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Vietnam Freight":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Vietnam Sales Price":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'

            if price_list == "Cambodia Internal Cost":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Cambodia Freight":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Cambodia Sales Price":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'

            if price_list == "Srilanka Internal Cost":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Srilanka Freight":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Srilanka Sales Price":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
           
            if price_list == "UK Freight":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "UK Destination Charges":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>DESTINATION CHARGES</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>DESTINATION CHARGES %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "UK Installer":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INSTALLER</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INSTALLER %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "UK Distributor":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>DISTRIBUTOR</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>DISTRIBUTOR %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
           
            if price_list == "Landing - NCMEF":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>LANDING</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>LANDING %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Internal - NCMEF":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Incentive - NCMEF":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INCENTIVE</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INCENTIVE %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Dist. Price - NCMEF":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>DISTRIBUTOR</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>DISTRIBUTOR %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Saudi Dist. - NCMEF":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SAUDI</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SAUDI %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SELLING PRICE</b></td></tr>'
            if price_list == "Project Group - NCMEF":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>PROJECT</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>PROJECT %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Retail - NCMEF":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>RETAIL</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>RETAIL %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Electra Qatar - NCMEF":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>ELECTRA</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>ELECTRA %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'

            
            
            
            
            if price_list == "India Landing":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b><center>LANDING</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>LANDING%</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "India SPC":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b><center>SPC</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SPC%</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "India STP":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b><center>STP</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>STP%</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "India LTP":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b><center>LTP</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>LTP%</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "India DTP":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b><center>DTP</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>DTP%</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "India MOP":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b><center>MOP</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>MOP%</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "India MRP":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b><center>MRP</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>MRP%</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
        else:
            data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=2 style="border: 1px solid black;font-size:11px;width:30%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b><center>INTERNAL COST</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SPECIAL PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SELLING PRICE</b></td></tr>'

    total_internal_cost = 0
    total_special_price = 0
    total_selling_price = 0
    cost_total = 0
    total_valuation_rate = 0
    spcl = 0
    total_warehouse = 0
    total_in_transit = 0
    total_stock = 0
    sum_of_total_stock = 0
    price_table = []
    dubai_landing_margin = 0
    dubai_incentive_margin = 0
    dubai_internal_margin = 0
    dubai_distributor_margin = 0
    saudi_margin = 0
    dubai_project_margin = 0
    dubai_retail_margin = 0
    dubai_electra_margin = 0
    d_sbu_margin = 0
    india_landing_margin = 0
    india_spc_margin = 0
    india_ltp_margin = 0
    india_dtp_margin = 0
    india_stp_margin = 0 
    india_mop_margin = 0
    india_mrp_margin = 0
    total_selling_price = 0

    singapore_internal_cost_total = 0  
    singapore_internal_cost_total_margin = 0  
    singapore_sales_price_total = 0  
    singapore_sales_price_total_margin = 0  
    singapore_freight_total = 0  
    singapore_freight_total_margin = 0
    singapore_freight_margin_total = 0
    
    vietnam_internal_cost_total = 0  
    vietnam_internal_cost_total_margin = 0  
    vietnam_sales_price_total = 0  
    vietnam_sales_price_total_margin = 0  
    vietnam_freight_total = 0  
    vietnam_freight_total_margin = 0  

    philippines_internal_cost_total = 0  
    philippines_internal_cost_total_margin = 0  
    philippines_sales_price_total = 0  
    philippines_sales_price_total_margin = 0  
    philippines_freight_total = 0  
    philippines_freight_total_margin = 0  

    malaysia_internal_cost_total = 0  
    malaysia_internal_cost_total_margin = 0  
    malaysia_sales_price_total = 0  
    malaysia_sales_price_total_margin = 0  
    malaysia_freight_total = 0  
    malaysia_freight_total_margin = 0  

    indonesia_internal_cost_total = 0
    indonesia_internal_cost_total_margin = 0 
    indonesia_sales_price_total = 0
    indonesia_sales_price_total_margin = 0
    indonesia_freight_total = 0
    indonesia_freight_total_margin = 0
    
    cambodia_internal_cost_total = 0
    cambodia_internal_cost_total_margin = 0 
    cambodia_sales_price_total = 0
    cambodia_sales_price_total_margin = 0
    cambodia_freight_total = 0
    cambodia_freight_total_margin = 0

    srilanka_internal_cost_total = 0
    srilanka_internal_cost_total_margin = 0 
    srilanka_sales_price_total = 0
    srilanka_sales_price_total_margin = 0
    srilanka_freight_total = 0
    srilanka_freight_total_margin = 0

    bangladesh_internal_cost_total = 0
    bangladesh_internal_cost_total_margin = 0 
    bangladesh_sales_price_total = 0
    bangladesh_sales_price_total_margin = 0
    bangladesh_freight_total = 0
    bangladesh_freight_total_margin = 0

    uk_freight_margin= 0
    uk_destination_charges_margin = 0
    uk_installer_margin = 0
    uk_distributor_margin = 0

    uk_freight_total= 0
    uk_freight_total_margin= 0
    uk_destination_charges_total = 0
    uk_destination_charges_total_margin= 0
    uk_installer_total = 0
    uk_installer_total_margin = 0
    uk_distributor_total = 0
    uk_distributor_total_margin = 0

    india_landing_total = 0
    india_landing_total_margin = 0
    india_spc_total = 0
    india_spc_total_margin = 0
    india_ltp_total = 0
    india_ltp_total_margin = 0
    india_dtp_total = 0
    india_dtp_total_margin = 0
    india_stp_total = 0 
    india_stp_total_margin = 0 
    india_mop_total = 0
    india_mop_total_margin = 0
    india_mrp_total = 0
    india_mrp_total_margin = 0

    sbu_total = 0
    i_sbu_total = 0
    d_sbu_total = 0
    sbu_total_margin = 0
    i_sbu_total_margin = 0
    d_sbu_total_margin = 0



     
  
    for i in item_details:
        total_selling_price = round((total_selling_price + i["amount"]),2)
        country = frappe.get_value("Company",{"name":company},["country"])
        warehouse_stock = frappe.db.sql("""
            select (sum(`tabBin`.actual_qty) - sum(b.reserved_stock)) as qty from `tabBin` b 
            join `tabWarehouse` wh on wh.name = b.warehouse
            join `tabCompany` c on c.name = wh.company
            where c.country = '%s' and b.item_code = '%s' and wh.company = '%s'
            """ % (country,i["item_code"],company),as_dict=True)[0]
        if not warehouse_stock["qty"]:
            warehouse_stock["qty"] = 0
        total_warehouse = total_warehouse + warehouse_stock["qty"]

        purchase_order = frappe.db.sql("""select sum(`tabPurchase Order Item`.qty) as qty from `tabPurchase Order`
                left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
                where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 and `tabPurchase Order`.company = '%s'  """%(i["item_code"],company),as_dict=True)[0] or 0 
        if not purchase_order["qty"]:
            purchase_order["qty"] = 0
        purchase_receipt = frappe.db.sql("""select sum(`tabPurchase Receipt Item`.qty) as qty from `tabPurchase Receipt`
                left join `tabPurchase Receipt Item` on `tabPurchase Receipt`.name = `tabPurchase Receipt Item`.parent
                where `tabPurchase Receipt Item`.item_code = '%s' and `tabPurchase Receipt`.docstatus = 1 and  `tabPurchase Receipt`.company = '%s' """%(i["item_code"],company),as_dict=True)[0] or 0 
        if not purchase_receipt["qty"]:
            purchase_receipt["qty"] = 0
        in_transit = purchase_order["qty"] - purchase_receipt["qty"]
        total_in_transit = in_transit + total_in_transit 
        total_stock =  warehouse_stock["qty"] + in_transit
        sum_of_total_stock = total_stock + sum_of_total_stock 
        if i["special_cost"] > 0:
            spcl = spcl + 1

        sbu = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':'STANDARD BUYING-USD'},["price_list_rate"])
        # sbu_total = sbu_total + sbu
        if not sbu:
            sbu = 0
        sbus = sbu * i["qty"]
        sbu_total = round((sbus + sbu_total),2)

        
        if territory == "Bangladesh" or territory == "Cambodia" or territory == "Indonesia" or territory == "Singapore" or territory == "Bangladesh" or territory == "Malaysia" or territory == "Sri Lanka" or territory == "Srilanka" or territory == "Vietnam" or territory == "Philippines" or territory == "United Kingdom":
            sbu_margin = round(((i["amount"]-sbu*i["qty"])/i["amount"]*100),2)
       
        if territory == "Dubai" or territory == "United Arab Emirates":
            ep = get_exchange_rate('USD',"AED")
            d_sbu = round(sbu*ep,1)
            d_sbus = round((d_sbu * i["qty"]),2)
            d_sbu_total = d_sbu_total + (d_sbu*i["qty"])
            d_sbu_margin = round(((i["amount"]- d_sbu*i["qty"])/i["amount"]*100),2)
       
        if territory == "India":
            ep = get_exchange_rate('USD',"INR")
            i_sbu = round(sbu*ep,1)
            i_sbu_total = i_sbu + i_sbu_total
            i_sbu_margin = round(((i["amount"]- i_sbu*i["qty"])/i["amount"]*100),2)

        if territory == "United Kingdom":
            uk_table = frappe.get_single("Margin Price Tool").uk
            item_group = frappe.get_value("Item",{"name":i["item_code"]},["item_sub_group"])
            for s in uk_table:
                if item_group == s.item_group:
                    uk_freight = round((sbu * s.freight),2)*i["qty"]
                    uk_destination_charges = round((uk_freight * s.destination_charges),2)*i["qty"]
                    uk_installer = round((uk_destination_charges/(100 - s.installer)*100),2)
                    uk_distributor = round((uk_installer/(100 - s.distributor)*100),2)
                    uk_freight_margin = (((i["amount"] - uk_freight)/i["amount"])*100)
                    uk_destination_charges_margin = (((i["amount"] - uk_destination_charges)/i["amount"])*100)
                    uk_installer_margin = (((i["amount"] -  uk_installer)/i["amount"])*100)
                    uk_distributor_margin = (((i["amount"] - uk_distributor)/i["amount"])*100)
                    uk_freight_total =  uk_freight + uk_freight_total 
                    uk_freight_total_margin= round(((total_selling_price - uk_freight_total)/total_selling_price*100),2)
                    uk_destination_charges_total = uk_destination_charges + uk_destination_charges_total
                    uk_destination_charges_total_margin= round(((total_selling_price - uk_destination_charges_total)/total_selling_price*100),2)
                    uk_installer_total = uk_installer + uk_installer_total
                    uk_installer_total_margin = round(((total_selling_price - uk_installer_total)/total_selling_price*100),2)
                    uk_distributor_total = uk_distributor + uk_distributor_total
                    uk_distributor_total_margin = round(((total_selling_price - uk_distributor_total)/total_selling_price*100),2)
                    

        if territory == "Singapore":
            singapore_table = frappe.get_single("Margin Price Tool").singapore
            item_group = frappe.get_value("Item",{"name":i["item_code"]},["item_sub_group"])
            for s in singapore_table:
                if item_group == s.item_group:
                    # singapore_sales_price = sbu * s.sales_price
                    sic = ((sbu * s.internal_cost))
                    singapore_internal_cost = sic*i["qty"]
                    singapore_sales_price = (((sic/(100 - s.sales_price))*100)* s.freight)*i["qty"]
                    singapore_freight = ((((sic/(100 - s.sales_price))*100)* s.freight)*i["qty"])
                    singapore_internal_cost_margin = (((i["amount"] - singapore_internal_cost)/i["amount"])*100)
                    singapore_sales_price_margin = (((i["amount"] - singapore_sales_price)/i["amount"])*100)
                    singapore_freight_margin = (((i["amount"] - singapore_freight)/i["amount"])*100)
                    singapore_internal_cost_total = round((singapore_internal_cost +  singapore_internal_cost_total),2)
                    singapore_internal_cost_total_margin = round(((total_selling_price - singapore_internal_cost_total)/total_selling_price*100),2)
                    singapore_sales_price_total = round((singapore_sales_price +  singapore_sales_price_total),2) 
                    singapore_sales_price_total_margin = round(((total_selling_price - singapore_sales_price_total)/total_selling_price*100),2)
                    singapore_freight_total = round((singapore_freight +  singapore_freight_total),2)
                    singapore_freight_total_margin = round(((total_selling_price - singapore_freight_total)/total_selling_price*100),2)
                
        
        if territory == "Vietnam":
            vietnam_table = frappe.get_single("Margin Price Tool").vietnam
            item_group = frappe.get_value("Item",{"name":i["item_code"]},["item_sub_group"])
            for s in vietnam_table:
                if item_group == s.item_group:
                    # singapore_sales_price = sbu * s.sales_price
                    vietnam_internal_cost = (((i["amount"] - vietnam_internal_cost)/i["amount"])*100)
                    vietnam_sales_price_margin = (((i["amount"] - vietnam_sales_price)/i["amount"])*100)
                    vietnam_freight_margin = (((i["amount"] - vietnam_freight)/i["amount"])*100)
                    vietnam_internal_cost_total = vietnam_internal_cost +  vietnam_internal_cost_total
                    vietnam_internal_cost_total_margin = round(((total_selling_price - vietnam_internal_cost_total)/total_selling_price*100),2)
                    vietnam_sales_price_total = vietnam_sales_price +  vietnam_sales_price_total 
                    vietnam_sales_price_total_margin = round(((total_selling_price - vietnam_sales_price_total)/total_selling_price*100),2)
                    vietnam_freight_total = vietnam_freight +  vietnam_freight_total 
                    vietnam_freight_total_margin = round(((total_selling_price - vietnam_freight_total)/total_selling_price*100),2)
                    
                    

        if territory == "Philippines":
            philippines_table = frappe.get_single("Margin Price Tool").philippines
            item_group = frappe.get_value("Item",{"name":i["item_code"]},["item_sub_group"])
            for s in philippines_table:
                if item_group == s.item_group:
                    # singapore_sales_price = sbu * s.sales_price
                    philippines_internal_cost = round((sbu * s.internal_cost),2)*i["qty"]
                    philippines_sales_price = ((philippines_internal_cost/(100 - s.sales_price))*100)*i["qty"]
                    philippines_freight = round((philippines_sales_price * s.freight),2)*i["qty"]
                    philippines_internal_cost_margin = (((i["amount"] - philippines_internal_cost)/i["amount"])*100)
                    philippines_sales_price_margin = (((i["amount"] - philippines_sales_price)/i["amount"])*100)
                    philippines_freight_margin = (((i["amount"] - philippines_freight)/i["amount"])*100)
                    philippines_internal_cost_total = philippines_internal_cost +  philippines_internal_cost_total
                    philippines_internal_cost_total_margin = round(((total_selling_price - philippines_internal_cost_total)/total_selling_price*100),2)
                    philippines_sales_price_total = philippines_sales_price +  philippines_sales_price_total 
                    philippines_sales_price_total_margin = round(((total_selling_price - philippines_sales_price_total)/total_selling_price*100),2)
                    philippines_freight_total = philippines_freight + philippines_freight_total 
                    philippines_freight_total_margin = round(((total_selling_price - philippines_freight_total)/total_selling_price*100),2)
                    

        if territory == "Malaysia":
            malaysia_table = frappe.get_single("Margin Price Tool").malaysia
            item_group = frappe.get_value("Item",{"name":i["item_code"]},["item_sub_group"])
            for s in malaysia_table:
                if item_group == s.item_group:
                    # singapore_sales_price = sbu * s.sales_price
                    malaysia_internal_cost = round((sbu * s.internal_cost),2) * i["qty"]
                    malaysia_sales_price = ((malaysia_internal_cost/(100 - s.sales_price))*100)* i["qty"]
                    malaysia_freight = round((malaysia_sales_price * s.freight),2)* i["qty"]
                    malaysia_internal_cost_margin = (((i["amount"] - malaysia_internal_cost)/i["amount"])*100)
                    malaysia__sales_price_margin = (((i["amount"] -   malaysia_sales_price)/i["amount"])*100)
                    malaysia_freight_margin = (((i["amount"] -  malaysia_freight)/i["amount"])*100)
                    malaysia_internal_cost_total = malaysia_internal_cost +  malaysia_internal_cost_total
                    malaysia_internal_cost_total_margin = round(((total_selling_price - malaysia_internal_cost_total)/total_selling_price*100),2)
                    malaysia_sales_price_total = malaysia_sales_price + malaysia_sales_price_total 
                    malaysia_sales_price_total_margin = round(((total_selling_price - malaysia_sales_price_total)/total_selling_price*100),2)
                    malaysia_freight_total = malaysia_freight + malaysia_freight_total 
                    malaysia_freight_total_margin = round(((total_selling_price - malaysia_freight_total)/total_selling_price*100),2)


        if territory == "Indonesia":
            indonesia_table = frappe.get_single("Margin Price Tool").indonesia
            item_group = frappe.get_value("Item",{"name":i["item_code"]},["item_sub_group"])
            for s in indonesia_table:
                if item_group == s.item_group:
                    # singapore_sales_price = sbu * s.sales_price
                    indonesia_internal_cost = round((sbu * s.internal_cost),2)* i["qty"]
                    indonesia_sales_price = ((indonesia_internal_cost/(100 - s.sales_price))*100)* i["qty"]
                    indonesia_freight = round((indonesia_sales_price * s.freight),2)* i["qty"]
                    indonesia_internal_cost_margin = (((i["amount"] - indonesia_internal_cost)/i["amount"])*100)
                    indonesia_sales_price_margin = (((i["amount"] -   indonesia_sales_price)/i["amount"])*100)
                    indonesia_freight_margin = (((i["amount"] - indonesia_freight)/i["amount"])*100)
                    indonesia_internal_cost_total = indonesia_internal_cost +  indonesia_internal_cost_total
                    indonesia_internal_cost_total_margin = round(((total_selling_price - indonesia_internal_cost_total)/total_selling_price*100),2)
                    indonesia_sales_price_total = indonesia_sales_price + indonesia_sales_price_total 
                    indonesia_sales_price_total_margin = round(((total_selling_price - indonesia_sales_price_total)/total_selling_price*100),2)
                    indonesia_freight_total = indonesia_freight + indonesia_freight_total 
                    indonesia_freight_total_margin = round(((total_selling_price - indonesia_freight_total)/total_selling_price*100),2)

                

        if territory == "Cambodia":
            cambodia_table = frappe.get_single("Margin Price Tool").cambodia
            item_group = frappe.get_value("Item",{"name":i["item_code"]},["item_sub_group"])
            for s in cambodia_table:
                if item_group == s.item_group:
                    # singapore_sales_price = sbu * s.sales_price
                    cambodia_internal_cost = round((sbu * s.internal_cost),2)* i["qty"]
                    cambodia_sales_price = ((cambodia_internal_cost/(100 - s.sales_price))*100)* i["qty"]
                    cambodia_freight = round((cambodia_sales_price * s.freight),2)* i["qty"]
                    cambodia_internal_cost_margin = (((i["amount"] - cambodia_internal_cost)/i["amount"])*100)
                    cambodia_sales_price_margin = (((i["amount"] -   cambodia_sales_price)/i["amount"])*100)
                    cambodia_freight_margin = (((i["amount"] - cambodia_freight)/i["amount"])*100)
                    cambodia_internal_cost_total = cambodia_internal_cost + cambodia_internal_cost_total
                    cambodia_internal_cost_total_margin = round(((total_selling_price - cambodia_internal_cost_total)/total_selling_price*100),2)
                    cambodia_sales_price_total = cambodia_sales_price + cambodia_sales_price_total 
                    cambodia_sales_price_total_margin = round(((total_selling_price - cambodia_sales_price_total)/total_selling_price*100),2)
                    cambodia_freight_total = cambodia_freight + cambodia_freight_total 
                    cambodia_freight_total_margin = round(((total_selling_price - cambodia_freight_total)/total_selling_price*100),2)


        if territory == "Srilanka" or territory == "Sri Lanka":
            srilanka_table = frappe.get_single("Margin Price Tool").srilanka
            item_group = frappe.get_value("Item",{"name":i["item_code"]},["item_sub_group"])
            for s in srilanka_table:
                if item_group == s.item_group:
                    # singapore_sales_price = sbu * s.sales_price
                    srilanka_internal_cost = round((sbu * s.internal_cost),2)*i["qty"]
                    srilanka_sales_price = ((srilanka_internal_cost/(100 - s.sales_price))*100)*i["qty"]
                    srilanka_freight = round((srilanka_sales_price * s.freight),2)*i["qty"]
                    srilanka_internal_cost_margin = (((i["amount"] - srilanka_internal_cost)/i["amount"])*100)
                    srilanka_sales_price_margin = (((i["amount"] - srilanka_sales_price)/i["amount"])*100)
                    srilanka_freight_margin = (((i["amount"] - srilanka_freight)/i["amount"])*100)
                    srilanka_internal_cost_total = srilanka_internal_cost + srilanka_internal_cost_total
                    srilanka_internal_cost_total_margin = round(((total_selling_price - srilanka_internal_cost_total)/total_selling_price*100),2)
                    srilanka_sales_price_total = srilanka_sales_price + srilanka_sales_price_total 
                    srilanka_sales_price_total_margin = round(((total_selling_price - srilanka_sales_price_total)/total_selling_price*100),2)
                    srilanka_freight_total = srilanka_freight + srilanka_freight_total 
                    srilanka_freight_total_margin = round(((total_selling_price - srilanka_freight_total)/total_selling_price*100),2)
                

        if territory == "Bangladesh":
            bangladesh_table = frappe.get_single("Margin Price Tool").bangladesh
            item_group = frappe.get_value("Item",{"name":i["item_code"]},["item_sub_group"])
            for s in bangladesh_table:
                if item_group == s.item_group:
                    # singapore_sales_price = sbu * s.sales_price
                    bangladesh_internal_cost = round((sbu * s.internal_cost),2)
                    bangladesh_sales_price = (bangladesh_internal_cost/(100 - s.sales_price))*100
                    bangladesh_freight = round((bangladesh_sales_price * s.freight),2)
                    bangladesh_internal_cost_margin = (((i["amount"] - bangladesh_internal_cost)/i["amount"])*100)
                    bangladesh_sales_price_margin = (((i["amount"] - bangladesh_sales_price)/i["amount"])*100)
                    bangladesh_freight_margin = (((i["amount"] - bangladesh_freight)/i["amount"])*100)
                    bangladesh_internal_cost_total = bangladesh_internal_cost + bangladesh_internal_cost_total
                    bangladesh_internal_cost_total_margin = round(((total_selling_price - bangladesh_internal_cost_total)/total_selling_price*100),2)
                    bangladesh_sales_price_total = bangladesh_sales_price + bangladesh_sales_price_total 
                    bangladesh_sales_price_total_margin = round(((total_selling_price - bangladesh_sales_price_total)/total_selling_price*100),2)
                    bangladesh_freight_total = bangladesh_freight + bangladesh_freight_total 
                    bangladesh_freight_total_margin = round(((total_selling_price - bangladesh_freight_total)/total_selling_price*100),2)
            



        if territory == "Dubai" or territory == "United Arab Emirates":
            dubai_table = frappe.get_single("Margin Price Tool").dubai
            item_group = frappe.get_value("Item",{"name":i["item_code"]},["item_sub_group"])
            for d in dubai_table:
                if item_group == d.item_group:
                    dubai_landing = (frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"Landing - NCMEF"},['price_list_rate'])*i["qty"])
                    
                    dubai_incentive = (frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"Incentive - NCMEF"},['price_list_rate'])*i['qty'])
                    
                    dubai_internal = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"Internal - NCMEF"},['price_list_rate'])*i['qty']
                    
                    dubai_distributor = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"Dist. Price - NCMEF"},['price_list_rate'])*i['qty']
                    
                    saudi = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"Saudi Dist. - NCMEF"},['price_list_rate'])*i['qty']
                    
                    dubai_project = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"Project Group - NCMEF"},['price_list_rate'])*i['qty']
                    
                    dubai_retail = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"Retail - NCMEF"},['price_list_rate'])*i["qty"]
                    
                    dubai_electra = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"Electra Qatar - NCMEF"},['price_list_rate'])
                    
                    dubai_landing_margin = (((i["amount"] - dubai_landing)/i["amount"])*100)
                    dubai_incentive_margin = round((((i["amount"] - dubai_incentive)/i["amount"])*100),2)
                    dubai_internal_margin = round((((i["amount"] - dubai_internal)/i["amount"])*100),2)
                    dubai_distributor_margin =  round((((i["amount"] - dubai_distributor)/i["amount"])*100),2)
                    saudi_margin =  round((((i["amount"] - saudi)/i["amount"])*100),2)
                    dubai_project_margin =  round((((i["amount"] - dubai_project)/i["amount"])*100),2)
                    dubai_retail_margin =  round((((i["amount"] - dubai_retail)/i["amount"])*100),2)
                    dubai_electra_margin =  round((((i["amount"] - dubai_electra)/i["amount"])*100),2)

        if territory == "India":
            india_table = frappe.get_single("Margin Price Tool").india
            item_group = frappe.get_value("Item",{"name":i["item_code"]},["item_sub_group"])
            for d in india_table: 
                if item_group == d.item_group:
                    india_landing = round((i_sbu * d.landing),2)*i["qty"]
                    india_spc  = round((india_landing/ d.spc),2)*i["qty"]
                    india_ltp = round((india_spc / d.ltp),2)*i["qty"]
                    india_dtp = round((india_ltp / d.dtp),2)*i["qty"]
                    india_stp = round((india_dtp / d.stp),2)*i["qty"]*i["qty"]
                    india_mop = round((india_stp / d.mop),2)*i["qty"]
                    india_mrp = round((india_mop / d.mrp),2)*i["qty"]
                    india_landing_margin = (((i["amount"] - india_landing)/i["amount"])*100)
                    india_spc_margin = (((i["amount"] - india_landing)/i["amount"])*100)
                    india_ltp_margin = (((i["amount"] - india_ltp)/i["amount"])*100)
                    india_dtp_margin = (((i["amount"] - india_dtp)/i["amount"])*100)
                    india_stp_margin = (((i["amount"] - india_stp)/i["amount"])*100) 
                    india_mop_margin = (((i["amount"] - india_mop)/i["amount"])*100)
                    india_mrp_margin = (((i["amount"] - india_mrp)/i["amount"])*100)  

                    india_landing_total = india_landing_total + india_landing
                    india_landing_total_margin = round(((total_selling_price -  india_landing_total)/total_selling_price*100),2)
                    india_spc_total =  india_spc_total +india_spc
                    india_spc_total_margin = round(((total_selling_price -  india_spc_total)/total_selling_price*100),2)
                    india_ltp_total =  india_ltp_total + india_ltp
                    india_ltp_total_margin = round(((total_selling_price -  india_ltp_total)/total_selling_price*100),2)
                    india_dtp_total =  india_dtp_total + india_dtp
                    india_dtp_total_margin = round(((total_selling_price -   india_dtp_total )/total_selling_price*100),2)
                    india_stp_total = india_stp_total + india_stp
                    india_stp_total_margin = round(((total_selling_price -  india_stp_total)/total_selling_price*100),2)
                    india_mop_total = india_mop_total + india_mop
                    india_mop_total_margin = round(((total_selling_price - india_mop_total)/total_selling_price*100),2)
                    india_mrp_total = india_mrp_total +  india_mrp
                    india_mrp_total_margin = round(((total_selling_price - india_mrp_total)/total_selling_price*100),2)
                    
                
       
        if "CFO" in frappe.get_roles(frappe.session.user) or "COO" in frappe.get_roles(frappe.session.user) or "HOD" in frappe.get_roles(frappe.session.user) or "Accounts User" in frappe.get_roles(frappe.session.user):
            if i["special_cost"] > 0:
                data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=2 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,i["qty"],total_stock,'','','','','','')
            else:
                if price_list == "Singapore Internal Cost":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],i["qty"],round(sbus,2), sbu_margin,round(singapore_internal_cost,2),round(singapore_internal_cost_margin,2),round(i["amount"],2))
                if price_list == "Singapore Sales Price":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],i["qty"],round(sbus,2),sbu_margin,round(singapore_sales_price,2),round(singapore_sales_price_margin,2),round(i["amount"],2))
                if price_list == "Singapore Freight":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],i["qty"],round(sbus,2), sbu_margin,round(singapore_freight,2),round(singapore_freight_margin,2),round(i["amount"],2))
                
                if price_list == "Vietnam Internal Cost":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(sbus,2),sbu_margin,round(vietnam_internal_cost,2),round(vietnam_internal_cost_margin,2),round(i["amount"],2))
                if price_list == "Vietnam Sales Price":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(sbus,2),sbu_margin,round(vietnam_sales_price,2),round(vietnam_sales_price_margin,2),round(i["amount"],2))
                if price_list == "Vietnam Freight":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(sbus,2),sbu_margin,round(vietnam_freight,2),round(vietnam_freight_margin,2),round(i["amount"],2))
                
                if price_list == "Bangladesh Internal Cost":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],i["qty"],round(sbus,2),sbu_margin,round(bangladesh_internal_cost,2),round(bangladesh_internal_cost_margin,2),round(i["amount"],2))
                if price_list == "Bangladesh Sales Price":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],i["qty"],round(sbus,2),sbu_margin,round(bangladesh_sales_price,2),round(bangladesh_sales_price_margin,2),round(i["amount"],2))
                if price_list == "Bangladesh Freight":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],i["qty"],round(sbus,2),sbu_margin,round(bangladesh_freight,2),round(bangladesh_freight_margin,2),round(i["amount"],2))

                if price_list == "Cambodia Internal Cost":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(sbus,2),sbu_margin,round(cambodia_internal_cost,2),round(cambodia_internal_cost_margin,2),round(i["amount"],2))
                if price_list == "Cambodia Sales Price":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(sbus,2),sbu_margin,round(cambodia_sales_price,2),round(cambodia_sales_price_margin,2),round(i["amount"],2))
                if price_list == "Cambodia Freight":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(sbus,2),sbu_margin,round(cambodia_freight,2),round(cambodia_freight_margin,2),round(i["amount"],2))

                if price_list == "Philippines Internal Cost":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(sbus,2),sbu_margin,round(philippines_internal_cost,2),round(philippines_internal_cost_margin,2),round(i["amount"],2))
                if price_list == "Philippines Sales Price":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(sbus,2),sbu_margin,round(philippines_sales_price,2),round(philippines_sales_price_margin,2),round(i["amount"],2))
                if price_list == "Philippines Freight":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(sbus,2),sbu_margin,round(philippines_freight,2),round(philippines_freight_margin,2),round(i["amount"],2))
                
                if price_list == "Malaysia Internal Cost":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(sbus,2),sbu_margin,malaysia_internal_cost,round(malaysia_internal_cost_margin,2),round(i["amount"],2))
                if price_list ==  "Malaysia Sales Price":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(sbus,2),sbu_margin,malaysia_sales_price,round(malaysia__sales_price_margin,2),round(i["amount"],2))
                if price_list == "Malaysia Freight":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(sbus,2),sbu_margin,round(malaysia_freight,2),round(malaysia_freight_margin,2),round(i["amount"],2))
                
                if price_list == "Indonesia Internal Cost":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(sbus,2),sbu_margin,round(indonesia_internal_cost,2),round(indonesia_internal_cost_margin,2),round(i["amount"],2))
                if price_list ==  "Indonesia Sales Price":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(sbus,2),sbu_margin,round(indonesia_sales_price,2),round(indonesia_sales_price_margin,2),round(i["amount"],2))
                if price_list == "Indonesia Freight":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(sbus,2),sbu_margin,round(indonesia_freight,2),round(indonesia_freight_margin,2),round(i["amount"],2))
                
                if price_list == "Srilanka Internal Cost":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(sbus,2),sbu_margin,round(srilanka_internal_cost,2),round(srilanka_internal_cost_margin,2),round(i["amount"],2))
                if price_list ==  "Srilanka Sales Price":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(sbus,2),sbu_margin,round(srilanka_sales_price,2),round(srilanka_sales_price_margin,2),round(i["amount"],2))
                if price_list == "Srilanka Freight":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(sbus,2),sbu_margin,round(srilanka_freight,2),round(srilanka_freight_margin,2),round(i["amount"],2))
                
                if price_list == "UK Freight":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(sbus,2),sbu_margin,round(uk_freight,2),round(uk_freight_margin,2),round(i["amount"],2))
                if price_list ==  "UK Destination Charges":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(sbus,2),sbu_margin,round(uk_destination_charges,2),round(uk_destination_charges_margin),round(i["amount"],2))
                if price_list == "UK Installer":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(sbus,2),sbu_margin,round(uk_installer,2),round(uk_installer_margin),round(i["amount"],2))
                if price_list == "UK Distributor":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(sbus,2),sbu_margin,round(uk_distributor,2),round(uk_distributor_margin,2),round(i["amount"],2))

                if price_list == "Landing - NCMEF":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],d_sbus, d_sbu_margin,round(dubai_landing,2),round(dubai_landing_margin,2),round(i["amount"],2))
                if price_list == "Internal - NCMEF":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],d_sbus, d_sbu_margin,round((dubai_internal*i["qty"]),2),dubai_internal_margin,round(i["amount"],2))
                if price_list == "Incentive - NCMEF":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],d_sbus, d_sbu_margin,dubai_incentive*i["qty"],dubai_incentive_margin,round(i["amount"],2))
                if price_list == "Dist. Price - NCMEF":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],d_sbus, d_sbu_margin,dubai_distributor*i["qty"],dubai_distributor_margin,round(i["amount"],2))
                if price_list == "Saudi Dist. - NCMEF":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],d_sbus, d_sbu_margin,saudi*i["qty"],saudi_margin,round(i["amount"],2))
                if price_list == "Project Group - NCMEF":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],d_sbus, d_sbu_margin,dubai_project*i["qty"],dubai_project_margin,round(i["amount"],2))
                if price_list == "Retail - NCMEF":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],d_sbus, d_sbu_margin,dubai_retail*i["qty"],dubai_retail_margin,round(i["amount"],2))
                if price_list == "Electra Qatar - NCMEF":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],d_sbus, d_sbu_margin,dubai_electra*i["qty"],dubai_electra_margin,round(i["amount"],2))
                
                if price_list == "India Landing":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],i_sbu, i_sbu_margin,india_landing*i["qty"],round(india_landing_margin,2),round(i["amount"],2))
                if price_list == "India LTP":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],i_sbu,i_sbu_margin,india_ltp*i["qty"],round(india_ltp_margin,2),round(i["amount"],2))
                if price_list == "India SPC":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],i_sbu,i_sbu_margin,india_spc*i["qty"],round(india_spc_margin,2),round(i["amount"],2))
                if price_list == "India DTP":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],i_sbu, i_sbu_margin,india_dtp*i["qty"],round(india_dtp_margin,2),round(i["amount"],2))
                if price_list == "India STP":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],i_sbu,i_sbu_margin,india_stp*i["qty"],round(india_stp_margin,2),round(i["amount"],2))
                if price_list == "India MOP":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],i_sbu,i_sbu_margin,india_mop*i["qty"],round(india_mop_margin,2),round(i["amount"],2))
                if price_list == "India MRP":
                    data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],i_sbu,i_sbu_margin,india_mrp*i["qty"],round(india_mrp_margin,2),round(i["amount"],2))
   
   
    sbu_total_margin = round(((total_selling_price - sbu_total)/total_selling_price*100),2)
    i_sbu_total_margin = round(((total_selling_price - i_sbu_total)/total_selling_price*100),2)
    d_sbu_total_margin = round(((total_selling_price - d_sbu_total)/total_selling_price*100),2)
    data_1 = ''
    if "CFO" in frappe.get_roles(frappe.session.user) or "COO" in frappe.get_roles(frappe.session.user) or "HOD" in frappe.get_roles(frappe.session.user) or "Accounts User" in frappe.get_roles(frappe.session.user):
        if spcl == 0:
            if price_list == "Singapore Internal Cost":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN </b></center></th><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%('',sbu_total,sbu_total_margin,singapore_internal_cost_total,singapore_internal_cost_total_margin,total_selling_price)
                total_cost = singapore_internal_cost_total
            if price_list == "Singapore Sales Price":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN </b></center></th><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%('',sbu_total,sbu_total_margin,singapore_sales_price_total,singapore_sales_price_total_margin,total_selling_price)       
                total_cost = singapore_sales_price_total
            if price_list == "Singapore Freight":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN </b></center></th><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%('',sbu_total,sbu_total_margin,singapore_freight_total,singapore_freight_total_margin,total_selling_price)
                total_cost = singapore_freight_total
            data_1 = '<table border=1>'
            data_1 += '<tr><td style="padding:5px;font-weight:bold">Total Cost Price</td><td style="padding:5px;text-align:right;color:#ab5207;">%s</td><td style="padding:5px;font-weight:bold">Total Selling Price</td><td style="padding:5px;text-align:right;color:#ab5207;font-weight:bold">%s</td></tr>' %(total_cost,total_selling_price)
            data_1 += '<tr><td style="padding:5px;font-weight:bold">Line Item Addition</td><td style="padding:5px;text-align:right">%s</td><td style="padding:5px;font-weight:bold">Footer Addition</td><td style="padding:5px;text-align:right;color:#ab5207;font-weight:bold">%s</td></tr>' %('','')
            data_1 += '<tr><td style="padding:5px;font-weight:bold">Line Item Discount</td><td style="padding:5px;text-align:right">%s</td><td style="padding:5px;font-weight:bold">Footer Discount</td><td style="padding:5px;text-align:right;color:#ab5207;font-weight:bold">%s</td></tr>' %('','')
            data_1 += '<tr><td style="padding:5px;font-weight:bold">Discount <td style="padding:5px;">%s</td><td style="padding:5px;font-weight:bold;">Net Sales Amount</td><td style="padding:5px;text-align:right;color:#ab5207;font-weight:bold">%s</td></tr>' %('',total_selling_price)
            data_1 += '<tr><td style="padding:5px;font-weight:bold"></td><td style="padding:5px;"></td><td style="padding:5px;font-weight:bold">Sales Profit</td><td style="padding:5px;text-align:right;color:#ab5207;font-weight:bold">%s</td></tr>' %(round((total_selling_price - total_cost),2))
            data_1 += '<tr><td style="padding:5px;font-weight:bold"></td><td style="padding:5px;"></td><td style="padding:5px;color:green;font-weight:bold">Profit %%</td><td style="padding:5px;text-align:right;color:green;font-weight:bold">%s %%</td></tr>' %(round(((total_selling_price - total_cost)/total_selling_price*100),2))
            data_1 += '</table>'
            if price_list == "Vietnam Internal Cost":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,vietnam_internal_cost_total_margin,'',sbu_total,sbu_total_margin,round(vietnam_internal_cost_total,2),'',round(total_selling_price,2))
            if price_list == "Vietnam Sales Price":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,vietnam_sales_price_total_margin,'',sbu_total,sbu_total_margin,round(vietnam_sales_price_total,2),'',round(total_selling_price,2))       
            if price_list == "Vietnam Freight":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,vietnam_freight_total_margin,'','',sbu_total,sbu_total_margin,round(vietnam_freight_total,2),round(total_selling_price,2))
        
            if price_list == "Philippines Internal Cost":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,philippines_internal_cost_total_margin,'',sbu_total,sbu_total_margin,round(philippines_internal_cost_total,2),'',round(total_selling_price,2))
            if price_list == "Philippines Sales Price":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,philippines_sales_price_total_margin,'',sbu_total,sbu_total_margin,round(philippines_sales_price_total,2),'',round(total_selling_price,2))       
            if price_list == "Philippines Freight":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,philippines_freight_total_margin,'',sbu_total,sbu_total_margin,round(philippines_freight_total,2),'',round(total_selling_price,2))
        
            if price_list == "Malaysia Internal Cost":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,malaysia_internal_cost_total_margin,'',sbu_total,sbu_total_margin,round(malaysia_internal_cost_total,2),'',round(total_selling_price,2))
            if price_list == "Malaysia Sales Price":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,malaysia_sales_price_total_margin,'',sbu_total,sbu_total_margin,round(malaysia_sales_price_total,2),'',round(total_selling_price,2))       
            if price_list == "Malaysia Freight":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,malaysia_freight_total_margin,'',sbu_total,sbu_total_margin,round(malaysia_freight_total,2),'',round(total_selling_price,2))
        
            if price_list == "Indonesia Internal Cost":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,indonesia_internal_cost_total_margin,'',sbu_total,sbu_total_margin,round(indonesia_internal_cost_total,2),'',round(total_selling_price,2))
            if price_list == "Indonesia Sales Price":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,indonesia_sales_price_total_margin,'',sbu_total,sbu_total_margin,round(indonesia_sales_price_total,2),'',round(total_selling_price,2))       
            if price_list == "Indonesia Freight":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,indonesia_freight_total_margin,'',sbu_total,sbu_total_margin,round(indonesia_freight_total,2),'',round(total_selling_price,2))
        
            if price_list == "Cambodia Internal Cost":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list, cambodia_internal_cost_total_margin,'',sbu_total,sbu_total_margin,round(cambodia_internal_cost_total,2),'',round(total_selling_price,2))
            if price_list == "Cambodia Sales Price":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,cambodia_sales_price_total_margin,'',sbu_total,sbu_total_margin,round(cambodia_sales_price_total,2),'',round(total_selling_price,2))       
            if price_list == "Cambodia Freight":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,cambodia_freight_total_margin,'',sbu_total,sbu_total_margin,round(cambodia_freight_total,2),'',round(total_selling_price,2))

            if price_list == "Srilanka Internal Cost":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,srilanka_internal_cost_total_margin,'',sbu_total,sbu_total_margin,round(srilanka_internal_cost_total,2),'',round(total_selling_price,2))
            if price_list == "Srilanka Sales Price":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,srilanka_sales_price_total_margin,'',sbu_total,sbu_total_margin,round(srilanka_sales_price_total,2),'',round(total_selling_price,2))       
            if price_list == "Srilanka Freight":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,srilanka_freight_total_margin,'',sbu_total,sbu_total_margin,round(srilanka_freight_total,2),'',round(total_selling_price,2))

            if price_list == "Bangladesh Internal Cost":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN </b></center></th><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%('',sbu_total,sbu_total_margin,round(bangladesh_internal_cost_total,2),bangladesh_internal_cost_total_margin,round(total_selling_price,2))
            if price_list == "Bangladesh Sales Price":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN </b></center></th><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%('',sbu_total,sbu_total_margin,round(bangladesh_sales_price_total,2),bangladesh_sales_price_total_margin,round(total_selling_price,2))       
            if price_list == "Bangladesh Freight":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN </b></center></th><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%('',sbu_total,sbu_total_margin,round(bangladesh_freight_total,2),bangladesh_freight_total_margin,round(total_selling_price,2))

            if price_list == "UK Freight":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,uk_freight_total_margin,'',sbu_total,sbu_total_margin,round(uk_freight_total,2),'',round(total_selling_price,2))
            if price_list == "UK Destination Charges":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,uk_destination_charges_total_margin,sbu_total_margin,sbu_total,'',round(uk_destination_charges_total,2),'',round(total_selling_price,2))       
            if price_list == "UK Installer":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,uk_installer_total_margin,'',sbu_total,sbu_total_margin,round(uk_installer_total,2),'',round(total_selling_price,2))
            if price_list == "UK Distributor":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,uk_distributor_total_margin,'',sbu_total,sbu_total_margin,round(uk_distributor_total,2),'',round(total_selling_price,2))
                
            if price_list == "India Landing":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,india_landing_total_margin,'',i_sbu_total,i_sbu_total_margin,round(india_landing_total,2),'',round(total_selling_price,2))
            if price_list == "India LTP":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,india_ltp_total_margin,'',i_sbu_total,i_sbu_total_margin,round(india_ltp_total,2),'',round(total_selling_price,2))       
            if price_list == "India SPC":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,india_spc_total_margin,'',i_sbu_total,i_sbu_total_margin,round(india_spc_total,2),'',round(total_selling_price,2))
            if price_list == "India DTP":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,india_dtp_total_margin,'',i_sbu_total,i_sbu_total_margin,round(india_dtp_total,2),'',round(total_selling_price,2))
            if price_list == "India STP":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,india_stp_total_margin,'',i_sbu_total,i_sbu_total_margin,round(india_stp_total,2),'',round(total_selling_price,2))       
            if price_list == "India MOP":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,india_mop_total_margin,'',i_sbu_total,i_sbu_total_margin,round(india_mop_total,2),'',round(total_selling_price,2))
            if price_list == "India MRP":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,india_mrp_total_margin,'',i_sbu_total,i_sbu_total_margin,round(india_mrp_total,2),'',round(total_selling_price,2))

            if price_list == "Landing - NCMEF":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,'','','','','','',round(total_selling_price,2))
            if price_list == "Internal - NCMEF":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,'','','','','','',round(total_selling_price,2))       
            if price_list == "Incentive - NCMEF":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,'','','','','','',round(total_selling_price,2))
            if price_list == "Dist. Price - NCMEF":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,'','','','','','',round(total_selling_price,2))
            if price_list == "Saudi Dist. - NCMEF":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,'','','','','','',round(total_selling_price,2))       
            if price_list == "Project Group - NCMEF":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,'','','','','','',round(total_selling_price,2))
            if price_list == "Retail - NCMEF":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,'','','','','','',round(total_selling_price,2))
            if price_list == "Electra Qatar - NCMEF":
                data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,'','','','','','',round(total_selling_price,2))
        else:
            data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) COST : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,'','','','','')
   
    data+='</table>'
    return data_1,data


@frappe.whitelist()
def margin_sm(item_details,company,currency,exchange_rate,user,price_list,territory):
    item_details = json.loads(item_details)
    data_1 = ''
    if "CFO" in frappe.get_roles(frappe.session.user) or "COO" in frappe.get_roles(frappe.session.user) or "HOD" in frappe.get_roles(frappe.session.user) or "Accounts User" in frappe.get_roles(frappe.session.user):
        data_1+= '<table class="table"><tr><th style="padding:1px;border: 1px solid black;font-size:14px;background-color:#e20026;color:white;" colspan=16><center><b>MARGIN BY VALUE & MARGIN BY PERCENTAGE</b></center></th></tr>'
        spl = 0
        for i in item_details:
            if i["special_cost"] > 0:
                spl = spl + 1
        if spl == 0:
            if price_list == "Singapore Internal Cost":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Singapore Freight":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Singapore Sales Price":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            
            if price_list == "Bangladesh Internal Cost":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Bangladesh Freight":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Bangladesh Sales Price":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'

            if price_list == "Philippines Internal Cost":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Philippines Freight":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Philippines Sales Price":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'

            if price_list == "Malaysia Internal Cost":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Malaysia Freight":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Malaysia Sales Price":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            
            if price_list == "Indonesia Internal Cost":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SELLING PRICE</b></td></tr>'
            if price_list == "Indonesia Freight":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SELLING PRICE</b></td></tr>'
            if price_list == "Indonesia Sales Price":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SELLING PRICE</b></td></tr>'

            if price_list == "Vietnam Internal Cost":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Vietnam Freight":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Vietnam Sales Price":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'

            if price_list == "Cambodia Internal Cost":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Cambodia Freight":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Cambodia Sales Price":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'

            if price_list == "Srilanka Internal Cost":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Srilanka Freight":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Srilanka Sales Price":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
           
            if price_list == "UK Freight":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "UK Destination Charges":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>DESTINATION CHARGES</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>DESTINATION CHARGES %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "UK Installer":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INSTALLER</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INSTALLER %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "UK Distributor":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>DISTRIBUTOR</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>DISTRIBUTOR %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            
            if price_list == "Dubai Landing":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>DUBAI LANDING</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>DUBAI LANDING %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Dubai Internal":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>DUBAI INTERNAL</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>DUBAI INTERNAL %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Dubai Incentive":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>DUBAI INCENTIVE</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>DUBAI INCENTIVE %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Dubai Distributor":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>DUBAI DISTRIBUTOR</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>DUBAI DISTRIBUTOR %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Saudi":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SAUDI</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SAUDI %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SELLING PRICE</b></td></tr>'
            if price_list == "Dubai Project":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>DUBAI PROJECT</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>DUBAI PROJECT %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Dubai Retail":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>DUBAI RETAIL</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>DUBAI RETAIL %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "Dubai Electra":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>DUBAI ELECTRA</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>DUBAI ELECTRA %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'

            
            
            
            
            if price_list == "India Landing":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INDIA LANDING</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INDIA LANDING %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "India SPC":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INDIA SPC</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INDIA SPC %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "India STP":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INDIA STP</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INDIA STP %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "India LTP":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INDIA LTP</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INDIA LTP %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "India DTP":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INDIA DTP</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INDIA DTP %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "India MOP":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INDIA MOP</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INDIA MOP %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
            if price_list == "India MRP":
                data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=3 style="border: 1px solid black;font-size:11px;width:40%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INDIA MRP</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INDIA MRP %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SP</b></td></tr>'
        else:
            data_1+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=2 style="border: 1px solid black;font-size:11px;width:30%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>STOCK</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>PO</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SPECIAL PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SELLING PRICE</b></td></tr>'

    total_internal_cost = 0
    total_special_price = 0
    total_selling_price = 0
    cost_total = 0
    total_valuation_rate = 0
    spcl = 0
    total_warehouse = 0
    total_in_transit = 0
    total_stock = 0
    sum_of_total_stock = 0
    price_table = []
    dubai_landing_margin = 0
    dubai_incentive_margin = 0
    dubai_internal_margin = 0
    dubai_distributor_margin = 0
    saudi_margin = 0
    dubai_project_margin = 0
    dubai_retail_margin = 0
    dubai_electra_margin = 0
    d_sbu_margin = 0
    india_landing_margin = 0
    india_spc_margin = 0
    india_ltp_margin = 0
    india_dtp_margin = 0
    india_stp_margin = 0 
    india_mop_margin = 0
    india_mrp_margin = 0
    total_selling_price = 0
    singapore_internal_cost_total = 0  
    singapore_internal_cost_total_margin = 0  
    singapore_sales_price_total = 0  
    singapore_sales_price_total_margin = 0  
    singapore_freight_total = 0  
    singapore_freight_total_margin = 0
    
    vietnam_internal_cost_total = 0  
    vietnam_internal_cost_total_margin = 0  
    vietnam_sales_price_total = 0  
    vietnam_sales_price_total_margin = 0  
    vietnam_freight_total = 0  
    vietnam_freight_total_margin = 0  

    philippines_internal_cost_total = 0  
    philippines_internal_cost_total_margin = 0  
    philippines_sales_price_total = 0  
    philippines_sales_price_total_margin = 0  
    philippines_freight_total = 0  
    philippines_freight_total_margin = 0  

    malaysia_internal_cost_total = 0  
    malaysia_internal_cost_total_margin = 0  
    malaysia_sales_price_total = 0  
    malaysia_sales_price_total_margin = 0  
    malaysia_freight_total = 0  
    malaysia_freight_total_margin = 0  

    indonesia_internal_cost_total = 0
    indonesia_internal_cost_total_margin = 0 
    indonesia_sales_price_total = 0
    indonesia_sales_price_total_margin = 0
    indonesia_freight_total = 0
    indonesia_freight_total_margin = 0
    
    cambodia_internal_cost_total = 0
    cambodia_internal_cost_total_margin = 0 
    cambodia_sales_price_total = 0
    cambodia_sales_price_total_margin = 0
    cambodia_freight_total = 0
    cambodia_freight_total_margin = 0

    srilanka_internal_cost_total = 0
    srilanka_internal_cost_total_margin = 0 
    srilanka_sales_price_total = 0
    srilanka_sales_price_total_margin = 0
    srilanka_freight_total = 0
    srilanka_freight_total_margin = 0

    bangladesh_internal_cost_total = 0
    bangladesh_internal_cost_total_margin = 0 
    bangladesh_sales_price_total = 0
    bangladesh_sales_price_total_margin = 0
    bangladesh_freight_total = 0
    bangladesh_freight_total_margin = 0

    uk_freight_margin= 0
    uk_destination_charges_margin = 0
    uk_installer_margin = 0
    uk_distributor_margin = 0

    uk_freight_total= 0
    uk_freight_total_margin= 0
    uk_destination_charges_total = 0
    uk_destination_charges_total_margin= 0
    uk_installer_total = 0
    uk_installer_total_margin = 0
    uk_distributor_total = 0
    uk_distributor_total_margin = 0

    india_landing_total = 0
    india_landing_total_margin = 0
    india_spc_total = 0
    india_spc_total_margin = 0
    india_ltp_total = 0
    india_ltp_total_margin = 0
    india_dtp_total = 0
    india_dtp_total_margin = 0
    india_stp_total = 0 
    india_stp_total_margin = 0 
    india_mop_total = 0
    india_mop_total_margin = 0
    india_mrp_total = 0
    india_mrp_total_margin = 0


     
  
    for i in item_details:
        total_selling_price = total_selling_price + i["amount"]
        country = frappe.get_value("Company",{"name":company},["country"])
        warehouse_stock = frappe.db.sql("""
            select (sum(`tabBin`.actual_qty) - sum(b.reserved_stock)) as qty from `tabBin` b 
            join `tabWarehouse` wh on wh.name = b.warehouse
            join `tabCompany` c on c.name = wh.company
            where c.country = '%s' and b.item_code = '%s' and wh.company = '%s'
            """ % (country,i["item_code"],company),as_dict=True)[0]
        if not warehouse_stock["qty"]:
            warehouse_stock["qty"] = 0
        total_warehouse = total_warehouse + warehouse_stock["qty"]

        purchase_order = frappe.db.sql("""select sum(`tabPurchase Order Item`.qty) as qty from `tabPurchase Order`
                left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
                where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 and `tabPurchase Order`.company = '%s'  """%(i["item_code"],company),as_dict=True)[0] or 0 
        if not purchase_order["qty"]:
            purchase_order["qty"] = 0
        purchase_receipt = frappe.db.sql("""select sum(`tabPurchase Receipt Item`.qty) as qty from `tabPurchase Receipt`
                left join `tabPurchase Receipt Item` on `tabPurchase Receipt`.name = `tabPurchase Receipt Item`.parent
                where `tabPurchase Receipt Item`.item_code = '%s' and `tabPurchase Receipt`.docstatus = 1 and  `tabPurchase Receipt`.company = '%s' """%(i["item_code"],company),as_dict=True)[0] or 0 
        if not purchase_receipt["qty"]:
            purchase_receipt["qty"] = 0
        in_transit = purchase_order["qty"] - purchase_receipt["qty"]
        total_in_transit = in_transit + total_in_transit 
        total_stock =  warehouse_stock["qty"] + in_transit
        sum_of_total_stock = total_stock + sum_of_total_stock 
        if i["special_cost"] > 0:
            spcl = spcl + 1

        sbu = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':'STANDARD BUYING-USD'},["price_list_rate"])
        if not sbu:
            sbu = 0
        sbus = sbu * i["qty"]
        if territory == "Bangladesh" or territory == "Cambodia" or territory == "Indonesia" or territory == "Singapore" or territory == "Bangladesh" or territory == "Malaysia" or territory == "Sri Lanka" or territory == "Srilanka" or territory == "Vietnam" or territory == "Philippines":
            sbu_margin = round(((i["amount"]-sbu*i["qty"])/i["amount"]*100),2)
        if territory == "Dubai":
            ep = get_exchange_rate('USD',"AED")
            d_sbu = round(sbu*ep,1)
            d_sbu_margin = round(((i["amount"]-d_sbu*i["qty"])/i["amount"]*100),2)
        if territory == "India":
            ep = get_exchange_rate('USD',"INR")
            i_sbu = round(sbu*ep,1)
            i_sbu_margin = round(((i["amount"]- i_sbu*i["qty"])/i["amount"]*100),2)

        
        if territory == "United Kingdom":
            uk_table = frappe.get_single("Margin Price Tool").uk
            item_group = frappe.get_value("Item",{"name":i["item_code"]},["item_sub_group"])
            for s in uk_table:
                if item_group == s.item_group:
                    uk_freight = round((sbu * s.freight),2)*i["qty"]
                    uk_destination_charges = round((uk_freight * s.destination_charges),2)*i["qty"]
                    uk_installer = round((uk_destination_charges/(100 - s.installer)*100),2)
                    uk_distributor = round((uk_installer/(100 - s.distributor)*100),2)
                    uk_freight_margin = (((i["amount"] - uk_freight)/i["amount"])*100)
                    uk_destination_charges_margin = (((i["amount"] - uk_destination_charges)/i["amount"])*100)
                    uk_installer_margin = (((i["amount"] -  uk_installer)/i["amount"])*100)
                    uk_distributor_margin = (((i["amount"] - uk_distributor)/i["amount"])*100)
                    uk_freight_total =  uk_freight + uk_freight_total 
                    uk_freight_total_margin= round(((total_selling_price - uk_freight_total)/total_selling_price*100),2)
                    uk_destination_charges_total = uk_destination_charges + uk_destination_charges_total
                    uk_destination_charges_total_margin= round(((total_selling_price - uk_destination_charges_total)/total_selling_price*100),2)
                    uk_installer_total = uk_installer + uk_installer_total
                    uk_installer_total_margin = round(((total_selling_price - uk_installer_total)/total_selling_price*100),2)
                    uk_distributor_total = uk_distributor + uk_distributor_total
                    uk_distributor_total_margin = round(((total_selling_price - uk_distributor_total)/total_selling_price*100),2)


        if territory == "Singapore":
            singapore_table = frappe.get_single("Margin Price Tool").singapore
            item_group = frappe.get_value("Item",{"name":i["item_code"]},["item_sub_group"])
            for s in singapore_table:
                if item_group == s.item_group:
                    # singapore_sales_price = sbu * s.sales_price
                    singapore_internal_cost = round((sbu * s.internal_cost),2)*i["qty"]
                    singapore_sales_price = ((singapore_internal_cost/(100 - s.sales_price))*100)*i["qty"]
                    singapore_freight = round((singapore_sales_price * s.freight),2)*i["qty"]
                    singapore_internal_cost_margin = (((i["amount"] - singapore_internal_cost)/i["amount"])*100)
                    singapore_sales_price_margin = (((i["amount"] - singapore_sales_price)/i["amount"])*100)
                    singapore_freight_margin = (((i["amount"] - singapore_freight)/i["amount"])*100)
                    singapore_internal_cost_total = singapore_internal_cost +  singapore_internal_cost_total
                    singapore_internal_cost_total_margin = round(((total_selling_price - singapore_internal_cost_total)/total_selling_price*100),2)
                    singapore_sales_price_total = singapore_sales_price +  singapore_sales_price_total 
                    singapore_sales_price_total_margin = round(((total_selling_price - singapore_sales_price_total)/total_selling_price*100),2)
                    singapore_freight_total = singapore_freight +  singapore_freight_total 
                    singapore_freight_total_margin = round(((total_selling_price - singapore_freight_total)/total_selling_price*100),2)
                    
                
        
        if territory == "Vietnam":
            vietnam_table = frappe.get_single("Margin Price Tool").vietnam
            item_group = frappe.get_value("Item",{"name":i["item_code"]},["item_sub_group"])
            for s in vietnam_table:
                if item_group == s.item_group:
                    # singapore_sales_price = sbu * s.sales_price
                    vietnam_internal_cost = round((sbu * s.internal_cost),2)*i["qty"]
                    vietnam_sales_price = ((vietnam_internal_cost/(100 - s.sales_price))*100)*i["qty"]
                    vietnam_freight = round((vietnam_sales_price * s.freight),2)*i["qty"]
                    vietnam_internal_cost_margin = (((i["amount"] - vietnam_internal_cost)/i["amount"])*100)
                    vietnam_sales_price_margin = (((i["amount"] - vietnam_sales_price)/i["amount"])*100)
                    vietnam_freight_margin = (((i["amount"] - vietnam_freight)/i["amount"])*100)
                    vietnam_internal_cost_total = vietnam_internal_cost +  vietnam_internal_cost_total
                    vietnam_internal_cost_total_margin = round(((total_selling_price - vietnam_internal_cost_total)/total_selling_price*100),2)
                    vietnam_sales_price_total = vietnam_sales_price +  vietnam_sales_price_total 
                    vietnam_sales_price_total_margin = round(((total_selling_price - vietnam_sales_price_total)/total_selling_price*100),2)
                    vietnam_freight_total = vietnam_freight +  vietnam_freight_total 
                    vietnam_freight_total_margin = round(((total_selling_price - vietnam_freight_total)/total_selling_price*100),2)
                    
                    

        if territory == "Philippines":
            philippines_table = frappe.get_single("Margin Price Tool").philippines
            item_group = frappe.get_value("Item",{"name":i["item_code"]},["item_sub_group"])
            for s in philippines_table:
                if item_group == s.item_group:
                    # singapore_sales_price = sbu * s.sales_price
                    philippines_internal_cost = round((sbu * s.internal_cost),2)*i["qty"]
                    philippines_sales_price = ((philippines_internal_cost/(100 - s.sales_price))*100)*i["qty"]
                    philippines_freight = round((philippines_sales_price * s.freight),2)*i["qty"]
                    philippines_internal_cost_margin = (((i["amount"] - philippines_internal_cost)/i["amount"])*100)
                    philippines_sales_price_margin = (((i["amount"] - philippines_sales_price)/i["amount"])*100)
                    philippines_freight_margin = (((i["amount"] - philippines_freight)/i["amount"])*100)
                    philippines_internal_cost_total = philippines_internal_cost +  philippines_internal_cost_total
                    philippines_internal_cost_total_margin = round(((total_selling_price - philippines_internal_cost_total)/total_selling_price*100),2)
                    philippines_sales_price_total = philippines_sales_price +  philippines_sales_price_total 
                    philippines_sales_price_total_margin = round(((total_selling_price - philippines_sales_price_total)/total_selling_price*100),2)
                    philippines_freight_total = philippines_freight + philippines_freight_total 
                    philippines_freight_total_margin = round(((total_selling_price - philippines_freight_total)/total_selling_price*100),2)
                    

        if territory == "Malaysia":
            malaysia_table = frappe.get_single("Margin Price Tool").malaysia
            item_group = frappe.get_value("Item",{"name":i["item_code"]},["item_sub_group"])
            for s in malaysia_table:
                if item_group == s.item_group:
                    # singapore_sales_price = sbu * s.sales_price
                    malaysia_internal_cost = round((sbu * s.internal_cost),2) * i["qty"]
                    malaysia_sales_price = ((malaysia_internal_cost/(100 - s.sales_price))*100)* i["qty"]
                    malaysia_freight = round((malaysia_sales_price * s.freight),2)* i["qty"]
                    malaysia_internal_cost_margin = (((i["amount"] - malaysia_internal_cost)/i["amount"])*100)
                    malaysia__sales_price_margin = (((i["amount"] -   malaysia_sales_price)/i["amount"])*100)
                    malaysia_freight_margin = (((i["amount"] -  malaysia_freight)/i["amount"])*100)
                    malaysia_internal_cost_total = malaysia_internal_cost +  malaysia_internal_cost_total
                    malaysia_internal_cost_total_margin = round(((total_selling_price - malaysia_internal_cost_total)/total_selling_price*100),2)
                    malaysia_sales_price_total = malaysia_sales_price + malaysia_sales_price_total 
                    malaysia_sales_price_total_margin = round(((total_selling_price - malaysia_sales_price_total)/total_selling_price*100),2)
                    malaysia_freight_total = malaysia_freight + malaysia_freight_total 
                    malaysia_freight_total_margin = round(((total_selling_price - malaysia_freight_total)/total_selling_price*100),2)


        if territory == "Indonesia":
            indonesia_table = frappe.get_single("Margin Price Tool").indonesia
            item_group = frappe.get_value("Item",{"name":i["item_code"]},["item_sub_group"])
            for s in indonesia_table:
                if item_group == s.item_group:
                    # singapore_sales_price = sbu * s.sales_price
                    indonesia_internal_cost = round((sbu * s.internal_cost),2)* i["qty"]
                    indonesia_sales_price = ((indonesia_internal_cost/(100 - s.sales_price))*100)* i["qty"]
                    indonesia_freight = round((indonesia_sales_price * s.freight),2)* i["qty"]
                    indonesia_internal_cost_margin = (((i["amount"] - indonesia_internal_cost)/i["amount"])*100)
                    indonesia_sales_price_margin = (((i["amount"] -   indonesia_sales_price)/i["amount"])*100)
                    indonesia_freight_margin = (((i["amount"] - indonesia_freight)/i["amount"])*100)
                    indonesia_internal_cost_total = indonesia_internal_cost +  indonesia_internal_cost_total
                    indonesia_internal_cost_total_margin = round(((total_selling_price - indonesia_internal_cost_total)/total_selling_price*100),2)
                    indonesia_sales_price_total = indonesia_sales_price + indonesia_sales_price_total 
                    indonesia_sales_price_total_margin = round(((total_selling_price - indonesia_sales_price_total)/total_selling_price*100),2)
                    indonesia_freight_total = indonesia_freight + indonesia_freight_total 
                    indonesia_freight_total_margin = round(((total_selling_price - indonesia_freight_total)/total_selling_price*100),2)

                

        if territory == "Cambodia":
            cambodia_table = frappe.get_single("Margin Price Tool").cambodia
            item_group = frappe.get_value("Item",{"name":i["item_code"]},["item_sub_group"])
            for s in cambodia_table:
                if item_group == s.item_group:
                    # singapore_sales_price = sbu * s.sales_price
                    cambodia_internal_cost = round((sbu * s.internal_cost),2)* i["qty"]
                    cambodia_sales_price = ((cambodia_internal_cost/(100 - s.sales_price))*100)* i["qty"]
                    cambodia_freight = round((cambodia_sales_price * s.freight),2)* i["qty"]
                    cambodia_internal_cost_margin = (((i["amount"] - cambodia_internal_cost)/i["amount"])*100)
                    cambodia_sales_price_margin = (((i["amount"] -   cambodia_sales_price)/i["amount"])*100)
                    cambodia_freight_margin = (((i["amount"] - cambodia_freight)/i["amount"])*100)
                    cambodia_internal_cost_total = cambodia_internal_cost + cambodia_internal_cost_total
                    cambodia_internal_cost_total_margin = round(((total_selling_price - cambodia_internal_cost_total)/total_selling_price*100),2)
                    cambodia_sales_price_total = cambodia_sales_price + cambodia_sales_price_total 
                    cambodia_sales_price_total_margin = round(((total_selling_price - cambodia_sales_price_total)/total_selling_price*100),2)
                    cambodia_freight_total = cambodia_freight + cambodia_freight_total 
                    cambodia_freight_total_margin = round(((total_selling_price - cambodia_freight_total)/total_selling_price*100),2)


        if territory == "Srilanka" or territory == "Sri Lanka":
            srilanka_table = frappe.get_single("Margin Price Tool").srilanka
            item_group = frappe.get_value("Item",{"name":i["item_code"]},["item_sub_group"])
            for s in srilanka_table:
                if item_group == s.item_group:
                    # singapore_sales_price = sbu * s.sales_price
                    srilanka_internal_cost = round((sbu * s.internal_cost),2)*i["qty"]
                    srilanka_sales_price = ((srilanka_internal_cost/(100 - s.sales_price))*100)*i["qty"]
                    srilanka_freight = round((srilanka_sales_price * s.freight),2)*i["qty"]
                    srilanka_internal_cost_margin = (((i["amount"] - srilanka_internal_cost)/i["amount"])*100)
                    srilanka_sales_price_margin = (((i["amount"] - srilanka_sales_price)/i["amount"])*100)
                    srilanka_freight_margin = (((i["amount"] - srilanka_freight)/i["amount"])*100)
                    srilanka_internal_cost_total = srilanka_internal_cost + srilanka_internal_cost_total
                    srilanka_internal_cost_total_margin = round(((total_selling_price - srilanka_internal_cost_total)/total_selling_price*100),2)
                    srilanka_sales_price_total = srilanka_sales_price + srilanka_sales_price_total 
                    srilanka_sales_price_total_margin = round(((total_selling_price - srilanka_sales_price_total)/total_selling_price*100),2)
                    srilanka_freight_total = srilanka_freight + srilanka_freight_total 
                    srilanka_freight_total_margin = round(((total_selling_price - srilanka_freight_total)/total_selling_price*100),2)
                

        if territory == "Bangladesh":
            bangladesh_table = frappe.get_single("Margin Price Tool").bangladesh
            item_group = frappe.get_value("Item",{"name":i["item_code"]},["item_sub_group"])
            for s in bangladesh_table:
                if item_group == s.item_group:
                    # singapore_sales_price = sbu * s.sales_price
                    bangladesh_internal_cost = round((sbu * s.internal_cost),2)
                    bangladesh_sales_price = (bangladesh_internal_cost/(100 - s.sales_price))*100
                    bangladesh_freight = round((bangladesh_sales_price * s.freight),2)
                    bangladesh_internal_cost_margin = (((i["amount"] - bangladesh_internal_cost)/i["amount"])*100)
                    bangladesh_sales_price_margin = (((i["amount"] - bangladesh_sales_price)/i["amount"])*100)
                    bangladesh_freight_margin = (((i["amount"] - bangladesh_freight)/i["amount"])*100)
                    bangladesh_internal_cost_total = bangladesh_internal_cost + bangladesh_internal_cost_total
                    bangladesh_internal_cost_total_margin = round(((total_selling_price - bangladesh_internal_cost_total)/total_selling_price*100),2)
                    bangladesh_sales_price_total = bangladesh_sales_price + bangladesh_sales_price_total 
                    bangladesh_sales_price_total_margin = round(((total_selling_price - bangladesh_sales_price_total)/total_selling_price*100),2)
                    bangladesh_freight_total = bangladesh_freight + bangladesh_freight_total 
                    bangladesh_freight_total_margin = round(((total_selling_price - bangladesh_freight_total)/total_selling_price*100),2)
            



        if territory == "Dubai" or territory == "United Arab Emirates":
            dubai_table = frappe.get_single("Margin Price Tool").dubai
            item_group = frappe.get_value("Item",{"name":i["item_code"]},["item_sub_group"])
            for d in dubai_table:
                if item_group == d.item_group:
                    dubai_landing = round(d_sbu * d.landing)*i["qty"]
                    dubai_incentive  = round((dubai_landing* d.incentive),2)*i["qty"]
                    dubai_internal = round((dubai_landing * d.internal),2)
                    dubai_distributor = round((dubai_landing * d.distributor),2)*i["qty"]
                    saudi = round((dubai_landing * d.saudi),2)*i["qty"]
                    dubai_project = round((dubai_landing * d.project),2)
                    dubai_retail = round((dubai_landing * d.retail),2)
                    dubai_electra = round((sbu * d.electra),2)
                    dubai_landing_margin = (((i["amount"] - dubai_landing)/i["amount"])*100)
                    dubai_incentive_margin = round((((i["amount"] - dubai_incentive)/i["amount"])*100),2)
                    dubai_internal_margin = round((((i["amount"] - dubai_internal)/i["amount"])*100),2)
                    dubai_distributor_margin =  round((((i["amount"] - dubai_distributor)/i["amount"])*100),2)
                    saudi_margin =  round((((i["amount"] - saudi)/i["amount"])*100),2)
                    dubai_project_margin =  round((((i["amount"] - dubai_project)/i["amount"])*100),2)
                    dubai_retail_margin =  round((((i["amount"] - dubai_retail)/i["amount"])*100),2)
                    dubai_electra_margin =  round((((i["amount"] - dubai_electra)/i["amount"])*100),2)

        if territory == "India":
            india_table = frappe.get_single("Margin Price Tool").india
            item_group = frappe.get_value("Item",{"name":i["item_code"]},["item_sub_group"])
            for d in india_table: 
                if item_group == d.item_group:
                    india_landing = round((i_sbu * d.landing),2)*i["qty"]
                    india_spc  = round((india_landing/ d.spc),2)*i["qty"]
                    india_ltp = round((india_spc / d.ltp),2)*i["qty"]
                    india_dtp = round((india_ltp / d.dtp),2)*i["qty"]
                    india_stp = round((india_dtp / d.stp),2)*i["qty"]*i["qty"]
                    india_mop = round((india_stp / d.mop),2)*i["qty"]
                    india_mrp = round((india_mop / d.mrp),2)*i["qty"]
                    india_landing_margin = (((i["amount"] - india_landing)/i["amount"])*100)
                    india_spc_margin = (((i["amount"] - india_landing)/i["amount"])*100)
                    india_ltp_margin = (((i["amount"] - india_ltp)/i["amount"])*100)
                    india_dtp_margin = (((i["amount"] - india_dtp)/i["amount"])*100)
                    india_stp_margin = (((i["amount"] - india_stp)/i["amount"])*100) 
                    india_mop_margin = (((i["amount"] - india_mop)/i["amount"])*100)
                    india_mrp_margin = (((i["amount"] - india_mrp)/i["amount"])*100)  

                    india_landing_total = india_landing_total + india_landing
                    india_landing_total_margin = round(((total_selling_price -  india_landing_total)/total_selling_price*100),2)
                    india_spc_total =  india_spc_total + india_spc
                    india_spc_total_margin = round(((total_selling_price -  india_spc_total)/total_selling_price*100),2)
                    india_ltp_total =  india_ltp_total + india_ltp
                    india_ltp_total_margin = round(((total_selling_price -  india_ltp_total)/total_selling_price*100),2)
                    india_dtp_total =  india_dtp_total + india_dtp
                    india_dtp_total_margin = round(((total_selling_price -   india_dtp_total )/total_selling_price*100),2)
                    india_stp_total = india_stp_total + india_stp
                    india_stp_total_margin = round(((total_selling_price -  india_stp_total)/total_selling_price*100),2)
                    india_mop_total = india_mop_total + india_mop
                    india_mop_total_margin = round(((total_selling_price - india_mop_total)/total_selling_price*100),2)
                    india_mrp_total = india_mrp_total + india_mrp
                    india_mrp_total_margin = round(((total_selling_price - india_mrp_total)/total_selling_price*100),2)
        if "CFO" in frappe.get_roles(frappe.session.user) or "COO" in frappe.get_roles(frappe.session.user) or "HOD" in frappe.get_roles(frappe.session.user) or "Accounts User" in frappe.get_roles(frappe.session.user):
            if i["special_cost"] > 0:
                data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=2 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,i["qty"],total_stock,'','','','','','')
            else:
                if price_list == "Singapore Internal Cost":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(singapore_internal_cost,2),round(singapore_internal_cost_margin,2),round(i["amount"],2))
                if price_list == "Singapore Sales Price":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(singapore_sales_price,2),round(singapore_sales_price_margin,2),round(i["amount"],2))
                if price_list == "Singapore Freight":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(singapore_freight,2),round(singapore_freight_margin,2),round(i["amount"],2))
                
                if price_list == "Vietnam Internal Cost":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(vietnam_internal_cost,2),round(vietnam_internal_cost_margin,2),round(i["amount"],2))
                if price_list == "Vietnam Sales Price":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(vietnam_sales_price,2),round(vietnam_sales_price_margin,2),round(i["amount"],2))
                if price_list == "Vietnam Freight":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(vietnam_freight,2),round(vietnam_freight_margin,2),round(i["amount"],2))
                
                if price_list == "Bangladesh Internal Cost":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(bangladesh_internal_cost,2),round(bangladesh_internal_cost_margin,2),round(i["amount"],2))
                if price_list == "Bangladesh Sales Price":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(bangladesh_sales_price,2),round(bangladesh_sales_price_margin,2),round(i["amount"],2))
                if price_list == "Bangladesh Freight":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(bangladesh_freight,2),round(bangladesh_freight_margin,2),round(i["amount"],2))

                if price_list == "Cambodia Internal Cost":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(cambodia_internal_cost,2),round(cambodia_internal_cost_margin,2),round(i["amount"],2))
                if price_list == "Cambodia Sales Price":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(cambodia_sales_price,2),round(cambodia_sales_price_margin,2),round(i["amount"],2))
                if price_list == "Cambodia Freight":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(cambodia_freight,2),round(cambodia_freight_margin,2),round(i["amount"],2))

                if price_list == "Philippines Internal Cost":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(philippines_internal_cost,2),round(philippines_internal_cost_margin,2),round(i["amount"],2))
                if price_list == "Philippines Sales Price":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(philippines_sales_price,2),round(philippines_sales_price_margin,2),round(i["amount"],2))
                if price_list == "Philippines Freight":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(philippines_freight,2),round(philippines_freight_margin,2),round(i["amount"],2))
                
                if price_list == "Malaysia Internal Cost":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(malaysia_internal_cost,2),round(malaysia_internal_cost_margin,2),round(i["amount"],2))
                if price_list ==  "Malaysia Sales Price":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(malaysia_sales_price,2),round(malaysia__sales_price_margin,2),round(i["amount"],2))
                if price_list == "Malaysia Freight":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(malaysia_freight,2),round(malaysia_freight_margin,2),round(i["amount"],2))
                
                if price_list == "Indonesia Internal Cost":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(indonesia_internal_cost,2),round(indonesia_internal_cost_margin,2),round(i["amount"],2))
                if price_list ==  "Indonesia Sales Price":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(indonesia_sales_price,2),round(indonesia_sales_price_margin,2),round(i["amount"],2))
                if price_list == "Indonesia Freight":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(indonesia_freight,2),round(indonesia_freight_margin,2),round(i["amount"],2))
                
                if price_list == "Srilanka Internal Cost":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(srilanka_internal_cost,2),round(srilanka_internal_cost_margin,2),round(i["amount"],2))
                if price_list ==  "Srilanka Sales Price":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(srilanka_sales_price,2),round(srilanka_sales_price_margin,2),round(i["amount"],2))
                if price_list == "Srilanka Freight":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(srilanka_freight,2),round(srilanka_freight_margin,2),round(i["amount"],2))
                
                if price_list == "UK Freight":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(uk_freight,2),round(uk_freight_margin,2),round(i["amount"],2))
                if price_list ==  "UK Destination Charges":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(uk_destination_charges,2),round(uk_destination_charges_margin),round(i["amount"],2))
                if price_list == "UK Installer":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(uk_installer,2),round(uk_installer_margin),round(i["amount"],2))
                if price_list == "UK Distributor":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round(uk_distributor,2),round(uk_distributor_margin,2),round(i["amount"],2))


                if price_list == "Dubai Landing":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],dubai_landing*i["qty"],round(dubai_landing_margin,2),round(i["amount"],2))
                if price_list == "Dubai Internal":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],dubai_internal*i["qty"],dubai_internal_margin,round(i["amount"],2))
                if price_list == "Dubai Incentive":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],dubai_incentive*i["qty"],dubai_incentive_margin,round(i["amount"],2))
                if price_list == "Dubai Distributor":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],dubai_distributor*i["qty"],dubai_distributor_margin,round(i["amount"],2))
                if price_list == "Saudi":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],saudi*i["qty"],saudi_margin,round(i["amount"],2))
                if price_list == "Dubai Project":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],dubai_project*i["qty"],dubai_project_margin,round(i["amount"],2))
                if price_list == "Dubai Retail":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],dubai_retail*i["qty"],dubai_retail_margin,round(i["amount"],2))
                if price_list == "Dubai Electra":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],dubai_electra*i["qty"],dubai_electra_margin,round(i["amount"],2))
                
                if price_list == "India Landing":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],india_landing*i["qty"],round(india_landing_margin,2),round(i["amount"],2))
                if price_list == "India LTP":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],india_ltp*i["qty"],round(india_ltp_margin,2),round(i["amount"],2))
                if price_list == "India SPC":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],india_spc*i["qty"],round(india_spc_margin,2),round(i["amount"],2))
                if price_list == "India DTP":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],india_dtp*i["qty"],round(india_dtp_margin,2),round(i["amount"],2))
                if price_list == "India STP":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],india_stp*i["qty"],round(india_stp_margin,2),round(i["amount"],2))
                if price_list == "India MOP":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],india_mop*i["qty"],round(india_mop_margin,2),round(i["amount"],2))
                if price_list == "India MRP":
                    data_1+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],india_mrp*i["qty"],round(india_mrp_margin,2),round(i["amount"],2))
   
   
   
   
    if "CFO" in frappe.get_roles(frappe.session.user) or "COO" in frappe.get_roles(frappe.session.user) or "HOD" in frappe.get_roles(frappe.session.user) or "Accounts User" in frappe.get_roles(frappe.session.user):
        if spcl == 0:
            if price_list == "Singapore Internal Cost":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,singapore_internal_cost_total_margin,'',round(singapore_internal_cost_total,2),'',round(total_selling_price,2))
            if price_list == "Singapore Sales Price":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,singapore_sales_price_total_margin,'',round(singapore_sales_price_total,2),'',round(total_selling_price,2))       
            if price_list == "Singapore Freight":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,singapore_freight_total_margin,'',round(singapore_freight_total,2),'',round(total_selling_price,2))
            
            if price_list == "Vietnam Internal Cost":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,vietnam_internal_cost_total_margin,'',round(vietnam_internal_cost_total,2),'',round(total_selling_price,2))
            if price_list == "Vietnam Sales Price":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,vietnam_sales_price_total_margin,'',round(vietnam_sales_price_total,2),'',round(total_selling_price,2))       
            if price_list == "Vietnam Freight":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,vietnam_freight_total_margin,'',round(vietnam_freight_total,2),'',round(total_selling_price,2))
        
            if price_list == "Philippines Internal Cost":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,philippines_internal_cost_total_margin,'',round(philippines_internal_cost_total,2),'',round(total_selling_price,2))
            if price_list == "Philippines Sales Price":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,philippines_sales_price_total_margin,'',round(philippines_sales_price_total,2),'',round(total_selling_price,2))       
            if price_list == "Philippines Freight":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,philippines_freight_total_margin,'',round(philippines_freight_total,2),'',round(total_selling_price,2))
        
            if price_list == "Malaysia Internal Cost":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,malaysia_internal_cost_total_margin,'',round(malaysia_internal_cost_total,2),'',round(total_selling_price,2))
            if price_list == "Malaysia Sales Price":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,malaysia_sales_price_total_margin,'',round(malaysia_sales_price_total,2),'',round(total_selling_price,2))       
            if price_list == "Malaysia Freight":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,malaysia_freight_total_margin,'',round(malaysia_freight_total,2),'',round(total_selling_price,2))
        
            if price_list == "Indonesia Internal Cost":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,indonesia_internal_cost_total_margin,'',round(indonesia_internal_cost_total,2),'',round(total_selling_price,2))
            if price_list == "Indonesia Sales Price":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,indonesia_sales_price_total_margin,'',round(indonesia_sales_price_total,2),'',round(total_selling_price,2))       
            if price_list == "Indonesia Freight":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,indonesia_freight_total_margin,'',round(indonesia_freight_total,2),'',round(total_selling_price,2))
        
            if price_list == "Cambodia Internal Cost":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list, cambodia_internal_cost_total_margin,'',round(cambodia_internal_cost_total,2),'',round(total_selling_price,2))
            if price_list == "Cambodia Sales Price":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,cambodia_sales_price_total_margin,'',round(cambodia_sales_price_total,2),'',round(total_selling_price,2))       
            if price_list == "Cambodia Freight":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,cambodia_freight_total_margin,'',round(cambodia_freight_total,2),'',round(total_selling_price,2))

            if price_list == "Srilanka Internal Cost":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,srilanka_internal_cost_total_margin,'',round(srilanka_internal_cost_total,2),'',round(total_selling_price,2))
            if price_list == "Srilanka Sales Price":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,srilanka_sales_price_total_margin,'',round(srilanka_sales_price_total,2),'',round(total_selling_price,2))       
            if price_list == "Srilanka Freight":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,srilanka_freight_total_margin,'',round(srilanka_freight_total,2),'',round(total_selling_price,2))

            if price_list == "Bangladesh Internal Cost":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,bangladesh_internal_cost_total_margin,'',round(bangladesh_internal_cost_total,2),'',round(total_selling_price,2))
            if price_list == "Bangladesh Sales Price":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,bangladesh_sales_price_total_margin,'',round(bangladesh_sales_price_total,2),'',round(total_selling_price,2))       
            if price_list == "Bangladesh Freight":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,bangladesh_freight_total_margin,'',round(bangladesh_freight_total,2),'',round(total_selling_price,2))
        
            if price_list == "UK Freight":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,uk_freight_total_margin,'',round(uk_freight_total,2),'',round(total_selling_price,2))
            if price_list == "UK Destination Charges":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,uk_destination_charges_total_margin,'',round(uk_destination_charges_total,2),'',round(total_selling_price,2))       
            if price_list == "UK Installer":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,uk_installer_total_margin,'',round(uk_installer_total,2),'',round(total_selling_price,2))
            if price_list == "UK Distributor":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,uk_distributor_total_margin,'',round(uk_distributor_total,2),'',round(total_selling_price,2))

            if price_list == "India Landing":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,india_landing_total_margin,'',round(india_landing_total,2),'',round(total_selling_price,2))
            if price_list == "India LTP":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,india_ltp_total_margin,'',round(india_ltp_total,2),'',round(total_selling_price,2))       
            if price_list == "India SPC":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,india_spc_total_margin,'',round(india_spc_total,2),'',round(total_selling_price,2))
            if price_list == "India DTP":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,india_dtp_total_margin,'',round(india_dtp_total,2),'',round(total_selling_price,2))
            if price_list == "India STP":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,india_stp_total_margin,'',round(india_stp_total,2),'',round(total_selling_price,2))       
            if price_list == "India MOP":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,india_mop_total_margin,'',round(india_mop_total,2),'',round(total_selling_price,2))
            if price_list == "India MRP":
                data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,india_mrp_total_margin,'',round(india_mrp_total,2),'',round(total_selling_price,2))
        else:
            data_1 += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=6><center><b>TOTAL MARGIN BASED ON (%s) COST : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%(price_list,'','','','','')
    data_1+='</table>'

    return data_1


@frappe.whitelist()
def check_item_inspection(doc,method):
    if not doc.is_return:
        for i in doc.items:
            if not i.skip_qc:
                item = frappe.get_value("Item",{"name":i.item_code},["request_for_quality_inspection"])
                inspection = frappe.db.exists("Item Inspection",{"item_code":i.item_code,"pr_number":doc.name,'docstatus':'1'})
                if item == 1:
                    if not inspection:
                        frappe.throw("Please inspect the items")
                else:
                    frappe.validated = True

@frappe.whitelist()
def match_headings(item_details,heading,sub_heading):
    item_details = json.loads(item_details)
    heading = json.loads(heading)
    return heading
    
@frappe.whitelist()
def get_default_currency(company):
    get_dc = frappe.db.sql("""select default_currency from `tabCompany` where name ='%s' """%(company),as_dict=1)[0]
    return get_dc['default_currency']

@frappe.whitelist()
def get_batch_no(purchase_order):
    get_batch = frappe.db.sql("""select batch from `tabPurchase Order` where name ='%s' """%(purchase_order),as_dict=1)[0]
    return get_batch['batch']

@frappe.whitelist()
def get_current_date():
    today = date.today()
    return today

@frappe.whitelist()
def get_supplier_in_no(purchase_receipt):
    get_in_no = frappe.db.sql("""select supplier_invoice_number from `tabPurchase Receipt` where name='%s' """%(purchase_receipt),as_dict=1)[0]
    return get_in_no['supplier_invoice_number']

@frappe.whitelist()
def get_file_no(purchase_receipt):
    file_no = frappe.db.sql("""select file_number from `tabPurchase Receipt` where name='%s' """%(purchase_receipt),as_dict=1)[0]
    return file_no['file_number']
        
@frappe.whitelist()
def get_company_name(purchase_receipt):
    company_name = frappe.db.sql("""select company from `tabPurchase Receipt` where name='%s' """%(purchase_receipt),as_dict=1)[0]
    return company_name['company']

@frappe.whitelist()
def get_company_name_dn(dn):
    company_name = frappe.db.sql("""select company from `tabDelivery Note` where name='%s' """%(dn),as_dict=1)[0]
    return company_name['company']

    

@frappe.whitelist()
def get_territory_name(purchase_receipt):
    territory_name = frappe.db.sql("""select territory from `tabPurchase Receipt` where name='%s' """%(purchase_receipt),as_dict=1)[0]
    return territory_name['territory']

# @frappe.whitelist()
# def attendance(doc,method):
#     frappe.throw("Not allowed to cancel,because Attendance is linked with approved leave application")
@frappe.whitelist()
def sales_order_duplicate(sales_order):
    childtab = frappe.db.sql(""" select `tabSales Order Item`.item_code,`tabSales Order Item`.is_free,`tabSales Order Item`.warehouse,`tabSales Order Item`.country_name,
    `tabSales Order Item`.material_request,`tabSales Order Item`.material_request_item,
    `tabSales Order Item`.item_name,`tabSales Order Item`.description,
    `tabSales Order Item`.gst_hsn_code,`tabSales Order Item`.is_nil_exempt,
    `tabSales Order Item`.item_group,`tabSales Order Item`.is_non_gst,
    `tabSales Order Item`.special_cost,`tabSales Order Item`.price_list_rate,
    `tabSales Order Item`.discount,`tabSales Order Item`.discount_rate,
    `tabSales Order Item`.disc_amt,`tabSales Order Item`.discount_value,
    `tabSales Order Item`.margin_percentage,`tabSales Order Item`.margin_rate,
    `tabSales Order Item`.margin_value,`tabSales Order Item`.sales_price,
    `tabSales Order Item`.prevdoc_docname,
    `tabSales Order Item`.base_rate,`tabSales Order Item`.conversion_factor,
    sum(`tabSales Order Item`.base_amount) as base_amount,
    `tabSales Order Item`.is_free_item,
    `tabSales Order Item`.grant_commission,
    `tabSales Order Item`.net_rate,
    `tabSales Order Item`.base_net_rate,
    sum(`tabSales Order Item`.net_amount) as net_amount,
    sum(`tabSales Order Item`.base_net_amount) as base_net_amount,
    sum(`tabSales Order Item`.billed_amt)as billed_amt,
    `tabSales Order Item`.valuation_rate,
    sum(`tabSales Order Item`.gross_profit) as gross_profit,`tabSales Order Item`.unit_price_document_currency,`tabSales Order Item`.base_price_list_rate,
    `tabSales Order Item`.delivery_date,sum(`tabSales Order Item`.qty) as qty,
    `tabSales Order Item`.uom,`tabSales Order Item`.rate,`tabSales Order Item`.warehouse,
    `tabSales Order Item`.bom_no,sum(`tabSales Order Item`.amount) as amount from `tabSales Order` 
    left join `tabSales Order Item` on `tabSales Order`.name = `tabSales Order Item`.parent where `tabSales Order`.name = '%s' group by `tabSales Order Item`.item_code,`tabSales Order Item`.is_free order by `tabSales Order Item`.idx """%(sales_order),as_dict = 1)
    return childtab


@frappe.whitelist()
def get_so_difference(sales_order,sales_invoice):
    so = frappe.db.sql(""" select `tabSales Order Item`.item_code,
    `tabSales Order Item`.delivery_date,sum(`tabSales Order Item`.qty) as qty from `tabSales Order` left join `tabSales Order Item` on `tabSales Order`.name = `tabSales Order Item`.parent where `tabSales Order`.name = '%s' group by `tabSales Order Item`.item_code"""%(sales_order),as_dict = 1)
    si = frappe.db.sql(""" select `tabSales Invoice Item`.item_code,sum(`tabSales Invoice Item`.qty) as qty from `tabSales Invoice` left join `tabSales Invoice Item` on `tabSales Invoice`.name = `tabSales Invoice Item`.parent where `tabSales Invoice`.name = '%s' group by `tabSales Invoice Item`.item_code"""%(sales_invoice),as_dict = 1)
    
    return so,si


@frappe.whitelist()
def mr_duplicate(material_request):
    childtab = frappe.db.sql(""" select `tabMaterial Request Item`.item_code,`tabMaterial Request Item`.item_name,`tabMaterial Request Item`.description,sum(`tabMaterial Request Item`.qty) as qty,`tabMaterial Request Item`.uom,`tabMaterial Request Item`.rate,`tabMaterial Request Item`.warehouse,`tabMaterial Request Item`.bom_no,sum(`tabMaterial Request Item`.amount) as amount from `tabMaterial Request` left join `tabMaterial Request Item` on `tabMaterial Request`.name = `tabMaterial Request Item`.parent where `tabMaterial Request`.name = '%s' group by `tabMaterial Request Item`.item_code"""%(material_request),as_dict = 1)
    return childtab

@frappe.whitelist()
def get_stock_entry(company,bom):
    inbound =  frappe.db.sql("""select `tabStock Transfer Detail`.serial_no,`tabStock Transfer Detail`.bom_inbound_qty ,`tabStock Transfer Detail`.balance_in_qty,`tabStock Transfer Detail`.bom_outbound_qty, `tabStock Transfer Detail`.item_code,`tabStock Transfer Detail`.target_warehouse, `tabStock Transfer Detail`.source_warehouse,
    `tabStock Transfer Detail`.batch,
    `tabStock Transfer Detail`.basic_rate,
    `tabStock Transfer Detail`.valuation_rate,
    `tabStock Transfer Detail`.basic_amount,
    `tabStock Transfer Detail`.amount,
    `tabStock Transfer Detail`.additional_cost,
    `tabStock Transfer Detail`.itemwise_additional_cost,
    `tabStock Transfer Detail`.qty,
    `tabStock Transfer Detail`.uom,
    `tabStock Transfer Detail`.updated_serial_no,
    `tabStock Transfer Detail`.item_name
    from `tabStock Transfer India` 
    left join `tabStock Transfer Detail` on `tabStock Transfer India`.name = `tabStock Transfer Detail`.parent
    where `tabStock Transfer Detail`.bom_inbound = '%s'  """%(bom),as_dict=True)

    outbound =  frappe.db.sql("""select `tabStock Transfer Outbound`.serial_no,`tabStock Transfer Outbound`.bom_inbound_qty,`tabStock Transfer Outbound`.bom_outbound_qty,`tabStock Transfer Outbound`.item_code,`tabStock Transfer Outbound`.target_warehouse, `tabStock Transfer Outbound`.source_warehouse from `tabStock Transfer India` 
    left join `tabStock Transfer Outbound` on `tabStock Transfer India`.name = `tabStock Transfer Outbound`.parent
    where `tabStock Transfer Outbound`.bom_inbound = '%s' """%(bom),as_dict=True)
   
    # inbound =  frappe.db.sql("""select `tabStock Entry Detail`.serial_no,`tabStock Entry Detail`.basic_rate,`tabStock Entry Detail`.item_code,sum(`tabStock Entry Detail`.qty) as qty,`tabStock Entry Detail`.t_warehouse,`tabStock Entry Detail`.s_warehouse from `tabStock Entry` 
    #     left join `tabStock Entry Detail` on `tabStock Entry`.name = `tabStock Entry Detail`.parent
    #     where `tabStock Entry`.bill_of_entry = '%s' and `tabStock Entry`.company = '%s' and `tabStock Entry`.docstatus !=2 group by `tabStock Entry Detail`.item_code """%(bom,company),as_dict=True)
    
    # pr =  frappe.db.sql("""select `tabPurchase Receipt Item`.serial_no,`tabPurchase Receipt Item`.item_code,`tabPurchase Receipt Item`.qty,`tabPurchase Receipt`.set_warehouse from `tabPurchase Receipt` 
    #     left join `tabPurchase Receipt Item` on `tabPurchase Receipt`.name = `tabPurchase Receipt Item`.parent
    #     where `tabPurchase Receipt`.bill_of_entry = '%s' and `tabPurchase Receipt`.company = '%s' and `tabPurchase Receipt`.docstatus = 1  """%(bom,company),as_dict=True)
    return inbound


@frappe.whitelist()
def date_validation(po_date):
    dayss = today()
    return dayss

@frappe.whitelist()
def get_country_name(company):
    country = frappe.db.sql("""select country from `tabCompany` where name ='%s' """%(company),as_dict=1)[0]
    return country['country']


@frappe.whitelist()
def get_foc_item(doc,method):
    name = (doc.name).lower()
    pr = frappe.get_doc("Purchase Receipt",{"name":doc.purchase_document_no})
    for i in pr.items:
        sno = i.serial_no.upper()
        if i.serial_no == name:
            frappe.db.set_value("Serial No","ADBC0000127","is_free", 1)
            frappe.db.commit()


@frappe.whitelist()
def get_foc_item_pr(doc,method):
    for i in doc.items:
        if i.is_free:
            s_name = (i.serial_no).upper() 
            ser_name = s_name.split("\n")
            for sn in ser_name:
                if frappe.db.exists("Serial No",sn):
                    frappe.db.set_value("Serial No",sn,"is_free",1)


@frappe.whitelist()
def get_foc_item_dn(doc,method):
    for i in doc.items:
        if i.is_free and i.serial_no:
            s_name = (i.serial_no).upper() 
            ser_name = s_name.split("\n")
            for sn in ser_name:
                if frappe.db.exists("Serial No",sn):
                    frappe.db.set_value("Serial No",sn,"is_free",1)

@frappe.whitelist()
def get_prepared_by_name(email):
    prep_name = frappe.db.sql("""select full_name from `tabUser` where email = '%s' """%(email),as_dict = 1)[0]
    return prep_name['full_name']

@frappe.whitelist()
def get_itinerary(travel_request):
    travel_request = frappe.get_doc("Travel Request",travel_request)
    return travel_request.itinerary

@frappe.whitelist()
def purchase_order_update():
    po = frappe.db.sql("""update `tabDelivery Note Item` set balance_qty = 0 where name ="8cbf05a990" """)


@frappe.whitelist()
def get_last_po(item_code,company):
    item = frappe.db.sql("""select `tabItem Supplier`.supplier as supplier from `tabItem`
        left join `tabItem Supplier` on `tabItem`.name = `tabItem Supplier`.parent
        where `tabItem`.name = '%s' """ % (item_code), as_dict=True)
    item_price = frappe.get_value("Item Price",{"item_code":item_code,"price_list":"STANDARD BUYING-USD"},["price_list_rate"])
    
    pos = frappe.db.sql("""select `tabPurchase Order`.supplier as supplier,`tabPurchase Order Item`.qty as qty,`tabPurchase Order Item`.rate as rate from `tabPurchase Order`
        left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
        where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 """ % (item_code), as_dict=True)
    if pos:
        return pos[0]
    else:
        return item[0],item_price
    
@frappe.whitelist()
def contact_details(name,email,mobile,customer):
    # values = json.loads(values)
    contact = frappe.new_doc("Contact")
    contact.first_name = name
    if email:
        contact.email_id_ = email
        contact.append('email_ids',{
            'email_id': email		
        })
    if mobile:
        contact.mobile_no = mobile
        contact.append('phone_nos',{
            'phone':mobile,
        })	
    
    contact.append('links',{
        'link_doctype':'Customer',
        "link_name": customer
    })
    contact.save(ignore_permissions=True)
    return contact.name

# @frappe.whitelist()
# def update_ce_so():
#     so = frappe.db.sql(""" update `tabPurchase Order` set conversion_rate = '1.38' where name = '%s' """%("PO-NSPL-2023-00126"))

   

@frappe.whitelist()
def get_electra_details(**args):
    data = ''
    data1 = ''
    data2=''
    i = 0
    aa = args['item']
    item = frappe.get_value('Item', {'item_code': args['item']}, 'item_code')
    if item:
        item = frappe.get_value('Item', {'item_code': args['item']}, 'item_code')
        group = frappe.get_value('Item', {'item_code': args['item']}, 'item_group')
        des = frappe.get_value('Item', {'item_code': args['item']}, 'description')
        
        cou = 0
        p_po = 0
        p_so = 0
        tot = 'Total'
        uom = 'Nos'

        stocks_query = frappe.db.sql("""
            SELECT 
                (SUM(`tabBin`.actual_qty) - SUM(reserved_stock)) AS actual_qty,
                warehouse,
                stock_uom,
                stock_value
            FROM tabBin
            WHERE item_code = %s 
            GROUP BY warehouse
        """, (item,), as_dict=True)

        if stocks_query:
            data += '''
                <table class="table table-bordered" style="width:75%">
                    <tr>
                        <th style="padding:1px;border: 1px solid black;background-color:#fe3f0c;color:white" colspan=11><center>NORDEN PRODUCT SEARCH</center></th>
                    </tr>
                    <tr>
                        <td colspan=2 style="padding:1px;border: 1px solid black;color:white;background-color:#6f6f6f;text-align: left"><b>Item Code</b></td>
                        <td colspan=9 style="padding:1px;border: 1px solid black;text-align: left"><b>{}</b></td>
                    </tr>
                    <tr>
                        <td colspan=2 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;text-align: left"><b>Item Name</b></td>
                        <td colspan=9 style="padding:1px;border: 1px solid black;text-align: left"><b>{}</b></td>
                    </tr>
                    <tr>
                        <td colspan=2 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;text-align: left"><b>Item Group</b></td>
                        <td colspan=9 style="padding:1px;border: 1px solid black;text-align: left"><b>{}</b></td>
                    </tr>
                    <tr>
                        <td colspan=2 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;text-align: left"><b>Description</b></td>
                        <td colspan=9 style="padding:1px;border: 1px solid black;text-align: left"><b>{}</b></td>
                    </tr>
                    <tr>
                        <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Company</b></center></td>
                        <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Warehouse</b></center></td>
                        <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>QTY</b></center></td>
                        <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>UOM</b></center></td>
                        <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Cost</b></center></td>
                        <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Selling Rate</b></center></td>
                        <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Currency</b></center></td>
                        <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Pending PO</b></center></td>
                        <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Pending SO</b></center></td>
                    </tr>
                '''.format(item, frappe.db.get_value('Item', item, 'item_name'), group, des)

            for stock in stocks_query:
                if stock.actual_qty >= 0:
                    stock_company = frappe.db.sql("""
                        SELECT company 
                        FROM tabWarehouse 
                        WHERE name = %s
                    """, (stock.warehouse,), as_dict=True)

                    for com in stock_company:
                        psoc_query = frappe.db.sql("""
                            SELECT SUM(`tabSales Order Item`.qty) AS qty 
                            FROM `tabSales Order`
                            LEFT JOIN `tabSales Order Item` ON `tabSales Order`.name = `tabSales Order Item`.parent
                            WHERE `tabSales Order Item`.item_code = %s 
                            AND `tabSales Order`.docstatus = 1 
                            AND `tabSales Order`.company = %s
                        """, (args['item'], com.company), as_dict=True)[0]
                        
                        if not psoc_query["qty"]:
                            psoc_query["qty"] = 0
                            
                        deliver = frappe.db.sql("""
                            SELECT SUM(`tabDelivery Note Item`.qty) AS qty 
                            FROM `tabDelivery Note`
                            LEFT JOIN `tabDelivery Note Item` ON `tabDelivery Note`.name = `tabDelivery Note Item`.parent
                            WHERE `tabDelivery Note Item`.item_code = %s 
                            AND `tabDelivery Note`.docstatus = 1 
                            AND `tabDelivery Note`.company = %s
                        """, (args['item'], com.company), as_dict=True)[0]
                        
                        if not deliver["qty"]:
                            deliver['qty'] = 0
                            
                        del_total = psoc_query['qty'] - deliver['qty']
                        
                        ppoc_query = frappe.db.sql("""
                            SELECT SUM(`tabPurchase Order Item`.qty) AS qty 
                            FROM `tabPurchase Order`
                            LEFT JOIN `tabPurchase Order Item` ON `tabPurchase Order`.name = `tabPurchase Order Item`.parent
                            WHERE `tabPurchase Order Item`.item_code = %s 
                            AND `tabPurchase Order`.docstatus != 2 
                            AND `tabPurchase Order`.company = %s
                        """, (args['item'], com.company), as_dict=True)[0]
                        
                        if not ppoc_query["qty"]:
                            ppoc_query["qty"] = 0
                            
                        ppoc_receipt = frappe.db.sql("""
                            SELECT SUM(`tabPurchase Receipt Item`.qty) AS qty 
                            FROM `tabPurchase Receipt`
                            LEFT JOIN `tabPurchase Receipt Item` ON `tabPurchase Receipt`.name = `tabPurchase Receipt Item`.parent
                            WHERE `tabPurchase Receipt Item`.item_code = %s 
                            AND `tabPurchase Receipt`.status = "Completed" 
                            AND `tabPurchase Receipt`.company = %s
                        """, (args['item'], com.company), as_dict=True)[0]
                        
                        if not ppoc_receipt["qty"]:
                            ppoc_receipt["qty"] = 0
                            
                        ppoc_total = ppoc_query["qty"] - ppoc_receipt["qty"]
                        
                        country, default_currency = frappe.get_value("Company", {"name": com.company}, ["country", "default_currency"])
                        
                        if country == "United Arab Emirates":
                            cost = frappe.get_value("Item Price", {"item_code": item, "price_list": "Electra Qatar - NCMEF"}, ["price_list_rate"])
                        else:
                            cost = frappe.get_value("Item Price", {"item_code": item, "price_list": "STANDARD BUYING-USD"}, ["price_list_rate"])
                            
                        pricelist = country + ' ' + "Sales Price"
                        
                        if country == "United Arab Emirates":
                            sp = frappe.get_value("Item Price", {"item_code": item, "price_list": "Internal - NCMEF"}, ["price_list_rate"])
                        else:
                            sp = frappe.get_value("Item Price", {"item_code": item, "price_list": pricelist}, ["price_list_rate"])
                        sp = sp if sp else 0.0	
                        data += '''
                            <tr>
                                <td colspan=1 style="padding:1px;border: 1px solid black">{}</td>
                                <td colspan=1 style="padding:1px;border: 1px solid black">{}</td>
                                <td colspan=1 style="padding:1px;border: 1px solid black"><center><b>{}</b></center></td>
                                <td colspan=1 style="padding:1px;border: 1px solid black"><center><b>{}</b></center></td>
                                <td colspan=1 style="padding:1px;border: 1px solid black"><center><b>{}</b></center></td>
                                <td colspan=1 style="padding:1px;border: 1px solid black"><center><b>{}</b></center></td>
                                <td colspan=1 style="padding:1px;border: 1px solid black"><center><b>{}</b></center></td>
                                <td colspan=1 style="padding:1px;border: 1px solid black"><center><b>{}</b></center></td>
                                <td colspan=1 style="padding:1px;border: 1px solid black"><center><b>{}</b></center></td>
                            </tr>
                        '''.format(
                            com.company,
                            stock.warehouse,
                            int(stock.actual_qty) or 0,
                            stock.stock_uom or '-',
                            "{:.2f}".format(cost) or 0,
                            "{:.2f}".format(sp),
                            default_currency,
                            int(ppoc_total) or 0,
                            int(del_total) or 0
                        )
                        
                        i += 1
                        cou += stock.actual_qty
                        p_po += ppoc_total
                        p_so += del_total

            data += '''
                <tr>
                    <td align="right" colspan=2 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><b>{}</b></td>
                    <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>{}</b></center></td>
                    <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>{}</b></center></td>
                    <td colspan=3 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b></b></center></td>
                    <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>{}</b></center></td>
                    <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>{}</b></center></td>
                </tr>
            '''.format(tot or 0, int(cou) or 0, uom, int(p_po) or 0, int(p_so) or 0)
            
            data += '</table>'
        else:
            i += 1
            data2 += '''
                <table width="75%">
                    <tr>
                        <td align="center" colspan=10 style="padding:1px;border: 1px solid black;background-color:#fe3f0c;color:white;"><b>NORDEN PRODUCT SEARCH</b></td>
                        
                    </tr>
                    <tr>
                        <td align="center" colspan=10 style="padding:1px;border: 1px solid black";><b>No Stock Available</b></td>
                    </tr>
                </table>
            '''
            data += data2
    else:
        i += 1
        data1 += '''
            <table width="75%">
                <tr>
                    <td align="center" colspan=10 style="padding:1px;border: 1px solid black;background-color:#fe3f0c;color:white;"><b>NORDEN PRODUCT SEARCH</b></td>
                </tr>
                <tr>
                    <td align="center" colspan=10 style="padding:1px;border: 1px solid black";><b>No Stock Available</b></td>
                </tr>
            </table>
        '''
        data += data1

    if i > 0:
        return data
    
@frappe.whitelist()
def get_electra_details_without_cost(**args): 
    data = ''
    data1 = ''
    data2=''
    i = 0
    aa = args['item']
    item = frappe.get_value('Item', {'item_code': args['item']}, 'item_code')
    if item:
        item = frappe.get_value('Item', {'item_code': args['item']}, 'item_code')
        group = frappe.get_value('Item', {'item_code': args['item']}, 'item_group')
        des = frappe.get_value('Item', {'item_code': args['item']}, 'description')
        
        cou = 0
        p_po = 0
        p_so = 0
        tot = 'Total'
        uom = 'Nos'

        stocks_query = frappe.db.sql("""
            SELECT 
                (SUM(`tabBin`.actual_qty) - SUM(reserved_stock)) AS actual_qty,
                warehouse,
                stock_uom,
                stock_value
            FROM tabBin
            WHERE item_code = %s 
            GROUP BY warehouse
        """, (item,), as_dict=True)

        if stocks_query:
            data += '''
                <table class="table table-bordered" style="width:75%">
                    <tr>
                        <th style="padding:1px;border: 1px solid black;background-color:#fe3f0c;color:white" colspan=10><center>NORDEN PRODUCT SEARCH</center></th>
                    </tr>
                    <tr>
                        <td colspan=2 style="padding:1px;border: 1px solid black;color:white;background-color:#6f6f6f;text-align: left"><b>Item Code</b></td>
                        <td colspan=8 style="padding:1px;border: 1px solid black;text-align: left"><b>{}</b></td>
                    </tr>
                    <tr>
                        <td colspan=2 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;text-align: left"><b>Item Name</b></td>
                        <td colspan=8 style="padding:1px;border: 1px solid black;text-align: left"><b>{}</b></td>
                    </tr>
                    <tr>
                        <td colspan=2 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;text-align: left"><b>Item Group</b></td>
                        <td colspan=8 style="padding:1px;border: 1px solid black;text-align: left"><b>{}</b></td>
                    </tr>
                    <tr>
                        <td colspan=2 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;text-align: left"><b>Description</b></td>
                        <td colspan=8 style="padding:1px;border: 1px solid black;text-align: left"><b>{}</b></td>
                    </tr>
                    <tr>
                        <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Company</b></center></td>
                        <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Warehouse</b></center></td>
                        <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>QTY</b></center></td>
                        <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>UOM</b></center></td>
                        <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Selling Rate</b></center></td>
                        <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Currency</b></center></td>
                        <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Pending PO</b></center></td>
                        <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Pending SO</b></center></td>
                    </tr>
                '''.format(item, frappe.db.get_value('Item', item, 'item_name'), group, des)

            for stock in stocks_query:
                if stock.actual_qty >= 0:
                    stock_company = frappe.db.sql("""
                        SELECT company 
                        FROM tabWarehouse 
                        WHERE name = %s
                    """, (stock.warehouse,), as_dict=True)

                    for com in stock_company:
                        psoc_query = frappe.db.sql("""
                            SELECT SUM(`tabSales Order Item`.qty) AS qty 
                            FROM `tabSales Order`
                            LEFT JOIN `tabSales Order Item` ON `tabSales Order`.name = `tabSales Order Item`.parent
                            WHERE `tabSales Order Item`.item_code = %s 
                            AND `tabSales Order`.docstatus = 1 
                            AND `tabSales Order`.company = %s
                        """, (args['item'], com.company), as_dict=True)[0]
                        
                        if not psoc_query["qty"]:
                            psoc_query["qty"] = 0
                            
                        deliver = frappe.db.sql("""
                            SELECT SUM(`tabDelivery Note Item`.qty) AS qty 
                            FROM `tabDelivery Note`
                            LEFT JOIN `tabDelivery Note Item` ON `tabDelivery Note`.name = `tabDelivery Note Item`.parent
                            WHERE `tabDelivery Note Item`.item_code = %s 
                            AND `tabDelivery Note`.docstatus = 1 
                            AND `tabDelivery Note`.company = %s
                        """, (args['item'], com.company), as_dict=True)[0]
                        
                        if not deliver["qty"]:
                            deliver['qty'] = 0
                            
                        del_total = psoc_query['qty'] - deliver['qty']
                        
                        ppoc_query = frappe.db.sql("""
                            SELECT SUM(`tabPurchase Order Item`.qty) AS qty 
                            FROM `tabPurchase Order`
                            LEFT JOIN `tabPurchase Order Item` ON `tabPurchase Order`.name = `tabPurchase Order Item`.parent
                            WHERE `tabPurchase Order Item`.item_code = %s 
                            AND `tabPurchase Order`.docstatus != 2 
                            AND `tabPurchase Order`.company = %s
                        """, (args['item'], com.company), as_dict=True)[0]
                        
                        if not ppoc_query["qty"]:
                            ppoc_query["qty"] = 0
                            
                        ppoc_receipt = frappe.db.sql("""
                            SELECT SUM(`tabPurchase Receipt Item`.qty) AS qty 
                            FROM `tabPurchase Receipt`
                            LEFT JOIN `tabPurchase Receipt Item` ON `tabPurchase Receipt`.name = `tabPurchase Receipt Item`.parent
                            WHERE `tabPurchase Receipt Item`.item_code = %s 
                            AND `tabPurchase Receipt`.status = "Completed" 
                            AND `tabPurchase Receipt`.company = %s
                        """, (args['item'], com.company), as_dict=True)[0]
                        
                        if not ppoc_receipt["qty"]:
                            ppoc_receipt["qty"] = 0
                            
                        ppoc_total = ppoc_query["qty"] - ppoc_receipt["qty"]
                        
                        country, default_currency = frappe.get_value("Company", {"name": com.company}, ["country", "default_currency"])
                        
                        if country == "United Arab Emirates":
                            cost = frappe.get_value("Item Price", {"item_code": item, "price_list": "Electra Qatar - NCMEF"}, ["price_list_rate"])
                        else:
                            cost = frappe.get_value("Item Price", {"item_code": item, "price_list": "STANDARD BUYING-USD"}, ["price_list_rate"])
                            
                        pricelist = country + ' ' + "Sales Price"
                        
                        if country == "United Arab Emirates":
                            sp = frappe.get_value("Item Price", {"item_code": item, "price_list": "Internal - NCMEF"}, ["price_list_rate"])
                        else:
                            sp = frappe.get_value("Item Price", {"item_code": item, "price_list": pricelist}, ["price_list_rate"])
                        sp = sp if sp else 0.0		
                        data += '''
                            <tr>
                                <td colspan=1 style="padding:1px;border: 1px solid black">{}</td>
                                <td colspan=1 style="padding:1px;border: 1px solid black">{}</td>
                                <td colspan=1 style="padding:1px;border: 1px solid black"><center><b>{}</b></center></td>
                                <td colspan=1 style="padding:1px;border: 1px solid black"><center><b>{}</b></center></td>
                                <td colspan=1 style="padding:1px;border: 1px solid black"><center><b>{}</b></center></td>
                                <td colspan=1 style="padding:1px;border: 1px solid black"><center><b>{}</b></center></td>
                                <td colspan=1 style="padding:1px;border: 1px solid black"><center><b>{}</b></center></td>
                                <td colspan=1 style="padding:1px;border: 1px solid black"><center><b>{}</b></center></td>
                            </tr>
                        '''.format(
                            com.company,
                            stock.warehouse,
                            int(stock.actual_qty) or 0,
                            stock.stock_uom or '-',
                            "{:.2f}".format(sp),
                            default_currency,
                            ppoc_total or 0,
                            int(del_total) or 0
                        )
                        
                        i += 1
                        cou += stock.actual_qty
                        p_po += ppoc_total
                        p_so += del_total

            data += '''
                <tr>
                    <td align="right" colspan=2 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><b>{}</b></td>
                    <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>{}</b></center></td>
                    <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>{}</b></center></td>
                    <td colspan=2 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b></b></center></td>
                    <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>{}</b></center></td>
                    <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>{}</b></center></td>
                </tr>
            '''.format(tot or 0, int(cou) or 0, uom, int(p_po) or 0, int(p_so) or 0)
            
            data += '</table>'
        else:
            i += 1
            data2 += '''
                <table width="75%">
                    <tr>
                        <td align="center" colspan=10 style="padding:1px;border: 1px solid black;background-color:#fe3f0c;color:white;"><b>NORDEN PRODUCT SEARCH</b></td>
                    </tr>
                    <tr>
                        <td align="center" colspan=10 style="padding:1px;border: 1px solid black";><b>No Stock Available</b></td>
                    </tr>
                </table>
            '''
            data += data2

    else:
        i += 1
        data1 += '''
            <table width="75%">
                <tr>
                    <td align="center" colspan=10 style="padding:1px;border: 1px solid black;background-color:#fe3f0c;color:white;"><b>NORDEN PRODUCT SEARCH</b></td>
                </tr>
                <tr>
                    <td align="center" colspan=10 style="padding:1px;border: 1px solid black";><b>No Stock Available</b></td>
                </tr>
            </table>
        '''
        data += data1

    if i > 0:
        return data



    
# def salary_slip():
#     salary = frappe.db.sql(""" SELECT SUM(`tabSalary Detail`.amount) AS arrears_total FROM `tabSalary Slip` INNER JOIN `tabEmployee` ON `tabSalary Slip`.employee = `tabEmployee`.name INNER JOIN `tabSalary Detail` ON `tabSalary Slip`.name = `tabSalary Detail`.parent WHERE  `tabEmployee`.status = 'Active' AND `tabEmployee`.payroll_category = 'NCPL Staff' AND `tabSalary Slip`.start_date BETWEEN '%s' AND '%s'   AND `tabSalary Detail`.salary_component = 'Arrear'  """%('2023-01-01',a,as_dict=True))[0]

# update project name in Sales order to sales invoice
@frappe.whitelist()
def update_sale():
    route = frappe.db.get_all('Sales Order',{'docstatus': 1 },['project_name','customer'])  
    for ro in route :
        if ro.project_name:
            print(ro.project_name)
            print(ro.customer)
            sales_invoice = frappe.db.get_all('Sales Invoice', {'customer': ro.customer}, ['name'])
            for sales in sales_invoice:
                print(sales.name)
                frappe.db.set_value('Sales Invoice', sales.name,'project_name',ro.project_name)
 

@frappe.whitelist()
def update_project_reference():
    route = frappe.db.get_all('Sales Invoice',{'docstatus': 1 },['*'])
    for i in route:
        print(i.name)
        pr = frappe.new_doc("Project Reference")
        pr.company = i.company
        pr.sales_person_name = i.sales_person_name
        pr.so_submitted_date = i.due_date
        pr.so_status_live = i.status
        pr.sales_invoice = i.name
        child = frappe.get_doc("Sales Invoice Item",{'parent':i.name})
        pr.append('items_table',{
            'items_name':child.item_name,
            'qty':child.qty,
            'item_group':child.item_group
        })
        pr.save(ignore_permissions=True)
        frappe.db.commit()

def update_mock_reference():
    route = frappe.db.get_all('Sales Invoice',{'docstatus': 1 },['*'])
    for i in route:
        print(i.name)
        mr = frappe.new_doc("Mock Reference")
        mr.company = i.company
        mr.project_name = i.name
        mr.sales_person_name = i.sales_person_name
        mr.so_submitted_date = i.due_date
        mr.so_status_live = i.status
        mr.sales_invoice = i.name
        child = frappe.get_doc("Sales Invoice Item",{'parent':i.name})
        mr.append('items_table',{
            'items_name':child.item_name,
            'qty':child.qty,
            'item_group':child.item_group
        })
        mr.save(ignore_permissions=True)
        frappe.db.commit()

# Travel Request Document Submitted Employee Advance New Doc Create
@frappe.whitelist()
def create_employee_advance(doc,method):
    emp_adv = frappe.new_doc("Employee Advance")
    emp_adv.employee = doc.employee
    emp_adv.company = doc.company
    emp_adv.purpose = doc.custom_purpose_of_travel
    emp_adv.advance_amount = doc.advance_amount
    emp_adv.posting_date = doc.posting_date
    emp_adv.currency = doc.currency
    emp_adv.save(ignore_permissions = True)

@frappe.whitelist()
def delete_pr():
    pr = frappe.db.sql(""" delete from `tabGL Entry`  where name = "ACC-GLE-2024-09510"  """)

@frappe.whitelist()
def create_mrb(doc,method):
    if not doc.is_return:
        for i in doc.items:
            if i.rejected_warehouse:
                mrb = frappe.new_doc("MRB")
                mrb.item_code = i.item_code
                mrb.description = i.description
                mrb.uom = i.uom
                mrb.purchase_receipt = doc.name
                mrb.qty = i.rejected_qty
                mrb.batch_no = i.batch_no
                
                mrb.purchase_order = doc.purchase_order_no
                ins = frappe.get_doc("Item Inspection",{"item_code":i.item_code,"pr_number":doc.name})
                mrb.inspection_date = ins.inspection_date
                mrb.inspected_by = ins.inspected_by
                mrb.company = doc.company
                mrb.rate = i.rate
                mrb.warehouse = i.rejected_warehouse
                mrb.save(ignore_permissions=True)
            else:
                pass


@frappe.whitelist()
def get_appraisal(doc,method):
    emp = frappe.get_doc("Employee",{'employee_name':doc.employee_name})
    emp.set('goals',[])
    for i in doc.goals:
        emp.append("goals",{
            "kra":i.kra,
            "per_weightage":i.per_weightage,
            "req_output":i.req_output,
            "min_output":i.min_output,
            "actual_output":i.actual_output,
            "earned_score":i.score_earned
        })
        emp.save(ignore_permissions=True)
    

@frappe.whitelist()
def get_appraisal_template(doc,method):
    emp = frappe.get_doc("Employee",{'employee_name':doc.employee_name})
    emp.set('template',[])
    for i in doc.goals:
        emp.append("template",{
            "kra":i.kra,
            "req_output":i.req_output,
            "min_output":i.min_output,
            "per_weightage":i.per_weightage
        })
        emp.save(ignore_permissions=True)   



@frappe.whitelist()
def trigger_mail_notification():
    table_html = ''
    leave_applications = frappe.get_list("Leave Application", {"workflow_state": "Pending for HOD"}, ['*'])

    if leave_applications:
        header = """<p>Dear Sir/Mam, <br> Please find the below list of Applications pending for your Approval.</p><table class='table table-bordered'>"""
        regards = "Thanks & Regards,<br>hrPRO"
        table_html += '<table class="table table-bordered" style="width:100%; background-color: steelblue; color: white;">'
        table_html += '<tr><th colspan="4" style="border: 1px solid black;">Leave Application ID</th>'
        table_html += '<th colspan="4" style="border: 1px solid black;">Employee Id</th>'
        table_html += '<th colspan="4" style="border: 1px solid black;">Employee Name</th>'
        table_html += '<th colspan="4" style="border: 1px solid black;">From Date</th>'
        table_html += '<th colspan="4" style="border: 1px solid black;">To Date</th>'
        table_html += '<th colspan="4" style="border: 1px solid black;">Leave Type</th></tr>'
        for leave in leave_applications:
            table_html += '<tr><td colspan="4" style="border: 1px solid black;">{}</td>'.format(leave.name)
            table_html += '<td colspan="4" style="border: 1px solid black;">{}</td>'.format(leave.employee)
            table_html += '<td colspan="4" style="border: 1px solid black;">{}</td>'.format(leave.employee_name)
            table_html += '<td colspan="4" style="border: 1px solid black;">{}</td>'.format(leave.from_date)
            table_html += '<td colspan="4" style="border: 1px solid black;">{}</td>'.format(leave.to_date)
            table_html += '<td colspan="4" style="border: 1px solid black;">{}</td></tr>'.format(leave.leave_type)
            frappe.sendmail(
                recipients = leave.leave_approver,
                subject='Reg. List of pending Approvals',
                message=header + table_html + regards
            )
        table_html += '</table><br>'



    expense_claim = frappe.get_list("Expense Claim", {"workflow_state": "Pending for HOD"},['*'])
    if expense_claim:
        header = """<p>Dear Sir/Mam, <br> Please find the below list of Applications pending for your Approval.</p><table class='table table-bordered'>"""
        regards = "Thanks & Regards,<br>hrPRO"
        table_html += '<table class="table table-bordered" style="width:100%; background-color: steelblue; color: white;">'
        table_html += '<tr><th colspan="4" style="border: 1px solid black;">Leave Application ID</th>'
        table_html += '<th colspan="4" style="border: 1px solid black;">Employee Id</th>'
        table_html += '<th colspan="4" style="border: 1px solid black;">Employee Name</th>'
        for expense in expense_claim:
            table_html += '<tr><td colspan="4" style="border: 1px solid black;">{}</td>'.format(expense.name)
            table_html += '<td colspan="4" style="border: 1px solid black;">{}</td>'.format(expense.employee)
            table_html += '<td colspan="4" style="border: 1px solid black;">{}</td>'.format(expense.employee_name)
            frappe.sendmail(
            recipients = expense.expense_approver,
            subject = 'Reg.List of pending Approvals',
            message = header + table_html + regards)
        table_html += '</table><br>'
        
    
    wfh = frappe.get_list("Work From Home Request", {"workflow_state": "Pending for HOD"}, ['*'])
    if wfh:
        header = """<p>Dear Sir/Mam, <br> Please find the below list of Applications pending for your Approval.</p><table class='table table-bordered'>"""
        regards = "Thanks & Regards,<br>hrPRO"
        table_html += '<table class="table table-bordered" style="width:100%; background-color: steelblue; color: white;">'
        table_html += '<tr><th colspan="4" style="border: 1px solid black;">Leave Application ID</th>'
        table_html += '<th colspan="4" style="border: 1px solid black;">Employee Id</th>'
        table_html += '<th colspan="4" style="border: 1px solid black;">Employee Name</th>'
        table_html += '<th colspan="4" style="border: 1px solid black;">Reason</th>'
        for work in wfh:
            table_html += '<tr><td colspan="4" style="border: 1px solid black;">{}</td>'.format(work.name)
            table_html += '<td colspan="4" style="border: 1px solid black;">{}</td>'.format(work.employee)
            table_html += '<td colspan="4" style="border: 1px solid black;">{}</td>'.format(work.employee_name)
            table_html += '<td colspan="4" style="border: 1px solid black;">{}</td>'.format(work.reason)

            frappe.sendmail(
            recipients = work.approver,
            subject = 'Reg.List of pending Approvals',
            message = header + table_html + regards)
        table_html += '</table><br>'
    
    travel= frappe.get_list("Travel Request",['*'])
    for tr in travel:
        header = """<p>Dear Sir/Mam, <br> Please find the below list of Applications pending for your Approval.</p><table class='table table-bordered'>"""
        regards = "Thanks & Regards,<br>hrPRO"
        table_html += '<table class="table table-bordered" style="width:100%; background-color: steelblue; color: white;">'
        table_html += '<tr><th colspan="4" style="border: 1px solid black;">Leave Application ID</th>'
        table_html += '<th colspan="4" style="border: 1px solid black;">Employee Id</th>'
        table_html += '<th colspan="4" style="border: 1px solid black;">Employee Name</th>'
        table_html += '<th colspan="4" style="border: 1px solid black;">Purpose of Travel</th>'
        if tr.workflow_state == "Pending for HOD":
            table_html += '<tr><td colspan="4" style="border: 1px solid black;">{}</td>'.format(tr.name)
            table_html += '<td colspan="4" style="border: 1px solid black;">{}</td>'.format(tr.employee)
            table_html += '<td colspan="4" style="border: 1px solid black;">{}</td>'.format(tr.employee_name)
            table_html += '<td colspan="4" style="border: 1px solid black;">{}</td>'.format(tr.custom_purpose_of_travel)

            reports_to = frappe.get_value("Employee",{"name":tr.reports_to},['user_id'])
            frappe.sendmail(
            recipients = reports_to,
            subject = 'Reg.List of pending Approvals',
            message = header + table_html + regards)
        table_html += '</table><br>'



# @frappe.whitelist()
# def notification_mail():
# 	role_name = "HOD"
# 	user_list = frappe.get_list("Has Role", fields=["parent"], filters={"role": role_name})
# 	for user in user_list:
# 		print(user.parent)
# 		header = """<p>Dear Sir/Mam, <br> Please find the below list of Application pending for your Approval.</p><table class='table table-bordered'> """
# 		regards = "Thanks & Regards,<br>hrPRO"
# 		table_html = ''
# 		emp = frappe.get_value("Employee",{'user_id':user.parent},['employee'])
# 		user_per = frappe.get_list("User Permission",{'user':user.parent,'allow':"Employee"},['for_value'])

# 		table_html += '<table class="table table-bordered" style="width:100% ; background-color:steelblue;color:white"><tr><td colspan = 4 style="border: 1px solid black">Leave Application ID</td><td colspan = 4 style="border: 1px solid black">Employee Id</td><td colspan = 4 style="border: 1px solid black">Employee Name</td><td colspan = 4 style="border: 1px solid black">From Date</td><td colspan = 4 style="border: 1px solid black">To Date</td><td colspan = 4 style="border: 1px solid black">Leave Type</td></tr>'         
# 		for user_per_list in user_per:
# 			if user_per_list.for_value != emp:
# 				leave_applications = frappe.get_list("Leave Application", {'employee': user_per_list.for_value},['*'])
# 				for leave in leave_applications:
# 					if leave.workflow_state == "Pending for HOD":
# 						table_html += '<tr><td colspan = 4 style="border: 1px solid black">%s</td><td colspan = 4 style="border: 1px solid black">%s</td><td colspan = 4 style="border: 1px solid black">%s</td><td colspan = 4 style="border: 1px solid black">%s</td><td colspan = 4 style="border: 1px solid black">%s</td><td colspan = 4 style="border: 1px solid black">%s</td></tr>'%(leave.name, leave.employee, leave.employee_name, leave.from_date, leave.to_date,leave.leave_type)
        
# 			else:
# 				table_html += '<tr><td colspan = 24 style="border: 1px solid black">No Pending for HOD in Leave Application </td></tr>'

# 		table_html += '</table><br>'
        

# 		table_html += '<table class="table table-bordered" style="width:100% ; background-color:steelblue;color:white" ><tr><td colspan = 4 style="border: 1px solid black">Expense Claim ID</td><td colspan = 4 style="border: 1px solid black">Employee Id</td><td colspan = 4 style="border: 1px solid black">Employee Name</td></tr>'         
# 		for user_per_list in user_per:
# 			if user_per_list.for_value != emp:
# 				expense_claim = frappe.get_list("Expense Claim", {'employee': user_per_list.for_value},['*'])
# 				# table_html = '<table><tr><td>ExpenseClaim ID</td><td>Employee Id</td><td>Employee Name</td><td>Posting Date</td><td></td></tr>'
# 				for expense in expense_claim:
# 					if expense.workflowstate == "Pending for HOD":
# 						table_html += '<tr><td colspan = 4 style="border: 1px solid black">{}</td><td  colspan = 4 style="border: 1px solid black">{}</td><td  colspan = 4 style="border: 1px solid black">{}</td></tr>'.format(expense.name, expense.employee, expense.employee_name)
# 			else:
# 				table_html += '<tr><td colspan = 12 style="border: 1px solid black">No Pending for HOD in Expense Claim </td></tr>'
# 		table_html += '</table><br>'
        
        
# 		table_html += '<table class="table table-bordered" style="width:100% ; background-color:steelblue;color:white" ><tr><td colspan = 4 style="border: 1px solid black">WFH ID</td><td colspan = 4 style="border: 1px solid black">Employee Id</td><td colspan = 4 style="border: 1px solid black">Employee Name</td><td colspan = 4 style="border: 1px solid black">Reason</td></tr>'         
# 		for user_per_list in user_per:
# 			if user_per_list.for_value != emp:
# 					wfh = frappe.get_list("Work From Home Request", {'employee': user_per_list.for_value},['*'])
# 					# table_html = '<table><tr><th>WFH ID</th><th>Employee Id</th><th>Employee Name</th><th>Posting Date</th><th></th></tr>'
# 					for work in wfh:
# 						if work.workflow_state == "Pending for HOD":
# 							table_html += '<tr><td colspan = 4 style="border: 1px solid black">{}</td><td colspan = 4 style="border: 1px solid black">{}</td><td colspan = 4 style="border: 1px solid black">{}</td><td colspan = 4 style="border: 1px solid black">{}</td></tr>'.format(work.name, work.employee, work.employee_name, work.reason)
# 			else:
# 				table_html += '<tr><td colspan = 16 style="border: 1px solid black">No Pending for HOD in Work from Home </td></tr>'
# 		table_html += '</table><br>'
    
                            
# 		table_html += '<table class="table table-bordered" style="width:100% ; background-color:steelblue;color:white" ><tr><td colspan = 4 style="border: 1px solid black">Travel Request ID</td><td colspan = 4 style="border: 1px solid black">Employee Id</td><td colspan = 4 style="border: 1px solid black">Employee Name</td><td colspan = 4 style="border: 1px solid black">Purpose of Travel</td></tr>'         
# 		for user_per_list in user_per:
# 			if user_per_list.for_value != emp:
# 					travel= frappe.get_list("Travel Request", {'employee': user_per_list.for_value},['*'])
# 					# table_html = '<table><tr><th>Travel Request ID</th><th>Employee Id</th><th>Employee Name</th><th>Posting Date</th><th></th></tr>'
# 					for tr in travel:
# 						if tr.workflow_state == "Pending for HOD":
# 							table_html += '<tr><td colspan = 4 style="border: 1px solid black">{}</td colspan = 4 style="border: 1px solid black"><td colspan = 4 style="border: 1px solid black">{}</td><td colspan = 4 style="border: 1px solid black">{}</td></tr>'.format(tr.name, tr.employee, tr.employee_name, tr.custom_purpose_of_travel)
# 			else:
# 				table_html += '<tr><td colspan = 16 style="border: 1px solid black">No Pending for HOD in Expense Claim </td></tr>'
# 		table_html += '</table><br>'

                        
# 		frappe.sendmail(
# 			# recipients=['user.parent'],
# 			recipients='maharaja.s@groupteampro.com',
# 			subject='Reg.List of pending Approvals',
# 			message=header+table_html+regards)
            
# def create_hooks_report():
# 	# job = frappe.db.exists('Scheduled Job Type', 'daily_emc_report')
# 	# if not job:
# 	emc = frappe.new_doc("Scheduled Job Type")  
# 	emc.update({
# 		"method": 'norden.custom.trigger_mail_notification',
# 		"frequency": 'Cron',
# 		"cron_format": ' 0 0 */2 * * *'
# 	})
# 	emc.save(ignore_permissions=True)


# def create_report():
# 	# job = frappe.db.exists('Scheduled Job Type', 'daily_emc_report')
# 	# if not job:
# 	emc = frappe.new_doc("Scheduled Job Type")  
# 	emc.update({
# 		"method": 'norden.custom.notification_mails_ec_ad',
# 		"frequency": 'Cron',
# 		"cron_format": ' 0 0 */2 * * *'
# 	})
# 	emc.save(ignore_permissions=True)


# def create_mail_report():
# 	# job = frappe.db.exists('Scheduled Job Type', 'daily_emc_report')
# 	# if not job:
# 	emc = frappe.new_doc("Scheduled Job Type")  
# 	emc.update({
# 		"method": 'norden.custom.notification_mails_ec_fi',
# 		"frequency": 'Cron',
# 		"cron_format": ' 0 0 */2 * * *'
# 	})
# 	emc.save(ignore_permissions=True)






@frappe.whitelist()
def notification_mails_ec_ad():
    role_name = "Admin"
    user_list = frappe.get_list("Has Role", fields=["parent"], filters={"role": role_name})
    for user in user_list:
        print(user.parent)
        header = """<p>Dear Sir/Mam, <br> Please find the below list of Application pending for your Approval.</p><table class='table table-bordered'> """
        regards = "Thanks & Regards,<br>hrPRO"
        table_html = ''
        emp = frappe.get_value("Employee",{'user_id':user.parent},['employee'])
        user_per = frappe.get_list("User Permission",{'user':user.parent,'allow':"Employee"},['for_value'])
        table_html += '<table class="table table-bordered" style="width:100% ; background-color:steelblue;color:white"><tr><td colspan = 4 style="border: 1px solid black">Expense Claim ID</td><td colspan = 4 style="border: 1px solid black">Employee Id</td><td colspan = 4 style="border: 1px solid black">Employee Name</td></tr>'         
        for user_per_list in user_per:
            if user_per_list.for_value != emp:
                expense_claim = frappe.get_list("Expense Claim", {'employee': user_per_list.for_value},['*'])
                for expen in expense_claim: 
                    if expen.workflow_state == "Pending for Admin Verification":
                        frappe.log_error (expen.workflow_state)
                        table_html += '<tr><td colspan = 4 style="border: 1px solid black">%s</td><td colspan = 4 style="border: 1px solid black">%s</td><td colspan = 4 style="border: 1px solid black">%s</td><td colspan = 4 style="border: 1px solid black">%s</td><td colspan = 4 style="border: 1px solid black">%s</td><td colspan = 4 style="border: 1px solid black">%s</td></tr>'%(expen.name, expen.employee, expen.employee_name)
        table_html += '</table><br>'
        frappe.sendmail(
                        recipients=[user.parent],
                        subject='Reg.List of pending Approvals',
                        message=header+table_html+regards)


@frappe.whitelist()
def notification_mails_ec_fi():
    role_name = "Finance"
    user_list = frappe.get_list("Has Role", fields=["parent"], filters={"role": role_name})
    for user in user_list:
        print(user.parent)
        header = """<p>Dear Sir/Mam, <br> Please find the below list of Application pending for your Approval.</p><table class='table table-bordered'> """
        regards = "Thanks & Regards,<br>hrPRO"
        table_html = ''
        emp = frappe.get_value("Employee",{'user_id':user.parent},['employee'])
        user_per = frappe.get_list("User Permission",{'user':user.parent,'allow':"Employee"},['for_value'])

        table_html += '<table class="table table-bordered" style="width:100% ; background-color:steelblue;color:white"><tr><td colspan = 4 style="border: 1px solid black">Expense Claim ID</td><td colspan = 4 style="border: 1px solid black">Employee Id</td><td colspan = 4 style="border: 1px solid black">Employee Name</td></tr>'         
        for user_per_list in user_per:
            if user_per_list.for_value != emp:
                expense_claim = frappe.get_list("Expense Claim", {'employee': user_per_list.for_value},['*'])
                
                
                for exp in expense_claim: 
                    if exp.workflow_state == "Pending for Finance":
                        frappe.log_error (exp.workflow_state)
                        table_html += '<tr><td colspan = 4 style="border: 1px solid black">%s</td><td colspan = 4 style="border: 1px solid black">%s</td><td colspan = 4 style="border: 1px solid black">%s</td><td colspan = 4 style="border: 1px solid black">%s</td><td colspan = 4 style="border: 1px solid black">%s</td><td colspan = 4 style="border: 1px solid black">%s</td></tr>'%(exp.name, exp.employee, exp.employee_name)
        
            # else:
            #     table_html += '<tr><td colspan = 24 style="border: 1px solid black">No Pending for Finance in Expense Claim </td></tr>'

        table_html += '</table><br>'
        frappe.sendmail(
            recipients=[user.parent],
            subject='Reg.List of pending Approvals',
            message=header+table_html+regards)


@frappe.whitelist()
def get_appraisal_kra(employee):
    emp = frappe.get_doc("Appraisal Template",{'employee':employee})
    
    return emp.goals
    


# if any changes in employee promotion appraisal child table that will reflect on appraisal template document child table 

@frappe.whitelist()
def update_appraisal_template(doc, method):
    child_table_values = []
    for child in doc.goals:
        child_table_values.append({
            "kra":child.kra,
            "req_output":child.req_output,
            "min_output":child.min_output,
            "per_weightage":child.per_weightage
        })
        appraisal_template = frappe.get_doc("Appraisal Template", {'employee':doc.employee},['*'])
        for i, child in enumerate(appraisal_template.goals):
            if i < len(child_table_values):
                child.kra = child_table_values[i]["kra"]
                child.req_output = child_table_values[i]["req_output"]
                child.min_output = child_table_values[i]["min_output"]
                child.per_weightage = child_table_values[i]["per_weightage"]

    appraisal_template.save()



@frappe.whitelist()
def appraisal_remainder_mail():
    role_name = "HOD"
    user_list = frappe.get_list("Has Role", fields=["parent"], filters={"role": role_name})
    for user in user_list:
        # print(user.parent)
        header = """<p>Dear Sir/Mam, <br> Please find the below list of Application pending for your Approval.</p><table class='table table-bordered'> """
        regards = "Thanks & Regards,<br>hrPRO"
        # table_html = ''
        emp = frappe.get_value("Employee",{'user_id':user.parent},['employee'])
        user_per = frappe.get_list("User Permission",{'user':user.parent,'allow':"Employee"},['for_value'])
    
        # table_html += '<table class="table table-bordered" style="width:100% ; background-color:steelblue;color:white"><tr><td colspan = 4 style="border: 1px solid black">Leave Application ID</td><td colspan = 4 style="border: 1px solid black">Employee Id</td><td colspan = 4 style="border: 1px solid black">Employee Name</td><td colspan = 4 style="border: 1px solid black">From Date</td><td colspan = 4 style="border: 1px solid black">To Date</td><td colspan = 4 style="border: 1px solid black">Leave Type</td></tr>'         
        for user_per_list in user_per:
            if user_per_list.for_value != emp:
                emp = frappe.get_list("Employee", {'employee': user_per_list.for_value},['*'])
                for emplo in emp:
                    if emplo.employment_type == "Full Time":
                        # print(emplo.employment_type)
                        emp_doj = frappe.get_list('Employee' ,{'employee': emplo},["date_of_joining"])
                        print(emp_doj)

                        # table_html += '<tr><td colspan = 4 style="border: 1px solid black">%s</td><td colspan = 4 style="border: 1px solid black">%s</td><td colspan = 4 style="border: 1px solid black">%s</td><td colspan = 4 style="border: 1px solid black">%s</td><td colspan = 4 style="border: 1px solid black">%s</td><td colspan = 4 style="border: 1px solid black">%s</td></tr>'%(leave.name, leave.employee, leave.employee_name, leave.from_date, leave.to_date,leave.leave_type)
                        # table_html += '</table><br>
        

# # for getting stock entry name in quotation,so
# @frappe.whitelist()
# def get_stock_entry_name(doc,method):
#     if doc.linked_quotation:
#         frappe.db.set_value("Quotation",doc.linked_quotation,"stock_entry",doc.name)
#     if doc.linked_sales_order:
#         frappe.db.set_value("Sales Order",doc.linked_sales_order,"stock_entry",doc.name)

# # for cancel stock entry name in quotation,so
# @frappe.whitelist()
# def cancel_stock_entry_name(doc,method):
#     if doc.linked_quotation:
#         frappe.db.set_value("Quotation",doc.linked_quotation,"stock_entry","")
#     if doc.linked_sales_order:
#         frappe.db.set_value("Sales Order",doc.linked_sales_order,"stock_entry","")


# maill trigger for re_allocation_date and document cancellationquote
@frappe.whitelist()
def check_se_and_send_mail_quote():
    stock_entry = frappe.db.sql("""select name,posting_date,re_posting_date,owner from `tabStock Entry` where linked_quotation != '' and docstatus = '1' """,as_dict=1)
    for s in stock_entry:
        diff_date = date.today() - s.posting_date
        diff_date_of_re_allocatiom = s.re_posting_date - s.posting_date
        if s.re_posting_date:
            if diff_date_of_re_allocatiom.days == 16:
                s_entry = frappe.get_doc("Stock Entry",s.name)
                s_entry.cancel()
                frappe.db.commit()
        else:
            if diff_date.days == 15:
                frappe.sendmail(
                    recipients = s.owner,
                    subject = 'Stock Entry- %s will be expired on tomorrow' %(s.name),
                    message = """Click the link of the document https://erp.nordencommunication.com/app/stock-entry/%s """ %(s.name)
                    )
            if diff_date.days == 16:
                s_entry = frappe.get_doc("Stock Entry",s.name)
                s_entry.cancel()
                frappe.db.commit()


# maill trigger for re_allocation_date and document cancellation sale_order
@frappe.whitelist()
def check_se_and_send_mail_linked_sales_order():
    stock_entry = frappe.db.sql("""select name,posting_date,re_posting_date,owner from `tabStock Entry` where linked_sales_order != '' and docstatus = '1' """,as_dict=1)
    for s in stock_entry:
        diff_date = date.today() - s.posting_date
        diff_date_of_re_allocatiom = s.re_posting_date - s.posting_date
        if s.re_posting_date:
            if diff_date_of_re_allocatiom.days == 16:
                s_entry = frappe.get_doc("Stock Entry",s.name)
                s_entry.cancel()
                frappe.db.commit()
        else:
            if diff_date.days == 15:
                frappe.sendmail(
                    recipients = s.owner,
                    subject = 'Stock Entry- %s will be expired on tomorrow' %(s.name),
                    message = """Click the link of the document https://erp.nordencommunication.com/app/stock-entry/%s """ %(s.name)
                    )
            if diff_date.days == 16:
                s_entry = frappe.get_doc("Stock Entry",s.name)
                s_entry.cancel()
                frappe.db.commit()
            


            
# re_allocation_date button function in stock entry
# @frappe.whitelist()
# def re_allocation_date(name,posting_date):
# 	re_posting_date = datetime.strptime(posting_date, "%Y-%m-%d")
# 	date_calc = re_posting_date + timedelta(days=15)
# 	final_date = date_calc.strftime('%Y-%m-%d')
# 	frappe.db.set_value("Stock Entry",name,"re_posting_date",final_date)
# 	frappe.msgprint("Re allocation has been done for another 15 days")
 




# @frappe.whitelist()
# def get_all_quot(name):
# 	quot = frappe.get_doc("Quotation",name)
# 	return quot.items

# @frappe.whitelist()
# def get_all_so(name):
# 	so = frappe.get_doc("Sales Order",name)
# 	return so.items

@frappe.whitelist()
def allow_holiday_list_to_user(holiday_list, user):
    user_permission = frappe.get_doc({
        'doctype': 'User Permission',
        'user': user,
        'allow': 'Holiday List',
        'for_value': holiday_list,
    })
    user_permission.insert()

    frappe.db.commit()
    return user_permission.name

@frappe.whitelist()
def enqueue_checkin_bulk_upload_csv(filename):
    frappe.enqueue(
        item_price_bulk_upload_csv, # python function or a module path as string
        queue="long", # one of short, default, long
        timeout=36000, # pass timeout manually
        is_async=True, # if this is True, method is run in worker
        now=False, # if this is True, method is run directly (not in a worker) 
        job_name='Item Price Updated', # specify a job name
        enqueue_after_commit=False, # enqueue the job after the database commit is done at the end of the request
        filename=filename, # kwargs are passed to the method as arguments
    )    

def item_price_bulk_upload_csv(filename):
    from frappe.utils.file_manager import get_file
    _file = frappe.get_doc("File", {"file_name": filename})
    filepath = get_file(filename)
    ips = read_csv_content(filepath[1])
    no_item = []
    for ip in ips:
        if frappe.db.exists('Item Price', {'item_code': ip[0]}):
            if frappe.db.exists('Item Price', {'item_code': ip[0], 'price_list': "Cost Rate - NCMEF"}) and ip[2]:
                rate = frappe.get_doc('Item Price', {'item_code': ip[0], 'price_list': "Cost Rate - NCMEF"})
                print(rate.price_list_rate)
                rate.valid_from = '2024-01-01'
                rate.price_list_rate = ip[2]
                rate.save(ignore_permissions=True)
                frappe.db.commit() 

            if frappe.db.exists('Item Price', {'item_code': ip[0], 'price_list': "Landing - NCMEF"}) and ip[3]:
                rate = frappe.get_doc(
                    'Item Price', {'item_code': ip[0], 'price_list': "Landing - NCMEF"})
                print(rate.price_list_rate)
                rate.valid_from = '2024-01-01'
                rate.price_list_rate = ip[3]
                rate.save(ignore_permissions=True)
                frappe.db.commit() 

            if frappe.db.exists('Item Price', {'item_code': ip[0], 'price_list': "Incentive - NCMEF"}) and ip[4]:
                rate = frappe.get_doc('Item Price', {'item_code': ip[0], 'price_list': "Incentive - NCMEF"})
                print(rate.price_list_rate)
                rate.valid_from = '2024-01-01'
                rate.price_list_rate = ip[4]
                rate.save(ignore_permissions=True)
                frappe.db.commit() 

            if frappe.db.exists('Item Price', {'item_code': ip[0], 'price_list': "Internal - NCMEF"}) and ip[5]:
                rate = frappe.get_doc('Item Price', {'item_code': ip[0], 'price_list': "Internal - NCMEF"})
                print(rate.price_list_rate)
                rate.valid_from = '2024-01-01'
                rate.price_list_rate = ip[5]
                rate.save(ignore_permissions=True)
                frappe.db.commit() 

            if frappe.db.exists('Item Price', {'item_code': ip[0], 'price_list': "Base Sales Price - NCMEF"}) and ip[6]:
                rate = frappe.get_doc('Item Price', {'item_code': ip[0], 'price_list': "Base Sales Price - NCMEF"})
                print(rate.price_list_rate)
                rate.valid_from = '2024-01-01'
                rate.price_list_rate = ip[6]
                rate.save(ignore_permissions=True)
                frappe.db.commit() 

            if frappe.db.exists('Item Price', {'item_code': ip[0], 'price_list': "Retail - NCMEF"}) and ip[7]:
                rate = frappe.get_doc('Item Price', {'item_code': ip[0], 'price_list': "Retail - NCMEF"})
                print(rate.price_list_rate)
                rate.valid_from = '2024-01-01'
                rate.price_list_rate = ip[7]
                rate.save(ignore_permissions=True)
                frappe.db.commit() 

            if frappe.db.exists('Item Price', {'item_code': ip[0], 'price_list': "Dist. Price - NCMEF"}) and ip[8]:
                rate = frappe.get_doc('Item Price', {'item_code': ip[0], 'price_list': "Dist. Price - NCMEF"})
                print(rate.price_list_rate)
                rate.valid_from = '2024-01-01'
                rate.price_list_rate = ip[8]
                rate.save(ignore_permissions=True)
                frappe.db.commit() 

            if frappe.db.exists('Item Price', {'item_code': ip[0], 'price_list': "Electra Qatar - NCMEF"}) and ip[9]:
                rate = frappe.get_doc('Item Price', {'item_code': ip[0], 'price_list': "Electra Qatar - NCMEF"})
                print(rate.price_list_rate)
                rate.valid_from = '2024-01-01'
                rate.price_list_rate = ip[9]
                rate.save(ignore_permissions=True)
                frappe.db.commit() 

            if frappe.db.exists('Item Price', {'item_code': ip[0], 'price_list': "Project Group - NCMEF"}) and ip[10]:
                rate = frappe.get_doc('Item Price', {'item_code': ip[0], 'price_list': "Project Group - NCMEF"})
                print(rate.price_list_rate)
                rate.valid_from = '2024-01-01'
                rate.price_list_rate = ip[10]
                rate.save(ignore_permissions=True)
                frappe.db.commit() 

            if frappe.db.exists('Item Price', {'item_code': ip[0], 'price_list': "Saudi Dist. - NCMEF"}) and ip[11]:
                rate = frappe.get_doc('Item Price', {'item_code': ip[0], 'price_list': "Saudi Dist. - NCMEF"})
                print(rate.price_list_rate)
                rate.valid_from = '2024-01-01'
                rate.price_list_rate = ip[11]
                rate.save(ignore_permissions=True)
                frappe.db.commit() 
        else:
            no_item.append(ip[0])
        frappe.log_error(title="No Item",message=no_item)

@frappe.whitelist()
def update_sales_person():
    quo = frappe.db.get_all("Sales Order",{'docstatus':1},['name','sale_person'])
    for i in quo:
        if i.sale_person:
            sal = frappe.db.get_value("Sales Person",{'user_id':i.sale_person},['name'])
            frappe.db.set_value('Sales Order', i.name, 'sales_person_user',sal, update_modified=False)
            print(i)
            


@frappe.whitelist()
def notification():
    expense_claims = frappe.get_all(
        'Expense Claim',
        filters={'workflow_state':'Pending for HOD'},
        fields=['name', 'expense_approver']
    )
    # role_name = "HOD"
    # user_list = frappe.get_list("Has Role", fields=["parent"], filters={"role": role_name})
    for user in expense_claims:
        print(user.expense_approver)
        header = """<p>Dear Sir/Mam, <br> Please find the below list of Application pending for your Approval.</p><table class='table table-bordered'> """
        regards = "Thanks & Regards,<br>hrPRO"
        table_html = ''
        # emp = frappe.get_value("Employee",{'user_id':user.expense_spprover},['employee'])
        # print(emp)
        user_per = frappe.get_list("User Permission",{'user':user.expense_approver,'allow':"Employee"},['for_value'])
        print(user_per)

        table_html += '<table class="table table-bordered" style="width:100% ; background-color:steelblue;color:white"><tr><td colspan = 4 style="border: 1px solid black">Expense Claim ID</td><td colspan = 4 style="border: 1px solid black">Employee Id</td><td colspan = 4 style="border: 1px solid black">Employee Name</td></tr>'         
        for user_per_list in user_per:
            # if user_per_list.for_value != emp:
            expense = frappe.get_list("Expense Claim", {'employee': user_per_list.for_value},['*'])
            for leave in expense:
                if leave.workflow_state == "Pending for HOD":
                    print(leave.workflow_state)
                    table_html += '<tr><td colspan = 4 style="border: 1px solid black">%s</td><td colspan = 4 style="border: 1px solid black">%s</td><td colspan = 4 style="border: 1px solid black">%s</td></tr>'%(leave.name, leave.employee, leave.employee_name)
        
            
        table_html += '</table><br>'
        frappe.sendmail(
        recipients=['janisha.g@groupteampro.com'],
        subject='Reg.List of pending Approvals',
        message=header+table_html+regards)

# def create_hooks_report():
# 	# job = frappe.db.exists('Scheduled Job Type', 'daily_emc_report')
# 	# if not job:
# 	emc = frappe.new_doc("Scheduled Job Type")  
# 	emc.update({
# 		"method": 'norden.custom.notification',
# 		"frequency": 'Cron',
# 		"cron_format": ' 0 0 */2 * * *'
# 	})
# 	emc.save(ignore_permissions=True)


from frappe.utils import flt
from frappe.utils import flt
@frappe.whitelist()
def get_detail_so(item_code, company):
    date = frappe.db.get_value("Custom Settings", "Custom Settings", "date")
    so_details = []
    
    sa = frappe.db.sql("""
        SELECT `tabSales Order Item`.parent AS parent,
            SUM(`tabSales Order Item`.qty) AS qty,
            `tabSales Order Item`.delivered_qty AS delivered_qty
        FROM `tabSales Order`
        LEFT JOIN `tabSales Order Item` ON `tabSales Order`.name = `tabSales Order Item`.parent
        WHERE `tabSales Order Item`.item_code = '%s'
        AND `tabSales Order`.docstatus != 2
        AND `tabSales Order`.company = '%s'
        AND `tabSales Order`.status != 'Closed'            
        AND `tabSales Order`.transaction_date >= '%s'
        GROUP BY `tabSales Order Item`.parent
        ORDER BY `tabSales Order`.transaction_date
    """ % (item_code, company, date), as_dict=True)
    sa_names = {i.parent for i in sa}
    for i in sa:
        
        total_reserved_qty =0
        stock_entry = frappe.get_all("Stock Reservation Entry", {"company": company,"item_code":item_code,"voucher_no":i.parent,"status": ["in", ["Reserved", "Partially Reserved"]]}, ['reserved_qty'])      
        prq = frappe.db.sql("""select (reserved_qty - delivered_qty) as partially_delivered from `tabStock Reservation Entry`
                                where item_code = '%s' and company = '%s' and status = 'Partially Delivered' and voucher_no = '%s' """ % (item_code,company,i.parent), as_dict=True)
        
        for reser in stock_entry:
            frappe.errprint(reser.reserved_qty)
            total_reserved_qty += reser.reserved_qty
        for prq_ in prq:
            total_reserved_qty += flt(prq_['partially_delivered']) or 0

        i.qty = i.qty or 0
        i.delivered_qty = i.delivered_qty or 0
        pending_qty = i.qty - i.delivered_qty
        sb = frappe.get_doc("Sales Order", i.parent)
        if total_reserved_qty > 0 or pending_qty > 0:
            so_details.append(frappe._dict({
                "parent": i.parent,
                "qty": i.qty,
                "reserved_qty": total_reserved_qty,
                "pending_qty": pending_qty,
                "rate": i.rate,
                "delivered_qty": i.delivered_qty,
                "transaction_date": sb.transaction_date,
                "customer": sb.customer,
                "po_no": sb.po_no,
                "status": sb.custom_reservation_status
            }))
    
    additional_entries = frappe.db.sql("""
        SELECT 
            `tabStock Reservation Entry`.voucher_no AS voucher_no,
            `tabStock Reservation Entry`.reserved_qty,
            `tabSales Order`.transaction_date,
            `tabSales Order`.customer,
            `tabSales Order`.po_no,
            `tabSales Order`.custom_reservation_status   
        FROM `tabStock Reservation Entry`
        LEFT JOIN `tabSales Order` ON `tabSales Order`.name = `tabStock Reservation Entry`.voucher_no
        LEFT JOIN `tabSales Order Item` ON `tabSales Order Item`.parent = `tabSales Order`.name
        WHERE `tabStock Reservation Entry`.item_code = %s
        AND  `tabStock Reservation Entry`.status IN ('Reserved', 'Partially Reserved')
        AND (`tabSales Order Item`.item_code != %s OR `tabSales Order Item`.item_code IS NULL)
        AND (`tabSales Order`.name IS NULL 
            OR (`tabSales Order`.docstatus != 2 
                AND `tabSales Order`.company = %s 
                AND `tabSales Order`.transaction_date >= %s))
        GROUP BY `tabStock Reservation Entry`.voucher_no
        ORDER BY `tabStock Reservation Entry`.creation
    """, (item_code, item_code, company, date), as_dict=True)


    for entry in additional_entries:
        if entry.voucher_no not in sa_names:
            if entry.reserved_qty > 0:
                so_details.append(frappe._dict({
                    "parent": entry.voucher_no,
                    "qty": 0,  
                    "reserved_qty": entry.reserved_qty or 0,
                    "pending_qty": 0,  
                    "rate": 0,  
                    "delivered_qty": 0,
                    "transaction_date": entry.transaction_date, 
                    "customer": entry.customer, 
                    "po_no": entry.po_no, 
                    "status": entry.custom_reservation_status
                }))
    
    return so_details


    
    
@frappe.whitelist()
def get_detail_po(item_code,company):
    date = frappe.db.get_value("Custom Settings","Custom Settings","date")
    po_details = []
    bal_qty = 0
    # pending_qty = 0
    sa = frappe.db.sql(""" select `tabPurchase Order Item`.parent as parent,`tabPurchase Order Item`.qty as qty , `tabPurchase Order Item`.received_qty as received_qty from `tabPurchase Order`
    left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
    where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus = 1 and `tabPurchase Order`.company = '%s' and `tabPurchase Order`.transaction_date >= '%s'  order by transaction_date""" %(item_code,company,date),as_dict=True)
    for i in sa:
    # 	pending_qty = i.qty - i.delivered_qty
        pos = frappe.db.sql("""select sum(`tabPurchase Receipt Item`.received_qty) as received_qty from `tabPurchase Receipt`
        left join `tabPurchase Receipt Item` on `tabPurchase Receipt`.name = `tabPurchase Receipt Item`.parent
        where `tabPurchase Receipt Item`.item_code = '%s' and `tabPurchase Receipt Item`.purchase_order = '%s' and `tabPurchase Receipt`.company = '%s'  and `tabPurchase Receipt`.docstatus = 1 """ % (item_code,i.parent,company), as_dict=True)
        req=0
        req=i.received_qty
        po = frappe.db.get_value("Item Inspection",{"po_number":i.parent,"item_code":item_code},["sample"])
        if not po:
            po = 0
        if not req:
            req =0
        bal_qty = i.qty - req
        bal = 0
        if bal_qty >0:
            bal = bal_qty
        sb = frappe.get_doc("Purchase Order", i.parent)
        po_details.append(frappe._dict({"mr":req,"qc":po,"parent":i.parent,"qty":i.qty,"bal_qty":bal,"transaction_date":sb.transaction_date,"supplier":sb.supplier}))
    return po_details

@frappe.whitelist()
def gt_detail_po():
    item_code = "124-16101WH"
    company = "Norden Communication Middle East FZE"
    po_details = []
    bal_qty = 0
    sa = frappe.db.sql(""" select `tabPurchase Order Item`.parent as parent,`tabPurchase Order Item`.qty as qty from `tabPurchase Order`
    left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
    where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 and `tabPurchase Order`.company = '%s'""" %(item_code,company),as_dict=True)
    for i in sa:
        print(i)

@frappe.whitelist()
def get_item_price_dt(item_code):
    # item_code = "114-40002104GY"
    use = frappe.session.user
    role = frappe.get_roles(use)
    data = []
    row = []
    user = frappe.get_all("User Permission",{"user":use,"allow":"Price List"},["*"])
    item = frappe.get_all("Item",{"name":item_code},["*"])
    for i in item:
        if "Cost Viewer" in role:
            std = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"STANDARD BUYING-USD"},["price_list_rate"])
            if std:
                row.append(frappe._dict({"price_list":"STANDARD BUYING-USD","price_list_rate":std}))
            if not std:
                std = 0
                row.append(frappe._dict({"price_list":"STANDARD BUYING-USD","price_list_rate":std}))
        for s in user:
            item = frappe.db.sql(""" select price_list_rate from `tabItem Price` where price_list = '%s' and item_code = '%s' """%(s.for_value,i.item_code),as_dict=True)
            if item:
                row.append(frappe._dict({"price_list":s.for_value,"price_list_rate":item[0]["price_list_rate"]}))
        data.append(row)
    return data	


@frappe.whitelist()
def return_conversion(currency,price_list_currency):
    conv_rate = get_exchange_rate(currency, price_list_currency)
    return conv_rate


@frappe.whitelist()
def internship_end_date():
    from frappe.utils import today, add_months, getdate
    from datetime import timedelta
    count = 0
    data = ''
    employee = frappe.get_all('Employee', {'status': 'Active', 'employment_type': 'Intern','company':'Norden Communication Middle East FZE'}, [
                              'name', 'employee_name', 'department', 'date_of_joining'])
    data += 'Dear Sir,<br>Kindly Find the List of Employees going to complete their Training<br><table class="table table-bordered">'
    data += '<table class="table table-bordered"><tr><th>Employee ID</th><th>Employee Name</th><th>Department</th><th>Training End Date</th></tr>'
    
    for emp in employee:
        end_date = add_months(emp.date_of_joining,6)
        reminder_date = add_months(end_date, -2)
        if (reminder_date <= getdate(today())):
            if (end_date >= getdate(today())):
                count += 1
                data += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (emp.name, emp.employee_name, emp.department, format_date(emp.internship_end_date))
    data += '</table>'
    if count > 0:
        frappe.sendmail(
            # recipients=['sahayasterwin17@gmail.com','sahayasterwin.a@groupteampro.com'],
            subject=('Internship End Date'),
            header=('Internship End Date'),
            message=data
        )


@frappe.whitelist()
def calc_trainee_period(joining_date):
    joining_date = (datetime.strptime(joining_date, '%Y-%m-%d')).date()
    pb_end_date = add_months(joining_date, 6)
    return pb_end_date


@frappe.whitelist()
def date_of_joining():
    from frappe.utils import today, add_months, getdate
    from datetime import timedelta
    data = ''
    employee = frappe.get_all('Employee', {'status': 'Active', 'employment_type': 'Full-time','company':'Norden Communication Middle East FZE'}, ['name', 'employee_name', 'department', 'date_of_joining'])
    data += 'Dear Sir/Madam,<br>Kindly Find the List of Employees going to complete their One Year So Annual Leave Allocation<br><table class="table table-bordered">'
    data += '<table class="table table-bordered"><tr><th>Employee ID</th><th>Employee Name</th><th>Department</th><th>Annual Leave</th></tr>'
    count = 0
    for emp in employee:
        one_year = add_months(emp.date_of_joining,12)
        reminder_date = add_months(one_year, -2)
        if (reminder_date <= getdate(today())):
            if (one_year >= getdate(today())):
                count += 1
                data += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
                emp.name, emp.employee_name, emp.department, format_date(emp.date_of_joining))
                print(emp.date_of_joining)
    data += '</table>'
    if count > 0:
        frappe.sendmail(
            # recipients=['sahayasterwin17@gmail.com','sahayasterwin.a@groupteampro.com'],
            subject=('Annual Leave Allocation'),
            header=('Annual Leave Allocation'),
            message=data
        )

@frappe.whitelist()
def get_order_qty(po_no):
    purchase_order = frappe.get_doc("Purchase Order",po_no)
    return purchase_order.items

@frappe.whitelist()
def get_salesorder_qty(so_no):
    sales_order = frappe.get_doc("Sales Order", so_no)
    return [
        {
            "name": d.name,        # row name
            "item_code": d.item_code,
            "qty": d.qty
        }
        for d in sales_order.items
    ]



@frappe.whitelist()
def get_po_qty(item,company):
    new_po = frappe.db.sql("""select sum(`tabPurchase Order Item`.qty) as qty,sum(`tabPurchase Order Item`.received_qty) as d_qty from `tabPurchase Order` left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus = 1 and `tabPurchase Order`.company = '%s' and `tabPurchase Order Item`.qty >= `tabPurchase Order Item`.received_qty """ % (item,company), as_dict=True)[0]
    if not new_po['qty']:
        new_po['qty'] = 0
    if not new_po['d_qty']:
        new_po['d_qty'] = 0
    ppoc_total = new_po['qty'] - new_po['d_qty']
    return ppoc_total


import frappe
from frappe.utils import today

@frappe.whitelist()
def update_marcom(doc,method):
    si = frappe.get_doc("Sales Order",{'name':doc.name})
    marcom_reference = frappe.new_doc("MARCOM  Project Reference")
    if si.project_name:
        marcom_reference.project_name = si.project_name
        marcom_reference.customer_contractor = si.customer
        marcom_reference.sales_invoice = si.name
        marcom_reference.consultant_company = si.consultant_company
        marcom_reference.consultant_name = si.consultant_name
        marcom_reference.company = si.company
        marcom_reference.sales_person_name = si.sales_person_user
        marcom_reference.so_submitted_date = today()
        marcom_reference.so_status_live = si.status
        marcom_reference.end_client_user_name = si.end_client_user_name
        marcom_reference.end_client_user_industry = si.end_client__user_industry
        marcom_reference.custom_territory = si.territory
        marcom_reference.custom_cluster = si.cluster
        marcom_reference.custom_total_qty = si.total_qty
        marcom_reference.custom_price_list_region = si.price_list_region
        for item in si.items:
            marcom_reference.append('items_table', {
                'items_name': item.item_name,
                'qty': item.qty,
                'item_group': item.item_group
            })
        marcom_reference.save(ignore_permissions=True)
        frappe.db.commit()
        print("MARCOM Project References created successfully.")
    
# @frappe.whitelist()
# def get_serial_no_details(serial_no):
# # def get_serial_no_details():
# # 	serial_no = "EN-210235U29E322C000006"
# 	sl = '%'+serial_no+'%'
# 	data = ''
# 	data += '<table  border= 1px solid black width = 100%>'
    
# 	pos = frappe.db.sql("""select `tabDelivery Note Item`.item_code as item_code,`tabDelivery Note Item`.against_sales_order as sales_order,`tabDelivery Note Item`.parent as parent,`tabDelivery Note Item`.warranty_terms as warranty_terms from `tabDelivery Note`
# 	left join `tabDelivery Note Item` on `tabDelivery Note`.name = `tabDelivery Note Item`.parent
# 	where `tabDelivery Note Item`.serial_no like '%s' and `tabDelivery Note`.docstatus != 2 """ % (sl), as_dict=True)
# 	if pos:
# 		for i in pos:
# 			if not i.warranty_terms:
# 				i.warranty_terms = "Not Disclosed"
# 			data += '<tr style = "background-color:#D9E2ED"><td colspan =2 style = "text-align:center"><b>Item Code</b></td><td style = "text-align:center"><b>Delivery Note</b></td><td colspan =2 style = "text-align:center"><b>Sales Invoice</b></td><td colspan =2 style = "text-align:center"><b>Delivery Date</b></td><td colspan =2 style = "text-align:center"><b>Invoiced Date</b></td><td colspan =2 style = "text-align:center"><b>Warranty Terms</b></td></tr>'
# 			date = frappe.db.get_value("Delivery Note",i.parent,'posting_date')
# 			si = frappe.db.sql("""select parent from `tabSales Invoice Item` where delivery_note = '%s' """%(i.parent),as_dict=1)[0]
# 			si_date = frappe.db.get_value("Sales Invoice",si['parent'],'posting_date')
# 			data += '<tr><td colspan =2 style = "text-align:center"><b>%s</b></td><td style="border: 1px solid black;font-weight:bold"><center><a href="https://erp.nordencommunication.com/app/delivery-note/%s">%s</a></center></td><td style="border: 1px solid black;font-weight:bold"><center><a href="https://erp.nordencommunication.com/app/sales-invoice/%s">%s</a></center></td><td colspan =2 style = "text-align:center"><b>%s</b></td><td colspan =2 style = "text-align:center"><b>%s</b></td><td colspan =2 style = "text-align:center"><b>%s</b></td></tr>'%(i.item_code,i.parent,i.parent,si['parent'],si['parent'],format_date(date),format_date(si_date),i.warranty_terms or '')
# 	else:
# 		data += '<tr style = "background-color:#D9E2ED"><td colspan =8 style = "text-align:center"><b>Not Delivered Yet</b></td></tr>'
    
# 	data += '</table>' 
# 	return data

@frappe.whitelist()
def get_sls():
    si = frappe.db.sql("""select parent from `tabSales Invoice Item` where delivery_note = 'DN-NCPLP-2023-00078' """,as_dict=1)[0]
    print(sl['parent'])


@frappe.whitelist()
def reminder_mail(message,email):
    frappe.sendmail(
        recipients=[email],
        message=message,
        subject=_("Reminder Mail"),
    )

@frappe.whitelist()
def margin_tool():
    cnt = 0
    doc = frappe.get_doc("Margin Price Tool")
    for row in doc.cambodia:
        count = 0
        items = frappe.get_all('Item',{'item_sub_group':row.item_group})
        for i in items:
            factory_price = frappe.db.get_value('Item Price',{'price_list':'STANDARD BUYING-USD','item_code':i.name},'price_list_rate')
            if factory_price:
                if row.internal_cost and row.internal_cost > 0:
                    existing_ip = frappe.db.exists('Item Price',{'price_list':'Cambodia Internal Cost','item_code':i.name})
                    if existing_ip:
                    # rate = factory_price * row.internal_cost
                    # print(rate)
                        count += 1
        cnt += count
    print(cnt)



@frappe.whitelist()
def set_val():
    sales_invoice = "SI-NCMEF-2023-00074"
    si_name = frappe.get_doc("Sales Invoice",sales_invoice)
    for s in si_name.items:
        sales = s.sales_order
        so_name = frappe.get_doc("Sales Order",sales)
        for si in so_name.items:
            quote = si.prevdoc_docname
    print(sales_invoice)
    print(sales)
    print(quote)
    quote_update = frappe.get_doc("Quotation",quote)
    for quo in quote_update.items:
        disc_amt = quo.discount_rate * quo.qty
    # 	# frappe.db.set_value("Sales Order Item", {"parent":i.parent,"item_code":k.item_code}, 'unit_price_document_currency', k.unit_price_document_currency)
    # 	# frappe.db.set_value("Sales Order Item", {"parent":i.parent,"item_code":k.item_code}, 'discount_value', k.discount_value)
        frappe.db.set_value("Quotation Item", {"parent":quote,"item_code":quo.item_code}, 'disc_amt', disc_amt)
    # 	# frappe.db.set_value("Sales Order Item", {"parent":i.parent,"item_code":k.item_code}, 'disc_amt', disc_amt)

    sale = frappe.get_doc("Sales Order",sales)
    for sa in sale.items:
        quot = frappe.get_doc("Quotation",sa.prevdoc_docname)
        for qu in quot.items:
            if sa.item_code == qu.item_code:
                frappe.db.set_value("Sales Order Item", {"parent":sales,"item_code":qu.item_code}, 'discount_value', qu.discount_value)
                frappe.db.set_value("Sales Order Item", {"parent":sales,"item_code":qu.item_code}, 'disc_amt', qu.disc_amt)
                frappe.db.set_value("Sales Order Item", {"parent":sales,"item_code":qu.item_code}, 'unit_price_document_currency', qu.unit_price_document_currency)

    sale_in = frappe.get_doc("Sales Invoice",sales_invoice)
    for sin in sale_in.items:
        so_ord = frappe.get_doc("Sales Order",sin.sales_order)
        for sd in so_ord.items:
            if sin.item_code == sd.item_code:
                frappe.db.set_value("Sales Invoice Item", {"parent":sales_invoice,"item_code":sd.item_code}, 'unit_price_document_currency', sd.unit_price_document_currency)
                frappe.db.set_value("Sales Invoice Item", {"parent":sales_invoice,"item_code":sd.item_code}, 'discount_value', sd.discount_value)
                frappe.db.set_value("Sales Invoice Item", {"parent":sales_invoice,"item_code":sd.item_code}, 'disc_amt', sd.disc_amt)

@frappe.whitelist()
def so_set_val():
    doc = frappe.get_doc("Sales Order","SO-NSPL-2023-00012")
    for i in doc.items:
        so = frappe.get_doc("Quotation",i.prevdoc_docname)
        for k in so.items:
            if i.item_code == k.item_code:
                disc_amt = k.discount_rate * k.qty
                print(k.item_code)
                print(k.unit_price_document_currency)
                frappe.db.set_value("Sales Order Item", {"parent":i.parent,"item_code":k.item_code}, 'discount_value', k.discount_value)
                frappe.db.set_value("Sales Order Item", {"parent":i.parent,"item_code":k.item_code}, 'disc_amt', disc_amt)
                frappe.db.set_value("Sales Order Item", {"parent":i.parent,"item_code":k.item_code}, 'unit_price_document_currency', k.unit_price_document_currency)
@frappe.whitelist()
def qo_set_val():
    so = frappe.get_doc("Quotation","F-Q-NSPL-2023-00051")
    for k in so.items:
        disc_amt = k.discount_rate * k.qty
        # frappe.db.set_value("Sales Order Item", {"parent":i.parent,"item_code":k.item_code}, 'unit_price_document_currency', k.unit_price_document_currency)
        # frappe.db.set_value("Sales Order Item", {"parent":i.parent,"item_code":k.item_code}, 'discount_value', k.discount_value)
        frappe.db.set_value("Quotation Item", {"parent":"F-Q-NSPL-2023-00051","item_code":k.item_code}, 'disc_amt', disc_amt)
        # frappe.db.set_value("Sales Order Item", {"parent":i.parent,"item_code":k.item_code}, 'disc_amt', disc_amt)



@frappe.whitelist()
def cancel_doc_je():
    doc = frappe.get_doc("Journal Entry","JE-NSPL-2022-00008")
    doc.cancel(ignore_mandatory=True)
    print(doc)

@frappe.whitelist()
def cal_val_rate():
    from erpnext.stock.stock_ledger import get_valuation_rate
    val = get_valuation_rate("127-32105BL","Norden Communication Pvt Ltd","Stock Entry","SE")
    print(val)

# @frappe.whitelist()
# def get_designation(designation):
# 	des = designation
# 	vac = no_of_position
# 	return des,vac

# @frappe.whitelist()
# def return_date():
# 	nam = ["F-Q-NCME-2023-01357-2","F-Q-NCME-2022-01712-1","F-Q-NCME-2023-03291","F-Q-NCME-2023-02939","F-Q-NCME-2022-01758","F-Q-NCME-2023-01245-1","F-Q-NCME-2023-00317","F-Q-NCME-2023-00892","F-Q-NCME-2023-00958-2","F-Q-NCME-2023-00634","F-Q-NCME-2023-01095","F-Q-NCME-2023-00991","F-Q-NCME-2023-01226-1","F-Q-NCME-2023-01314","F-Q-NCME-2023-01423-1","F-Q-NCME-2023-01495","F-Q-NCME-2023-01071","F-Q-NCME-2023-01196","F-Q-NCME-2023-01210","F-Q-NCME-2023-01447","F-Q-NCME-2023-01475","F-Q-NCME-2023-03291","F-Q-NCME-2023-00317","F-Q-NCME-2023-02382-1","F-Q-NCME-2023-02068-1","F-Q-NCME-2022-02300","F-Q-NCME-2023-00402","F-Q-NCME-2023-01180","F-Q-NCME-2023-01186","F-Q-NCME-2023-01776-2","F-Q-NCME-2023-01742","F-Q-NCME-2023-00626","F-Q-NCME-2022-02447","F-Q-NCME-2023-00542","F-Q-NCME-2023-00820","F-Q-NCME-2023-01336-1","F-Q-NCME-2023-01870-1","F-Q-NCME-2023-01722","F-Q-NCME-2023-01989-1","F-Q-NCME-2023-02441","F-Q-NCME-2023-02445","F-Q-NCME-2022-01607"]
# 	for i in nam:
# 		date = frappe.db.sql(""" update  `tabQuotation` set valid_till = "2023-08-31" where name = '%s' """%(i),as_dict=1)
# 	print(date)

@frappe.whitelist()
def get_item_group():
    item_group = frappe.db.sql("""select (sum(`tabBin`.actual_qty) - sum(reserved_stock)) as actual_qt from `tabBin` left join `tabItem` where `tabItem`.item_sub_group = %s """ % ("Telephone Cables"), as_dict=True)
    print(item_group)

@frappe.whitelist()
def get_available_batches():
        acct_parts = i.name.split(' - ')
        if len(acct_parts) == 3:
            acc = acct_parts[0] +' '+ acct_parts[1]
        # elif len(acct_parts) == 3:
            # acc = acct_parts[1]
        # else:
        # 	acc = None
            print(acc)

@frappe.whitelist()
def time_difference(to_time,from_time):
    value = time_diff(to_time,from_time)
    val = value.total_seconds() / 60
    total_hours = int(val // 60)
    remaining_minutes = int(val % 60)
    return f"{total_hours} hours {remaining_minutes} minutes"

@frappe.whitelist()
def minutes_calculate(to_time,from_time,amount,over_time):
    value = time_diff(to_time,from_time)
    val = value.total_seconds() / 60
    total_value=float(over_time)/60
    total_amount =float(total_value) * val
    return round(total_amount,2)
    
@frappe.whitelist()
def remove():
    value = frappe.db.get_list("Purchase Order", {"docstatus": ("!=", 2)}, ["name", "our_trn"])
    for i in value:
        if i.our_trn:
            frappe.db.set_value("Purchase Order",i.name,"order_confirmation_no",i.our_trn)

@frappe.whitelist()
def delivery_note():
    value = frappe.db.get_list("Sales Invoice",{"docstatus":("!=",2)},["name"])
    for i in value:
        print(i.name)
        doc = frappe.get_doc("Sales Invoice",i.name)
        for j in doc.items:
            print(j.delivery_note)
            frappe.db.set_value("Delivery Note",j.delivery_note,"invoice_number",i.name)

@frappe.whitelist()
def update_invoice_number(doc,method):
    for j in doc.items:
        frappe.db.set_value("Delivery Note",j.delivery_note,"invoice_number",doc.name)

        
@frappe.whitelist()
def return_total_amt(doc,sales_order_number):
    sale = frappe.get_doc("Sales Order",sales_order_number)
    total = 0
    amt = 0
    tax_rate = 0
    for i in doc.sales_order_details:
        amt += i.amount
    for j in sale.taxes:
        tax_rate = amt * (j.rate/100)
    total = amt + tax_rate
    return round(amt,2),round(tax_rate,2),round(total,2)

@frappe.whitelist()
def purchase_receipt_item(purchase_receipt):
    childtab = frappe.db.sql(""" select `tabPurchase Receipt Item`.item_code,
    `tabPurchase Receipt Item`.item_name,
    `tabPurchase Receipt Item`.description,
    `tabPurchase Receipt Item`.item_group,
    `tabPurchase Receipt Item`.uom,
    `tabPurchase Receipt Item`.received_stock_qty,
    `tabPurchase Receipt Item`.stock_qty,
    `tabPurchase Receipt Item`.conversion_factor,
    `tabPurchase Receipt Item`.stock_uom_rate,
    `tabPurchase Receipt Item`.warehouse,
     `tabPurchase Receipt Item`.item_inspection,
    `tabPurchase Receipt Item`.rejected_warehouse,
    `tabPurchase Receipt Item`.material_request,
    `tabPurchase Receipt Item`.alpha_series,
     `tabPurchase Receipt Item`.starting_s_no,
       GROUP_CONCAT(`tabPurchase Receipt Item`.rejected_serial_no  separator '\n') as rejected_serial_no,
    `tabPurchase Receipt Item`.manufacturer,
       `tabPurchase Receipt Item`.manufacturer_part_no,
    `tabPurchase Receipt Item`.weight_uom,
    `tabPurchase Receipt Item`.provisional_expense_account,
    `tabPurchase Receipt Item`.project,
    `tabPurchase Receipt Item`.schedule_date,
    `tabPurchase Receipt Item`.purchase_order,
    `tabPurchase Receipt Item`.expense_account,
    `tabPurchase Receipt Item`.cost_center,
    `tabPurchase Receipt Item`.price_list_rate,
    `tabPurchase Receipt Item`.base_price_list_rate,
    `tabPurchase Receipt Item`.discount_percentage,
    `tabPurchase Receipt Item`.discount_amount,
    `tabPurchase Receipt Item`.landed_cost_voucher_amount,
    `tabPurchase Receipt Item`.weight_per_unit,
    `tabPurchase Receipt Item`.rate,
    `tabPurchase Receipt Item`.base_rate,
    `tabPurchase Receipt Item`.base_amount,
    `tabPurchase Receipt Item`.net_rate,
    `tabPurchase Receipt Item`.base_net_rate,
    `tabPurchase Receipt Item`.base_net_amount,
    `tabPurchase Receipt Item`.total_weight,
     GROUP_CONCAT(`tabPurchase Receipt Item`.serial_no  separator '\n') as serial_no,
    sum(`tabPurchase Receipt Item`.received_qty) as received_qty,
    sum(`tabPurchase Receipt Item`.qty) as qty,
    sum(`tabPurchase Receipt Item`.ordered) as ordered,
    sum(`tabPurchase Receipt Item`.balance) as balance,
    sum(`tabPurchase Receipt Item`.rejected_qty)as rejected_qty,
    sum(`tabPurchase Receipt Item`.billed_amt)as billed_amt,
    sum(`tabPurchase Receipt Item`.amount) as amount from `tabPurchase Receipt` left join `tabPurchase Receipt Item` on `tabPurchase Receipt`.name = `tabPurchase Receipt Item`.parent where `tabPurchase Receipt`.name = '%s' group by `tabPurchase Receipt Item`.item_code"""%(purchase_receipt),as_dict = 1)
    return childtab

@frappe.whitelist()
def pay_entry(type):
    if type=="Payable":
        pay= frappe.db.get_list("Payment Entry",{"pdc_i":1,"pdc_completed":0},["name","reference_date","reference_no","paid_amount","posting_date","paid_from"])
    else:
        pay= frappe.db.get_list("Payment Entry",{"pdc_r":1,"pdc_completed":0},["name","reference_date","reference_no","paid_amount","posting_date","paid_to"])
    return pay

@frappe.whitelist() 
def create_journal_entry(type,payment_entry,date):
    if type=="Payable":
        pay=frappe.get_doc("Payment Entry",payment_entry)
        je = frappe.new_doc("Journal Entry")
        je.company = pay.company
        je.posting_date = date
        je.voucher_type = "Journal Entry"
        je.pay_to_recd_from = pay.party
        dict_list = []
        dict_list.append(frappe._dict({"account":pay.paid_from,"debit": pay.paid_amount,"credit": 0}))
        dict_list.append(frappe._dict({"account": "Rakbank (The National Bank of Ras Al Khaimah) - NCME","debit": 0,"credit": pay.paid_amount}))
        for i in dict_list:
           
            je.append('accounts', {
                'account': i.account,
                'debit_in_account_currency':i.debit,
                'credit_in_account_currency':i.credit
            })
        je.save(ignore_permissions=True)
        frappe.db.set_value("Payment Entry",pay.name,"pdc_completed",1)
        return je.name
    else:
        pay=frappe.get_doc("Payment Entry",payment_entry)
        je = frappe.new_doc("Journal Entry")
        je.company = pay.company
        je.posting_date = date
        je.voucher_type = "Journal Entry"
        je.pay_to_recd_from = pay.party
        dict_list = []
        dict_list.append(frappe._dict({"account":pay.paid_to,"debit": 0,"credit": pay.paid_amount}))
        dict_list.append(frappe._dict({"account": "Rakbank (The National Bank of Ras Al Khaimah) - NCME","debit": pay.paid_amount,"credit":0}))
        for i in dict_list:
           
            je.append('accounts', {
                'account': i.account,
                'debit_in_account_currency':i.debit,
                'credit_in_account_currency':i.credit
            })
        je.save(ignore_permissions=True)
        frappe.db.set_value("Payment Entry",pay.name,"pdc_completed",1)
        return je.name

@frappe.whitelist()
def amount_calculate(total_amount):
    value=total_amount
    amount = int(value) * 12
    val = int(amount) / 365
    amt =float(val)
    cal = float(amt) / 9
    overtime = round(cal,2)
    return overtime



# @frappe.whitelist()
# def get_stock_details(doc):
#     item_details = doc.items
#     data = ''
#     data += '<h4><center><b>PICKING LIST</b></center></h4>'
#     data += '<table class="table table-bordered">'
#     data += '<tr>'
#     data += '<td colspan=3 style="width:13%;padding:1px;border:1px solid black;font-size:14px;background-color:#e20026;color:white;text-align:center">PRODUCT</td>'
#     data += '<td colspan=3 style="width:70px;padding:1px;border:1px solid black;font-size:14px;background-color:#e20026;color:white;text-align:center">DESCRIPTION</td>'
#     data += '<td colspan=3 style="width:70px;padding:1px;border:1px solid black;font-size:14px;background-color:#e20026;color:white;text-align:center">QTY</td>'
#     data += '<td colspan=3 style="width:70px;padding:1px;border:1px solid black;font-size:14px;background-color:#e20026;color:white;text-align:center">WAREHOUSE</td></tr>'
    
#     for j in item_details:
#         del_note = frappe.db.get_all("Delivery Note", {"file_number": doc.file_number,"docstatus":("!=",2)}, ['*'])
#         if del_note:
#             del_qty = 0
#             for i in del_note:
#                 deli_note = frappe.get_doc("Delivery Note", i.name)
#                 if deli_note.items:
#                     for item in deli_note.items:
#                         if j.item_code == item.item_code:
#                             del_qty += item.qty 
#         # reser_qty = frappe.db.get_value("Stock Reservation Entry",{"voucher_no":doc.name,"item_code":j.item_code,"docstatus":("!=",2)},["reserved_qty"])
#         # if reser_qty:
#             warehouse = []
#             st = 0
#             reser=0
#             ware = frappe.db.get_list("Warehouse", {"company": doc.company}, ['name'])
#             bin_location = None
#             for w in ware:
#                 sto = frappe.get_all("Bin", {"item_code": j.item_code, "warehouse": w.name}, ['actual_qty','reserved_qty'])
#                 for qty in sto:
#                     st+=qty.actual_qty
#                     reser+=qty.reserved_qty
#                     warehouse.append(w.name)
#                     value = st-reser
#             data += '<tr><td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' % (j.item_code)
#             data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' % (j.description)
#             if value > j.qty:
#                 data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' % (j.qty)
#             else:
#                 data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' % (j.qty-value)
#             if warehouse:
#                 data += '<td style="text-align:center;border: 1px solid black" colspan=3>%s</td>' %(', '.join(map(str, warehouse)))
#             else:
#                 data += '<td style="text-align:center;border: 1px solid black" colspan=3></td>'
        
        # else:
        #     warehouse=[]
        #     st = 0
        #     ware = frappe.db.get_list("Warehouse",{"company":doc.company},['name'])
        #     for w in ware:
        #         sto = frappe.db.get_value("Bin",{"item_code":j.item_code,"warehouse":w.name},['actual_qty'])
        #         if sto and sto>0:
        #             st+=sto
        #             warehouse.append(w.name)
        #     data += '<tr><td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' %(j.item_code)
        #     data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' %(j.description)
        #     data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' %(j.qty)
        #     if warehouse:
        #         data += '<td style="text-align:center;border: 1px solid black" colspan=3>%s</td>' %(', '.join(map(str, warehouse)))
        #     else:
        #         data += '<td style="text-align:center;border: 1px solid black" colspan=3></td>'

    data += '</tr>'
    # data += '<tr>'
    data += '</table>'
    return data

# @frappe.whitelist()
# def del_leave():
# 	leave=frappe.db.sql(""" delete from `tabLeave Allocation` where leave_type= 'Annual Leave' and docstatus = 1 """,as_dict=1)
# 	print(leave)
@frappe.whitelist()
def on_dn_submission(doc,method):
    if doc.company == 'Norden Communication Middle East FZE':
        so = frappe.db.get_value("Sales Order",{"name":doc.so_no},["finance_head_approval"])
        if so == 'Pending':
            frappe.throw("Pending For Finance Head Approval")

@frappe.whitelist()
def get_pending_for_finance_head(name):
    data=frappe.db.set_value("Sales Order",{"name":name},'finance_head_approval','Approved')
    frappe.msgprint('Approved Successfully')
    return data

@frappe.whitelist()
def update_values():
    value=frappe.db.get_list("Batch",["name","reference_doctype","reference_name","item","warehouse"])
    for i in value:
        # print(i.reference_doctype)
        # doc=frappe.db.get_doc(i.reference_name)
        # print(doc)
        if i.reference_doctype and i.reference_name:
            condition=frappe.db.exists(i.reference_doctype,i.reference_name)
            if condition:
                if i.reference_doctype=='Stock Reconciliation':
                    
                    doc=frappe.get_doc(i.reference_doctype,i.reference_name)
                    frappe.db.set_value("Batch",i.name,"company",doc.company)
     
     

# @frappe.whitelist() 
# def prepayment_journal_entry(name,date,party_type):
# 	if party_type == "Supplier":
# 		pay = frappe.get_doc("Prepayment",name)
# 		for d in pay.get("prepayment_details"):
# 			if not d.journal_entry_number:
# 				jour = frappe.new_doc("Journal Entry")
# 				jour.company = pay.company
# 				jour.posting_date = date
# 				jour.voucher_type = "Journal Entry"
# 				jour.pay_to_recd_from = pay.party
# 				dict_list = []
# 				dict_list.append(frappe._dict({"account": "Prepaid Rent - NCME","debit": pay.payment_amount,"credit": 0}))
# 				dict_list.append(frappe._dict({"account": "Trade Creditors - NCME","party_type":pay.party_type,"party":pay.party,"debit": 0,"credit": pay.payment_amount}))
# 				for i in dict_list:
                    
# 					jour.append('accounts', {
# 						'account': i.account,
# 						'party_type':i.party_type,
# 						'party':i.party,
# 						'debit_in_account_currency':i.debit,
# 						'credit_in_account_currency':i.credit   
# 					})
# 				jour.save(ignore_permissions=True)
# 				d.db_set("journal_entry_number", jour.name)
                
# 				return jour.name
    
# 	elif party_type == "Employee":
# 		pay = frappe.get_doc("Prepayment",name)
# 		for d in pay.get("prepayment_details"):
# 			if not d.journal_entry_number:
# 				jour = frappe.new_doc("Journal Entry")
# 				jour.company = pay.company
# 				jour.posting_date = date
# 				jour.voucher_type = "Journal Entry"
# 				jour.pay_to_recd_from = pay.party
# 				dict_list = []
# 				dict_list.append(frappe._dict({"account":"Prepaid Rent - NCME","debit": pay.payment_amount,"credit": 0}))
# 				dict_list.append(frappe._dict({"account": "Staff account - NCME","party_type":pay.party_type,"party":pay.party,"debit": 0,"credit": pay.payment_amount}))
# 				for i in dict_list:
                    
# 					jour.append('accounts', {
# 						'account': i.account,
# 						'party_type':i.party_type,
# 						'party':i.party,
# 						'debit_in_account_currency':i.debit,
# 						'credit_in_account_currency':i.credit
# 					})
# 				jour.save(ignore_permissions=True)
# 				d.db_set("journal_entry_number", jour.name)
# 				return jour.name

@frappe.whitelist()
def update_company(doc,method):
    if doc.reference_doctype=="Purchase Receipt":
        document=frappe.get_doc(doc.reference_doctype,doc.reference_name)
        doc.company=document.company
        if document.set_warehouse:
            doc.warehouse= document.set_warehouse
        doc.save(ignore_permissions=True)
    if doc.reference_doctype=="Stock Entry":
        document=frappe.get_doc(doc.reference_doctype,doc.reference_name)
        doc.company=document.company
        for j in document.items:
            if doc.item==j.item_code:
                doc.warehouse=j.t_warehouse
    if doc.reference_doctype=="Stock Reconciliation":
        document=frappe.get_doc(doc.reference_doctype,doc.reference_name)
        doc.company=document.company
        for j in document.items:
            if doc.item==j.item_code:
                doc.warehouse=j.warehouse
                doc.save(ignore_permissions=True)

@frappe.whitelist()
def update_todo(doc,method):
    if doc.reference_type=="Quotation":
        document=frappe.get_doc(doc.reference_type,doc.reference_name)
        doc.customer=document.party_name
        doc.save(ignore_permissions=True)

@frappe.whitelist()
def update_customer():
    value=frappe.db.get_list("ToDo",["name","reference_type","reference_name"])
    for i in value:
        if i.reference_type and i.reference_name:
            if i.reference_type=="Quotation":
                doc=frappe.get_doc(i.reference_type,i.reference_name)
                frappe.db.set_value("ToDo",i.name,"customer",doc.party_name)


@frappe.whitelist()
def update_workflow_status(name,state):
    doc = frappe.get_doc("Quotation",name)
    doc.work_flow = state
    doc.save(ignore_permissions=True)

@frappe.whitelist()
def calculate_working_days():
    from erpnext.setup.doctype.holiday_list.holiday_list import is_holiday
    holiday_list_name = 'Norden-Tamilnadu 2023 Holiday List'
    start_date = getdate(today())
    working_days = 9
    current_date = start_date
    holiday = []
    while working_days > 0:
        if not is_holiday(holiday_list_name, current_date):
            holiday.append(current_date)
            working_days -= 1
        current_date = add_days(current_date, 1)
    print(holiday[-1])
    print(date_diff(holiday[-1],start_date))

@frappe.whitelist()
def item_group_stock():
    query = """
    SELECT W.company,I.item_sub_group, (sum(`tabBin`.actual_qty) - sum(B.reserved_stock)) as QTY
    FROM `tabWarehouse` W
    LEFT JOIN `tabBin` B ON W.name = B.warehouse
    LEFT JOIN `tabItem` I ON B.item_code = I.name
    GROUP BY W.company, I.item_sub_group
    """
    items_by_company = frappe.db.sql(query, as_dict=True)
    for i in items_by_company:
        print(i)


@frappe.whitelist()
def get_stock_details(doc):
    item_details = frappe.db.sql(""" select item_code,description, sum(qty)as qty,sum(delivered_qty)as delivered_qty from `tabSales Order Item` where parent = '%s' group by item_code order by idx """%(doc.name),as_dict = 1)
    data = ''
    data += '<h4><center><b>PICKING LIST</b></center></h4>'
    data += '<table class="table table-bordered">'
    data += '<tr>'
    data += '<td colspan=3 style="width:13%;padding:1px;border:1px solid black;font-size:14px;background-color:#e20026;color:white;text-align:center">PRODUCT</td>'
    data += '<td colspan=3 style="width:70px;padding:1px;border:1px solid black;font-size:14px;background-color:#e20026;color:white;text-align:center">DESCRIPTION</td>'
    data += '<td colspan=3 style="width:70px;padding:1px;border:1px solid black;font-size:14px;background-color:#e20026;color:white;text-align:center">QTY</td>'
    data += '<td colspan=3 style="width:70px;padding:1px;border:1px solid black;font-size:14px;background-color:#e20026;color:white;text-align:center">WAREHOUSE</td>'
    data += '<td colspan=3 style="width:70px;padding:1px;border:1px solid black;font-size:14px;background-color:#e20026;color:white;text-align:center">RACK</td></tr>'
    for j in item_details:
        qty = 0
        av_qty = j.qty - j.delivered_qty
        if av_qty > 0:
            qty = av_qty
        available_qty = 0
        warehouse=[]
        rack_name = []
        ware = frappe.db.get_list("Warehouse",{"company":doc.company,"custom_is_pick_list":0},['name'])
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
                """, (doc.name, j.item_code), as_dict=1)
        
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
            
            racks = frappe.db.sql("""
                SELECT 
                    rack,
                    SUM(actual_qty) AS balance_qty
                FROM `tabStock Ledger Entry`
                WHERE item_code = %s
                AND warehouse = %s
                AND is_cancelled = 0
                AND rack IS NOT NULL
                GROUP BY rack
                HAVING SUM(actual_qty) > 0
            """, (j.item_code, w.name), as_dict=1)
            for r in racks:
                if r.balance_qty > 0:
                    # rack_name.append(r.rack)
                    rack_name.append(f"{r.rack} - {r.balance_qty}")
        if available_qty > 0:
            data += '<tr><td style="text-align:center;border: 1px solid black" colspan=3>%s</td>' %(j.item_code)
            data += '<td style="text-align:center;border: 1px solid black" colspan=3>%s</td>' %(j.description)
            data += '<td style="text-align:center;border: 1px solid black;text-align:right" colspan=3>%s</td>' %(available_qty)
            if warehouse:
                data += '<td style="text-align:center;border: 1px solid black" colspan=3>%s</td>' %(', '.join(map(str, warehouse)))
            else:
                data += '<td style="text-align:center;border: 1px solid black" colspan=3></td>'
            if rack_name:
                data += '<td style="text-align:center;border: 1px solid black" colspan=3>%s</td>' %(', '.join(map(str, rack_name)))
            else:
                data += '<td style="text-align:center;border: 1px solid black" colspan=3></td>'
    data += '</tr>'
    data += '</table>'
    return data

@frappe.whitelist()
def get_stock(doc):
    # item_details = doc.items
    item_details = frappe.db.sql(""" select item_code,description, sum(qty)as qty,sum(delivered_qty)as delivered_qty from `tabSales Order Item` where parent = '%s' group by item_code order by idx """%(doc.name),as_dict = 1)

    data = ''
    data += '<h4><center><b>NON AVAILABLE QTY</b></center></h4>'
    data += '<table class="table table-bordered">'

    data += '<tr>'
    data += '<td colspan=4 style="color:#FFFFFF;width:13%;padding:1px;border:1px solid black;font-size:14px;background-color:#e20026;color:white;text-align:center">PRODUCT</td>'
    data += '<td colspan=4 style="width:70px;padding:1px;border:1px solid black;font-size:14px;background-color:#e20026;color:white;text-align:center">DESCRIPTION</td>'
    data += '<td colspan=4 style="width:70px;padding:1px;border:1px solid black;font-size:14px;background-color:#e20026;color:white;text-align:center">QTY</td>'	
    for j in item_details:
        del_note = frappe.db.get_all("Delivery Note", {"file_number": doc.file_number,"docstatus":("!=",2)}, ['*'])
        if del_note:
            del_qty = 0
            for i in del_note:
                deli_note = frappe.get_doc("Delivery Note", i.name)
                if deli_note.items:
                    for item in deli_note.items:
                        if j.item_code == item.item_code:
                            del_qty += item.qty
                        else:
                            del_qty = 0
            available_qty = 0
            nonavailable_qty = 0
            warehouse = []
            ware = frappe.db.get_list("Warehouse", {"company": doc.company,"custom_is_pick_list":0}, ['name'])
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
                    """, (doc.name, j.item_code), as_dict=1)
                    stock = sum([value.get("actual_qty", 0) for value in bin]) - sum([value.get("reserved_stock", 0) for value in bin])

                    if reserve:
                        reser_qty = reserve[0]['reserved_qty']
                    else:
                        reser_qty = 0

                    if reser_qty and reser_qty > 0:
                        available_qty = reser_qty
                    else:
                        if stock and j.qty >= stock:
                            available_qty = stock
                            
                        elif stock and j.qty < stock:
                            available_qty = j.qty
            if available_qty > 0:
                nonavailable_qty = (j.qty - j.delivered_qty) - available_qty
            else:           
                nonavailable_qty = j.qty - j.delivered_qty 
            if nonavailable_qty>0:
                data += '<tr><td style="text-align:center;border: 1px solid black" colspan=4>%s</td>' %(j.item_code)
                data += '<td style="text-align:center;border: 1px solid black" colspan=4>%s</td>' %(j.description)
                data += '<td style="text-align:center;border: 1px solid black;text-align:right" colspan=4>%s</td>' %(nonavailable_qty)
                data += '</tr>'
        else:
            available_qty = 0
            nonavailable_qty = 0
            warehouse = []
            ware = frappe.db.get_list("Warehouse", {"company": doc.company}, ['name'])
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
                    """, (doc.name, j.item_code), as_dict=1)
                    stock = sum([value.get("actual_qty", 0) for value in bin]) - sum([value.get("reserved_stock", 0) for value in bin])

                    if reserve:
                        reser_qty = reserve[0]['reserved_qty']
                    else:
                        reser_qty = 0

                    if reser_qty and reser_qty > 0:
                        available_qty = reser_qty
                    else:
                        if stock and j.qty >= stock:
                            available_qty = stock
                            
                        elif stock and j.qty < stock:
                            available_qty = j.qty
                        else:
                            available_qty = 0
            nonavailable_qty = j.qty - available_qty
            if nonavailable_qty > 0:
                data += '<tr><td style="text-align:center;border: 1px solid black" colspan=4>%s</td>' %(j.item_code)
                data += '<td style="text-align:center;border: 1px solid black" colspan=4>%s</td>' %(j.description)
                data += '<td style="text-align:center;border: 1px solid black;text-align:right" colspan=4>%s</td>' %(nonavailable_qty)
                data += '</tr>'
    data += '</tr>'
    data += '</table>'
    return data

# @frappe.whitelist()
# def check_leave(fd,emp):
# 	date_string = str(fd)
# 	date_obj = datetime.strptime(date_string, "%Y-%m-%d")
# 	month = date_obj.month
# 	start_date, end_date = get_start_end_dates(2023, month)
# 	sd = start_date.strftime("%Y-%m-%d")
# 	ed = end_date.strftime("%Y-%m-%d")
# 	# c = frappe.db.sql(""" select name from `tabLeave Application` where from_date between '2023-09-01' and '2022-09-30' and docstatus = 1 """ ,as_dict=1)
# 	c = frappe.get_all("Leave Application",{"docstatus":1,"employee":emp,'from_date': ['between', (sd,ed)]},["*"])
# 	count = 0
# 	if c:
# 		for i in c:
# 			count = i.total_leave_days + count
# 	return count
    

# def get_start_end_dates(year, month):
# 	# Create the first day of the month
# 	start_date = datetime(year, month, 1)

# 	# Get the number of days in the month
# 	_, last_day = monthrange(year, month)

# 	# Create the last day of the month
# 	end_date = datetime(year, month, last_day)

# 	return start_date, end_date

# @frappe.whitelist()
# def check_wfh_tech(fd,emp):
# 	date_string = str(fd)
# 	date_obj = datetime.strptime(date_string, "%Y-%m-%d")
# 	month = date_obj.month
# 	start_date, end_date = get_start_end_dates(2023, month)
# 	sd = start_date.strftime("%Y-%m-%d")
# 	ed = end_date.strftime("%Y-%m-%d")
# 	c = frappe.get_all("Work From Home Request",{"docstatus":1,"employee":emp,'work_from_date': ['between', (sd,ed)]},["*"])
# 	count = 0
# 	if c:
# 		for i in c:
# 			count = i.total_working_days + count
# 	return count
    
# @frappe.whitelist()
# def check_wfh_non_tech(fd,emp):
# 	date_string = str(fd)
# 	date_obj = datetime.strptime(date_string, "%Y-%m-%d")
# 	month = date_obj.month
# 	start_date, end_date = get_start_end_dates(2023, month)
# 	sd = start_date.strftime("%Y-%m-%d")
# 	ed = end_date.strftime("%Y-%m-%d")
# 	c = frappe.get_all("Work From Home Request",{"docstatus":1,"employee":emp,'work_from_date': ['between', (sd,ed)]},["*"])
# 	count = 0
# 	if c:
# 		for i in c:
# 			count = i.total_working_days + count
# 	return count

@frappe.whitelist()
def get_so_child(sales_order):
    if sales_order:
        so = frappe.get_doc("Sales Order",sales_order)
        return so.items

@frappe.whitelist()
def get_invoice_type():
    doc=frappe.get_list("Delivery Note",{"company":"Norden Communication Middle East FZE","docstatus":("!=",2)},["name","invoice_type"])
    for i in doc:
        if i.invoice_type ==None:
            values = frappe.get_doc("Delivery Note",i.name)
            if values.taxes:
                print(i.name)
                frappe.db.set_value("Delivery Note",i.name,"invoice_type","Taxable")
            else:
                frappe.db.set_value("Delivery Note",i.name,"invoice_type","Non Taxable")

# @frappe.whitelist()
# def update_so_wf():
# 	bn = frappe.db.sql(""" update  `tabPurchase Order`  set plc_conversion_rate = "83.45" where name = "PO-NCPLP-2024-00033"  """)
    # wh = frappe.db.sql(""" update  `tabSerial No`  set warehouse = "Stores - NSPL" where name = "NVS-DC900021CM-5"  """)

import frappe
from frappe.utils.file_manager import get_file
from frappe.utils.csvutils import read_csv_content

@frappe.whitelist()
def bulk_upload_serial_number(file_name):
    file_path = get_file(file_name)
    pps = read_csv_content(file_path[1])
    for pp in pps:
        # print(pp[3])
        name = pp[3]
        if frappe.db.exists('Serial No', {'name': name}):
            # print("HI")
            existing_serial = frappe.get_doc('Serial No',{'name':name},['*'])
            print(existing_serial.name)
            frappe.db.sql("UPDATE `tabSerial No` SET batch_no = %s WHERE name = %s", (pp[1], pp[3]))
            frappe.db.sql("UPDATE `tabSerial No` SET warehouse = %s WHERE name = %s", (pp[2], pp[3]))
            # existing_serial.save(ignore_permissions = True)
            # frappe.db.commit()
            print("Completed")

# @frappe.whitelist()
# def del_salary_slip():
# 	sal=frappe.db.sql(""" delete from `tabAdditional Salary` where docstatus = 2 """,as_dict=1)
# 	print(sal)

@frappe.whitelist() 
def prepayment_journal_entry(name,date,party_type):
    if party_type == "Supplier":
        pay = frappe.get_doc("Prepayment",name)
        for d in pay.get("prepayment_details"):
            if not d.journal_entry_number:
                jour = frappe.new_doc("Journal Entry")
                jour.company = pay.company
                jour.posting_date = date
                jour.voucher_type = "Journal Entry"
                jour.pay_to_recd_from = pay.party
                dict_list = []
                dict_list.append(frappe._dict({"account": pay.expense_account_name,"cost_center":"Main - NCME","debit": d.prepayment_amount,"credit": 0}))
                dict_list.append(frappe._dict({"account": pay.prepayment_account,"party_type":pay.party_type,"party":pay.party,"cost_center":"Main - NCME","debit": 0,"credit": d.prepayment_amount}))
                for i in dict_list:
                    
                    jour.append('accounts', {
                        'account': i.account,
                        'party_type':i.party_type,
                        'party':i.party,
                        'cost_center':i.cost_center,

                        'debit_in_account_currency':i.debit,
                        'credit_in_account_currency':i.credit
                    })
                jour.save(ignore_permissions=True)
                jour.submit()
                d.db_set("journal_entry_number", jour.name)
                
                return jour.name
    
    elif party_type == "Employee":
        pay = frappe.get_doc("Prepayment",name)
        for d in pay.get("prepayment_details"):
            if not d.journal_entry_number:
                jour = frappe.new_doc("Journal Entry")
                jour.company = pay.company
                jour.posting_date = date
                jour.voucher_type = "Journal Entry"
                jour.pay_to_recd_from = pay.party
                dict_list = []
                dict_list.append(frappe._dict({"account":pay.expense_account_name,"cost_center":"Main - NCME","debit": d.prepayment_amount,"credit": 0}))
                dict_list.append(frappe._dict({"account": pay.prepayment_account,"party_type":pay.party_type,"party":pay.party,"cost_center":"Main - NCME","debit": 0,"credit": d.prepayment_amount}))
                for i in dict_list:
                    
                    jour.append('accounts', {
                        'account': i.account,
                        'party_type':i.party_type,
                        'party':i.party,
                        'cost_center':i.cost_center,

                        'debit_in_account_currency':i.debit,
                        'credit_in_account_currency':i.credit
                    })
                jour.save(ignore_permissions=True)
                jour.submit()

                d.db_set("journal_entry_number", jour.name)
                return jour.name

# @frappe.whitelist()
# def return_tax_html(doc):
# 	from erpnext.controllers.taxes_and_totals import get_itemised_tax_breakup_header, get_itemised_tax_breakup_data
# 	tax_accounts = []
# 	for tax in doc.taxes:
# 		if getattr(tax, "category", None) and tax.category == "Valuation":
# 			continue
# 		if tax.description not in tax_accounts:
# 			tax_accounts.append(tax.description)
# 	headers = get_itemised_tax_breakup_header(doc.doctype + " Item", tax_accounts)
# 	itemised_tax_data = get_itemised_tax_breakup_data(doc)
    
# 	data = '<table class="table table-bordered">'
# 	data += "<tr>"
# 	for key in headers:
# 		data += "<td style ='border-color:#e20026;border-right-color:white;background-color: #e20026;color: white;text-align:center'>%s</td>" % (key)
# 	data += "</tr>"
# 	total = 0
# 	for item in itemised_tax_data:
# 		for hsn in doc.items:
# 			data += "<tr>"
# 			data += "<td style ='border-color:#e20026;text-align:right'>%s</td>" % (hsn.gst_hsn_code)
# 			total += item.taxable_amount
# 			data += "<td style ='border-color:#e20026;text-align:right' class='text-right'>%s</td>" % (frappe.utils.fmt_money(item.taxable_amount, currency=doc.get("currency")))
# 			for tax_account in tax_accounts:
# 				tax_details = item.get(tax_account)
# 				if tax_details:
# 					if doc.get('is_return'):
# 						data += "<td style ='border-color:#e20026;text-align:right' class='text-right'>(%s%%) %s</td>" % ((tax_details["tax_rate"]),frappe.utils.fmt_money(tax_details["tax_amount"] / doc.conversion_rate, currency=doc.get("currency")))
# 					else:
# 						data += "<td style ='border-color:#e20026;text-align:right' class='text-right'>(%s%%) %s</td>" % ((tax_details["tax_rate"]),frappe.utils.fmt_money(tax_details["tax_amount"] / doc.conversion_rate, currency=doc.get("currency")))
# 			data += "</tr>"
# 	tot = 0
# 	data += "<tr>"
# 	data += "<td style ='border-color:#e20026;text-align:right;font-weight:bold'>Total</td>"
# 	data += "<td style ='border-color:#e20026;text-align:right;font-weight:bold' class='text-right'>%s</td>" % (frappe.utils.fmt_money(total, currency=doc.get("currency")))
# 	for tax_account in tax_accounts:
# 		tot = 0
# 		for item in itemised_tax_data:
# 			tax_details = item.get(tax_account)
# 			if tax_details:
# 				if doc.get('is_return'):
# 					tot += tax_details["tax_amount"] / doc.conversion_rate
# 				else:
# 					tot += tax_details["tax_amount"] / doc.conversion_rate
# 		data += "<td style ='border-color:#e20026;text-align:right;font-weight:bold' class='text-right'>%s</td>" % (frappe.utils.fmt_money(tot, currency=doc.get("currency")))
# 	data += "</tr>"
# 	data += "</table>"
# 	return data





@frappe.whitelist()
def return_tax_html(doc):
    from erpnext.controllers.taxes_and_totals import get_itemised_tax_breakup_header, get_itemised_tax_breakup_data
    tax_accounts = []
    for tax in doc.taxes:
        if getattr(tax, "category", None) and tax.category == "Valuation":
            continue
        if tax.description not in tax_accounts:
            tax_accounts.append(tax.description)
    headers = get_itemised_tax_breakup_header(doc.doctype + " Item", tax_accounts)
    itemised_tax_data = get_itemised_tax_breakup_data(doc)
    
    data = '<table class="table table-bordered">'
    data += "<tr>"
    for key in headers:
        data += "<td style ='border-color:#e20026;border-right-color:white;background-color: #e20026;color: white;text-align:center'>%s</td>" % (key)
    data += "</tr>"
    total = 0
    for item in itemised_tax_data:
        data += "<tr>"
        data += "<td style ='border-color:#e20026;text-align:right'>%s</td>" % (frappe.db.get_value('Sales Invoice Item',{'parent':doc.name,'item_code':item.item},'gst_hsn_code'))
        total += item.taxable_amount
        data += "<td style ='border-color:#e20026;text-align:right' class='text-right'>%s</td>" % (frappe.utils.fmt_money(item.taxable_amount, currency=doc.get("currency")))
        for tax_account in tax_accounts:
            tax_details = item.get(tax_account)
            if tax_details:
                if doc.get('is_return'):
                    data += "<td style ='border-color:#e20026;text-align:right' class='text-right'>(%s%%) %s</td>" % ((tax_details["tax_rate"]),frappe.utils.fmt_money(tax_details["tax_amount"] / doc.conversion_rate, currency=doc.get("currency")))
                else:
                    data += "<td style ='border-color:#e20026;text-align:right' class='text-right'>(%s%%) %s</td>" % ((tax_details["tax_rate"]),frappe.utils.fmt_money(tax_details["tax_amount"] / doc.conversion_rate, currency=doc.get("currency")))
        data += "</tr>"
    tot = 0
    data += "<tr>"
    data += "<td style ='border-color:#e20026;text-align:right;font-weight:bold'>Total</td>"
    data += "<td style ='border-color:#e20026;text-align:right;font-weight:bold' class='text-right'>%s</td>" % (frappe.utils.fmt_money(total, currency=doc.get("currency")))
    for tax_account in tax_accounts:
        tot = 0
        for item in itemised_tax_data:
            tax_details = item.get(tax_account)
            if tax_details:
                if doc.get('is_return'):
                    tot += tax_details["tax_amount"] / doc.conversion_rate
                else:
                    tot += tax_details["tax_amount"] / doc.conversion_rate
        data += "<td style ='border-color:#e20026;text-align:right;font-weight:bold' class='text-right'>%s</td>" % (frappe.utils.fmt_money(tot, currency=doc.get("currency")))
    data += "</tr>"
    data += "</table>"
    return data


@frappe.whitelist()
def returntaxhtml(doc):
    from erpnext.controllers.taxes_and_totals import get_itemised_tax_breakup_header, get_itemised_tax_breakup_data
    
    # Fetch itemised tax breakup header and data
    tax_accounts = []
    for tax in doc.taxes:
        if getattr(tax, "category", None) and tax.category == "Valuation":
            continue
        if tax.description not in tax_accounts:
            tax_accounts.append(tax.description)
    
    headers = get_itemised_tax_breakup_header(doc.doctype + " Item", tax_accounts)
    itemised_tax_data = get_itemised_tax_breakup_data(doc)
    
    # Initialize a dictionary to store sums grouped by HSN code
    hsn_grouped_sums = {}
    
    # Iterate over itemised tax data to calculate sums for each HSN code
    for item in itemised_tax_data:
        hsn_code = frappe.db.get_value('Sales Invoice Item', {'parent': doc.name, 'item_code': item.item}, 'gst_hsn_code')
        
        if hsn_code not in hsn_grouped_sums:
            hsn_grouped_sums[hsn_code] = {'total_taxable_amount': 0, 'total_tax_amount': 0}
        
        taxable_amount = item['taxable_amount']
        
        # Check for applicable tax types dynamically
        for account in tax_accounts:
            if 'CGST' in account or 'SGST' in account or 'IGST' in account:
                tax_rate = item.get(account, {}).get('tax_rate', 0)
                tax_amount = item.get(account, {}).get('tax_amount', 0)
                
                # Calculate tax amount based on tax rate
                if tax_rate == 9:
                    hsn_grouped_sums[hsn_code]['total_tax_amount'] += tax_amount / 2  # Split tax amount for CGST and SGST
                elif tax_rate == 18:
                    hsn_grouped_sums[hsn_code]['total_tax_amount'] += tax_amount
        
        hsn_grouped_sums[hsn_code]['total_taxable_amount'] += taxable_amount
    
    # Initialize the HTML string
    data = '<table class="table table-bordered">'
    data += "<tr>"
    
    # Add headers to the HTML table
    for key in headers:
        data += "<td style='border-color:#e20026;border-right-color:white;background-color:#e20026;color:white;text-align:center'>{}</td>".format(key)
    data += "</tr>"
    
    total_taxable_amount = 0
    
    total = 0
    # Iterate over the grouped sums list to populate the HTML table
    for hsn_code, sums in hsn_grouped_sums.items():
        data += "<tr>"
        data += "<td style='border-color:#e20026;text-align:right'>{}</td>".format(hsn_code)
        total_taxable_amount += sums['total_taxable_amount']
        data += "<td style='border-color:#e20026;text-align:right' class='text-right'>{}</td>".format(frappe.utils.fmt_money(sums['total_taxable_amount'], currency=doc.get("currency")))
        
        # Add tax amounts dynamically based on tax types
        for account in tax_accounts:
            tax_details = item.get(account)
            if tax_details:
                tax_rate = tax_details.get("tax_rate", 0)
                tax_amount = sums['total_tax_amount']
                tax_value = item.get(account, {}).get('tax_amount', 0)
                if tax_rate == 9:
                    data += "<td style='border-color:#e20026;text-align:right' class='text-right'>(%s%%)  %s</td>" % ((tax_rate),frappe.utils.fmt_money(tax_amount / doc.conversion_rate, currency=doc.get("currency")))
                elif tax_rate == 18:
                    data += "<td style='border-color:#e20026;text-align:right' class='text-right'>(%s%%)  %s</td>" % ((tax_rate),frappe.utils.fmt_money(tax_amount / doc.conversion_rate, currency=doc.get("currency")))
                else:
                    data += "<td style='border-color:#e20026;text-align:right' class='text-right'>%s</td>" % (frappe.utils.fmt_money(tax_value / doc.conversion_rate, currency=doc.get("currency"))
)

        
        data += "</tr>"
    
    tot = 0
    data += "<tr>"
    data += "<td style ='border-color:#e20026;text-align:right;font-weight:bold'>Total</td>"
    data += "<td style ='border-color:#e20026;text-align:right;font-weight:bold' class='text-right'>%s</td>" % (frappe.utils.fmt_money(total_taxable_amount, currency=doc.get("currency")))
    for tax_account in tax_accounts:
        tot = 0
        for item in itemised_tax_data:
            tax_details = item.get(tax_account)
            if tax_details:
                if doc.get('is_return'):
                    tot += tax_details["tax_amount"] / doc.conversion_rate
                else:
                    tot += tax_details["tax_amount"] / doc.conversion_rate
        data += "<td style ='border-color:#e20026;text-align:right;font-weight:bold' class='text-right'>%s</td>" % (frappe.utils.fmt_money(tot, currency=doc.get("currency")))
    
    data += "</tr>"
    data += "</table>"
    
    return data

@frappe.whitelist()
def return_tax_invoice(doc):
    from erpnext.controllers.taxes_and_totals import get_itemised_tax_breakup_header, get_itemised_tax_breakup_data
    
    # Fetch itemised tax breakup header and data
    tax_accounts = []
    for tax in doc.taxes:
        if getattr(tax, "category", None) and tax.category == "Valuation":
            continue
        if tax.description not in tax_accounts:
            tax_accounts.append(tax.description)
    
    headers = get_itemised_tax_breakup_header(doc.doctype + " Item", tax_accounts)
    itemised_tax_data = get_itemised_tax_breakup_data(doc)
    
    # Initialize a dictionary to store sums grouped by HSN code
    hsn_grouped_sums = {}
    
    # Iterate over itemised tax data to calculate sums for each HSN code
    for item in itemised_tax_data:
        hsn_code = frappe.db.get_value('Sales Invoice Item', {'parent': doc.name, 'item_code': item.item}, 'gst_hsn_code')
        
        if hsn_code not in hsn_grouped_sums:
            hsn_grouped_sums[hsn_code] = {'total_taxable_amount': 0, 'total_tax_amount': 0}
        
        taxable_amount = item['taxable_amount']
        
        # Check for applicable tax types dynamically
        for account in tax_accounts:
            if 'CGST' in account or 'SGST' in account or 'IGST' in account:
                tax_rate = item.get(account, {}).get('tax_rate', 0)
                tax_amount = item.get(account, {}).get('tax_amount', 0)
                
                # Calculate tax amount based on tax rate
                if tax_rate == 9:
                    hsn_grouped_sums[hsn_code]['total_tax_amount'] += tax_amount / 2  # Split tax amount for CGST and SGST
                elif tax_rate == 18:
                    hsn_grouped_sums[hsn_code]['total_tax_amount'] += tax_amount
        
        hsn_grouped_sums[hsn_code]['total_taxable_amount'] += taxable_amount
    
    # Initialize the HTML string
    data = '<table class="table table-bordered">'
    data += "<tr>"
    
    # Add headers to the HTML table
    for key in headers:
        data += "<td style='border-color:black;text-align:center'><b>{}</b></td>".format(key)
    data += "</tr>"
    
    total_taxable_amount = 0
    
    total = 0
    # Iterate over the grouped sums list to populate the HTML table
    for hsn_code, sums in hsn_grouped_sums.items():
        data += "<tr style='border-color:black'>"
        data += "<td style='border-color:black;text-align:right'>{}</td>".format(hsn_code)
        total_taxable_amount += sums['total_taxable_amount']
        data += "<td style='border-color:black;text-align:right' class='text-right'>{}</td>".format(frappe.utils.fmt_money(sums['total_taxable_amount'], currency=doc.get("currency")))
        
        # Add tax amounts dynamically based on tax types
        for account in tax_accounts:
            tax_details = item.get(account)
            if tax_details:
                tax_rate = tax_details.get("tax_rate", 0)
                tax_amount = sums['total_tax_amount']
                
                if tax_rate == 9:
                    data += "<td style='border-color:black;text-align:right' class='text-right'>(%s%%)  %s</td>" % ((tax_rate),frappe.utils.fmt_money(tax_amount / doc.conversion_rate, currency=doc.get("currency")))
                elif tax_rate == 18:
                    data += "<td style='border-color:black;text-align:right' class='text-right'>(%s%%)  %s</td>" % ((tax_rate),frappe.utils.fmt_money(tax_amount / doc.conversion_rate, currency=doc.get("currency")))
        
        data += "</tr>"
    
    tot = 0
    data += "<tr style = 'border-color:black'>"
    data += "<td style ='border-color:black;text-align:right;font-weight:bold'>Total</td>"
    data += "<td style ='border-color:black;text-align:right;font-weight:bold' class='text-right'>%s</td>" % (frappe.utils.fmt_money(total_taxable_amount, currency=doc.get("currency")))
    for tax_account in tax_accounts:
        tot = 0
        for item in itemised_tax_data:
            tax_details = item.get(tax_account)
            if tax_details:
                if doc.get('is_return'):
                    tot += tax_details["tax_amount"] / doc.conversion_rate
                else:
                    tot += tax_details["tax_amount"] / doc.conversion_rate
        data += "<td style ='border-color:black;text-align:right;font-weight:bold' class='text-right'>%s</td>" % (frappe.utils.fmt_money(tot, currency=doc.get("currency")))
    
    data += "</tr>"
    data += "</table>"
    
    return data

# @frappe.whitelist()
# def returntaxhtml(doc):
#     from erpnext.controllers.taxes_and_totals import get_itemised_tax_breakup_header, get_itemised_tax_breakup_data
    
#     # Fetch itemised tax breakup header and data
#     tax_accounts = []
#     for tax in doc.taxes:
#         if getattr(tax, "category", None) and tax.category == "Valuation":
#             continue
#         if tax.description not in tax_accounts:
#             tax_accounts.append(tax.description)
#     headers = get_itemised_tax_breakup_header(doc.doctype + " Item", tax_accounts)
#     itemised_tax_data = get_itemised_tax_breakup_data(doc)
    
#     # Initialize a dictionary to store sums grouped by HSN code
#     hsn_grouped_sums = {}
    
#     # Iterate over itemised tax data to calculate sums for each HSN code
#     for item in itemised_tax_data:
#         hsn_code = frappe.db.get_value('Sales Invoice Item', {'parent': doc.name, 'item_code': item.item}, 'gst_hsn_code')
        
#         if hsn_code not in hsn_grouped_sums:
#             hsn_grouped_sums[hsn_code] = {'total_taxable_amount': 0, 'total_tax_amount': 0}
        
#         taxable_amount = item['taxable_amount']
        
#         # Check if both CGST and SGST are present or only IGST is present based on GST rate
#         if 'Output Tax CGST @ 9.0' in item and 'Output Tax SGST @ 9.0' in item:
#             sgst_tax_amount = item['Output Tax SGST @ 9.0']['tax_amount']
#             cgst_tax_amount = item['Output Tax CGST @ 9.0']['tax_amount']
            
#             hsn_grouped_sums[hsn_code]['total_taxable_amount'] += taxable_amount
#             hsn_grouped_sums[hsn_code]['total_tax_amount'] += sgst_tax_amount + cgst_tax_amount
#         elif 'Output Tax IGST @ 18.0' in item:
#             igst_tax_amount = item['Output Tax IGST @ 18.0']['tax_amount']
            
#             hsn_grouped_sums[hsn_code]['total_taxable_amount'] += taxable_amount
#             hsn_grouped_sums[hsn_code]['total_tax_amount'] += igst_tax_amount 
    
#     # Initialize the HTML string
#     data = '<table class="table table-bordered">'
#     data += "<tr>"
    
#     # Add headers to the HTML table
#     for key in headers:
#         data += "<td style='border-color:#e20026;border-right-color:white;color:white;text-align:center'>{}</td>".format(key)
#     data += "</tr>"
    
#     total_taxable_amount = 0
    
#     # Iterate over the grouped sums list to populate the HTML table
#     for hsn_code, sums in hsn_grouped_sums.items():
#         data += "<tr>"
#         data += "<td style='border-color:#e20026;text-align:right'>{}</td>".format(hsn_code)
#         total_taxable_amount += sums['total_taxable_amount']
#         data += "<td style='border-color:#e20026;text-align:right' class='text-right'>{}</td>".format(frappe.utils.fmt_money(sums['total_taxable_amount'], currency=doc.get("currency")))
        
#         # Check if both CGST and SGST are present or only IGST is present based on GST rate
#         if 'Output Tax CGST @ 9.0' in item and 'Output Tax SGST @ 9.0' in item:
#             data += "<td style='border-color:#e20026;text-align:right' class='text-right'>{}</td>".format(frappe.utils.fmt_money(sums['total_tax_amount'] / 2 / doc.conversion_rate, currency=doc.get("currency")))
#             data += "<td style='border-color:#e20026;text-align:right' class='text-right'>{}</td>".format(frappe.utils.fmt_money(sums['total_tax_amount'] / 2 / doc.conversion_rate, currency=doc.get("currency")))
#         elif 'Output Tax IGST @ 18.0' in item:
#             data += "<td style='border-color:#e20026;text-align:right' class='text-right'>{}</td>".format(frappe.utils.fmt_money(sums['total_tax_amount'] / doc.conversion_rate, currency=doc.get("currency")))
#             data += "<td style='border-color:#e20026;text-align:right' class='text-right'></td>"
        
#         data += "</tr>"
    
#     # Add total row to the HTML table
#     data += "<tr>"
#     data += "<td style='border-color:#e20026;text-align:right;font-weight:bold'>Total</td>"
#     data += "<td style='border-color:#e20026;text-align:right;font-weight:bold' class='text-right'>{}</td>".format(frappe.utils.fmt_money(total_taxable_amount, currency=doc.get("currency")))
#     data += "<td style='border-color:#e20026;text-align:right;font-weight:bold' class='text-right'></td>"
#     data += "<td style='border-color:#e20026;text-align:right;font-weight:bold' class='text-right'></td>"
#     data += "</tr>"
#     data += "</table>"
    
#     return data







@frappe.whitelist()
def update_fields():
    value=frappe.get_all("Sales Order",["name","consultant_company","consultant_name","end_client_user_name","end_client__user_industry"])
    for i in value:
        if not i.consultant_company:
            frappe.db.set_value("Sales Order",i.name,"consultant_company","Confidential")
        if not i.consultant_name:
            frappe.db.set_value("Sales Order",i.name,"consultant_name","Confidential")
        if not i.end_client_user_name:
            frappe.db.set_value("Sales Order",i.name,"end_client_user_name","Confidential")
        if not i.end_client__user_industry:
            frappe.db.set_value("Sales Order",i.name,"end_client__user_industry","Confidential")
@frappe.whitelist()
def update_consultant_name():
    frappe.db.set_value("Sales Order","SO-NCMEFT-2023-00347","consultant_name","Confidential")

@frappe.whitelist()
def get_qty_from_stock(so_no):
    items_data = {}

    stock = frappe.get_all(
        'Stock Reservation Entry',
        filters={'voucher_no': so_no, 'docstatus': ('!=', 2)},
        fields=['item_code', 'reserved_qty', 'voucher_detail_no']
    )

    for entry in stock:
        row_id = entry.voucher_detail_no  # Unique row reference
        reserved_qty = entry.reserved_qty
        item_code = entry.item_code

        if row_id in items_data:
            items_data[row_id]['reserved_qty'] += reserved_qty
        else:
            items_data[row_id] = {
                'item_code': item_code,
                'reserved_qty': reserved_qty
            }

    result = [
        {'sales_order_item': row_id, 'item_code': data['item_code'], 'reserved_qty': data['reserved_qty']}
        for row_id, data in items_data.items()
    ]

    return result


@frappe.whitelist()
def get_data(serial_no):
    data = '<table border="1" style="width: 100%;">'
    if serial_no:
        serial_no_value = frappe.db.get_value("Serial and Batch Entry", {'serial_no': serial_no}, ['parent'])
        if serial_no_value:
            value = frappe.get_all('Serial and Batch Bundle', {'name': serial_no_value}, ['voucher_no', 'voucher_type', 'item_code'])
            dn_date = frappe.db.get_value("Delivery Note", {'name': value[0]['voucher_no']}, ['posting_date'])
            data += '<tr style="background-color:#D9E2ED;">'
            data += '<td colspan="2" style="text-align:center;"><b>Item Code</b></td>'
            if value and value[0].get('voucher_type') == 'Delivery Note':
                si_parent = frappe.get_value("Sales Invoice Item", {'delivery_note': value[0]['voucher_no']}, ['parent'])
                si_date = frappe.db.get_value("Sales Invoice", {'name': si_parent}, ['posting_date']) if si_parent else None
                data += '<td colspan="2" style="text-align:center;"><b>Delivery Note</b></td>'
                if si_parent:
                    data += '<td colspan="2" style="text-align:center;"><b>Sales Invoice</b></td>'
                if dn_date:
                    data += '<td colspan="2" style="text-align:center;"><b>Delivery Date</b></td>'
                    if si_date:
                        data += '<td colspan="2" style="text-align:center;"><b>Invoiced Date</b></td>'
            pr = frappe.db.get_value("Serial and Batch Bundle",{"item_code":format(value[0]['item_code']),"voucher_type":"Purchase Receipt"},["voucher_type"])
            if pr:
                data += '<td colspan="2" style="text-align:center;"><b>Purchase Receipt</b></td>'
            stock = frappe.db.get_value("Serial and Batch Bundle",{"item_code":format(value[0]['item_code']),"voucher_type":"Stock Entry"},["voucher_type"])
            if stock:
                data += '<td colspan="2" style="text-align:center;"><b>Stock Entry</b></td>'
            data += '<td colspan="2" style="text-align:center;"><b>Warranty Terms</b></td>'
            data += '</tr>'
            data += '<tr>'
            data += '<td colspan="2" style="text-align:center;"><b>{}</b></td>'.format(value[0]['item_code'])
            if value and value[0].get('voucher_type') == 'Delivery Note':
                data += '<td colspan="2" style="text-align:center;"><b>{}</b></td>'.format(value[0]['voucher_no'])
                if si_parent:
                    data += '<td colspan="2" style="text-align:center;"><b>{}</b></td>'.format(si_parent)
                if dn_date:
                    data += '<td colspan="2" style="text-align:center;"><b>{}</b></td>'.format(dn_date)
                    if si_date:
                        data += '<td colspan="2" style="text-align:center;"><b>{}</b></td>'.format(si_date)
            pr_value = frappe.db.get_value("Serial and Batch Bundle",{"item_code":format(value[0]['item_code']),"voucher_type":"Purchase Receipt"},["voucher_no"])
            if pr_value:
                data += '<td colspan="2" style="text-align:center;"><b>{}</b></td>'.format(pr_value)
            stock_entry = frappe.db.get_value("Serial and Batch Bundle",{"item_code":format(value[0]['item_code']),"voucher_type":"Stock Entry"},["voucher_no"])
            if stock_entry:
                data += '<td colspan="2" style="text-align:center;"><b>{}</b></td>'.format(stock_entry)
            data += '<td colspan="2" style="text-align:center;"><b>Not Disclosure</b></td>'
            data += '</tr>'
        else:
            item_code = frappe.db.get_value("Serial No", {'name': serial_no}, ['item_code'])
            dn = frappe.db.get_value("Delivery Note Item", {'item_code': item_code}, ['parent'])			
            if dn:
                dn_date = frappe.db.get_value("Delivery Note", {'name': dn}, ['posting_date'])
                si_parent = frappe.get_value("Sales Invoice Item", {'delivery_note': dn}, ['parent'])
                si_date = frappe.db.get_value("Sales Invoice", {'name': si_parent}, ['posting_date']) if si_parent else None
                
                data += '<tr style="background-color:#D9E2ED;">'
                data += '<td colspan="2" style="text-align:center;"><b>Item Code</b></td>'
                data += '<td colspan="2" style="text-align:center;"><b>Delivery Note</b></td>'
                
                if si_parent:
                    data += '<td colspan="2" style="text-align:center;"><b>Sales Invoice</b></td>'
                
                if dn_date:
                    data += '<td colspan="2" style="text-align:center;"><b>Delivery Date</b></td>'
                    if si_date:
                        data += '<td colspan="2" style="text-align:center;"><b>Invoiced Date</b></td>'
                
                data += '<td colspan="2" style="text-align:center;"><b>Warranty Terms</b></td>'
                data += '</tr>'
                data += '<tr>'
                data += '<td colspan="2" style="text-align:center;"><b>{}</b></td>'.format(item_code)
                data += '<td colspan="2" style="text-align:center;"><b>{}</b></td>'.format(dn)
                
                if si_parent:
                    data += '<td colspan="2" style="text-align:center;"><b>{}</b></td>'.format(si_parent)
                
                if dn_date:
                    data += '<td colspan="2" style="text-align:center;"><b>{}</b></td>'.format(dn_date)
                    if si_date:
                        data += '<td colspan="2" style="text-align:center;"><b>{}</b></td>'.format(si_date)
                
                data += '<td colspan="2" style="text-align:center;"><b>Not Disclosure</b></td>'
                data += '</tr>'
            else:
                data += '<tr><td colspan="10" style="text-align:center;"><b>Not Delivered Yet</b></td></tr>'

    data += '</table>'
    return data


@frappe.whitelist()
def update_marcom_values():
    marcom_projects = frappe.get_all("MARCOM  Project Reference", ['sales_invoice', 'name','consultant_company','consultant_name','custom_territory','custom_cluster','custom_total_qty','custom_price_list_region','so_submitted_date','so_status_live'])
    for project in marcom_projects:
        if project.sales_invoice is not None:
            so_values=frappe.get_all('Sales Order',{'name':project.sales_invoice},['sales_person_user','consultant_company','consultant_name','territory','cluster','total_qty','price_list_region','transaction_date','status'])
            for j in so_values:
                if not project.consultant_company:
                    frappe.db.set_value("MARCOM  Project Reference", project.name, 'consultant_company', j.consultant_company)
                if not project.consultant_name:
                    frappe.db.set_value("MARCOM  Project Reference", project.name, 'consultant_name', j.consultant_name)
                if not project.custom_territory:
                    frappe.db.set_value("MARCOM  Project Reference", project.name, 'custom_territory', j.territory)
                if not project.custom_cluster:
                    frappe.db.set_value("MARCOM  Project Reference", project.name, 'custom_cluster', j.cluster)
                if not project.custom_total_qty:
                    frappe.db.set_value("MARCOM  Project Reference", project.name, 'custom_total_qty', j.total_qty)
                if not project.custom_price_list_region:
                    frappe.db.set_value("MARCOM  Project Reference", project.name, 'custom_price_list_region', j.price_list_region)
                if not project.so_submitted_date:
                    frappe.db.set_value("MARCOM  Project Reference", project.name, 'so_submitted_date', j.transaction_date)
                if not project.so_status_live:
                    frappe.db.set_value("MARCOM  Project Reference", project.name, 'so_status_live', j.status)

@frappe.whitelist()
def update_qc_status(doc,method):
    value = 0
    if doc.pr_number:
        pr_item = frappe.get_doc("Purchase Receipt", doc.pr_number)
        if pr_item.docstatus != 2:	
            for k in pr_item.items:			
                inspect = frappe.db.count("Item Inspection", {"pr_number": doc.pr_number, "item_code": k.item_code,"docstatus":("!=",2)})
                if inspect:
                    value += inspect
            status = value / len(pr_item.items)
            frappe.db.set_value("Purchase Receipt",doc.pr_number,'custom_qc_pecentage',status*100)
            frappe.db.set_value("Purchase Receipt",doc.pr_number,'custom_count_of_item_inspection',value)
            if status == 0:
                frappe.db.set_value("Purchase Receipt",doc.pr_number,'custom_qc_status',"QC Pending")
            elif status == 1:
                frappe.db.set_value("Purchase Receipt",doc.pr_number,'custom_qc_status',"QC Completed")
            else:
                frappe.db.set_value("Purchase Receipt",doc.pr_number,'custom_qc_status',"QC Partially Completed")



@frappe.whitelist()
def update_qc_status_stock(doc,method):
    value = 0
    if doc.stock_entry:
        se_item = frappe.get_doc("Stock Entry", doc.stock_entry)
        if se_item.docstatus != 2:	
            for k in se_item.items:			
                inspect = frappe.db.count("Item Inspection", {"item_code": k.item_code,"docstatus":("!=",2)})
                if inspect:
                    value += inspect
            status = value / len(se_item.items)
            frappe.db.set_value("Stock Entry",doc.stock_entry,'custom_qc_percentage',status*100)
            frappe.db.set_value("Stock Entry",doc.stock_entry,'custom_count_of_item_inspection',value)
            if status == 0:
                frappe.db.set_value("Stock Entry",doc.stock_entry,'custom_qc_status',"QC Pending")
            elif status == 1:
                frappe.db.set_value("Stock Entry",doc.stock_entry,'custom_qc_status',"QC Completed")
            else:
                frappe.db.set_value("Stock Entry",doc.stock_entry,'custom_qc_status',"QC Partially Completed")
    
    

@frappe.whitelist()
def delete_pi():
    delete = frappe.db.sql(""" delete from `tabGL Entry` where name = 'ACC-GLE-2023-14024' """)

@frappe.whitelist()
def valuation_rate():
    latest_vr = frappe.db.get_value("Bin",{'item_code':'ENR-01004-N-LK','warehouse':'Stores - NCPL'},['valuation_rate'])
    if latest_vr:
        print(latest_vr)

        
@frappe.whitelist()
def item_ins_serial(bundle):
    item = frappe.get_doc("Serial and Batch Bundle",bundle)
    serial_numbers = []
    # return item.entries.serial_no
    for i in item.entries:
        serial_numbers.append(i.serial_no)
    return serial_numbers,i.batch_no
    
@frappe.whitelist()
def item_ins():
    item = frappe.get_doc("Serial and Batch Bundle","SABB-00000804")
    for i in item.entries:
        print(i.serial_no)
        print(i.batch_no)
        
        
from frappe.utils import now, cstr

# @frappe.whitelist()
# def create_serial_nums(item_code, docname,doctype, batch, serial_numbers):
#     item = frappe.get_cached_value("Item", item_code, ["description", "item_code", "batch_number_series"], as_dict=1)
#     like_filter = "%" + item.batch_number_series.split('.')[0] + "%"
#     batch_ser = frappe.db.get_value("Batch", filters={'name': ['like', like_filter]}, fieldname=["name"], order_by="name", as_dict=1)
#     last_five_digits = batch_ser.name
#     incremented_number = int(batch_ser.name[-5:]) + 1
#     new_string = batch_ser.name[:-5] + str(incremented_number).zfill(5)
    
#     batch_nos_details = []
#     user = frappe.session.user
#     batch_nos_details.append((new_string, new_string, now(), now(), user, user, item.item_code, item.item_name, item.description))
    
#     fields = ["name", "batch_id", "creation", "modified", "owner", "modified_by", "item", "item_name", "description"]
#     values = batch_nos_details  # Replace set(batch_nos_details) with batch_nos_details
    
#     frappe.db.bulk_insert("Batch", fields=fields, values=values)
#     frappe.msgprint(_("Batch Nos are created successfully"), alert=True)

# 	doc = frappe.get_doc(doctype, docname)
# 	success = True
# 	individual_serials = serial_numbers.split('\n')
# 	for individual_serial in individual_serials:
# 		individual_serial = individual_serial.strip()
# 		if not frappe.db.exists("Serial No", individual_serial):
# 			frappe.get_doc({
# 				"doctype": "Serial No",
# 				"serial_no": individual_serial,
# 				"creation": now(),
# 				"modified": now(),
# 				"owner": frappe.session.user,
# 				"modified_by": frappe.session.user,
# 				"item_code": item_code,
# 				"status": "Inactive",
# 				"batch_no": batch,
# 				"company": doc.company
# 			}).insert(ignore_permissions=True)
# 		else:
# 			success = False
# 			frappe.msgprint(_("Serial Number {0} already exists.").format(cstr(individual_serial)))
# 	if success:
# 		frappe.msgprint(_("Serial Numbers are created successfully"))
# 	return success


@frappe.whitelist()
def split_serial_numbers(serial_numbers):
    entries = []
    split_serial_numbers = serial_numbers.split('\n')

    for serial_number in split_serial_numbers:
        new_data = {
            'serial_no': serial_number.strip(),
            'batch_no': frappe.db.get_value("Serial No",serial_number.strip(),'batch_no')
        }
        entries.append(new_data)

    return entries


@frappe.whitelist()
def create_serial_nums(company,item_code, docname, doctype, serial_numbers):
    item = frappe.get_cached_value("Item", item_code, ["description", "item_code", "batch_number_series"], as_dict=1)
    if item.batch_number_series:
        like_filter = "%" + item.batch_number_series.split('.')[0] + "%"
        batch_ser = frappe.db.get_value("Batch", filters={'name': ['like', like_filter]}, fieldname=["name"], order_by="name", as_dict=1)
        if batch_ser:
            last_five_digits = batch_ser.name
            incremented_number = int(batch_ser.name[-5:]) + 1
            batch_name = batch_ser.name[:-5] + str(incremented_number).zfill(5)
        else:
            last_five_digits = "00000"
            incremented_number = 1
            batch_name = item.batch_number_series.split('.')[0] + str(incremented_number).zfill(5)


    
        batch_nos_details = []
        user = frappe.session.user
        batch_nos_details.append((batch_name, batch_name, now(), now(), user, user, item.item_code, item.item_name, item.description))
    
        fields = ["name", "batch_id", "creation", "modified", "owner", "modified_by", "item", "item_name", "description"]
        values = batch_nos_details
        
        frappe.db.bulk_insert("Batch", fields=fields, values=values)
        frappe.msgprint(_("Batch Nos are created successfully"), alert=True)

        # doc = frappe.get_doc(doctype, docname)
        success = True
        individual_serials = serial_numbers.split('\n')
        
        for individual_serial in individual_serials:
            individual_serial = individual_serial.strip()
            
            if not frappe.db.exists("Serial No", individual_serial):
                frappe.get_doc({
                    "doctype": "Serial No",
                    "serial_no": individual_serial,
                    "creation": now(),
                    "modified": now(),
                    "owner": frappe.session.user,
                    "modified_by": frappe.session.user,
                    "item_code": item_code,
                    "status": "Inactive",
                    # "batch_no": batch,
                    "company": company
                }).insert(ignore_permissions=True)
            else:
                success = False
                frappe.msgprint(_("Serial Number {0} already exists.").format(cstr(individual_serial)))
        
        if success:
            frappe.msgprint(_("Serial Numbers are created successfully"))
        
        return success ,batch_name

@frappe.whitelist()
def update_target():
    target = frappe.db.get_value("Sales Person", {'name':"Le Minh The"}, ['target'])
    print(target)
    
    
@frappe.whitelist()
def request_for_sample():
    doc = frappe.get_doc("Custom Settings","Custom Settings")
    for d in doc.mail_settings:
        if d.doctype_name == "Request for Sample Item" and d.company:
            data = ''
            count = 0
            items = frappe.db.sql("""select * from `tabRequest for Sample Item` where workflow_state = 'Issued' and company ='%s' """%(d.company),as_dict= True)
            data += 'Dear Sir/Mam,<br><br>Kindly Find the List of Sample Items Not Returned<br><table class="table table-bordered">'
            data += '<table class="table table-bordered"><tr><th>Document Name</th><th>Item Code</th><th>Qty</th><th>Rate</th><th>Customer</th><th>Company</th><th>Source Warehouse</th><th>Target Warehouse</th></tr>'
            for i in items:
                diff_date = date.today() - i.date
                item = frappe.db.get_value("Sample Items",{'parent':i.name},['item'])
                qty = frappe.db.get_value("Sample Items",{'parent':i.name},['quantity'])
                rate = frappe.db.get_value("Sample Items",{'parent':i.name},['rate'])
                if diff_date.days >= int(d.validity) and i.workflow_state == "Issued":
                    count += 1
                    data += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (i.name,item,qty,rate,i.customer,i.company,i.source_warehouse,i.target_warehouse)
            data += '</table>'
            if count > 0:
                frappe.sendmail(
                    recipients= d.recipients.split('\n'),
                    subject=('Sample Items Not Returned'),
                    message=data
                )

    # doc = frappe.get_doc("Custom Settings","Custom Settings")
    # for d in doc.mail_settings:
    #     if d.doctype_name == "Request for Sample Item" and d.company:
    #         u_list = []
    #         user_list = frappe.db.sql("""select user from `tabRequest for Sample Item` where workflow_state = 'Issued' """,as_dict= True)
    #         for us in user_list:
    #             if us.user not in u_list:
    #                 u_list.append(us.user)
    #         for li in u_list:
    #             data = ''	
    #             count = 0
    #             items = frappe.db.sql("""select * from `tabRequest for Sample Item` where workflow_state = 'Issued' and user = '%s' and company ='%s' """%(li,d.company),as_dict= True)
    #             data += 'Dear Sir/Mam,<br><br>Kindly Find the List of Sample Items Not Returned<br><table class="table table-bordered">'
    #             data += '<table class="table table-bordered"><tr><th>Document Name</th><th>Item Code</th><th>Qty</th><th>Rate</th><th>Customer</th><th>Company</th><th>Source Warehouse</th><th>Target Warehouse</th></tr>'
    #             for i in items:
    #                 diff_date = date.today() - i.date
    #                 item = frappe.db.get_value("Sample Items",{'parent':i.name},['item'])
    #                 qty = frappe.db.get_value("Sample Items",{'parent':i.name},['quantity'])
    #                 rate = frappe.db.get_value("Sample Items",{'parent':i.name},['rate'])
    #                 if diff_date.days >= int(d.validity) and i.workflow_state == "Issued":
    #                     count += 1
    #                     data += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (i.name,item,qty,rate,i.customer,i.company,i.source_warehouse,i.target_warehouse)
    #             data += '</table>'
    #             if count > 0:
    #                 frappe.sendmail(
    #                     recipients= li,
    #                     subject=('Sample Items Not Returned'),
    #                     message=data
    #                 )
     
        
@frappe.whitelist()
def serial_data():
    request_item = frappe.get_doc("Request for Sample Item","SMP-NSPL-2022-00005")
    for s in request_item.items:     
        print(s.item)          
        serial = frappe.get_doc("Serial No",{"item_code":s.item,"company":request_item.company,"name":s.serial_no})
        print(serial)



    

@frappe.whitelist()
def ledger_account():
    from_date = "2023-04-01"
    to_date = "2023-12-31"
    company = "Norden Communication Pvt Ltd"
    account = "Stock Adjustment - NCPL"
    ledger = frappe.db.sql("""select account, sum(debit) as opening_debit, sum(credit) as opening_credit from `tabGL Entry` where company = 'Norden Communication Pvt Ltd' and posting_date between '%s' and '%s' and account  = 'Sales - NCPL' """%(from_date,to_date),as_dict=True)
    # ledger = frappe.db.sql("""select account, sum(debit) as opening_debit, sum(credit) as opening_credit from `tabGL Entry` where company = 'Norden Communication Pvt Ltd' and (posting_date < '%s' or (ifnull(is_opening, 'No') = 'Yes' and posting_date >= '%s')) and account  = 'Stock Adjustment - NCPL' """%(from_date,to_date),as_dict=True)
    for g in ledger:
        print(g.opening_debit)
        # if not g.opening_debit:
        #     g.opening_debit = 0
        # if not g.opening_credit:
        #     g.opening_credit = 0
        # sq = frappe.db.sql(""" select company, sum(debit_in_account_currency) as debit,sum(credit_in_account_currency) as credit from `tabGL Entry` where company = 'Norden Communication Pvt Ltd' and account = 'Stock Adjustment - NCPL' and posting_date between '%s' and '%s' """%(from_date,to_date),as_dict=True)
        # for i in sq:
        #     if not i.credit:
        #         i.credit = 0
        #     if not i.debit:
        #         i.debit = 0
        #     op_credit = g.opening_credit + i.credit
        #     op_debit = g.opening_debit + i.debit
        #     print(op_debit)
  

# @frappe.whitelist()
# def update_budget():
#     name = frappe.db.get_value("Budget",{'company':'Norden Communication Pvt Ltd'},['name'])
#     print(name)
#     amount = frappe.get_all("Budget Account",{'parent':name},['account','budget_amount'])
#     for i in amount:
#         print(i.budget_amount)
#         print(i.account)


@frappe.whitelist()
def pr_number_item():
    pr = frappe.get_doc("Purchase Receipt","PR-NCPLP-2023-00191")
    for i in pr.items:
        print(i.conversion_factor)

@frappe.whitelist()
def update_budget():
    target = frappe.db.get_value("Budget", {'company':'Norden Communication Pvt Ltd'}, ['name'])
    if target:
        print(target)
        amount = frappe.get_all("Budget Account",{'parent':target},['account'])
        for i in amount:
            print(i.account)
            ledger = frappe.db.sql("""select account, sum(debit) as opening_debit from `tabGL Entry` where company = 'Norden Communication Pvt Ltd' and account  = '%s' """%(i.account),as_dict=True)
            for j in ledger:
                print(ledger)

@frappe.whitelist()
def si_name():
    si_names=frappe.get_all("Sales Invoice",{'company':'Norden Communication Middle East FZE'},['territory'],distinct = True)
    for i in si_names:
        print(i)

@frappe.whitelist()
def gross_profit():
    total = 0
    to_tal = 0
    value =0
    account = frappe.get_all('Account',['name','parent_account'])
    for i in account:
        
        if i.parent_account =='Stock Expenses - NCPL':
            
            gl_entries = frappe.get_all("GL Entry", {'company':'Norden Communication Pvt Ltd','account':i.name,'fiscal_year':'2023 - 2024'}, ['debit'])
            for entry in gl_entries:
                total += entry.debit
        if i.parent_account =='Direct Expenses - NCPL':
            print(i.name)
            gl_entries = frappe.get_all("GL Entry", {'company':'Norden Communication Pvt Ltd','account': i.name,'fiscal_year':'2023 - 2024'}, ['debit'])
            for entry in gl_entries:
                to_tal += entry.debit
        if i.parent_account == 'Indirect Expenses - NCPL':
            gl_entries = frappe.get_all("GL Entry", {'company':'Norden Communication Pvt Ltd','account': i.name,'fiscal_year':'2023 - 2024'}, ['debit'])
            for entry in gl_entries:
                value += entry.debit
    print(total-to_tal-value - 208848175.91399997)

@frappe.whitelist()
def company():
    total =0
    gross = frappe.get_all("GL Entry",{'account':'Sales - NCPL','company':'Norden Communication Pvt Ltd','fiscal_year':'2023 - 2024','is_cancelled':'0'},['credit'])
    for i in gross:
        total +=i.credit
    print(total)

@frappe.whitelist()
def get_store_warehouse(company):
    like_filter = "%"+"Stores "+"%"
    store_warehouse = frappe.db.get_value('Warehouse', filters={"company":company,"custom_stores":1,'name': ['like', like_filter]})
    return store_warehouse
            
@frappe.whitelist()
def account():
    total =0
    gross = frappe.get_all("Account",{'parent_account':'Direct Expenses - NCPL','company':'Norden Communication Pvt Ltd'},['name'])
    for i in gross:
        print(i.name)
  
@frappe.whitelist()
def get_rework_warehouse(company):
    like_filter = "%"+"Rework"+"%"
    store_warehouse = frappe.db.get_value('Warehouse', filters={"company":company,'name': ['like', like_filter]})
    return store_warehouse

@frappe.whitelist()
def get_rtv_warehouse(company):
    like_filter = "%"+"RTV"+"%"
    store_warehouse = frappe.db.get_value('Warehouse', filters={"company":company,'name': ['like', like_filter]})
    return store_warehouse

@frappe.whitelist()
def update_employee_no(name,employee_number):
    emp = frappe.get_doc("Employee",name)
    emps=frappe.get_all("Employee",{"status":"Active"},['*'])
    for i in emps:
        if emp.employee_number == employee_number:
            pass
        elif i.employee_number == employee_number:
            frappe.throw(f"Employee Number already exists for {i.name}")
        else:
            frappe.db.set_value("Employee",name,"employee_number",employee_number)
            frappe.rename_doc("Employee", name, employee_number, force=1)
            return employee_number

@frappe.whitelist()
def mrb_create(doc,method):
    if doc.company == "Norden Communication Pvt Ltd":
        data = '' 
        data += 'Dear Sir/Mam,<br><br>MRB Created Against Purchase Receipt<br><table class="table table-bordered" border="1">'
        data += '<tr><td>Purchase Receipt</td><td>%s</td></tr>' % doc.name
        data += '<tr><td>Item Code</td><td>%s</td></tr>' % doc.item_code
        data += '<tr><td>Item Name</td><td>%s</td></tr>' % doc.description
        data += '</table>'
        qc = frappe.get_single("QC Team").qc_team
        for j in qc:
            frappe.sendmail(
                recipients= j.email_id,
                subject=('MRB Creation'),
                message=data
            )


@frappe.whitelist()
def pr_create(doc,method):
    if doc.company == "Norden Communication Pvt Ltd":
        data = '' 
        data += 'Dear Sir/Mam,<br><br>Kindly Check the Submitted Purchase Receipt<br><table class="table table-bordered" border="1">'
        data += '<tr><td>Purchase Receipt</td><td>%s</td></tr>' % doc.name
        for i in doc.items:
            data += '<tr><td>Item Code</td><td>%s</td></tr>' % i.item_code
            data += '<tr><td>Item Name</td><td>%s</td></tr>' % i.description
            data += '</table>'
            qc = frappe.get_single("QC Team").qc_team
            for j in qc:
                frappe.sendmail(
                    recipients= j.email_id,
                    subject=('Purchase Receipt'),
                    message=data
                )

@frappe.whitelist()
def update_field_ins():
    att = frappe.db.sql(""" update  `tabItem Inspection`  set sample_qty = sample_reference """)


@frappe.whitelist()
def update_batch_qty():
    po = frappe.db.sql("""update `tabBatch` set batch_qty = '0' where name ='B3F127B' """)


# @frappe.whitelist()
# def list_invoices():
# 	list = frappe.db.get_list("Sales Invoice",{'title':'{customer_name}'},['name','customer'])
# 	for i in list:
# 		frappe.db.set_value("Sales Invoice",i.name,'title',i.customer)
# 		print(i.customer)


@frappe.whitelist()
def count_qty():
    sl = frappe.db.sql(""" select name from `tabStock Entry` where posting_date between "2023-01-01" and "2023-01-31" and docstatus != 2 """,as_dict=True)
    for i in sl:
        qty_list = frappe.get_all("Stock Entry Detail", {"parent": i.name}, ["qty"])
        total_qty = 0
        for entry in qty_list:
            total_qty += entry.get("qty", 0)
        print("Total Quantity:", total_qty)

# @frappe.whitelist()
# def count_qty(item=None,warehouse=None,rack = None):
#     if rack:
#         entries = frappe.get_all("Stock Ledger Entry", filters={"is_cancelled": 0,"item_code":item,"rack":rack,"warehouse":warehouse}, fields=["actual_qty"])
#         total_qty = sum(entry["actual_qty"] for entry in entries)
#         rack = rack
#         return {"rack": rack, "qty": total_qty}
#     else:
#         entries = frappe.get_all("Stock Ledger Entry", 
#                                  filters={"is_cancelled": 0, "item_code": item, "warehouse": warehouse}, 
#                                  fields=["actual_qty", "rack"])
        
#         rack_qty_map = {}
#         for entry in entries:
#             if entry["rack"]:
#                 rack_name = entry["rack"]
#                 rack_qty_map[rack_name] = rack_qty_map.get(rack_name, 0) + entry["actual_qty"]
        
#         return [{"rack": rack, "qty": qty} for rack, qty in rack_qty_map.items()]


@frappe.whitelist()
def count_qty(item=None, warehouse=None, rack=None):

    filters = {
        "is_cancelled": 0,
        "item_code": item,
        "warehouse": warehouse
    }

    if rack:
        filters["rack"] = rack

    entries = frappe.get_all(
        "Stock Ledger Entry",
        filters=filters,
        fields=["rack", "actual_qty"]
    )

    rack_qty_map = {}

    for entry in entries:
        rack_value = entry.rack or ""   # 👈 handle empty rack

        rack_qty_map.setdefault(rack_value, 0)
        rack_qty_map[rack_value] += entry.actual_qty

    result = []

    for r, qty in rack_qty_map.items():
        if qty > 0:
            result.append({
                "rack": r,   # will return "" if no rack
                "qty": qty
            })

    return result

@frappe.whitelist()
def qty_count():
    current_year = datetime.now().year
    jan_start_date = f"{current_year}-01-01"
    jan_end_date = f"{current_year}-01-31"
    jan_si = frappe.db.sql("""SELECT name FROM `tabSales Invoice` WHERE posting_date BETWEEN %s AND %s AND docstatus != 2 AND company = %s """, (jan_start_date, jan_end_date, "Norden Communication Middle East FZE"), as_dict=True)
    jan_qty = 0
    for jan in jan_si:
        jan_qty += frappe.get_value("Sales Invoice Item", {"parent": jan.name}, fieldname="sum(qty)")
    print(jan_qty)


# @frappe.whitelist()
# def update_batch_series():
# 	count = frappe.db.get_list("Item",{'has_serial_no':1,'disabled':0},['name'])
# 	for i in count:
# 		frappe.db.set_value("Item",i.name,'batch_number_series',i.name+'.######',update_modified=False)
# 		print(i.name+'.######')

@frappe.whitelist()
def set_batch():
    # list = frappe.db.get_list("Serial No", {'item_code': "NVS-L1001006CS", 'warehouse': "Stores - NCPL"},limit=438, order_by='name asc')
    # for i in list:
    frappe.db.set_value('Serial No',"NVS70140001TP102023003",'batch_no','NVS701TP')
        # print(list)


# @frappe.whitelist()
# def update_conv_rate():
# 	name = 'F-Q-NSPL-2023-00474'
# 	frappe.db.set_value('Quotation',name,'conversion_rate','1.38',update_modified=False)
# 	frappe.db.set_value('Quotation',name,'plc_conversion_rate','1.38',update_modified=False)



# @frappe.whitelist()
# def update_custom_delivered_qty():
# 	delivery_note=frappe.get_all("Delivery Note",{"docstatus":("!=",2),"creation":("<=","2024-02-27")},["*"])
# 	for d in delivery_note:
# 		# if not d.custom_packed_by:
# 		# 	frappe.db.set_value("Delivery Note",d.name,"custom_packed_by", d.packed_by)
# 		if not d.custom_contact:
# 			frappe.db.set_value("Delivery Note",d.name,"custom_contact", d.contact_resp)
@frappe.whitelist()
def check_query():
    doc = frappe.get_doc("Quotation","F-Q-NSPL-2023-00486")

    for j in doc.items:
        country = frappe.get_value("Company", {"name": doc.company}, ["country"])
        warehouse_stock = frappe.db.sql("""
            SELECT SUM(b.actual_qty - b.reserved_stock) AS qty
            FROM `tabBin` AS b
            JOIN `tabWarehouse` AS wh ON wh.name = b.warehouse
            JOIN `tabCompany` AS c ON c.name = wh.company
            WHERE c.country = %s AND b.item_code = %s
        """, (country, j.item_code), as_dict=True)[0]
        if not warehouse_stock["qty"]:
            warehouse_stock["qty"] = 0



# @frappe.whitelist()
# def update_serialno(filename):
# 	from frappe.utils.file_manager import get_file
# 	_file = frappe.get_doc("File", {"file_name": filename})
# 	filepath = get_file(filename)
# 	ips = read_csv_content(filepath[1])
# 	for ip in ips:
# 		frappe.db.set_value("Serial No",ip[0],"warehouse","Stores - NSPL",update_modified=False)
# 		print(ip[0])
# 		print(ip[1])

# @frappe.whitelist()
# def update_sostatus():
# 	frappe.db.set_value("Quotation",'F-Q-NCMET-2024-00437','work_flow','Pending for Sales Manager')


@frappe.whitelist()
def getdetailso():
    item_code = "122-41T180WH"
    company = "Norden Communication Middle East FZE"
    so_details = []
    pending_qty = 0
    sa = frappe.db.sql("""
        SELECT `tabSales Order Item`.parent AS parent,
            sum(`tabSales Order Item`.qty) AS qty,
            `tabSales Order Item`.delivered_qty AS delivered_qty
        FROM `tabSales Order`
        LEFT JOIN `tabSales Order Item` ON `tabSales Order`.name = `tabSales Order Item`.parent
        WHERE `tabSales Order Item`.item_code = '%s'
        AND `tabSales Order`.docstatus != 2
        AND `tabSales Order`.company = '%s'
        GROUP BY `tabSales Order Item`.parent
        ORDER BY `tabSales Order`.transaction_date
    """ % (item_code, company), as_dict=True)

    for i in sa:
        reser_qty = frappe.db.get_value("Stock Reservation Entry",{"voucher_no":i.parent,"docstatus":("!=",2),"item_code":item_code,"status": ["in", ["Reserved", "Partially Reserved"]]},["reserved_qty"])
        if not i.qty:
            i.qty = 0
        if not i.delivered_qty:
            i.delivered_qty = 0
        pending_qty = i.qty - i.delivered_qty
        sb = frappe.get_doc("Sales Order", i.parent)
        if sb.custom_reservation_status == "Reserved":
            so_details.append(frappe._dict({"parent":i.parent,"qty":i.qty,"reserved_qty":reser_qty,"pending_qty":pending_qty,"rate":i.rate,"delivered_qty":i.delivered_qty,"transaction_date":sb.transaction_date,"customer":sb.customer,"po_no":sb.po_no,"status":sb.custom_reservation_status}))
        else:
            so_details.append(frappe._dict({"parent":i.parent,"qty":i.qty,"pending_qty":pending_qty,"rate":i.rate,"delivered_qty":i.delivered_qty,"transaction_date":sb.transaction_date,"customer":sb.customer,"po_no":sb.po_no,"status":" "}))
    return sa

# @frappe.whitelist()
# def update_poqty():
#     att = frappe.db.sql(""" delete from `tabGL Entry` where voucher_no = "DN-24-00001" """)

@frappe.whitelist()
def avaliable_qty():
    ac=0
    reser=0
    warehouse = frappe.get_all("Warehouse",{"company":"Norden Communication Middle East FZE"},["name"])
    for i in warehouse:
        value = frappe.get_all("Bin",{"item_code":"352-SLCLC","warehouse":i.name},["actual_qty","reserved_stock"])
        for j in value:
            ac+=j.actual_qty
            reser+=j.reserved_stock
    print(ac-reser)

@frappe.whitelist()
def pick_list_duplicate(doc):
    pl = frappe.db.sql(""" select `tabPick List Item`.item_code,
    sum(`tabPick List Item`.qty) as qty,
    `tabPick List Item`.item_name,`tabPick List Item`.description,`tabPick List Item`.stock_uom from `tabPick List` 
    left join `tabPick List Item` on `tabPick List`.name = `tabPick List Item`.parent where `tabPick List`.name = '%s' group by `tabPick List Item`.item_code order by `tabPick List Item`.idx """%(doc),as_dict = 1)
    return pl
        

@frappe.whitelist()
def region_price_list(territory):
    list = frappe.db.get_list("Price List based on Territory",{'territory':territory},['name'])
    return list



@frappe.whitelist()
def create_internal_price(item_code,company,doc_currency):
    # w_house = frappe.db.get_value("Warehouse",{'default_for_stock_transfer':1,'company':company},['name'])
    # val_rate = frappe.db.get_value("Bin",{'item_code':item_code,'warehouse':w_house},['valuation_rate'])* 1.3
    val_rate = frappe.db.get_value("Item Price",{'item_code':item_code,'price_list':"STANDARD BUYING-USD"},['price_list_rate'])* 1.3
    cur = frappe.db.get_value("Price List",{'name':"Internal Transfer Price"},['currency'])
    usd_cur = frappe.db.get_value("Price List",{'name':"STANDARD BUYING-USD"},['currency'])
    # cr_ex = get_exchange_rate(frappe.get_value("Company",company,["default_currency"]),cur)
    cr_ex = get_exchange_rate(usd_cur,cur)
    cp = cr_ex * val_rate
    existing_ip = frappe.db.exists('Item Price',{'price_list':'Internal Transfer Price','item_code':item_code})
    if not existing_ip:
        price_list = "Internal Transfer Price"
        doc = frappe.new_doc("Item Price")
        doc.item_code = item_code
        doc.price_list = price_list
        doc.selling = 1
        doc.buying = 1
        doc.valid_from = '2022-01-01'
        doc.price_list_rate = cp
        doc.save(ignore_permissions=True)
        frappe.db.commit()

    # else:
    #     frappe.db.set_value("Item Price",existing_ip,'price_list_rate',cp)
    #     frappe.db.set_value("Item Price",existing_ip,'valid_from','2022-01-01')


@frappe.whitelist()
def update_sales_percentage():
    list = frappe.db.get_list("Sales Invoice",{'docstatus':0},["name","sales_person_user"])
    for i in list:
        if i.sales_person_user:
            doc = frappe.get_doc("Sales Invoice",i.name)
            si = ["SI-NCI-22-00475","PI-NCI-23-00008","SI-NCI-23-00071"]
            # si = ["PI-NCI-23-00008","SI-PI-NCMEF-2024-00002","SI-PI-NCMEF-2024-00001","PI-NCI-23-00029","PI-NCI-23-00030","SI-NCI-23-00209","SI-NCI-23-00096","SI-NCI-23-00211","SI-NCI-23-00224","SI-NCI-23-00225"]
            if not doc.sales_team and not doc.sales_person_user and doc.name not in si:
                print(i.name)
                doc.set("sales_team",[])
                doc.append("sales_team",{
                    "allocated_amount":doc.net_total,
                    "sales_person":doc.sales_person_user,
                    "allocated_percentage":100
                })
                doc.save(ignore_permissions=True)
                doc.flags.ignore_mandatory = True

@frappe.whitelist()
def get_base_rate(so_no,item,territory):
    so=frappe.get_doc("Sales Order",so_no)
    quot=frappe.get_doc("Quotation",{"file_number":so.file_number})
    for j in quot.items:
        if j.item_code==item:
            item_group=frappe.db.get_value("Item",{"name":item},['item_sub_group'])
            
            margin_price=frappe.get_doc("Margin Price Tool")
            if territory in ['Dubai','United Arab Emirates']:
                
                for t in margin_price.dubai:
                    if t.item_group == item_group:
                        internal_cost = j.base_cost * t.internal
                        landing_cost = j.base_cost * t.landing
                        incentive_cost = j.base_cost * t.incentive
                        return j.base_cost,internal_cost,landing_cost,incentive_cost
                        # frappe.db.set_value("Sales Invoice Item",name,"custom_base_cost",internal_cost)
            

@frappe.whitelist()
def get_base_cost(name, item):
    items = frappe.db.get_all("Sales Order Item", {"parent": name, 'item_code': item}, ['*'])
    val = items[0].custom_base_rate
    landing_cost = items[0].custom_landing_rate
    incentive_cost = items[0].custom_incentive_rate
    internal_cost = items[0].custom_internal_rate
    return [val, landing_cost, incentive_cost, internal_cost]

@frappe.whitelist()
def update_account_currency(name):
    account=frappe.db.get_value("Account",{"name":name},['account_currency'])
    return account

@frappe.whitelist()
def update_base_rate_new(doc,method):
    so=frappe.get_doc("Sales Order",doc.name)
    if so.company=='Norden Communication Middle East FZE':
        for i in so.items:
            items = frappe.db.get_all("Sales Order Item", {"parent": doc.name, 'item_code': i.item_code}, ['*'])
            warehouse = frappe.db.get_value("Warehouse", {'company': "Norden Communication Middle East FZE", 'default_for_stock_transfer': 1}, ['name'])
            val_rate = frappe.db.get_value("Bin", {"item_code": i.item_code, "warehouse": warehouse}, ['valuation_rate'])
            val = 0
            landing_cost = 0
            incentive_cost = 0
            internal_cost = 0
            item_group = frappe.db.get_value("Item", {"name": i.item_code}, ['item_sub_group'])

            if val_rate>0:
                    val = float(val_rate)
            else:
                val=frappe.db.get_value("Item Price", {"item_code": i.item_code, 'price_list': "Cost Rate - NCMEF"}, ['price_list_rate'])
                if not val:
                    val=0
            margin_price = frappe.get_doc("Margin Price Tool")
            for t in margin_price.dubai:
                if t.item_group == item_group:
                    landing_cost = val * t.landing
                    incentive_cost = landing_cost * t.incentive

            price = frappe.db.get_value("Item Price", {"item_code": i.item_code, 'price_list': "Internal - NCMEF"}, ['price_list_rate'])
            if price:
                internal_cost = price

            i.custom_base_rate = val
            i.custom_internal_rate = internal_cost
            i.custom_landing_rate = landing_cost
            i.custom_incentive_rate = incentive_cost

        so.save(ignore_permissions=True)
        frappe.db.commit()

@frappe.whitelist()
def get_del_base_cost(name, item):
    items = frappe.db.get_all("Sales Order Item", {"parent": name, 'item_code': item}, ['*'])
    val = items[0].custom_base_rate
    landing_cost = items[0].custom_landing_rate
    incentive_cost = items[0].custom_incentive_rate
    internal_cost = items[0].custom_internal_rate
    return [val, landing_cost, incentive_cost, internal_cost]
# @frappe.whitelist()
# def update_emirate():
#     list = frappe.db.get_list("Address",{"country":"United Arab Emirates"},['name','emirate'])
#     for i in list:
#         if i.emirate:
#             doc = frappe.get_doc("Address",i.name)
#             for k in doc.links:
#                 if k.link_doctype == "Customer":
#                     val = frappe.db.get_value("Customer",k.link_name,"territory")
#                     if val != i.emirate:
#                         # d = frappe.get_doc("Customer",k.link_name)
#                         # d.territory = i.emirate
#                         # d.save(ignore_permissions=True)
#                         frappe.db.set_value("Customer",k.link_name,"territory",i.emirate)
#                         print(k.link_name)


@frappe.whitelist()
def return_mr_stock(company,item_code):
    warehouse_stock = frappe.db.sql("""
            SELECT SUM(b.actual_qty - b.reserved_stock) AS qty
            FROM `tabBin` AS b
            JOIN `tabWarehouse` AS wh ON wh.name = b.warehouse
            JOIN `tabCompany` AS c ON c.name = wh.company
            WHERE c.name = %s AND b.item_code = %s AND wh.is_scrap !=1
        """, (company,item_code), as_dict=True)[0]
    return warehouse_stock

@frappe.whitelist()
def update_ins():
    new_po = frappe.db.sql("""select sum(`tabPurchase Order Item`.qty) as qty,sum(`tabPurchase Order Item`.received_qty) as d_qty from `tabPurchase Order`
    left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
    where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus = 1 and `tabPurchase Order`.company = '%s' and `tabPurchase Order Item`.qty >= `tabPurchase Order Item`.received_qty """ % ('121-41T18024B','Norden Communication Middle East FZE'), as_dict=True)[0]
    if not new_po['qty']:
        new_po['qty'] = 0
    if not new_po['d_qty']:
        new_po['d_qty'] = 0
    ppoc_total = new_po['qty'] - new_po['d_qty']
    print(ppoc_total)
    # frappe.db.set_value("Request for Sample Item", "SMP-NCPLP-2023-00018", "stock_returned","SE-2024-00303")
    # frappe.db.set_value("Request for Sample Item", "SMP-NCPLP-2023-00020", "stock_issued","SE-2024-00087")
    # frappe.db.set_value("Request for Sample Item", "SMP-NCPLP-2023-00020", "custom_is_stock_issued",1)



def update_series_based_on_fy():
    date = "2024-04-01"
    company = "Norden Africa"
    doctype = "File Number"
    company_series = frappe.db.get_value("Company Series",{'company': company, 'document_type': doctype, 'with_tax': 0},'series')
    updated_series = company_series
    fy_info = frappe.db.sql(""" SELECT year, year_start_date, year_end_date FROM `tabFiscal Year` LEFT JOIN `tabFiscal Year Company` ON `tabFiscal Year`.name = `tabFiscal Year Company`.parent WHERE `tabFiscal Year`.custom_active_fy = 1 AND `tabFiscal Year Company`.company = %s """, (company), as_dict=True)
    if fy_info and doctype != "File Number": 
        if len(fy_info[0]['year']) == 4:
            fy_year = fy_info[0]['year']
            previous_year = int(fy_year)-1
            fy_start_date = datetime.strptime(str(fy_info[0]['year_start_date']), '%Y-%m-%d').date()
            fy_end_date = datetime.strptime(str(fy_info[0]['year_end_date']), '%Y-%m-%d').date()
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()        
            if fy_start_date <= date_obj <= fy_end_date:
                updated_series = company_series
            else:
                if "YYYY" in company_series:
                    updated_series = company_series.replace("YYYY", str(previous_year))
        else:
            fy_year = fy_info[0]['year']
            fyear = fy_year[0:4]
            f_year = str(fy_year[2:4]) + str(fy_year[-2:])
            prev_year = str(int(fy_year[2:4]) - 1) + str(int(fy_year[-2:]) -1)
            previous_year = int(fyear)-1
            fy_start_date = datetime.strptime(str(fy_info[0]['year_start_date']), '%Y-%m-%d').date()
            fy_end_date = datetime.strptime(str(fy_info[0]['year_end_date']), '%Y-%m-%d').date()
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()        
            if fy_start_date <= date_obj <= fy_end_date:
                updated_series = company_series
            else:
                if fyear in company_series:
                    updated_series = company_series.replace(fyear, str(previous_year))
                elif f_year in company_series and doctype == "Sales Invoice":
                    updated_series = company_series.replace(f_year, str(prev_year))
    return updated_series

@frappe.whitelist()
def list_se():
    list = frappe.db.sql(""" select name from `tabStock Entry` where name = 'SE-NCPLP-2023-00477' """,as_dict =1)
    for i in list:
        doc = frappe.get_doc("Stock Entry",i.name)
        for k in doc.items:
            if k.serial_and_batch_bundle:
                cal = k.qty + frappe.db.get_value("Serial and Batch Bundle",k.serial_and_batch_bundle,'total_qty')
                # if cal != 0:
                # 	print(i.name)
                # 	print(k.item_code)
                print(cal)
@frappe.whitelist()
def update():
    frappe.db.sql("update `tabLeave Application` set workflow_state='Pending for HOD' where name='HR-LAP-2024-00342'")


# @frappe.whitelist()
# def update_slw():
# 	doc = frappe.get_doc("Bin",'c10d5e8fcf')
# 	doc.actual_qty = 3
# 	doc.flags.ignore_validate_update_after_submit = True
# 	doc.save(ignore_permissions=True)


    # doc = frappe.get_doc("Batch",'NVS-90010251MA00010')
    # doc.batch_qty = 3
    # doc.flags.ignore_validate_update_after_submit = True
    # doc.save(ignore_permissions=True)

    # doc = frappe.get_doc("Serial and Batch Bundle","SABB-00020974")
    # doc.avg_rate = 25,658.5633
    # doc.total_amount = 76975.71
    # doc.voucher_detail_no = "f0ced4c1ea"
    # doc.flags.ignore_validate_update_after_submit = True
    # doc.save(ignore_permissions=True)
    # doc = frappe.get_doc("Stock Ledger Entry","MAT-SLE-2024-08987")

    # doc.serial_and_batch_bundle = "SABB-00022499"
    # doc.qty_after_transaction = 3
    # doc.stock_value = 76975.71
    # doc.stock_value_difference = -25658.57
    # doc.flags.ignore_validate_update_after_submit = True
    # doc.save(ignore_permissions=True)

@frappe.whitelist()
def getitemrate():
    item_code = "ENB-BTUJ66"
    price_list = "Project Group - NCMEF"
    doc_currency = "SAR"
    uom = frappe.db.get_value("Item",item_code,'stock_uom')
    unit_price = frappe.get_value("Item Price",{"item_code":item_code,"price_list":price_list},["price_list_rate"])
    unit_price_document_currency = 0
    if unit_price:
        print(get_exchange_rate("AED",doc_currency))
        print(get_exchange_rate(doc_currency,"AED"))
        unit_price_document_currency = unit_price * get_exchange_rate(frappe.get_value("Item Price",{"item_code":item_code,"price_list":price_list},["currency"]),doc_currency)
    return unit_price,unit_price_document_currency,uom

@frappe.whitelist()
def submit_dn():
    frappe.db.sql("""UPDATE `tabSerial No` SET batch_no = 'NVS-11160030MS1' WHERE name = 'NVS-11160030MS072023002'""")
    # company = frappe.db.get_list("Company")
    # for com in company:
    # 	doc = frappe.db.sql("""
    # 		SELECT b.actual_qty, b.reserved_stock, b.warehouse, b.stock_uom, b.stock_value, c.company_name 
    # 		FROM tabBin b
    # 		JOIN tabWarehouse w ON b.warehouse = w.name
    # 		JOIN tabCompany c ON w.company = c.name
    # 		WHERE b.item_code = '%s' AND w.company = '%s'
    # 		ORDER BY c.company_name
    # 	""" % ("52-1502RD2", com.name), as_dict=True)
    # 	# stocks = frappe.db.sql("""select (sum(`tabBin`.actual_qty) - sum(reserved_stock)) as actual_qty,`tabBin`.warehouse as warehouse,`tabBin`.stock_uom as stock_uom,`tabBin`.stock_value as stock_value from `tabBin`
    # 	# 						join `tabWarehouse` on `tabWarehouse`.name = `tabBin`.warehouse
    # 	# 						join `tabCompany` on `tabCompany`.name = `tabWarehouse`.company
    # 	# 						where `tabBin`.item_code = '%s' and `tabWarehouse`.company = '%s' """ % (item,company), as_dict=True)
    # 	for i in doc:
    # 		print(i)

@frappe.whitelist()
def list_cdn_qty():
    list = frappe.db.sql(""" select parent from `tabDelivery Note Item` where custom_custom_delivered_qty != qty and custom_custom_delivered_qty >0 """,as_dict = 1)
    for i in list:
        print(i.parent)

@frappe.whitelist()
def dn_contact_details(name,email,mobile,customer):
    contact = frappe.new_doc("Contact")
    contact.first_name = name
    if email:
        contact.email_id_ = email
        contact.append('email_ids',{
            'email_id': email		
        })
    if mobile:
        contact.mobile_no = mobile
        contact.append('phone_nos',{
            'phone':mobile,
        })
    contact.custom_delivery_note = 1
    contact.append('links',{
        'link_doctype':'Customer',
        "link_name": customer
    })
    contact.save(ignore_permissions=True)
    return contact.name

@frappe.whitelist()
def submitse():
    se = frappe.get_doc("Stock Entry","SE-NCMEF-2024-00403")
    se.submit()

@frappe.whitelist()
def get_file_number(doc,method):
    if not doc.amended_from:
        if doc.doctype=="Opportunity":
            company_series = frappe.db.get_value("Company Series",{'company':doc.company,'document_type':'File Number','with_tax':0},'series')
            fn_doc = frappe.new_doc("File Number")
            fn_doc.company = doc.company
            fn_doc.naming_series = company_series
            fn_doc.save(ignore_permissions=False)
            frappe.db.set_value("Opportunity",doc.name,"file_number",fn_doc.name)

        elif doc.doctype =="Quotation":
            if not doc.opportunity:
                company_series = frappe.db.get_value("Company Series",{'company':doc.company,'document_type':'File Number','with_tax':0},'series')
                fn_doc = frappe.new_doc("File Number")
                fn_doc.company = doc.company
                fn_doc.naming_series = company_series
                fn_doc.save(ignore_permissions=False)
                frappe.db.set_value("Quotation",doc.name,"file_number",fn_doc.name)
            else:
                file_no = frappe.db.get_value("Opportunity",{"name":doc.opportunity},["file_number"])
                frappe.db.set_value("Quotation",doc.name,"file_number",file_no)

        elif doc.doctype=="Material Request":
            if not doc.sales_order_number:
                company_series = frappe.db.get_value("Company Series",{'company':doc.company,'document_type':'File Number','with_tax':0},'series')
                fn_doc = frappe.new_doc("File Number")
                fn_doc.company = doc.company
                fn_doc.naming_series = company_series
                fn_doc.save(ignore_permissions=False)
                frappe.db.set_value("Material Request",doc.name,"file_number",fn_doc.name)
            else:
                file_no = frappe.db.get_value("Sales Order",{"name":doc.sales_order_number},["file_number"])
                frappe.db.set_value("Material Request",doc.name,"file_number",file_no)

    else:
        if not doc.file_number:
            if doc.doctype=="Opportunity":
                company_series = frappe.db.get_value("Company Series",{'company':doc.company,'document_type':'File Number','with_tax':0},'series')
                fn_doc = frappe.new_doc("File Number")
                fn_doc.company = doc.company
                fn_doc.naming_series = company_series
                fn_doc.save(ignore_permissions=False)
                frappe.db.set_value("Opportunity",doc.name,"file_number",fn_doc.name)

            elif doc.doctype =="Quotation":
                if not doc.opportunity:
                    company_series = frappe.db.get_value("Company Series",{'company':doc.company,'document_type':'File Number','with_tax':0},'series')
                    fn_doc = frappe.new_doc("File Number")
                    fn_doc.company = doc.company
                    fn_doc.naming_series = company_series
                    fn_doc.save(ignore_permissions=False)
                    frappe.db.set_value("Quotation",doc.name,"file_number",fn_doc.name)
                else:
                    file_no = frappe.db.get_value("Opportunity",{"name":doc.opportunity},["file_number"])
                    frappe.db.set_value("Quotation",doc.name,"file_number",file_no)

            elif doc.doctype=="Material Request":
                if not doc.sales_order_number:
                    company_series = frappe.db.get_value("Company Series",{'company':doc.company,'document_type':'File Number','with_tax':0},'series')
                    fn_doc = frappe.new_doc("File Number")
                    fn_doc.company = doc.company
                    fn_doc.naming_series = company_series
                    fn_doc.save(ignore_permissions=False)
                    frappe.db.set_value("Material Request",doc.name,"file_number",fn_doc.name)
                else:
                    file_no = frappe.db.get_value("Sales Order",{"name":doc.sales_order_number},["file_number"])
                    frappe.db.set_value("Material Request",doc.name,"file_number",file_no)


@frappe.whitelist()
def delete_file_number():
    att = frappe.db.sql(""" delete from `tabSubmission Queue` where name='109a7eb421' """)
    print(att)

@frappe.whitelist()
def check_qc_completion(doc,method):
    if doc.custom_skip_qc==0:

        for i in doc.locations:
        
            if i.custom_inspection_completed==0 and i.custom_skip_qc==0:
                
                frappe.throw(f"Item Inspection is not completed for the Item:{i.item_code}")



@frappe.whitelist()
def get_stockdetails():
    doc = frappe.get_doc("Sales Order","SO-NCMEFT-2024-00507")
    for j in doc.items:
        del_note = frappe.db.get_all("Delivery Note", {"file_number": doc.file_number,"docstatus":("!=",2)}, ['*'])
        if del_note:
            del_qty = 0
            for i in del_note:
                deli_note = frappe.get_doc("Delivery Note", i.name)
                if deli_note.items:
                    for item in deli_note.items:
                        if j.item_code == item.item_code:
                            del_qty += item.qty
            available_qty = 0
            nonavailable_qty = 0
            warehouse = []
            st = 0
            ware = frappe.db.get_list("Warehouse", {"company": doc.company}, ['name'])
            for w in ware:
                bin = frappe.get_all("Bin",{"item_code":j.item_code,"warehouse":w.name},['actual_qty','reserved_stock'])
                sto = sum([value.get("actual_qty", 0) for value in bin]) - sum([value.get("reserved_stock", 0) for value in bin])
                if sto and sto>0:
                    st+=sto
                    warehouse.append(w.name)

                    reserve = frappe.db.sql("""
                        SELECT (sum(reserved_qty) - sum(delivered_qty)) as reserved_qty 
                        FROM `tabStock Reservation Entry` 
                        WHERE voucher_no = %s 
                        AND item_code = %s 
                        AND docstatus != 2
                    """, (doc.name, j.item_code), as_dict=1)

                    if reserve:
                        reser_qty = reserve[0]['reserved_qty']
                    else:
                        reser_qty = 0

                    if reser_qty and reser_qty > 0:
                        available_qty = reser_qty
                    else:
                        if sto and j.qty > sto:
                            available_qty = sto
                            
                        elif sto and j.qty < sto:
                            available_qty = j.qty
            nonavailable_qty = (j.qty - del_qty) - available_qty
        else:
            available_qty = 0
            nonavailable_qty = 0
            warehouse = []
            st = 0
            ware = frappe.db.get_list("Warehouse", {"company": doc.company}, ['name'])
            for w in ware:
                bin = frappe.get_all("Bin",{"item_code":j.item_code,"warehouse":w.name},['actual_qty','reserved_stock'])
                sto = sum([value.get("actual_qty", 0) for value in bin]) - sum([value.get("reserved_stock", 0) for value in bin])
                if sto and sto>0:
                    st+=sto
                    warehouse.append(w.name)

                    reserve = frappe.db.sql("""
                        SELECT (sum(reserved_qty) - sum(delivered_qty)) as reserved_qty
                        FROM `tabStock Reservation Entry` 
                        WHERE voucher_no = %s 
                        AND item_code = %s 
                        AND docstatus != 2
                    """, (doc.name, j.item_code), as_dict=1)

                    if reserve:
                        reser_qty = reserve[0]['reserved_qty']
                    else:
                        reser_qty = 0

                    if reser_qty and reser_qty > 0:
                        available_qty = reser_qty
                    else:
                        if sto and j.qty > sto:
                            available_qty = sto
                            
                        elif sto and j.qty < sto:
                            available_qty = j.qty
            nonavailable_qty = j.qty - available_qty
            print(nonavailable_qty)



@frappe.whitelist()
def return_dn_qty(name):
    dn_qty = frappe.db.sql(""" select delivered_qty from `tabSales Order Item` where name = '%s' """%(name),as_dict=True)[0]
    return dn_qty

@frappe.whitelist()
def pick_qty_list():
    doc = frappe.get_doc("Sales Order","SO-NCMEF-2024-00243")
    for j in doc.items:
        av_qty = j.qty - j.delivered_qty
        if av_qty > 0:
            qty = av_qty
        available_qty = 0
        warehouse=[]
        st = 0
        ware = frappe.db.get_list("Warehouse",{"company":doc.company},['name'])
        for w in ware:
            bin = frappe.get_all("Bin",{"item_code":j.item_code,"warehouse":w.name},['actual_qty','reserved_stock'])
            sto = sum([value.get("actual_qty", 0) for value in bin]) - sum([value.get("reserved_stock", 0) for value in bin])
            # if sto and sto>0:
            st+=sto
            warehouse.append(w.name)

            reserve = frappe.db.sql("""
                SELECT (sum(reserved_qty) - sum(delivered_qty)) as reserved_qty
                FROM `tabStock Reservation Entry` 
                WHERE voucher_no = %s 
                AND item_code = %s 
                AND docstatus != 2
            """, (doc.name, j.item_code), as_dict=1)

            if reserve:
                reser_qty = reserve[0]['reserved_qty']
            else:
                reser_qty = 0

            if reser_qty and reser_qty > 0:
                available_qty = reser_qty
            else:
                if sto and qty > sto:
                    available_qty = sto
                    
                elif sto and qty < sto:
                    available_qty = qty
        print(available_qty)


    
@frappe.whitelist()
def modify_file_number():
    # att = frappe.db.sql(""" update  `tabDelivery Note`  set file_number = 'NCME000633' where name='DN-NCMEFT-2024-00652'  """)
    att = frappe.db.sql(""" update  `tabDelivery Note`  set file_number = 'NCPL000071' where name='DN-NCPLP-2024-00317'  """)
    # att = frappe.db.sql(""" update  `tabDelivery Note`  set file_number = 'NCME000671' where name='DN-NCPLP-2024-00329'  """)
    # att = frappe.db.sql(""" update  `tabDelivery Note`  set file_number = 'NSPL000056' where name='DN-NSPL-2024-00079'  """)
    # att = frappe.db.sql(""" update  `tabDelivery Note`  set file_number = 'NCPL000117' where name='DN-NCPLP-2024-00352'  """)
    # att = frappe.db.sql(""" update  `tabDelivery Note`  set file_number = 'NCPL000117' where name='DN-NCPLP-2024-00363'  """)
    # att = frappe.db.sql(""" update  `tabDelivery Note`  set file_number = 'F-Q-NCPLP-00768' where name='DN-NCPLP-2024-00367'  """)
    # att = frappe.db.sql(""" update  `tabDelivery Note`  set file_number = 'NCME000651' where name='DN-NCMEF-2024-00563'  """)
    # att = frappe.db.sql(""" update  `tabDelivery Note`  set file_number = 'NCME000671' where name='DN-NCPLP-2024-00336'  """)
    # att = frappe.db.sql(""" update  `tabDelivery Note`  set file_number = 'F-Q-NCPLP-00768' where name='SR-NCMEFT-2024-00020'  """)
    # att = frappe.db.sql(""" update  `tabDelivery Note`  set file_number = 'F-Q-NCPLP-00768' where name='SO-NCPLP-2024-00149'  """)
    # att = frappe.db.sql(""" update  `tabDelivery Note`  set file_number = 'F-Q-NCPLP-00768' where name='DN-NCPLP-2024-00231'  """)
    att = frappe.db.sql(""" update  `tabDelivery Note`  set file_number = 'NCME000671' where name='DN-NCMEFT-2024-00619'  """)
    # att = frappe.db.sql(""" update  `tabDelivery Note`  set file_number = 'NCME000671' where name='DN-NCPLP-2024-00308'  """)
    print(att)


# @frappe.whitelist()
# def serial_number_check(doc):
# 	data = '<table border=1><tr style="text-align: center"><td style="background-color:#e20026;color:white">Item Code</td><td style="background-color:#e20026;color:white">Serial Numbers</td></tr>'
# 	for i in doc.get("items"):
# 		has_serial_no = frappe.db.get_value ('Item',{"name":i.item_code},'has_serial_no')
# 		if has_serial_no == 1 and i.serial_and_batch_bundle:
# 			serial_numbers = []
# 			bundle_doc = frappe.get_doc('Serial and Batch Bundle', i.serial_and_batch_bundle)
# 			for j in bundle_doc.entries:
# 				serial_numbers.append(j.serial_no)
# 			serial_numbers_str = ', '.join(serial_numbers)
# 			data += '<tr style="text-align: center"><td>{}</td><td>{}</td></tr>'.format(i.item_code, serial_numbers_str)	
# 	data += '</table>'
# 	return data	

@frappe.whitelist()
def serial_number_check(doc):
    data = ''
    serial_number_exists = False  

    table_header = '<table border=1 width="100%"><tr style="text-align: center"><td style="background-color:#e20026;color:white" width="20%">Item Code</td><td style="background-color:#e20026;color:white">Serial Numbers</td></tr>'
    table_rows = ''

    for i in doc.get("items"):
        has_serial_no = frappe.db.get_value('Item', {"name": i.item_code}, 'has_serial_no')
        if has_serial_no == 1 and i.serial_and_batch_bundle:
            serial_numbers = []
            bundle_doc = frappe.get_doc('Serial and Batch Bundle', i.serial_and_batch_bundle)
            for j in bundle_doc.entries:
                serial_numbers.append(j.serial_no)
            serial_numbers_str = ', '.join(serial_numbers)
            if serial_numbers_str:  
                serial_number_exists = True
                table_rows += '<tr style="text-align: center"><td>{}</td><td>{}</td></tr>'.format(i.item_code, serial_numbers_str)

    if serial_number_exists:
        data = table_header + table_rows + '</table>'

    return data



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

# @frappe.whitelist()
# def update_old_file_numbers():
# 	files = frappe.get_all("Purchase Order", ["custom_file_number", "file_number","name"])
# 	count=0
# 	for i in files:
# 		if i.custom_file_number and not i.file_number:
# 			count+=1
# 	# print(count)
# 			frappe.db.set_value("Purchase Order",i.name,"file_number",i.custom_file_number)

@frappe.whitelist()
def validate_cheque_no(cheque_no):
    journal_entry=frappe.get_all("Journal Entry",{'cheque_no':cheque_no,"docstatus":("!=",2)},['*'])
    if journal_entry:
        i=0
        doc_name=[]
        for je in journal_entry:
            i+=1
            doc_name.append(je.name)
        return i,doc_name

@frappe.whitelist()
def update_file_number():
    file_no = frappe.get_all("Sales Order",{"docstatus":("!=", 2),"transaction_date":("between",("2024-06-01","2024-07-05"))},["*"])
    count = 0
    for i in file_no:
        if not i.file_number:
            file = frappe.db.get_value("Quotation",{"name":i.name})
            # company_series = frappe.db.get_value("Company Series",{'company':i.company,'document_type':'File Number','with_tax':0},'series')
            # fn_doc = frappe.new_doc("File Number")
            # fn_doc.company = i.company
            # fn_doc.naming_series = company_series
            # fn_doc.save(ignore_permissions=False)
            # frappe.db.set_value("Quotation",i.name,"file_number",fn_doc.name)
    print(count)

@frappe.whitelist()
def to_reserve_on_inspection(doc,method):
    if doc.pr_number:
        pr = frappe.get_doc("Purchase Receipt",doc.pr_number)
        to_reserve = []
        for s in pr.items:
            if s.sales_order:
                so_doc = frappe.get_doc("Sales Order",s.sales_order)
                for i in so_doc.items:
                    to_reserve.append(frappe._dict({"idx":i.idx,"item_code":i.item_code,"qty_to_reserve":(i.qty - i.stock_reserved_qty),"sales_order_item":i.name,"warehouse":so_doc.set_warehouse}))
                from erpnext.stock.doctype.stock_reservation_entry.stock_reservation_entry import (
                    create_stock_reservation_entries_for_so_items as create_stock_reservation_entries,
                )

                create_stock_reservation_entries(
                    sales_order=so_doc,
                    items_details=to_reserve,
                    from_voucher_type="Purchase Receipt"
                )

@frappe.whitelist()
def to_reserve_on_pr(doc,method):
    to_reserve = []
    for s in doc.items:
        if s.sales_order:
            so_doc = frappe.get_doc("Sales Order",s.sales_order)
            for i in so_doc.items:
                to_reserve.append(frappe._dict({"idx":i.idx,"item_code":i.item_code,"qty_to_reserve":(i.qty - i.stock_reserved_qty),"sales_order_item":i.name,"warehouse":so_doc.set_warehouse}))
            from erpnext.stock.doctype.stock_reservation_entry.stock_reservation_entry import (
                create_stock_reservation_entries_for_so_items as create_stock_reservation_entries,
            )

            create_stock_reservation_entries(
                sales_order=so_doc,
                items_details=to_reserve,
                from_voucher_type="Purchase Receipt"
            )

    
from datetime import datetime, timedelta
from frappe import _, db, sendmail
import frappe
from datetime import datetime, timedelta

@frappe.whitelist()
def annual_leave_expiry_alert_mail():
    
    data = ""
    employees = frappe.db.sql("""SELECT * FROM `tabEmployee` WHERE status = 'Active' AND company ='Norden Communication Middle East FZE' GROUP BY name, date_of_joining ORDER BY date_of_joining """, as_dict=True)
    # frappe.errprint(employees)
    today = datetime.now().date()
    future_date = today + timedelta(days=30)
    recipients = []

    for emp in employees:
        employee_hire_date = emp.date_of_joining
        expiry_date = datetime(today.year, employee_hire_date.month, employee_hire_date.day).date()
        # abcd ='jothi.m@groupteampro.com'  
        # efgh ='gifty.p@groupteampro.com'
        if expiry_date == future_date and "Employee ID : {emp_id}" not in data:
            emp_tuple_expiry_year = (emp.name, emp.employee_name, emp.department, emp.date_of_joining)
            formatted_date = emp_tuple_expiry_year[3].strftime('%d-%m-%y')
            expiry_date_formated =expiry_date.strftime('%d-%m-%y')
            # data += "Employee ID : {} <br> Employee Name: {} <br> Department: {} <br> Date of Joining: {} ".format(emp_tuple_expiry_year[0], emp_tuple_expiry_year[1], emp_tuple_expiry_year[2], formatted_date)
            # recipient = abcd
            emp_id = emp_tuple_expiry_year[0]
            emp_email = frappe.db.get_value("Employee",{'name':emp_id},['company_email'])
            emp_user = frappe.db.get_value("Employee",{'name':emp_id},['user_id'])
            if emp_email:
                # recipient = efgh or abcd
                recipient = emp_email 
                if recipient:
                    recipients.append(recipient)
                if recipients:
                    emp_id = emp.emp_tuple_expiry_year
                    data += "Employee ID : <b>{}</b> <br> Employee Name:<b> {}</b> <br> Department: <b>{}</b> <br> Date of Joining: <b>{}</b> <br>Date of Expiry:<b>{}</b> ".format(emp_tuple_expiry_year[0], emp_tuple_expiry_year[1], emp_tuple_expiry_year[2], formatted_date,expiry_date_formated)
                    # current_date = datetime.now().date()
                    # current_formatted_date = current_date.strftime('%d-%m-%y')
                    subject = 'Reminder For Annual Leave Expiry'
                    message_body = """Dear Sir/Madam,<br>Annual allocated leaves are going to expire in 30 days.<br><br>Employee Details for your reference:<br><br>{}<br><br><br>Thanks & Regards,<br>HR Department,<br>Norden Communication Middle East FZE<br><br>*This email has been automatically generated. Please do not reply*""".format(data)
                    frappe.sendmail(recipients=recipients, subject=subject, message=message_body)
            
                # break
            else:
                # recipient = efgh or abcd
                recipient = emp_user 
                if recipient:
                    recipients.append(recipient)
                if recipients:
                    data += "Employee ID : {} <br> Employee Name: {} <br> Department: {} <br> Date of Joining: {} ".format(emp_tuple_expiry_year[0], emp_tuple_expiry_year[1], emp_tuple_expiry_year[2], formatted_date,expiry_date_formated)
                    current_date = datetime.now().date()
                    current_formatted_date = current_date.strftime('%d-%m-%y')
                    subject = 'Reminder For Annual Leave Expiry '
                    message_body = """<b>Dear Sir/Madam,<br>Annual allocated leaves are going to expire in 30 days.<br>Employee Details for your reference:<br><br>{}<br><br>Thanks & Regards,<br>HR Department,<br>Norden Communication Middle East FZE<br></b><br>*This email has been automatically generated. Please do not reply*""".format(data)
                    frappe.sendmail(recipients=recipients, subject=subject, message=message_body)



@frappe.whitelist()
def update_role():
    user_list=frappe.get_all("User",{'enabled':1},['*'],limit=20,order_by='modified ASC')
    for u in user_list:
        usr=frappe.get_doc("User",u.name)
        usr.append("roles",{
            "role":"Item Restrict"
        })
        usr.save(ignore_permissions=True)
        print(u.name)


@frappe.whitelist()
def get_ex_stock_qty(item_code, company):
    company_sc = frappe.get_value("Company", {'name': company}, ['abbr'])
    ex_stock_qty = 0
    warehouse = '% - ' + company_sc
    
    # Query to get bins where warehouse is not a scrap warehouse
    bin_docs = frappe.db.sql("""
        SELECT b.actual_qty, b.reserved_stock
        FROM `tabBin` b
        JOIN `tabWarehouse` w ON b.warehouse = w.name
        WHERE b.item_code = %s
          AND b.warehouse LIKE %s
          AND w.is_scrap = 0
          AND w.custom_stock_is_shown_only_in_product_search = 0
    """, (item_code, warehouse), as_dict=True)
    
    # Calculate ex stock quantity
    for i in bin_docs:
        ex_stock_qty += (i.actual_qty - i.reserved_stock)
    
    return ex_stock_qty


@frappe.whitelist()
def update_exp_claim():
    frappe.db.sql("""update `tabExpense Claim` set workflow_state = 'Pending for HOD' where name = 'HR-EXP-2024-00182'""")

@frappe.whitelist()
def validate_item_price_list(doc,method):
    if doc.is_new():
        if frappe.db.exists("Item Price",{'item_code':doc.item_code,'price_list':doc.price_list}):
            frappe.throw("Already same Price List Available for this Item")

# @frappe.whitelist()
# def duplicated_sales_order():
#     # dup =frappe.db.sql("""select count(name) from `tabSales Order` where docstatus=1 and transaction_date between %s and %s group by file_number""" %("2024-01-01","2024-08-07"),as_dict=1,)
#     print(dup)

# @frappe.whitelist()
# def duplicated_sales_order():

# 	sales_orders = frappe.get_all(
# 		"Sales Order",
# 		filters=[
# 			["docstatus", "=", 1],
# 			["transaction_date", "timespan", "this year"],
# 			["file_number", "is", "set"]
# 		],
# 		fields=["count(name) as count","file_number"],
# 		group_by="file_number"
# 	)
    
# 	duplicates = sum(1 for so in sales_orders if so['count'] > 1)
    
# 	print(duplicates)

# 	duplicate_file_numbers = [so['file_number'] for so in sales_orders if so['count'] > 1]

# 	if duplicate_file_numbers:
# 		duplicate_sales_orders = frappe.get_all(
# 			"Sales Order",
# 			filters=[
# 				["docstatus", "=", 1],
# 				["transaction_date", "timespan", "this year"],
# 				["file_number", "in", duplicate_file_numbers]
# 			],
# 			fields=["name"],
# 		)
        
# 		duplicate_names = [so['name'] for so in duplicate_sales_orders]
# 		print(duplicate_names)
# 		print(len(duplicate_names))

# @frappe.whitelist()
# def duplicated_sales_order():
#     from datetime import datetime

#     current_year = datetime.now().year
#     start_date = f"{current_year}-01-01"
#     end_date = f"{current_year}-12-31"

#     # Get all sales orders with file numbers and their creation dates
#     sales_orders = frappe.get_all(
#         "Sales Order",
#         filters=[
#             ["docstatus", "=", 1],
#             ["transaction_date", "between", [start_date, end_date]],
#             ["file_number", "is", "set"]
#         ],
#         fields=["name", "file_number", "creation"],
#     )

#     # Organize sales orders by file_number
#     from collections import defaultdict
#     file_number_dict = defaultdict(list)
    
#     for so in sales_orders:
#         file_number_dict[so['file_number']].append(so)
    
#     # Print the first created document for each file_number
#     first_created_documents = []
#     for file_number, docs in file_number_dict.items():
#         if len(docs) > 1:
#             sorted_docs = sorted(docs, key=lambda x: x['creation'])
#             first_created_documents.append(sorted_docs[0])  # Append the earliest created document
    
#     # Print details of the first created documents
#     for doc in first_created_documents:
#         print(f"File Number: {doc['file_number']}, Document Name: {doc['name']}, Creation Date: {doc['creation']}")
    
#     print("Number of first created documents:", len(first_created_documents))


@frappe.whitelist()
def modify_file_number_so():
    att = frappe.db.sql(""" update  `tabSales Order`  set file_number = 'NSPL000169' where name='SO-NSPL-2024-00127'  """)
    print(att)
    
# @frappe.whitelist()
# def modify_file_number_q():
#     att = frappe.db.sql(""" update  `tabQuotation`  set file_number = 'NSA000016' where name='F-Q-NSA-2022-00308'  """)
#     print(att)

@frappe.whitelist()
def modify_file_number_si():
    att = frappe.db.sql(""" update  `tabSales Invoice`  set file_number = 'NCPL000254' where name='PI-NCI-24-00111'  """)
    # att = frappe.db.sql(""" update  `tabSales Invoice`  set file_number = 'NCPL000256' where name='CNE2425-00013'  """)
    # att = frappe.db.sql(""" update  `tabSales Invoice`  set file_number = 'NCPL000256' where name='NID2425-00324'  """)
    # att = frappe.db.sql(""" update  `tabSales Invoice`  set file_number = 'NCPL000256' where name='NID2425-00323'  """)
    print(att)

@frappe.whitelist()
def modify_file_number_dn():
    att = frappe.db.sql(""" update  `tabDelivery Note`  set file_number = 'NCPL000256' where name='DN-NCPLP-2024-00466'  """)
    att = frappe.db.sql(""" update  `tabDelivery Note`  set file_number = 'NCPL000256' where name='DN-NCPLP-2024-00465'  """)
    print(att)

@frappe.whitelist()
def update_approve_by_finance_cancel_state():
    sales_order=frappe.get_all("Sales Order",{'docstatus':2,'finance_head_approval':'Approved'},['*'])
    i=0
    for so in sales_order:
        frappe.db.sql("""update `tabSales Order` set finance_head_approval='Cancelled' where name=%s""",(so.name))
        i+=1
    print(i)

@frappe.whitelist()
def get_file_quotation(company):
    company_series = frappe.db.get_value("Company Series",{'company':company,'document_type':'File Number','with_tax':0},'series')
    fn_doc = frappe.new_doc("File Number")
    fn_doc.company = company
    fn_doc.naming_series = company_series
    fn_doc.save(ignore_permissions=False)
    return fn_doc
    
@frappe.whitelist()
def validate_taxes_presence(doc,method):
    if doc.invoice_type=='Taxable' and doc.company=='Norden Communication Middle East FZE':
        if doc.taxes:
            vat_present = False
            for i in doc.taxes:
                if 'VAT' in i.account_head:
                    vat_present = True
                    break

            if not vat_present:
                frappe.throw("VAT is not added in Taxes")
                
        else:
            frappe.throw("VAT is not added in Taxes")


@frappe.whitelist()
def set_batch_number():
    frappe.db.set_value("Purchase Order","PO-NSPL-2024-00077-1","batch","NSPL-2024-00077-1")
    frappe.db.set_value("Purchase Order","PO-NCUL-2024-00003-1","batch","NCUL-2024-00003-1")
    frappe.db.set_value("Purchase Order","PO-SNTL-2024-00024-1","batch","SNTL-2024-00024-1")

@frappe.whitelist()
def create_cluster_and_update_up(doc,method):
    cluster=frappe.new_doc("Cluster")
    cluster.cluster=doc.custom_territory+' - '+doc.sales_person_name
    cluster.user=doc.user_id
    cluster.save(ignore_permissions=True)
    frappe.db.commit()
    user_per=frappe.new_doc("User Permission")
    user_per.user=doc.user_id
    user_per.allow="Cluster"
    user_per.for_value=cluster.name
    user_per.apply_to_all_doctypes=1
    user_per.save(ignore_permissions=True)
    user_per=frappe.new_doc("User Permission")
    user_per.user=doc.user_id
    user_per.allow="Sales Person"
    user_per.for_value=doc.name
    user_per.apply_to_all_doctypes=1
    user_per.save(ignore_permissions=True)


#For updating the Base Cost in SO
@frappe.whitelist()
def update_base_rate_for_zero_rate():
    sales_order=frappe.get_all("Sales Order",{'company':'Norden Communication Middle East FZE','transaction_date':('between',('2024-01-01','2024-09-05')),"workflow_state":'Approved'},['name'])
    for doc in sales_order:
        so=frappe.get_doc("Sales Order",doc.name)
        for i in so.items:
            if i.custom_base_rate==0:
                print(i.item_code)
                items = frappe.db.get_all("Sales Order Item", {"parent": doc.name, 'item_code': i.item_code}, ['*'])
                warehouse = frappe.db.get_value("Warehouse", {'company': "Norden Communication Middle East FZE", 'default_for_stock_transfer': 1}, ['name'])
                val_rate = frappe.db.get_value("Bin", {"item_code": i.item_code, "warehouse": warehouse}, ['valuation_rate'])
                val = 0
                landing_cost = 0
                incentive_cost = 0
                
                item_group = frappe.db.get_value("Item", {"name": i.item_code}, ['item_sub_group'])
                val=frappe.db.get_value("Item Price", {"item_code": i.item_code, 'price_list': "Cost Rate - NCMEF"}, ['price_list_rate'])
                if not val:
                    val=0
                margin_price = frappe.get_doc("Margin Price Tool")
                for t in margin_price.dubai:
                    if t.item_group == item_group:
                        landing_cost = val * t.landing
                        incentive_cost = landing_cost * t.incentive

                
                frappe.db.sql("""update `tabSales Order Item` set custom_base_rate=%s where name=%s and parent=%s""",(val,i.name,doc.name))
                frappe.db.sql("""update `tabSales Order Item` set custom_incentive_rate=%s where name=%s and parent=%s""",(incentive_cost,i.name,doc.name))
                frappe.db.sql("""update `tabSales Order Item` set custom_landing_rate=%s where name=%s and parent=%s""",(landing_cost,i.name,doc.name))
                
            if i.custom_internal_rate==0:
                print(i.item_code)
                internal_cost = 0
                price = frappe.db.get_value("Item Price", {"item_code": i.item_code, 'price_list': "Internal - NCMEF"}, ['price_list_rate'])
                if price:
                    internal_cost = price
                frappe.db.sql("""update `tabSales Order Item` set custom_internal_rate=%s where name=%s and parent=%s""",(internal_cost,i.name,doc.name))

@frappe.whitelist()
def update_base_rate_for_zero_rate_in_si():
    sales_invoice=frappe.get_all("Sales Invoice",{'company':'Norden Communication Middle East FZE','posting_date':('between',('2024-01-01','2024-01-31')),"docstatus":('!=',2)},['name'])
    for doc in sales_invoice:
        si=frappe.get_doc("Sales Invoice",doc.name)
        for i in si.items:
            if i.custom_base_cost==0:
                print(doc.name)
                items = frappe.db.get_all("Sales Order Item", {"parent": i.sales_order, 'item_code': i.item_code}, ['*'])
                val = items[0].custom_base_rate*i.qty
                landing_cost = items[0].custom_landing_rate*i.qty
                incentive_cost = items[0].custom_incentive_rate*i.qty
                internal_cost = items[0].custom_internal_rate*i.qty
                print(i.item_code)

                frappe.db.sql("""update `tabSales Invoice Item` set custom_base_cost=%s where name=%s and parent=%s""",(val,i.name,doc.name))
                frappe.db.sql("""update `tabSales Invoice Item` set custom_landing_cost=%s where name=%s and parent=%s""",(landing_cost,i.name,doc.name))
                frappe.db.sql("""update `tabSales Invoice Item` set custom_incentive_cost=%s where name=%s and parent=%s""",(incentive_cost,i.name,doc.name))
            if i.custom_internal_cost==0:
                print(i.item_code)
                items = frappe.db.get_all("Sales Order Item", {"parent": i.sales_order, 'item_code': i.item_code}, ['*'])
                internal_cost = items[0].custom_internal_rate*i.qty

                frappe.db.sql("""update `tabSales Invoice Item` set custom_internal_cost=%s where name=%s and parent=%s""",(internal_cost,i.name,doc.name))

@frappe.whitelist()
def update_rack(doc,method):
    for i in doc.items:
        if i.rack:
            frappe.db.sql("""
                UPDATE `tabStock Ledger Entry`
                SET rack = %s
                WHERE voucher_no = %s
                AND item_code = %s
                AND actual_qty = %s AND is_cancelled=0 AND docstatus<2
                ORDER BY creation DESC
                LIMIT 1
            """, (i.rack, doc.name, i.item_code, i.qty), as_dict=True)

# @frappe.whitelist()
# def update_rackwise_items(company, custom_merge_item):
#     items = []
#     merge_pick_list_item = json.loads(custom_merge_item)
    
#     # Prepare a list of item codes and warehouses for bulk query
#     item_codes_warehouses = [(j['item_code'], j['warehouse']) for j in merge_pick_list_item]
    
#     # Fetch serial and batch bundle data in one query
#     serial_and_batch_bundles = frappe.db.sql("""
#         SELECT item_code, warehouse, serial_and_batch_bundle AS sb 
#         FROM `tabStock Ledger Entry`
#         WHERE (item_code, warehouse) IN %s
#         AND is_cancelled = 0 
#         AND docstatus < 2 
#         AND serial_and_batch_bundle != '' 
#         AND rack != '' 
#         ORDER BY creation ASC
#     """, (item_codes_warehouses,), as_dict=True)
    
#     # Build a dictionary for serial and batch bundle data
#     sb_bundle_dict = {}
#     for entry in serial_and_batch_bundles:
#         sb_bundle_dict.setdefault((entry.item_code, entry.warehouse), []).append(entry.sb)
    
#     # Prepare a list of batch numbers to fetch batch data in bulk
#     batch_no_list = []
#     for sb_list in sb_bundle_dict.values():
#         for sb in sb_list:
#             doc = frappe.get_doc('Serial and Batch Bundle', sb)
#             for sbe in doc.entries:
#                 if sbe.batch_no:
#                     batch_no_list.append(sbe.batch_no)
    
#     # Fetch batch details in bulk
#     batch_data = frappe.db.sql("""
#         SELECT name, batch_qty, creation 
#         FROM `tabBatch` 
#         WHERE name IN %s AND batch_qty > 0
#     """, (batch_no_list,), as_dict=True)
    
#     # Create a dictionary for batch data
#     batch_dict = {batch.name: batch for batch in batch_data}
    
#     # This will hold merged items
#     merged_items = {}
    
#     # Process each item from the merge_pick_list_item
#     for j in merge_pick_list_item:
#         qty = j['qty']
#         if qty <= 0:
#             continue
        
#         serial_and_batch_data = []
#         for sb in sb_bundle_dict.get((j['item_code'], j['warehouse']), []):
#             doc = frappe.get_doc('Serial and Batch Bundle', sb)
#             for sbe in doc.entries:
#                 batch_no = sbe.batch_no
#                 if batch_no and batch_no in batch_dict:
#                     batch_info = batch_dict[batch_no]
#                     creation_date = batch_info.creation
#                     batch_qty = batch_info.batch_qty
#                     serial_and_batch_data.append((sb, batch_no, creation_date, batch_qty))
        
#         # Remove duplicates and sort by creation date
#         unique_serial_and_batch_data = list(set(serial_and_batch_data))
#         sorted_data = sorted(unique_serial_and_batch_data, key=lambda x: x[2])
        
#         for sb, batch_no, creation_date, batch_qty in sorted_data:
#             if qty <= 0:
#                 break

#             # Calculate total quantity available in the batch
#             total_quantity = sum(sbe.qty for sbe in frappe.get_doc('Serial and Batch Bundle', sb).entries if sbe.batch_no == batch_no)
            
#             if total_quantity > 0:
#                 if batch_qty >= total_quantity:
#                     batch_qty -= total_quantity
#                     used_quantity = min(total_quantity, qty)
#                 else:
#                     used_quantity = min(batch_qty, qty)
#                     batch_qty = 0
                
#                 qty -= used_quantity
                
#                 # Fetch rack and warehouse information
#                 rack_warehouse = frappe.db.get_value(
#                     "Stock Ledger Entry",
#                     {'serial_and_batch_bundle': sb},
#                     ['rack', 'warehouse']
#                 )
                
#                 # Ensure rack_warehouse is a tuple and correctly unpacked
#                 if rack_warehouse:
#                     rack, warehouse = rack_warehouse
#                 else:
#                     rack, warehouse = '', ''  # Handle cases where no data is found
                
#                 # Create a unique key for merging
#                 key = (j['item_code'], rack, batch_no)
                
#                 if key in merged_items:
#                     # If the item is already in merged_items, add to the quantity
#                     merged_items[key]['qty'] += used_quantity
#                 else:
#                     # Otherwise, create a new entry
#                     merged_items[key] = {
#                         'item_code': j['item_code'],
#                         'item_name': j['item_name'],
#                         'description': j['description'],
#                         'qty': used_quantity,
#                         'rack': rack,
#                         'uom': j['uom'],
#                         'against_sales_order': j['against_sales_order'],
#                         'warehouse': warehouse,
#                         'sales_order_item': j['sales_order_item'],
#                         'batch': batch_no
#                     }
    
#     # Convert merged_items back to a list for the return value
#     items = list(merged_items.values())
    
#     return items



# @frappe.whitelist()
# def update_rackwise_items(company, custom_merge_item):
# 	items = []
# 	merge_pick_list_item = json.loads(custom_merge_item)
    
# 	# Prepare a list of item codes and warehouses for bulk query
# 	item_codes_warehouses = [(j['item_code'], j['warehouse']) for j in merge_pick_list_item]
    
# 	# Fetch serial and batch bundle data in one query
# 	# Fetch serial and batch bundle data and sum actual_qty for each item and warehouse
# 	serial_and_batch_bundles = frappe.db.sql("""
# 		SELECT item_code, warehouse, serial_and_batch_bundle AS sb, rack, SUM(actual_qty) AS total_qty
# 		FROM `tabStock Ledger Entry`
# 		WHERE (item_code, warehouse) IN %s
# 		AND is_cancelled = 0 
# 		AND serial_and_batch_bundle != '' 
# 		AND rack != '' 
# 		GROUP BY item_code, warehouse, rack
# 		ORDER BY creation ASC
# 	""", (item_codes_warehouses,), as_dict=True)

    
# 	# Build a dictionary for serial and batch bundle data
# 	sb_bundle_dict = {}
# 	for entry in serial_and_batch_bundles:
# 		sb_bundle_dict.setdefault((entry.item_code, entry.warehouse), []).append(entry.sb)
    
# 	# Prepare a list of batch numbers to fetch batch data in bulk
# 	batch_no_list = []
# 	for sb_list in sb_bundle_dict.values():
# 		for sb in sb_list:
# 			doc = frappe.get_doc('Serial and Batch Bundle', sb)
# 			for sbe in doc.entries:
# 				if sbe.batch_no:
# 					batch_no_list.append(sbe.batch_no)
# 	frappe.errprint(batch_no_list)
# 	if batch_no_list:
# 		# Fetch batch details in bulk
# 		batch_data = frappe.db.sql("""
# 			SELECT name, batch_qty, creation 
# 			FROM `tabBatch` 
# 			WHERE name IN %s AND batch_qty > 0
# 		""", (batch_no_list,), as_dict=True)
        
# 		# Create a dictionary for batch data
# 		batch_dict = {batch.name: batch for batch in batch_data}
# 		for j in merge_pick_list_item:
# 			qty = j['qty']
# 			if qty <= 0:
# 				continue

# 			serial_and_batch_data = []
# 			for entry in serial_and_batch_bundles:
# 				if entry['item_code'] == j['item_code'] and entry['warehouse'] == j['warehouse']:
# 					sb = entry['sb']
# 					total_quantity = entry['total_qty']  # Use summed quantity

# 					doc = frappe.get_doc('Serial and Batch Bundle', sb)
# 					for sbe in doc.entries:
# 						batch_no = sbe.batch_no
# 						if batch_no and batch_no in batch_dict:
# 							batch_info = batch_dict[batch_no]
# 							creation_date = batch_info.creation
# 							batch_qty = batch_info.batch_qty
# 							serial_and_batch_data.append((sb, batch_no, creation_date, batch_qty))

# 					# Remove duplicates and sort by creation date
# 					unique_serial_and_batch_data = list(set(serial_and_batch_data))
# 					sorted_data = sorted(unique_serial_and_batch_data, key=lambda x: x[2])

# 					for sb, batch_no, creation_date, batch_qty in sorted_data:
# 						if qty <= 0:
# 							break

# 						# Use total_quantity (sum of actual_qty from SLE)
# 						if total_quantity > 0:
# 							if batch_qty >= total_quantity:
# 								batch_qty -= total_quantity
# 								used_quantity = min(total_quantity, qty)
# 							else:
# 								used_quantity = min(batch_qty, qty)
# 								batch_qty = 0

# 							qty -= used_quantity

# 							# Fetch rack and warehouse information
# 							rack = entry['rack']
# 							warehouse = entry['warehouse']

# 							items.append({
# 								'item_code': j['item_code'],
# 								'item_name': j['item_name'],
# 								'description': j['description'],
# 								'qty': used_quantity,
# 								'rack': rack,
# 								'uom': j['uom'],
# 								'against_sales_order': j['against_sales_order'],
# 								'warehouse': warehouse,
# 								'sales_order_item': j['sales_order_item'],
# 								'batch': batch_no
# 							})
# 		# Process each item from the merge_pick_list_item
# 	# 	for j in merge_pick_list_item:
# 	# 		qty = j['qty']
# 	# 		if qty <= 0:
# 	# 			continue
            
# 	# 		serial_and_batch_data = []
# 	# 		for sb in sb_bundle_dict.get((j['item_code'], j['warehouse']), []):
# 	# 			doc = frappe.get_doc('Serial and Batch Bundle', sb)
# 	# 			for sbe in doc.entries:
# 	# 				batch_no = sbe.batch_no
# 	# 				if batch_no and batch_no in batch_dict:
# 	# 					batch_info = batch_dict[batch_no]
# 	# 					creation_date = batch_info.creation
# 	# 					batch_qty = batch_info.batch_qty
# 	# 					serial_and_batch_data.append((sb, batch_no, creation_date, batch_qty))
            
# 	# 		# Remove duplicates and sort by creation date
# 	# 		unique_serial_and_batch_data = list(set(serial_and_batch_data))
# 	# 		sorted_data = sorted(unique_serial_and_batch_data, key=lambda x: x[2])
            
# 	# 		for sb, batch_no, creation_date, batch_qty in sorted_data:
# 	# 			if qty <= 0:
# 	# 				break

# 	# 			# Calculate total quantity available in the batch
# 	# 			total_quantity = sum(sbe.qty for sbe in frappe.get_doc('Serial and Batch Bundle', sb).entries if sbe.batch_no == batch_no)
                
# 	# 			if total_quantity > 0:
# 	# 				if batch_qty >= total_quantity:
# 	# 					batch_qty -= total_quantity
# 	# 					used_quantity = min(total_quantity, qty)
# 	# 				else:
# 	# 					used_quantity = min(batch_qty, qty)
# 	# 					batch_qty = 0
                    
# 	# 				qty -= used_quantity
                    
# 	# 				# Fetch rack and warehouse information
# 	# 				rack_warehouse = frappe.db.get_value(
# 	# 					"Stock Ledger Entry",
# 	# 					{'serial_and_batch_bundle': sb},
# 	# 					['rack', 'warehouse']
# 	# 				)
                    
# 	# 				# Ensure rack_warehouse is a tuple and correctly unpacked
# 	# 				if rack_warehouse:
# 	# 					rack, warehouse = rack_warehouse
# 	# 				else:
# 	# 					rack, warehouse = '', ''  # Handle cases where no data is found
                    
# 	# 				items.append({
# 	# 					'item_code': j['item_code'],
# 	# 					'item_name': j['item_name'],
# 	# 					'description': j['description'],
# 	# 					'qty': used_quantity,
# 	# 					'rack': rack,
# 	# 					'uom': j['uom'],
# 	# 					'against_sales_order': j['against_sales_order'],
# 	# 					'warehouse': warehouse,
# 	# 					'sales_order_item': j['sales_order_item'],
# 	# 					'batch': batch_no
# 	# 				})
    
    # return items



# @frappe.whitelist()
# def update_rackwise_items(company, custom_merge_item):
# 	items = []
# 	merge_pick_list_item = json.loads(custom_merge_item)
    
# 	# Prepare a list of item codes and warehouses for bulk query
# 	item_codes_warehouses = [(j['item_code'], j['warehouse']) for j in merge_pick_list_item]
    
# 	# Fetch serial and batch bundle data and sum actual_qty for each item and warehouse
# 	serial_and_batch_bundles = frappe.db.sql("""
# 		SELECT item_code, warehouse, serial_and_batch_bundle AS sb, rack, SUM(actual_qty) AS total_qty
# 		FROM `tabStock Ledger Entry`
# 		WHERE (item_code, warehouse) IN %s
# 		AND is_cancelled = 0 
# 		AND serial_and_batch_bundle != '' 
# 		AND rack != '' 
# 		GROUP BY item_code, warehouse, rack, serial_and_batch_bundle
# 		ORDER BY creation ASC
# 	""", (item_codes_warehouses,), as_dict=True)

# 	# Build a dictionary for serial and batch bundle data
# 	sb_bundle_dict = {}
# 	for entry in serial_and_batch_bundles:
# 		sb_bundle_dict.setdefault((entry.item_code, entry.warehouse), []).append(entry.sb)
    
# 	# Prepare a list of batch numbers to fetch batch data in bulk
# 	batch_no_list = []
# 	for sb_list in sb_bundle_dict.values():
# 		for sb in sb_list:
# 			doc = frappe.get_doc('Serial and Batch Bundle', sb)
# 			for sbe in doc.entries:
# 				if sbe.batch_no:
# 					batch_no_list.append(sbe.batch_no)

# 	if batch_no_list:
# 		# Fetch batch details in bulk
# 		batch_data = frappe.db.sql("""
# 			SELECT name, batch_qty, creation 
# 			FROM `tabBatch` 
# 			WHERE name IN %s AND batch_qty > 0
# 		""", (batch_no_list,), as_dict=True)
        
# 		# Create a dictionary for batch data
# 		batch_dict = {batch.name: batch for batch in batch_data}
# 		merged_items = {}

# 		# Process each item from the merge_pick_list_item
# 		for j in merge_pick_list_item:
# 			qty = j['qty']
# 			if qty <= 0:
# 				continue

# 			serial_and_batch_data = []
# 			for entry in serial_and_batch_bundles:
# 				if entry['item_code'] == j['item_code'] and entry['warehouse'] == j['warehouse']:
# 					sb = entry['sb']
# 					total_quantity = entry['total_qty']  # Use summed quantity

# 					doc = frappe.get_doc('Serial and Batch Bundle', sb)
# 					for sbe in doc.entries:
# 						batch_no = sbe.batch_no
# 						if batch_no and batch_no in batch_dict:
# 							batch_info = batch_dict[batch_no]
# 							creation_date = batch_info.creation
# 							batch_qty = batch_info.batch_qty
# 							serial_and_batch_data.append((sb, batch_no, creation_date, batch_qty))

# 					# Remove duplicates and sort by creation date
# 					unique_serial_and_batch_data = list(set(serial_and_batch_data))
# 					sorted_data = sorted(unique_serial_and_batch_data, key=lambda x: x[2])

# 					for sb, batch_no, creation_date, batch_qty in sorted_data:
# 						if qty <= 0:
# 							break
# 						frappe.errprint(total_quantity)
# 						# Use total_quantity (sum of actual_qty from SLE)
# 						if total_quantity > 0:
# 							if batch_qty >= total_quantity:
# 								batch_qty -= total_quantity
# 								used_quantity = min(total_quantity, qty)
# 							else:
# 								used_quantity = min(batch_qty, qty)
# 								batch_qty = 0

# 							qty -= used_quantity
# 							frappe.errprint(entry['rack'])
# 							# Fetch rack and warehouse information
# 							rack = entry['rack']
# 							warehouse = entry['warehouse']

# 							# Create a unique key for each combination of item_code, warehouse, rack, and batch_no
# 							key = (j['item_code'], warehouse, rack, batch_no)

# 							# If the same item, rack, and batch already exist, accumulate the quantity
# 							if key in merged_items:
# 								merged_items[key]['qty'] += used_quantity
# 							else:
# 								merged_items[key] = {
# 									'item_code': j['item_code'],
# 									'item_name': j['item_name'],
# 									'description': j['description'],
# 									'qty': used_quantity,
# 									'rack': rack,
# 									'uom': j['uom'],
# 									'against_sales_order': j['against_sales_order'],
# 									'warehouse': warehouse,
# 									'sales_order_item': j['sales_order_item'],
# 									'batch': batch_no
# 								}

# 		# Convert merged_items dictionary to the final items list
# 		items = list(merged_items.values())
    
# 	return items

# @frappe.whitelist()
# def update_non_available_qty_in_pick_list(so):
# 	items = []
# 	sales_order = frappe.get_doc("Sales Order", so)
    
# 	# Prepare a list of item codes and warehouses for bulk query
# 	item_codes_warehouses = [(j.item_code, j.warehouse) for j in sales_order.items]

# 	# Fetch serial and batch bundle data in one query
# 	serial_and_batch_bundles = frappe.db.sql("""
# 		SELECT item_code, warehouse, serial_and_batch_bundle AS sb, rack, SUM(actual_qty) AS total_qty
# 		FROM `tabStock Ledger Entry`
# 		WHERE (item_code, warehouse) IN %s
# 		AND is_cancelled = 0 
# 		AND docstatus < 2 
# 		AND serial_and_batch_bundle != '' 
# 		AND rack != '' 
# 		GROUP BY item_code, warehouse, serial_and_batch_bundle, rack
# 		ORDER BY creation DESC
# 	""", (item_codes_warehouses,), as_dict=True)
    
# 	# Build a dictionary for serial and batch bundle data
# 	sb_bundle_dict = {}
# 	for entry in serial_and_batch_bundles:
# 		sb_bundle_dict.setdefault((entry.item_code, entry.warehouse), []).append(entry.sb)
    
# 	# Prepare a list of batch numbers to fetch batch data in bulk
# 	batch_no_list = []
# 	for sb_list in sb_bundle_dict.values():
# 		for sb in sb_list:
# 			doc = frappe.get_doc('Serial and Batch Bundle', sb)
# 			for sbe in doc.entries:
# 				if sbe.batch_no:
# 					batch_no_list.append(sbe.batch_no)
# 	if batch_no_list:
# 		# Fetch batch details in bulk
# 		batch_data = frappe.db.sql("""
# 			SELECT name, batch_qty, creation 
# 			FROM `tabBatch` 
# 			WHERE name IN %s AND batch_qty > 0
# 		""", (batch_no_list,), as_dict=True)
        
# 		# Create a dictionary for batch data
# 		batch_dict = {batch.name: batch for batch in batch_data}
        
# 		# Process each item from the sales order
# 		for j in sales_order.items:
# 			qty = j.qty - j.picked_qty
# 			if qty <= 0:
# 				continue
# 			serial_and_batch_data = []
# 			for entry in serial_and_batch_bundles:
# 				if entry['item_code'] == j.item_code and entry['warehouse'] == j.warehouse:
# 					sb = entry['sb']
# 					total_quantity = entry['total_qty']  # Use summed quantity

# 					doc = frappe.get_doc('Serial and Batch Bundle', sb)
# 					for sbe in doc.entries:
# 						batch_no = sbe.batch_no
# 						if batch_no and batch_no in batch_dict:
# 							batch_info = batch_dict[batch_no]
# 							creation_date = batch_info.creation
# 							batch_qty = batch_info.batch_qty
# 							serial_and_batch_data.append((sb, batch_no, creation_date, batch_qty))

# 					# Remove duplicates and sort by creation date
# 					unique_serial_and_batch_data = list(set(serial_and_batch_data))
# 					sorted_data = sorted(unique_serial_and_batch_data, key=lambda x: x[2])

# 					for sb, batch_no, creation_date, batch_qty in sorted_data:
# 						if qty <= 0:
# 							break

# 						# Use total_quantity (sum of actual_qty from SLE)
# 						if total_quantity > 0:
# 							if batch_qty >= total_quantity:
# 								batch_qty -= total_quantity
# 								used_quantity = min(total_quantity, qty)
# 							else:
# 								used_quantity = min(batch_qty, qty)
# 								batch_qty = 0

# 							qty -= used_quantity
# 			nonavailable_qty = qty
# 			if nonavailable_qty > 0:
# 				items.append({
# 					'item_code': j.item_code,
# 					'description': j.description,
# 					'pending_qty': nonavailable_qty,
# 				})
    
# 	return items


@frappe.whitelist()
def count_qty_rack(item,rack,warehouse):
    entries = frappe.get_all("Stock Ledger Entry", filters={"is_cancelled": 0,"item_code":item,"rack":rack,"warehouse":warehouse}, fields=["actual_qty"])
    total_qty = sum(entry["actual_qty"] for entry in entries)
    return total_qty

@frappe.whitelist()
def create_stock_entry(doc,method):
    stock = frappe.new_doc("Stock Entry")
    stock.stock_entry_type = "Material Transfer"
    stock.company = doc.company
    stock.custom_rack_transfer = doc.name
    stock.set_posting_time = 1
    stock.posting_date = doc.posting_date
    stock.posting_time = doc.posting_time
    for i in doc.items:
        stock.append('items',{
            'item_code':doc.item,
            's_warehouse': doc.warehouse,
            't_warehouse':doc.warehouse,
            'qty':i.new_qty,
            'basic_rate':frappe.db.get_value("Item",{"name":doc.item},["valuation_rate"]),
            'uom':frappe.db.get_value("Item",{"name":doc.item},["stock_uom"]),
            'rack':i.current_rack,
            'to_rack':i.new_rack,
        })
    stock.save(ignore_permissions=True)
    stock.submit()



@frappe.whitelist()
def update_rack_name():
    frappe.db.sql("""
        UPDATE `tabStock Ledger Entry`
        SET rack = 'IND18-25-PLT69 - NCME'
        WHERE name='MAT-SLE-2024-25767'
    """,as_dict=True)

# @frappe.whitelist()
# def update_rackwise_items(company, custom_merge_item):
# 	items = []
# 	merge_pick_list_item = json.loads(custom_merge_item)
    
# 	# Prepare a list of item codes and warehouses for bulk query
# 	item_codes_warehouses = [(j['item_code'], j['warehouse']) for j in merge_pick_list_item]
    
# 	# Fetch serial and batch bundle data and sum actual_qty for each item and warehouse
# 	serial_and_batch_bundles = frappe.db.sql("""
# 		SELECT item_code, warehouse, serial_and_batch_bundle AS sb, rack, SUM(actual_qty) AS total_qty
# 		FROM `tabStock Ledger Entry`
# 		WHERE (item_code, warehouse) IN %s
# 		AND is_cancelled = 0 
# 		AND serial_and_batch_bundle != '' 
# 		AND rack != ''
# 		AND rack != 'Main Rack' 
# 		GROUP BY item_code, warehouse, rack
# 		ORDER BY creation ASC
# 	""", (item_codes_warehouses,), as_dict=True)

# 	# Build a dictionary for serial and batch bundle data
# 	sb_bundle_dict = {}
# 	for entry in serial_and_batch_bundles:
# 		sb_bundle_dict.setdefault((entry.item_code, entry.warehouse), []).append(entry.sb)
    
# 	# Prepare a list of batch numbers to fetch batch data in bulk
# 	batch_no_list = []
# 	for sb_list in sb_bundle_dict.values():
# 		for sb in sb_list:
# 			doc = frappe.get_doc('Serial and Batch Bundle', sb)
# 			for sbe in doc.entries:
# 				if sbe.batch_no:
# 					batch_no_list.append(sbe.batch_no)

# 	if batch_no_list:
# 		# Fetch batch details in bulk
# 		batch_data = frappe.db.sql("""
# 			SELECT name, batch_qty, creation 
# 			FROM `tabBatch` 
# 			WHERE name IN %s AND batch_qty > 0
# 		""", (batch_no_list,), as_dict=True)
        
# 		# Create a dictionary for batch data
# 		batch_dict = {batch.name: batch for batch in batch_data}
# 		merged_items = {}

# 		# Process each item from the merge_pick_list_item
# 		for j in merge_pick_list_item:
# 			qty = j['qty']
# 			if qty <= 0:
# 				continue

# 			serial_and_batch_data = []
# 			for entry in serial_and_batch_bundles:
# 				if entry['item_code'] == j['item_code'] and entry['warehouse'] == j['warehouse']:
# 					sb = entry['sb']
# 					total_quantity = entry['total_qty']  # Use summed quantity

# 					doc = frappe.get_doc('Serial and Batch Bundle', sb)
# 					for sbe in doc.entries:
# 						batch_no = sbe.batch_no
# 						if batch_no and batch_no in batch_dict:
# 							batch_info = batch_dict[batch_no]
# 							creation_date = batch_info.creation
# 							batch_qty = batch_info.batch_qty
# 							serial_and_batch_data.append((sb, batch_no, creation_date, batch_qty, sbe.qty))

# 					# Remove duplicates and sort by creation date
# 					unique_serial_and_batch_data = list(set(serial_and_batch_data))
# 					sorted_data = sorted(unique_serial_and_batch_data, key=lambda x: x[2])

# 					for sb, batch_no, creation_date, batch_qty, sbe_qty in sorted_data:
# 						if qty <= 0:
# 							break
# 						frappe.errprint(total_quantity)
# 						# frappe.errprint(f"Total Qty Before Processing: {total_quantity}, SBE Qty: {sbe_qty}")

# 						# Adjust based on actual SBE qty
# 						if sbe_qty < 0:
# 							# If the entry qty is negative, subtract it
# 							qty_to_deduct = min(abs(sbe_qty), qty)
# 							total_quantity -= qty_to_deduct
# 							qty -= qty_to_deduct
# 						else:
# 							if total_quantity > 0:
# 								used_quantity = min(batch_qty, qty, total_quantity)

# 								qty -= used_quantity
# 								total_quantity -= used_quantity

# 								# Fetch rack and warehouse information
# 								rack = entry['rack']
# 								warehouse = entry['warehouse']

# 								# Create a unique key for each combination of item_code, warehouse, rack, and batch_no
# 								key = (j['item_code'], warehouse, rack, batch_no)

# 								# If the same item, rack, and batch already exist, accumulate the quantity
# 								if key in merged_items:
# 									frappe.errprint(f"Existing Key: {key} - Adding {used_quantity}")
# 									merged_items[key]['qty'] += used_quantity
# 								else:
# 									frappe.errprint(f"New Key: {key} - Adding {used_quantity}")
# 									merged_items[key] = {
# 										'item_code': j['item_code'],
# 										'item_name': j['item_name'],
# 										'description': j['description'],
# 										'qty': used_quantity,
# 										'rack': rack,
# 										'uom': j['uom'],
# 										'against_sales_order': j['against_sales_order'],
# 										'warehouse': warehouse,
# 										'sales_order_item': j['sales_order_item'],
# 										'batch': batch_no
# 									}

# 		# Convert merged_items dictionary to the final items list
# 		items = list(merged_items.values())
    
# 	return items


# @frappe.whitelist()
# def update_non_available_qty_in_pick_list(so):
# 	items = []
# 	sales_order = frappe.get_doc("Sales Order", so)
    
# 	# Prepare a list of item codes and warehouses for bulk query
# 	item_codes_warehouses = [(j.item_code, j.warehouse) for j in sales_order.items]

# 	# Fetch serial and batch bundle data in one query
# 	serial_and_batch_bundles = frappe.db.sql("""
# 		SELECT item_code, warehouse, serial_and_batch_bundle AS sb, rack, SUM(actual_qty) AS total_qty
# 		FROM `tabStock Ledger Entry`
# 		WHERE (item_code, warehouse) IN %s
# 		AND is_cancelled = 0 
# 		AND serial_and_batch_bundle != '' 
# 		AND rack != ''
# 		AND rack != 'Main Rack' 
# 		GROUP BY item_code, warehouse,rack
# 		ORDER BY creation DESC
# 	""", (item_codes_warehouses,), as_dict=True)
    
# 	# Build a dictionary for serial and batch bundle data
# 	sb_bundle_dict = {}
# 	for entry in serial_and_batch_bundles:
# 		sb_bundle_dict.setdefault((entry.item_code, entry.warehouse), []).append(entry.sb)
    
# 	# Prepare a list of batch numbers to fetch batch data in bulk
# 	batch_no_list = []
# 	for sb_list in sb_bundle_dict.values():
# 		for sb in sb_list:
# 			doc = frappe.get_doc('Serial and Batch Bundle', sb)
# 			for sbe in doc.entries:
# 				if sbe.batch_no:
# 					batch_no_list.append(sbe.batch_no)

# 	if batch_no_list:
# 		# Fetch batch details in bulk
# 		batch_data = frappe.db.sql("""
# 			SELECT name, batch_qty, creation 
# 			FROM `tabBatch` 
# 			WHERE name IN %s AND batch_qty > 0
# 		""", (batch_no_list,), as_dict=True)
        
# 		# Create a dictionary for batch data
# 		batch_dict = {batch.name: batch for batch in batch_data}
        
# 		# Process each item from the sales order
# 		for j in sales_order.items:
# 			qty = j.qty - (j.delivered_qty)
# 			if qty <= 0:
# 				continue

# 			serial_and_batch_data = []
# 			for entry in serial_and_batch_bundles:
# 				if entry['item_code'] == j.item_code and entry['warehouse'] == j.warehouse:
# 					sb = entry['sb']
# 					total_quantity = entry['total_qty']  # Use summed quantity

# 					doc = frappe.get_doc('Serial and Batch Bundle', sb)
# 					for sbe in doc.entries:
# 						batch_no = sbe.batch_no
# 						if batch_no and batch_no in batch_dict:
# 							batch_info = batch_dict[batch_no]
# 							creation_date = batch_info.creation
# 							batch_qty = batch_info.batch_qty
# 							serial_and_batch_data.append((sb, batch_no, creation_date, batch_qty, sbe.qty))

# 					# Remove duplicates and sort by creation date
# 					unique_serial_and_batch_data = list(set(serial_and_batch_data))
# 					sorted_data = sorted(unique_serial_and_batch_data, key=lambda x: x[2])

# 					for sb, batch_no, creation_date, batch_qty, sbe_qty in sorted_data:
# 						if qty <= 0:
# 							break

# 						# Adjust based on actual SBE qty
# 						if sbe_qty < 0:
# 							# If the entry qty is negative, subtract it
# 							qty_to_deduct = min(abs(sbe_qty), qty)
# 							total_quantity -= qty_to_deduct
# 							qty -= qty_to_deduct
# 						else:
# 							if total_quantity > 0:
# 								used_quantity = min(batch_qty, qty, total_quantity)

# 								qty -= used_quantity
# 								total_quantity -= used_quantity

# 			# Check remaining non-available qty after processing
# 			nonavailable_qty = qty
# 			if nonavailable_qty > 0:
# 				items.append({
# 					'item_code': j.item_code,
# 					'description': j.description,
# 					'pending_qty': nonavailable_qty,
# 				})
    
# 	return items


# import frappe

# def hide_inspect_button(doc, method):
# 		if doc.skip_qc==1:
# 			frappe.get_meta('Purchase Receipt Item').get_field('inspect').hidden = 1
# 		else:
# 			frappe.get_meta('Purchase Receipt Item').get_field('inspect').hidden = 0

@frappe.whitelist()
def update_file_number_opportunity():
    count = 0
    opportunities = frappe.get_all('Opportunity', filters={'file_number': ''}, fields=['name','company'])
    for opp in opportunities:
        count +=1
    # print(count)
        doc = frappe.new_doc('File Number')
        company_series = frappe.db.get_value("Company Series",{'company':opp.company,'document_type':'File Number','with_tax':0},'series')
        doc.company = opp.company
        doc.naming_series = company_series
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        doc_name = doc.name
        print(doc_name)

        frappe.db.set_value('Opportunity', opp['name'], 'file_number', doc_name)
@frappe.whitelist()
def update_file_number_quotation():
    count = 0
    quotations = frappe.get_all('Quotation',filters={'file_number': '','opportunity': ['!=', ''],'transaction_date': ['between', ['2024-01-01', '2024-10-15']],'docstatus': ['!=', '2']},fields=['name', 'opportunity'])

    for opp in quotations:
        count += 1
        filenumber = frappe.db.get_value("Opportunity", {'name': opp['opportunity']}, 'file_number')
        # if filenumber: 
        frappe.db.set_value('Quotation', opp['name'], 'file_number', filenumber)

    print(count)

@frappe.whitelist()
def validate_payment_terms_template(so_no):
    template=frappe.db.get_value("Sales Order",{"name":so_no},["payment_terms_template"])
    return template

@frappe.whitelist()
def update_outbond():
    po = frappe.db.sql("""update `tabOutbond Request` set docstatus = 0 where name ='OBR-000008' """)

@frappe.whitelist()
def update_stock_details(sales_order):
    items=[]
    item_details = frappe.db.sql(""" select name,uom,warehouse,item_code, description, item_name, sum(qty) as qty, sum(delivered_qty) as delivered_qty, sum(picked_qty) as picked_qty from `tabSales Order Item` where parent = '%s' group by item_code order by idx """%(sales_order),as_dict = 1)
    
    for j in item_details:
        qty = 0
        av_qty = j.qty - (j.delivered_qty+(j.picked_qty))
        if av_qty > 0:
            qty = av_qty
        available_qty = 0
        # ware = frappe.db.get_list("Warehouse",{"company":doc.company},['name'])
        # for w in ware:
        bin = frappe.get_all("Bin",{"item_code":j.item_code,"warehouse":j.warehouse},['actual_qty','reserved_stock'])
        sto = sum([value.get("actual_qty", 0) for value in bin])
        if sto and sto>0:
            reserve = frappe.db.sql("""
                SELECT (sum(reserved_qty) - sum(delivered_qty)) as reserved_qty 
                FROM `tabStock Reservation Entry` 
                WHERE voucher_no = %s 
                AND item_code = %s 
                AND docstatus != 2
            """, (sales_order, j.item_code), as_dict=1)
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
        if available_qty > 0:
            items.append({
                'item_code': j.item_code,
                'description': j.description,
                'qty': available_qty,
                "item_name":j.item_name,
                'sales_order':sales_order,
                'warehouse':j.warehouse,
                "uom":j.uom,
                'sales_order_item':j.name,
                'stock_qty':available_qty,
            })
    return items

@frappe.whitelist()
def update_nonavailable_stock(sales_order):
    # item_details = doc.items
    doc=frappe.get_doc("Sales Order", sales_order)
    item_details = frappe.db.sql(""" select item_code,description, sum(qty)as qty,sum(delivered_qty)as delivered_qty, warehouse from `tabSales Order Item` where parent = '%s' group by item_code order by idx """%(doc.name),as_dict = 1)
    items=[]
    
    for j in item_details:
        del_note = frappe.db.get_all("Delivery Note", {"file_number": doc.file_number,"docstatus":("!=",2)}, ['*'])
        if del_note:
            del_qty = 0
            for i in del_note:
                deli_note = frappe.get_doc("Delivery Note", i.name)
                if deli_note.items:
                    for item in deli_note.items:
                        if j.item_code == item.item_code:
                            del_qty += item.qty
            available_qty = 0
            nonavailable_qty = 0
            
            bin = frappe.get_all("Bin",{"item_code":j.item_code,"warehouse":j.warehouse},['actual_qty','reserved_stock'])
            sto = sum([value.get("actual_qty", 0) for value in bin])
            if sto and sto>0:
                
                reserve = frappe.db.sql("""
                    SELECT (sum(reserved_qty) - sum(delivered_qty)) as reserved_qty
                    FROM `tabStock Reservation Entry` 
                    WHERE voucher_no = %s 
                    AND item_code = %s 
                    AND docstatus != 2
                """, (doc.name, j.item_code), as_dict=1)
                stock = sum([value.get("actual_qty", 0) for value in bin]) - sum([value.get("reserved_stock", 0) for value in bin])

                if reserve:
                    reser_qty = reserve[0]['reserved_qty']
                else:
                    reser_qty = 0

                if reser_qty and reser_qty > 0:
                    available_qty = reser_qty
                else:
                    if stock and j.qty >= stock:
                        available_qty = stock
                        
                    elif stock and j.qty < stock:
                        available_qty = j.qty
            nonavailable_qty = (j.qty - del_qty) - available_qty

            if nonavailable_qty > 0:
                items.append({
                    'item_code': j.item_code,
                    'description': j.description,
                    'nonavailable_qty': nonavailable_qty,
                    
                })
        else:
            available_qty = 0
            nonavailable_qty = 0
            
            bin = frappe.get_all("Bin",{"item_code":j.item_code,"warehouse":j.warehouse},['actual_qty','reserved_stock'])
            sto = sum([value.get("actual_qty", 0) for value in bin])
            if sto and sto>0:
            
                reserve = frappe.db.sql("""
                    SELECT (sum(reserved_qty) - sum(delivered_qty)) as reserved_qty 
                    FROM `tabStock Reservation Entry` 
                    WHERE voucher_no = %s 
                    AND item_code = %s 
                    AND docstatus != 2
                """, (doc.name, j.item_code), as_dict=1)
                stock = sum([value.get("actual_qty", 0) for value in bin]) - sum([value.get("reserved_stock", 0) for value in bin])

                if reserve:
                    reser_qty = reserve[0]['reserved_qty']
                else:
                    reser_qty = 0

                if reser_qty and reser_qty > 0:
                    available_qty = reser_qty
                else:
                    if stock and j.qty >= stock:
                        available_qty = stock
                        
                    elif stock and j.qty < stock:
                        available_qty = j.qty
            nonavailable_qty = j.qty - available_qty
            if nonavailable_qty > 0:
               items.append({
                    'item_code': j.item_code,
                    'description': j.description,
                    'nonavailable_qty': nonavailable_qty,
                    
                })
    return items

@frappe.whitelist()
def update_sales_order_qty():
    sales_order=frappe.get_doc("Sales Order","SO-NCMEF-2024-00437-2")
    for so in sales_order.items:
        if so.qty!=so.sales_order_qty_:
            print(so.name)
            frappe.db.set_value("Sales Order Item",so.name,'sales_order_qty_',so.qty)


@frappe.whitelist()
def create_job_fail():
    job = frappe.db.exists('Scheduled Job Type', 'cron_failed')
    if not job:
        emc = frappe.new_doc("Scheduled Job Type")
        emc.update({
            "method": 'norden.custom.cron_failed_method',
            "frequency": 'Cron',
            "cron_format": '*/5 * * * *'
        })
        emc.save(ignore_permissions=True)


@frappe.whitelist()
def cron_failed_method():
    cutoff_time = datetime.now() - timedelta(minutes=5)
    failed_jobs = frappe.get_all(
        "Scheduled Job Log",
        filters={
            "status": "Failed",
            "creation": [">=", cutoff_time]
        },
        fields=["scheduled_job_type"]
    )
    unique_job_types = set()
    for job in failed_jobs:
        unique_job_types.add(job['scheduled_job_type'])

    for job_type in unique_job_types:
        frappe.sendmail(
            recipients = ["erp@groupteampro.com","pavithra.s@groupteampro.com"],
            subject = 'Failed Cron List - Norden',
            message = 'Dear Sir / Mam <br> Kindly find the below failed Scheduled Job  %s'%(job_type)
        )

@frappe.whitelist()
def get_valuation_rate_from_sle():
    valuation_rate=frappe.db.sql("""SELECT 
        item_code,
        valuation_rate
    FROM 
        `tabStock Ledger Entry`
    WHERE 
        warehouse like '%- NCME'
        AND is_cancelled = 0
        AND voucher_type = 'Purchase Receipt'
        AND creation = (
            SELECT 
                MAX(creation)
            FROM 
                `tabStock Ledger Entry` AS sub
            WHERE 
                sub.item_code = `tabStock Ledger Entry`.item_code
                AND sub.warehouse like '%- NCME'
                AND sub.is_cancelled = 0
                AND sub.voucher_type = 'Purchase Receipt'
    )""",as_dict=1)
    count=0
    for i in valuation_rate:
        item_group = frappe.db.get_value("Item", {"name": i.item_code}, ['item_sub_group'])
        margin_price = frappe.get_doc("Margin Price Tool")
        if frappe.db.exists("Item Price",{'item_code':i.item_code,'price_list':'Cost Rate - NCMEF'}):
            item_price=frappe.get_doc("Item Price",{'item_code':i.item_code,'price_list':'Cost Rate - NCMEF'})
            if item_price.price_list_rate != i.valuation_rate:
                item_price.price_list_rate = i.valuation_rate
                item_price.save(ignore_permissions=True)
        else:
            item_price = frappe.new_doc("Item Price")
            item_price.item_code=i.item_code
            item_price.price_list='Cost Rate - NCMEF'
            item_price.price_list_rate=i.valuation_rate
            item_price.valid_from='2022-01-01'
            item_price.save(ignore_permissions=True)
        for t in margin_price.dubai:
            if t.item_group == item_group:
                
                landing_cost = i.valuation_rate * t.landing
                incentive_cost = landing_cost * t.incentive
                if frappe.db.exists("Item Price",{'item_code':i.item_code,'price_list':'Landing - NCMEF'}):
                    item_price=frappe.get_doc("Item Price",{'item_code':i.item_code,'price_list':'Landing - NCMEF'})
                    if item_price.price_list_rate != landing_cost:
                        
                        item_price.price_list_rate = landing_cost
                        item_price.save(ignore_permissions=True)
                else:
                    item_price = frappe.new_doc("Item Price")
                    item_price.item_code=i.item_code
                    item_price.price_list='Landing - NCMEF'
                    item_price.price_list_rate=landing_cost
                    item_price.valid_from='2022-01-01'
                    item_price.save(ignore_permissions=True)
                if frappe.db.exists("Item Price",{'item_code':i.item_code,'price_list':'Incentive - NCMEF'}):
                    item_price=frappe.get_doc("Item Price",{'item_code':i.item_code,'price_list':'Incentive - NCMEF'})
                    if item_price.price_list_rate != incentive_cost:
                        item_price.price_list_rate = incentive_cost
                        item_price.save(ignore_permissions=True)
                else:
                    item_price = frappe.new_doc("Item Price")
                    item_price.item_code=i.item_code
                    item_price.price_list='Incentive - NCMEF'
                    item_price.price_list_rate=incentive_cost
                    item_price.valid_from='2022-01-01'
                    item_price.save(ignore_permissions=True)
        # print(f'Item {i.item_code} - val_rate :{i.valuation_rate}')
        count+=1
    print(count)

@frappe.whitelist()
def get_stock_manuel():
    # item_details = doc.items
    doc=frappe.get_doc("Sales Order",'SO-NCMEFT-2024-01358')
    item_details = frappe.db.sql(""" select item_code,description, sum(qty)as qty,sum(delivered_qty)as delivered_qty from `tabSales Order Item` where parent = '%s' group by item_code order by idx """%(doc.name),as_dict = 1)

    data = ''
    data += '<h4><center><b>NON AVAILABLE QTY</b></center></h4>'
    data += '<table class="table table-bordered">'

    data += '<tr>'
    data += '<td colspan=4 style="color:#FFFFFF;width:13%;padding:1px;border:1px solid black;font-size:14px;background-color:#e20026;color:white;text-align:center">PRODUCT</td>'
    data += '<td colspan=4 style="width:70px;padding:1px;border:1px solid black;font-size:14px;background-color:#e20026;color:white;text-align:center">DESCRIPTION</td>'
    data += '<td colspan=4 style="width:70px;padding:1px;border:1px solid black;font-size:14px;background-color:#e20026;color:white;text-align:center">QTY</td>'	
    for j in item_details:
        
        del_note = frappe.db.get_all("Delivery Note", {"file_number": doc.file_number,"docstatus":("=",1)}, ['*'])
        if del_note:
            del_qty = 0
            for i in del_note:
                deli_note = frappe.get_doc("Delivery Note", i.name)
                if deli_note.items:
                    for item in deli_note.items:
                        if j.item_code == item.item_code:
                            del_qty += item.qty
            available_qty = 0
            nonavailable_qty = 0
            warehouse = []
            ware = frappe.db.get_list("Warehouse", {"company": doc.company}, ['name'])
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
                    """, (doc.name, j.item_code), as_dict=1)
                    stock = sum([value.get("actual_qty", 0) for value in bin]) - sum([value.get("reserved_stock", 0) for value in bin])

                    if reserve:
                        reser_qty = reserve[0]['reserved_qty']
                    else:
                        reser_qty = 0

                    if reser_qty and reser_qty > 0:
                        available_qty = reser_qty
                    else:
                        if stock and j.qty >= stock:
                            available_qty = stock
                            
                        elif stock and j.qty < stock:
                            available_qty = j.qty
            nonavailable_qty = (j.qty - del_qty) - available_qty
            print(f'{j.item_code} - {del_qty}')
            if nonavailable_qty > 0:
                data += '<tr><td style="text-align:center;border: 1px solid black" colspan=4>%s</td>' %(j.item_code)
                data += '<td style="text-align:center;border: 1px solid black" colspan=4>%s</td>' %(j.description)
                data += '<td style="text-align:center;border: 1px solid black;text-align:right" colspan=4>%s</td>' %(nonavailable_qty)
                data += '</tr>'
        else:
            available_qty = 0
            nonavailable_qty = 0
            warehouse = []
            ware = frappe.db.get_list("Warehouse", {"company": doc.company}, ['name'])
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
                    """, (doc.name, j.item_code), as_dict=1)
                    stock = sum([value.get("actual_qty", 0) for value in bin]) - sum([value.get("reserved_stock", 0) for value in bin])

                    if reserve:
                        reser_qty = reserve[0]['reserved_qty']
                    else:
                        reser_qty = 0

                    if reser_qty and reser_qty > 0:
                        available_qty = reser_qty
                    else:
                        if stock and j.qty >= stock:
                            available_qty = stock
                            
                        elif stock and j.qty < stock:
                            available_qty = j.qty
            nonavailable_qty = j.qty - available_qty
            if nonavailable_qty > 0:
                data += '<tr><td style="text-align:center;border: 1px solid black" colspan=4>%s</td>' %(j.item_code)
                data += '<td style="text-align:center;border: 1px solid black" colspan=4>%s</td>' %(j.description)
                data += '<td style="text-align:center;border: 1px solid black;text-align:right" colspan=4>%s</td>' %(nonavailable_qty)
                data += '</tr>'
    data += '</tr>'
    data += '</table>'
    return data

@frappe.whitelist()
def update_inspect(item,name,serial_and_batch_bundle=None):
    if frappe.db.get_value("Item Inspection",{"docstatus":1,"item_code":item,"pr_number":name,"serial_and_batch_bundle":serial_and_batch_bundle}):
        return "Yes"


@frappe.whitelist()
def invoice_cancel(doc,method):
    if doc.irn:
        if frappe.db.get_value("e-Invoice Log",{"sales_invoice":doc.name}):
            created_time = doc.creation
            time_diff = frappe.utils.now_datetime() - created_time
            if time_diff > timedelta(hours=24):
                frappe.throw("This document is linked with E Invoice ,So you can't able to cancel")

@frappe.whitelist()
def get_items_from_so(so):
    items=[]
    sales_order=frappe.get_doc("Sales Order",so)
    for s in sales_order.items:
        items.append({'item_code':s.item_code,
        'item_name':s.item_name,
        'qty':s.qty})
    return items

import frappe

import frappe

import frappe

@frappe.whitelist()
def clear_sales_team_entry():
    parent = "SI-NCMEFT-2025-01132"
    sales_person = "Suresh Chandran Puthumana"
    allocated_percentage = 100
    allocated_amount = 96421.63

    # Insert a new row
    frappe.db.sql("""
        INSERT INTO `tabSales Team`
        (name, parent, parentfield, parenttype, sales_person, allocated_percentage, allocated_amount, idx)
        VALUES (%s, %s, 'sales_team', 'Sales Invoice', %s, %s, %s, 1)
    """, (
        frappe.utils.now(),  # unique name for row
        parent,
        sales_person,
        allocated_percentage,
        allocated_amount
    ))

    frappe.db.commit()
    return "Sales Team updated successfully."

@frappe.whitelist()
def create_sales_team_value():
    frappe.db.sql("""
        DELETE FROM `tabSales Team`
        WHERE parent = 'SI-NCMEFT-2025-01132'
    """)

@frappe.whitelist()
def update_sales_person_tab_new():
    sales_invoices = frappe.db.sql("""
        SELECT si.name, si.sales_person_user, si.base_total
        FROM `tabSales Invoice` si
        LEFT JOIN `tabSales Team` st ON st.parent = si.name
        WHERE st.sales_person IS NULL
          AND si.docstatus = 1
          AND si.company = 'Norden Communication Middle East FZE'
          AND si.posting_date BETWEEN '2025-01-01' AND '2025-08-31'
    """, as_dict=True)

    count = 0
    for row in sales_invoices:
        if not row.sales_person_user:
            continue

        # Load Sales Invoice
        si_doc = frappe.get_doc("Sales Invoice", row.name)

        # Append sales team row
        si_doc.append("sales_team", {
            "sales_person": row.sales_person_user,
            "allocated_percentage": 100,
            "allocated_amount": row.base_total
        })

        si_doc.save(ignore_permissions=True)
        count += 1

    frappe.db.commit()
    return f"Updated {count} Sales Invoices."


# @frappe.whitelist()
# def update_workflow_state():	
#     frappe.db.set_value("Logistics Request","LR-NCPLP-2023-00002",'workflow_state','Pending for Checklist Confirmation')

# @frappe.whitelist()
# def update_custom_po_number():	
    # frappe.db.set_value("Sales Order", {'name':"SO-NCMEFT-2025-00188"}, 'po_no', '70287-0')
    # frappe.db.set_value("Sales Order", {'name':"SO-NCMEFT-2025-00188"}, 'po_date', '2025-02-13')
    # frappe.db.set_value("Delivery Note",{'name':'DN-NCMEFT-2025-00367'},'po_no','70287-0')
    # frappe.db.set_value("Delivery Note",{'name':'DN-NCMEFT-2025-00367'},'po_date','2025-02-13')
    # frappe.db.set_value("Delivery Note",{'name':'DN-NCMEFT-2025-00266'},'po_no','70287-0')
    # frappe.db.set_value("Delivery Note",{'name':'DN-NCMEFT-2025-00266'},'po_date','2025-02-13')
    # sales_invoice_list = frappe.db.get_all('Sales Invoice',{'so_no':'SO-NCMEFT-2025-00188','docstatus':['!=',2]},'name')
    # for si in sales_invoice_list:
    # 	print(si.name)
    # 	frappe.db.set_value("Sales Invoice",{'name':si.name},'po_no','70287-0')
    # 	frappe.db.set_value("Sales Invoice",{'name':si.name},'po_date','2025-02-13')

@frappe.whitelist()
def update_lot_no(doc,method):
    if doc.reference_doctype == "Purchase Receipt":
        lot_no = frappe.db.get_value("Purchase Receipt",{"name":doc.reference_name},["custom_supplier_lot_number"])
        if lot_no:
            doc.custom_supplier_lot_number = lot_no
            doc.save(ignore_permissions=True)


@frappe.whitelist()
def validate_reserved_stock_in_pick_list(doc,method):
    msg = ''
    for i in doc.locations:
        if not frappe.db.exists("Stock Reservation Entry",{'item_code':i.item_code,'warehouse':i.warehouse,'docstatus':1,'status':('!=','Delivered'),'voucher_type':'Sales Order','voucher_no':i.sales_order,'voucher_detail_no': i.sales_order_item}):
            reserved_stock,actual_qty = frappe.db.get_value("Bin",{'warehouse':i.warehouse,'item_code':i.item_code},['reserved_stock','actual_qty'])
            available_qty = actual_qty - reserved_stock
            if i.qty>available_qty:
                msg = _("{0} units of {1} needed in {2} to complete this transaction.As the full stock is reserved for other sales orders, you're not allowed to consume the stock.").format(
                    i.qty-available_qty,
                    i.item_code,
                    i.warehouse,
                )
                frappe.throw(msg, title=_("Insufficient Stock"))

@frappe.whitelist()
def update_rackwise_items(company, custom_merge_item):
    items = []
    merge_pick_list_item = json.loads(custom_merge_item)
    
    item_codes_warehouses = [(j['item_code'], j['warehouse']) for j in merge_pick_list_item]

    # Fetch rack-wise total available quantity from Stock Ledger Entry
    serial_and_batch_bundles = frappe.db.sql("""
        SELECT item_code, warehouse, rack, SUM(actual_qty) AS total_qty
        FROM `tabStock Ledger Entry`
        WHERE (item_code, warehouse) IN %s
        AND is_cancelled = 0 
        AND serial_and_batch_bundle != '' 
        AND rack != ''
        AND rack != 'Main Rack' 
        GROUP BY item_code, warehouse, rack
        HAVING total_qty > 0
        ORDER BY creation ASC
    """, (item_codes_warehouses,), as_dict=True)

    # Dictionary to track merged quantities per (item_code, warehouse, rack)
    merged_items = {}

    # Process each pick list item
    for j in merge_pick_list_item:
        qty = j['qty']
        if qty <= 0:
            continue  # Skip if no quantity is required

        for entry in serial_and_batch_bundles:
            # Ensure the stock entry matches the required item and warehouse
            if entry['item_code'] == j['item_code'] and entry['warehouse'] == j['warehouse']:
                if qty <= 0:  # Stop when requested quantity is fulfilled
                    break

                used_quantity = min(qty, entry['total_qty'])

                # Create a unique key for item_code, warehouse, and rack
                key = (j['item_code'], entry['warehouse'], entry['rack'])

                # If the same item and rack exist, accumulate quantity
                if key in merged_items:
                    merged_items[key]['qty'] += used_quantity
                else:
                    merged_items[key] = {
                        'item_code': j['item_code'],
                        'item_name': j['item_name'],
                        'description': j['description'],
                        'qty': used_quantity,
                        'rack': entry['rack'],
                        'uom': j['uom'],
                        'against_sales_order': j['against_sales_order'],
                        'warehouse': entry['warehouse'],
                        'sales_order_item': j['sales_order_item'],
                    }

                # Reduce available quantity in rack and requested quantity
                qty -= used_quantity
                entry['total_qty'] -= used_quantity

    # Convert merged_items dictionary to a list for return
    items = list(merged_items.values())

    return items


@frappe.whitelist()
def update_non_available_qty_in_pick_list(custom_merge_item):
    items = []
    # sales_order = frappe.get_doc("Sales Order", so)
    merge_pick_list_item = json.loads(custom_merge_item)
    # Prepare a list of item codes and warehouses for bulk query
    item_codes_warehouses = [(j['item_code'], j['warehouse']) for j in merge_pick_list_item]

    serial_and_batch_bundles = frappe.db.sql("""
        SELECT item_code, warehouse, rack, SUM(actual_qty) AS total_qty
        FROM `tabStock Ledger Entry`
        WHERE (item_code, warehouse) IN %s
        AND is_cancelled = 0 
        AND serial_and_batch_bundle != '' 
        AND rack != ''
        AND rack != 'Main Rack'
        GROUP BY item_code, warehouse, rack
        ORDER BY creation ASC
    """, (item_codes_warehouses,), as_dict=True)

    # Process each item from the sales order
    for j in merge_pick_list_item:
        qty = j['qty']  # Ensure no negative values
        if qty <= 0:
            continue  # Skip if no quantity is required

        for entry in serial_and_batch_bundles:
            # Ensure we match both item_code and warehouse before allocating stock
            if entry['item_code'] == j['item_code'] and entry['warehouse'] == j['warehouse']:
                if qty <= 0:
                    break  # Stop processing if qty is fulfilled

                used_quantity = min(qty, entry['total_qty'])
                qty -= used_quantity
                entry['total_qty'] -= used_quantity
        
        if qty > 0:
            items.append({
                'item_code': j['item_code'],
                'description': j['description'],
                'pending_qty': qty,
            })
    
    return items

@frappe.whitelist()
def repost_manuel():
    from erpnext.stock.doctype.repost_item_valuation.repost_item_valuation import repost
    sle_id = "c497acd99b"
    repost(sle_id)


@frappe.whitelist()
def update_batch_test():
    att = frappe.db.sql(""" update  `tabSerial No`  set warehouse = 'UAE - Warehouse - NSPL' where name ='EN-486047C2527A00047' """)


@frappe.whitelist()
def automate_inspect_creation(doc,method):
    if doc.company == "Norden Communication Pvt Ltd":
        for i in doc.items:
            ip = frappe.new_doc("Item Inspection")
            ip.naming_series = frappe.db.get_value("Company Series",{'company': doc.company, 'document_type':"Item Inspection", 'with_tax': 0},'series')
            ip.po_number = doc.purchase_order_no
            ip.pr_number = doc.name
            ip.item_code = i.item_code
            ip.received_quantity = i.received_stock_qty
            ip.warehouse = doc.set_warehouse

            ip.inspection_lot_qty = i.received_qty
            ip.inspection_lot_no = i.received_qty
            ip.serial = i.serial_no
            ip.id = i.name
            ip.uom = i.stock_uom
            ip.supplier_name = doc.supplier
            ip.invoice_no = doc.supplier_invoice_number
            
            ip.batch_number = i.batch_no
            ip.company_name = doc.company
            ip.batch = i.batch_no
            ip.serial_and_batch_bundle = i.serial_and_batch_bundle
            if i.serial_and_batch_bundle:
                item = frappe.get_doc("Serial and Batch Bundle",i.serial_and_batch_bundle)
                serial_numbers = []
                # return item.entries.serial_no
                for j in item.entries:
                    if j.serial_no:
                        serial_numbers.append(j.serial_no)
                ip.serial_number = '\n'.join(serial_numbers)
            ip.save()
            frappe.db.sql("""UPDATE `tabPurchase Receipt Item` SET custom_inspect_completed = 1 WHERE parent = %s""",(doc.name,))


@frappe.whitelist()
def create_pi(doc, method):
    if doc.company == "Norden Communication Pvt Ltd":
        pdi = frappe.new_doc("PDI Completion Details")
        pdi.po = doc.name

        for i in doc.items:
            pdi.append('pdi_completion', {
                'item_code': i.item_code,
                'qty': i.qty,
                'po_qty':i.qty
            })

        pdi.naming_series = frappe.db.get_value(
            "Company Series",
            {
                'company': doc.company,
                'document_type': "PDI Completion Details",
                'with_tax': 0
            },
            'series'
        )
        pdi.company = doc.company
        pdi.status = "Draft"
        pdi.save(ignore_permissions=True)


# @frappe.whitelist()
# def set_address():
#     frappe.db.set_value(
#     "Sales Invoice",
#     "NRIC/EX/2025-004",
#     "company_address_display",
#     """Office No:301- B 3rd Floor,
#     Building No : SCK 01 Smart City
#     Kakkanad Kochi
#     Kerala, State Code: 32
#     Postal Code: 682042
#     India
#     Phone: 9961232425
#     Email: accounts@norden.in
#     GSTIN: 32AAICN1519J1ZL"""
#     )

@frappe.whitelist()
def update_sales_person_tab():
    # sales_team = frappe.db.sql("""select * from `tabSales Team` limit 1""",as_dict=True)
    # print(sales_team)
    sales_invoice = frappe.db.sql("""select si.name,si.sales_person_user,si.base_total from `tabSales Invoice` si left join `tabSales Team` st on st.parent = si.name where st.sales_person is null and si.sales_person_user is not null and si.docstatus = 1 and si.company = 'Norden Communication Middle East FZE' and si.posting_date between '2025-06-01' and '2025-06-30'""", as_dict=True)
    ind = 0
    for i in sales_invoice:
        ind += 1
        print(i.name)
        si=frappe.get_doc("Sales Invoice",i.name)
        si.append('sales_team',{
            'sales_person':i.sales_person_user,
            'allocated_percentage':100,
            'allocated_amount':i.base_total
        })
        si.save(ignore_permissions=True)
        
            
    print(ind)


@frappe.whitelist()
def update_buying_amount():
    row_name = frappe.get_all("Sales Invoice Item",{"parent":"SR-NCMEF-2025-00009-2"},["name"])
    for i in row_name:
        print(i.name)


@frappe.whitelist()
def get_bill_value():
    # value = frappe.db.get_value("Purchase Receipt",{"name":"PR-NCPLP-2025-00125"},["per_billed"])
    Reser = frappe.db.set_value("Sales Order","SO-NCMEF-2025-00156",'custom_reservation_status'," ")
    # print(value)

# @frappe.whitelist()
# def update_reserve_check():
#     items = frappe.get_all(
#         "Sales Order Item",
#         filters={
#             "parent": "SO-NCMEF-2025-00156",
#             "item_code": ["!=", "114-40002104GY"]
#         },
#         fields=["name"]
#     )

#     for item in items:
#         frappe.db.set_value("Sales Order Item", item.name, "reserve_stock", value)

#     frappe.db.commit()





import frappe
from frappe.utils import today,formatdate, fmt_money

def send_mail_for_so_summary():


    #  Submitted Orders
    so_list_submitted = frappe.get_all(
        "Sales Order",
        filters={
            "transaction_date": today(),
            "docstatus": 1,
            "company":"Norden Communication Middle East FZE"
        },
        fields=["base_grand_total"]
    )
    total_count_submitted = len(so_list_submitted)
    total_value_submitted = sum(so.base_grand_total for so in so_list_submitted)
    total_value_submitted_fmt = total_value_submitted
    
    # s_person
    so_list = frappe.db.sql("""
        SELECT 
            so.transaction_date AS date,
            sp.sales_person AS sales_person,
            COUNT(so.name) AS so_count,
            SUM(so.base_grand_total) AS total_value
        FROM `tabSales Order` so
        LEFT JOIN `tabSales Team` sp ON sp.parent = so.name
        WHERE so.transaction_date = %s
          AND so.docstatus = 1
          AND so.company='Norden Communication Middle East FZE'
        GROUP BY sp.sales_person
        ORDER BY sp.sales_person
    """, today(), as_dict=True)

    # Calculate grand totals
    grand_total_count = sum(row.so_count for row in so_list)
    grand_total_value = sum(row.total_value for row in so_list)
    
    #cancelled _sales_p
    so_list_cancelled_sp = frappe.db.sql("""
        SELECT
            so.transaction_date AS date,
            sp.sales_person AS sales_person,
            COUNT(so.name) AS so_count,
            SUM(so.base_grand_total) AS total_value
        FROM `tabSales Order` so
        LEFT JOIN `tabSales Team` sp ON sp.parent = so.name
        WHERE so.transaction_date = %s
          AND so.docstatus = 2
          AND so.company='Norden Communication Middle East FZE'
        GROUP BY sp.sales_person
        ORDER BY sp.sales_person
    """, (today(),), as_dict=True)

    grand_total_count_cancel_sp = sum(row.get("so_count", 0) for row in so_list_cancelled_sp)
    grand_total_value_cancel_sp = sum(row.get("total_value", 0) for row in so_list_cancelled_sp)


    #Cancelled Orders
    so_list_cancelled = frappe.get_all(
        "Sales Order",
        filters={
            "transaction_date": today(),
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

    <p>Please find below the details of <b>Sales Orders</b> (Date Wise Status):</p>
    """

    if total_count_submitted > 0:
        html_content += f"""
        <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
        <tr>
        <td colspan="3" style="background-color:#a7d3e0;font-weight:bold;">Incoming SO Value<br>Date wise Status</td>
        </tr>
        <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>Date</td>
        <td>No Of SO's Processed</td>
        <td>Total SO Value</td>
        </tr>
        <tr>
        <td>{formatdate(today())}</td>
        <td>{total_count_submitted}</td>
        <td style="text-align:right;">{fmt_money(total_value_submitted_fmt,2)}</td>
        </tr>
        <tr style="background-color:#a7d3e0;font-weight:bold;"">
        <td style="background-color:#a7d3e0;font-weight:bold;">Grand Total</td>
        <td>{total_count_submitted}</td>
        <td style="text-align:right;">{fmt_money(total_value_submitted_fmt,2)}</td>
        </tr>
        </table>
        """
    else:
    # No sales orders today
        html_content += f"""
    <table border="1" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
    <tr>
    <td colspan="3" style="background-color:#a7d3e0;font-weight:bold;">
        Incoming SO Value<br>Date wise Status
    </td>
    </tr>
     <tr style="background-color:#dee9ec; font-weight:bold;padding:10px;">
    <td>Date</td>
    <td>No Of SO's Processed</td>
    <td>Total SO Value</td>
    </tr>
    <tr>
    <td colspan="3" style="padding:10px; color:red; font-weight:bold;">
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
        <td colspan="4" style="background-color:#a7d3e0;font-weight:bold;">
            Incoming SO Value<br>
            Date & Sales Person wise Status
        </td>
    </tr>
    <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>Date</td>
        <td>Sales Person</td>
        <td>No Of SO's</td>
        <td>Total SO Value</td>
    </tr>
    """

        for row in so_list:
            html_content += f"""
    <tr>
    <td>{formatdate(today())}</td>
    <td style="text-align:left;">{row.sales_person or ''}</td>
    <td>{row.so_count or 0}</td>
    <td style="text-align:right;">{fmt_money(row.total_value,2) or 0}</td>
    </tr>
    """

        html_content += f"""
    <tr style="background-color:#a7d3e0; font-weight:bold;">
    <td colspan="2">Grand Total</td>
    <td>{grand_total_count or 0}</td>
    <td style="text-align:right;">{fmt_money(grand_total_value,2) or 0}</td>
    </tr>
    </table>
    """
    else:
    # No sales person today
        html_content += f"""
     <br><br><br>
    <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
    <tr>
        <td colspan="4" style="background-color:#a7d3e0;font-weight:bold;">
        Incoming SO Value<br>Date wise Status
        </td>
    </tr>
    <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>Date</td>
        <td>Sales Person</td>
        <td>No Of SO's</td>
        <td>Total SO Value</td>
    </tr>
    <tr>
    <td colspan="4" style="padding:10px; color:red; font-weight:bold;">
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
        <td colspan="3" style="background-color:#a7d3e0;font-weight:bold;">Cancelled SO Value<br>Date wise Status</td>
    </tr>
    <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>Date</td>
        <td>No Of SO's Processed</td>
        <td>Total SO Value</td>
    </tr>
    <tr>
        <td>{formatdate(today())}</td>
        <td>{total_count_cancelled}</td>
        <td style="text-align:right;">{fmt_money(total_value_cancelled_fmt,2)}</td>
    </tr>
    <tr style="background-color:#a7d3e0;font-weight:bold;">
        <td>Grand Total</td>
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
        <td colspan="3" style="background-color:#a7d3e0;font-weight:bold;">
        Cancelled SO Value<br>Date wise Status
        </td>
    </tr>
    <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>Date</td>
        <td>No Of SO's Processed</td>
        <td>Total SO Value</td>
    </tr>
    <tr>
        <td colspan="3" style="padding:10px; color:red; font-weight:bold;">
        No Cancel Sales Orders for {formatdate(today())}
    </td>
    </tr>
    </table>
    """

# cancelled
    html_content += """
    <br><br>
    <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
    <tr>
        <td colspan="4" style="background-color:#a7d3e0;font-weight:bold;">Cancelled SO Value<br>Date & Sales Person wise Status</td>
    </tr>
    <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>Date</td>
        <td>Sales Person</td>
        <td>No Of SO's</td>
        <td>Total SO Value</td>
    </tr>
    """
    if so_list_cancelled_sp:
        for row in so_list_cancelled_sp:
            html_content += f"""
        <tr>
            <td style="text-align:left;">{formatdate(today())}</td>
            <td>{row.get('sales_person') or ''}</td>
            <td>{row.get('so_count') or 0}</td>
            <td style="text-align:right;">{fmt_money(row.get('total_value'),2) or 0}</td>
        </tr>
        """
        html_content += f"""
        <tr style="background-color:#a7d3e0; font-weight:bold;">
        <td>{today()}</td>
        <td>Grand Total</td>
        <td>{grand_total_count_cancel_sp or 0}</td>
        <td style="text-align:right;">{fmt_money(grand_total_value_cancel_sp,2) or 0}</td>
        </tr>
        """
    else:
        html_content += f"""
        <tr>
        <td colspan="4" style="padding:10px; color:red; font-weight:bold;">
            No  Cancel Sales Order in Sales Person  {formatdate(today())}
        </td>
        </tr>
        """

    html_content += "</table>"
        

    # ===== Send email =====
    frappe.sendmail(
        recipients=["asif@norden.co.uk","sujith@nordenco.ae","anoop@nordencommunication.com","zackeria@nordenco.ae","deepak@nordenco.ae","muthuselvan.e@groupteampro.com"],
        subject=f"Today's Sales Order Summary - {formatdate(today())}",
        message=html_content
    )

    print("Email sent successfully!")




@frappe.whitelist()
def sales_order_date_wise_summary():
    job = frappe.db.exists('Scheduled Job Type', 'send_mail_for_si_summary')
    if not job:
        sjt = frappe.new_doc("Scheduled Job Type")
        sjt.update({
            "method": 'norden.custom.send_mail_for_si_summary',
            "frequency": 'Cron',
            # minute hour day month day_of_week
            "cron_format": '30 20 * * 1-5'  # Mon-Fri at 6 PM
        })
        sjt.save(ignore_permissions=True)

import frappe
from frappe.utils import today,formatdate, fmt_money

def send_mail_for_si_summary():
    so_list_submitted = frappe.get_all(
        "Sales Invoice",
        filters={
            "posting_date": today(),
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
        WHERE so.posting_date = %s
          AND so.docstatus = 1
          AND so.company='Norden Communication Middle East FZE'
        GROUP BY sp.sales_person
        ORDER BY sp.sales_person
    """, today(), as_dict=True)

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
        WHERE so.posting_date = %s
          AND so.docstatus = 2
          AND so.company='Norden Communication Middle East FZE'
        GROUP BY sp.sales_person
        ORDER BY sp.sales_person
    """, (today(),), as_dict=True)

    grand_total_count_cancel_sp = sum(row.get("so_count", 0) for row in so_list_cancelled_sp)
    grand_total_value_cancel_sp = sum(row.get("total_value", 0) for row in so_list_cancelled_sp)


    so_list_cancelled = frappe.get_all(
        "Sales Invoice",
        filters={
            "posting_date": today(),
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

    <p>Please find below the details of <b>Sales Invoices</b> (Date Wise Status):</p>
    """

    if total_count_submitted > 0:
        html_content += f"""
        <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
        <tr>
        <td colspan="3" style="background-color:#a7d3e0;font-weight:bold;">Total Invoiced<br>Date wise Status</td>
        </tr>
        <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>Date</td>
        <td>No Of Invoices</td>
        <td>Total Invoice Value in AED</td>
        </tr>
        <tr>
        <td>{formatdate(today())}</td>
        <td>{total_count_submitted}</td>
        <td style="text-align:right;">{fmt_money(total_value_submitted_fmt,2)}</td>
        </tr>
        <tr style="background-color:#a7d3e0;font-weight:bold;"">
        <td style="background-color:#a7d3e0;font-weight:bold;">Grand Total</td>
        <td>{total_count_submitted}</td>
        <td style="text-align:right;">{fmt_money(total_value_submitted_fmt,2)}</td>
        </tr>
        </table>
        """
    else:
        html_content += f"""
    <table border="1" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
    <tr>
    <td colspan="3" style="background-color:#a7d3e0;font-weight:bold;">
        Total Invoiced<br>Date wise Status
    </td>
    </tr>
     <tr style="background-color:#dee9ec; font-weight:bold;padding:10px;">
    <td>Date</td>
    <td>No Of Invoices</td>
    <td>Total Invoice Value in AED</td>
    </tr>
    <tr>
    <td colspan="3" style="padding:10px; color:red; font-weight:bold;">
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
        <td colspan="4" style="background-color:#a7d3e0;font-weight:bold;">
            Total Invoiced<br>
            Date & Sales Person wise Status
        </td>
    </tr>
    <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>Date</td>
        <td>Sales Person</td>
        <td>No Of Invoices</td>
        <td>Total Invoiced Value in AED</td>
    </tr>
    """

        for row in so_list:
            html_content += f"""
    <tr>
    <td>{formatdate(today())}</td>
    <td style="text-align:left;">{row.sales_person or ''}</td>
    <td>{row.so_count or 0}</td>
    <td style="text-align:right;">{fmt_money(row.total_value,2) or 0}</td>
    </tr>
    """

        html_content += f"""
    <tr style="background-color:#a7d3e0; font-weight:bold;">
    <td colspan="2">Grand Total</td>
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
        <td colspan="4" style="background-color:#a7d3e0;font-weight:bold;">
        Total Invoiced<br>Date wise Status
        </td>
    </tr>
    <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>Date</td>
        <td>Sales Person</td>
        <td>No Of Invoices</td>
        <td>Total Invoiced Value in AED</td>
    </tr>
    <tr>
    <td colspan="4" style="padding:10px; color:red; font-weight:bold;">
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
        <td colspan="3" style="background-color:#a7d3e0;font-weight:bold;">Total Cancelled Invoice<br>Date wise Status</td>
    </tr>
    <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>Date</td>
        <td>No Of Invoices</td>
        <td>Total Invoice Value in AED</td>
    </tr>
    <tr>
        <td>{formatdate(today())}</td>
        <td>{total_count_cancelled}</td>
        <td style="text-align:right;">{fmt_money(total_value_cancelled_fmt,2)}</td>
    </tr>
    <tr style="background-color:#a7d3e0;font-weight:bold;">
        <td>Grand Total</td>
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
        <td colspan="3" style="background-color:#a7d3e0;font-weight:bold;">
        Total Cancelled Invoice<br>Date wise Status
        </td>
    </tr>
    <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>Date</td>
        <td>No Of Invoices</td>
        <td>Total Invoiced Value in AED</td>
    </tr>
    <tr>
        <td colspan="3" style="padding:10px; color:red; font-weight:bold;">
        No Cancel Sales Invoices for {formatdate(today())}
    </td>
    </tr>
    </table>
    """

    html_content += """
    <br><br>
    <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
    <tr>
        <td colspan="4" style="background-color:#a7d3e0;font-weight:bold;">Total Cancelled Invoice<br>Date & Sales Person wise Status</td>
    </tr>
    <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>Date</td>
        <td>Sales Person</td>
        <td>No Of Invoices</td>
        <td>Total Invoiced Value in AED</td>
    </tr>
    """
    if so_list_cancelled_sp:
        for row in so_list_cancelled_sp:
            html_content += f"""
        <tr>
            <td style="text-align:left;">{formatdate(today())}</td>
            <td>{row.get('sales_person') or ''}</td>
            <td>{row.get('so_count') or 0}</td>
            <td style="text-align:right;">{fmt_money(row.get('total_value'),2) or 0}</td>
        </tr>
        """
        html_content += f"""
        <tr style="background-color:#a7d3e0; font-weight:bold;">
        <td>{today()}</td>
        <td>Grand Total</td>
        <td>{grand_total_count_cancel_sp or 0}</td>
        <td style="text-align:right;">{fmt_money(grand_total_value_cancel_sp,2) or 0}</td>
        </tr>
        """
    else:
        html_content += f"""
        <tr>
        <td colspan="4" style="padding:10px; color:red; font-weight:bold;">
            No  Cancel Sales Invoices in Sales Person  {formatdate(today())}
        </td>
        </tr>
        """

    html_content += "</table>"
        

    frappe.sendmail(
        recipients=["asif@norden.co.uk","sujith@nordenco.ae","anoop@nordencommunication.com","zackeria@nordenco.ae","deepak@nordenco.ae"],
        # recipients="divya.p@groupteampro.com",
        subject=f"Today's Sales Invoice Summary - {formatdate(today())}",
        message=html_content
    )


import frappe
from frappe.utils import today, formatdate, fmt_money, nowdate, get_first_day, get_last_day

def send_mail_for_so_summary_monthly():
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
        # recipients='jenisha.p@groupteampro.com',
        recipients=["asif@norden.co.uk","sujith@nordenco.ae","anoop@nordencommunication.com","zackeria@nordenco.ae","deepak@nordenco.ae"],
        subject=f"Monthly Sales Order Summary - {formatdate(today())}",
        message=html_content
    )

    print("Email sent successfully!")



import frappe
from frappe.utils import today, formatdate, fmt_money, nowdate, get_first_day, get_last_day

def send_mail_for_si_summary_monthly():
    current_date = nowdate()
    # current_date="2025-12-31"
    # start_date = "2025-12-01"
    # end_date = "2025-12-31"
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
        recipients=["asif@norden.co.uk","sujith@nordenco.ae","anoop@nordencommunication.com","zackeria@nordenco.ae","deepak@nordenco.ae"],
        subject=f"Monthly Sales Invoice Summary - {formatdate(today())}",
        message=html_content
    )

    print("Email sent successfully!")

import frappe
from frappe.utils import today, formatdate, fmt_money, nowdate, get_first_day, get_last_day

def send_mail_for_si_summary_monthly_test():
    # current_date = nowdate()
    current_date="2025-09-30"
    start_date = get_first_day(current_date)
    end_date = get_last_day(current_date)
    # if nowdate() != get_last_day(nowdate()):
    #     return
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
        No Sales Invoices for {formatdate(current_date)}
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
        No Submitted Sales Invoices In Sales Person  {formatdate(current_date)}
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
        No Cancel Sales Invoices for {formatdate(current_date)}
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
            No  Cancel Sales Invoices in Sales Person  {formatdate(current_date)}
        </td>
        </tr>
        """

    html_content += "</table>"
        

    frappe.sendmail(
        # recipients='divya.p@groupteampro.com',
        recipients=["divya.p@groupteampro.com","asif@norden.co.uk","sujith@nordenco.ae","anoop@nordencommunication.com","zackeria@nordenco.ae","deepak@nordenco.ae"],
        subject=f"Monthly Sales Invoice Summary - {formatdate(current_date)}",
        message=html_content
    )

    print("Email sent successfully!")


@frappe.whitelist()
def update_supplier():
    frappe.db.set_value("Purchase Order", "PO-NCMEF-2025-00312", "supplier", "Fujian LiFO Communication Co.,Ltd")

import frappe

@frappe.whitelist()
def submit_stock_entry():
    frappe.db.set_value("Request for Sample Item","SMP-NCPLP-2025-00152","stock_issued","SE-NCPLP-2025-00314")
    

import frappe

@frappe.whitelist()
def submit_delivery_note():
    try:
        dn_name = "DN-NCMEFT-2025-01551-2"  # Replace with your DN name dynamically if needed
        dn = frappe.get_doc("Delivery Note", dn_name)

        # Check if already submitted
        if dn.docstatus == 1:
            return f"Delivery Note {dn.name} is already submitted."

        # Optional: ensure mandatory validations
        dn.flags.ignore_permissions = True  # bypass user permission if needed
        dn.submit()
        frappe.db.commit()

        return f"Delivery Note {dn.name} submitted successfully."

    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(), title="Delivery Note Submit Error")
        return f"Error while submitting Delivery Note: {str(e)}"


def get_detail_so_test():
    item_code='113-11001104GY'
    company='Norden Communication Middle East FZE'
    date = frappe.db.get_value("Custom Settings", "Custom Settings", "date")
    so_details = []
    
    sa = frappe.db.sql("""
        SELECT `tabSales Order Item`.parent AS parent,
            SUM(`tabSales Order Item`.qty) AS qty,
            `tabSales Order Item`.delivered_qty AS delivered_qty
        FROM `tabSales Order`
        LEFT JOIN `tabSales Order Item` ON `tabSales Order`.name = `tabSales Order Item`.parent
        WHERE `tabSales Order Item`.item_code = '%s'
        AND `tabSales Order`.docstatus != 2
        AND `tabSales Order`.company = '%s'
        AND `tabSales Order`.per_delivered != 100
        AND `tabSales Order`.status != 'Closed'            
        AND `tabSales Order`.transaction_date >= '%s'
        GROUP BY `tabSales Order Item`.parent
        ORDER BY `tabSales Order`.transaction_date
    """ % (item_code, company, date), as_dict=True)
    sa_names = {i.parent for i in sa}
    print(sa_names)
    for i in sa:
        
        total_reserved_qty =0
        stock_entry = frappe.get_all("Stock Reservation Entry", {"company": company,"item_code":item_code,"voucher_no":i.parent,"status": ["in", ["Reserved", "Partially Reserved"]]}, ['reserved_qty'])      
        prq = frappe.db.sql("""select (reserved_qty - delivered_qty) as partially_delivered from `tabStock Reservation Entry`
                                where item_code = '%s' and company = '%s' and status = 'Partially Delivered' and voucher_no = '%s' """ % (item_code,company,i.parent), as_dict=True)
        
        for reser in stock_entry:
            frappe.errprint(reser.reserved_qty)
            total_reserved_qty += reser.reserved_qty
        for prq_ in prq:
            total_reserved_qty += flt(prq_['partially_delivered']) or 0

        i.qty = i.qty or 0
        i.delivered_qty = i.delivered_qty or 0
        pending_qty = i.qty - i.delivered_qty
        sb = frappe.get_doc("Sales Order", i.parent)

        so_details.append(frappe._dict({
            "parent": i.parent,
            "qty": i.qty,
            "reserved_qty": total_reserved_qty,
            "pending_qty": pending_qty,
            "rate": i.rate,
            "delivered_qty": i.delivered_qty,
            "transaction_date": sb.transaction_date,
            "customer": sb.customer,
            "po_no": sb.po_no,
            "status": sb.custom_reservation_status
        }))
    # print(so_details)
    additional_entries = frappe.db.sql("""
        SELECT 
            `tabStock Reservation Entry`.voucher_no AS voucher_no,
            `tabStock Reservation Entry`.reserved_qty,
            `tabSales Order`.transaction_date,
            `tabSales Order`.customer,
            `tabSales Order`.po_no,
            `tabSales Order`.custom_reservation_status   
        FROM `tabStock Reservation Entry`
        LEFT JOIN `tabSales Order` ON `tabSales Order`.name = `tabStock Reservation Entry`.voucher_no
        LEFT JOIN `tabSales Order Item` ON `tabSales Order Item`.parent = `tabSales Order`.name
        WHERE `tabStock Reservation Entry`.item_code = %s
        AND  `tabStock Reservation Entry`.status IN ('Reserved', 'Partially Reserved')
        AND (`tabSales Order Item`.item_code != %s OR `tabSales Order Item`.item_code IS NULL)
        AND (`tabSales Order`.name IS NULL 
            OR (`tabSales Order`.docstatus != 2 
                AND `tabSales Order`.company = %s 
                AND `tabSales Order`.transaction_date >= %s))
        GROUP BY `tabStock Reservation Entry`.voucher_no
        ORDER BY `tabStock Reservation Entry`.creation
    """, (item_code, item_code, company, date), as_dict=True)

    print(additional_entries)
    for entry in additional_entries:
        print(entry.voucher_no)
        if entry.voucher_no not in sa_names:
            
            so_details.append(frappe._dict({
                "parent": entry.voucher_no,
                "qty": 0,  
                "reserved_qty": entry.reserved_qty or 0,
                "pending_qty": 0,  
                "rate": 0,  
                "delivered_qty": 0,
                "transaction_date": entry.transaction_date, 
                "customer": entry.customer, 
                "po_no": entry.po_no, 
                "status": entry.custom_reservation_status
            }))
    
    # return so_details




import frappe
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
import re

@frappe.whitelist()
def download_stock_report(docname):
    doc = frappe.get_doc("Sales Order", docname)

    wb = Workbook()
    ws = wb.active
    ws.title = "Stock Report"

    header_fill = PatternFill(start_color="E20026", end_color="E20026", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    border = Border(left=Side(style='thin'), right=Side(style='thin'),
                    top=Side(style='thin'), bottom=Side(style='thin'))

    ws.merge_cells('A1:D1')
    ws['A1'] = "PICKING LIST"
    ws['A1'].font = Font(bold=True, size=14)
    ws['A1'].alignment = center_align

    headers1 = ["PRODUCT", "DESCRIPTION", "QTY", "WAREHOUSE"]
    ws.append(headers1)
    for col in range(1, 5):
        cell = ws.cell(row=2, column=col)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align
        cell.border = border

    item_details = frappe.db.sql("""
        SELECT item_code, description, SUM(qty) AS qty, SUM(delivered_qty) AS delivered_qty
        FROM `tabSales Order Item`
        WHERE parent = %s
        GROUP BY item_code
        ORDER BY idx
    """, (doc.name,), as_dict=1)

    row = 3
    for j in item_details:
        clean_desc = re.sub(r'<[^>]+>', '', j.description or '').strip()
        qty = max(j.qty - j.delivered_qty, 0)
        available_qty = 0
        warehouses = []

        ware_list = frappe.db.get_list("Warehouse", {"company": doc.company}, ['name'])
        for w in ware_list:
            bins = frappe.get_all("Bin", {"item_code": j.item_code, "warehouse": w.name}, ['actual_qty', 'reserved_stock'])
            sto = sum([b.get("actual_qty", 0) for b in bins])
            if sto > 0:
                warehouses.append(w.name)
                reserve = frappe.db.sql("""
                    SELECT (SUM(reserved_qty) - SUM(delivered_qty)) AS reserved_qty
                    FROM `tabStock Reservation Entry`
                    WHERE voucher_no = %s AND item_code = %s AND docstatus != 2
                """, (doc.name, j.item_code), as_dict=1)
                reser_qty = reserve[0]['reserved_qty'] if reserve else 0
                stock = sto - sum([b.get("reserved_stock", 0) for b in bins])
                if reser_qty and reser_qty > 0:
                    available_qty = reser_qty
                elif stock and qty >= stock:
                    available_qty = stock
                elif stock and qty < stock:
                    available_qty = qty

        if available_qty > 0:
            ws.append([j.item_code, clean_desc, float(available_qty), ', '.join(warehouses)])
            for col in range(1, 5):
                cell = ws.cell(row=row, column=col)
                cell.border = border
                if col == 3:
                    cell.alignment = Alignment(horizontal="right")
                    cell.number_format = '0.0'
                elif col == 4:
                    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                else:
                    cell.alignment = Alignment(horizontal="center", vertical="center")
            row += 1

    ws.column_dimensions['A'].width = 25
    ws.column_dimensions['B'].width = 60
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 70  

    row += 3

    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
    ws.cell(row=row, column=1).value = "NON AVAILABLE QTY"
    ws.cell(row=row, column=1).font = Font(bold=True, size=14)
    ws.cell(row=row, column=1).alignment = center_align
    row += 1

    headers2 = ["PRODUCT", "DESCRIPTION", "QTY"]
    for idx, h in enumerate(headers2, start=1):
        cell = ws.cell(row=row, column=idx)
        cell.value = h
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align
        cell.border = border
    row += 1

    for j in item_details:
        clean_desc = re.sub(r'<[^>]+>', '', j.description or '').strip()
        del_note = frappe.db.get_all("Delivery Note", {"file_number": doc.file_number, "docstatus": ("!=", 2)}, ['name'])
        del_qty = 0
        if del_note:
            for i in del_note:
                deli_note = frappe.get_doc("Delivery Note", i.name)
                for item in deli_note.items:
                    if j.item_code == item.item_code:
                        del_qty += item.qty

        available_qty = 0
        ware_list = frappe.db.get_list("Warehouse", {"company": doc.company}, ['name'])
        for w in ware_list:
            bins = frappe.get_all("Bin", {"item_code": j.item_code, "warehouse": w.name}, ['actual_qty', 'reserved_stock'])
            sto = sum([b.get("actual_qty", 0) for b in bins])
            if sto > 0:
                reserve = frappe.db.sql("""
                    SELECT (SUM(reserved_qty) - SUM(delivered_qty)) AS reserved_qty
                    FROM `tabStock Reservation Entry`
                    WHERE voucher_no = %s AND item_code = %s AND docstatus != 2
                """, (doc.name, j.item_code), as_dict=1)
                reser_qty = reserve[0]['reserved_qty'] if reserve else 0
                stock = sto - sum([b.get("reserved_stock", 0) for b in bins])
                if reser_qty and reser_qty > 0:
                    available_qty = reser_qty
                elif stock and j.qty >= stock:
                    available_qty = stock
                elif stock and j.qty < stock:
                    available_qty = j.qty

        nonavailable_qty = (j.qty - del_qty) - available_qty if del_note else j.qty - available_qty
        if nonavailable_qty > 0:
            ws.append([j.item_code, clean_desc, float(nonavailable_qty)])
            for col in range(1, 4):
                cell = ws.cell(row=row, column=col)
                cell.border = border
                if col == 3:
                    cell.alignment = Alignment(horizontal="right")
                    cell.number_format = '0.0'
                else:
                    cell.alignment = Alignment(horizontal="center", vertical="center")
            row += 1

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    frappe.local.response.filename = f"Stock_Report_{doc.name}.xlsx"
    frappe.local.response.filecontent = output.getvalue()
    frappe.local.response.type = "binary"
    
    
    
@frappe.whitelist()
def get_valuation_rate_from_sle_print():
    valuation_rate = frappe.db.sql("""
        SELECT 
            item_code,
            valuation_rate
        FROM 
            `tabStock Ledger Entry`
        WHERE 
            warehouse LIKE '%- NCME'
            AND is_cancelled = 0
            AND voucher_type = 'Purchase Receipt'
            AND creation = (
                SELECT MAX(creation)
                FROM `tabStock Ledger Entry` AS sub
                WHERE 
                    sub.item_code = "NPS-C1020240"
                    AND sub.warehouse LIKE '%- NCME'
                    AND sub.is_cancelled = 0
                    AND sub.voucher_type = 'Purchase Receipt'
            )
    """, as_dict=1)

    margin_price = frappe.get_doc("Margin Price Tool")

    count = 0

    for i in valuation_rate:
        item_group = frappe.db.get_value(
            "Item", "NPS-C1020240", "item_sub_group"
        )

        landing_cost = 0
        incentive_cost = 0

        for t in margin_price.dubai:
            if t.item_group == item_group:
                landing_cost = i.valuation_rate * t.landing
                incentive_cost = landing_cost * t.incentive
                break

        print(
            f"Item: {i.item_code} | "
            f"Valuation: {i.valuation_rate} | "
            f"Landing: {landing_cost} | "
            f"Incentive: {incentive_cost}"
        )

        count += 1

    print(f"Total items processed: {count}")
    
    
import frappe
from frappe import _
from frappe.utils import flt

@frappe.whitelist()
def check_rack_qty(doc, method):
    if doc.company == "Norden Communication Middle East FZE":
        for item in doc.items:
            if item.rack:
                # total_qty = frappe.db.sql("""
                #     SELECT SUM(actual_qty)
                #     FROM `tabStock Ledger Entry`
                #     WHERE item_code = %s
                #     AND warehouse = %s
                #     AND is_cancelled = 0
                #     AND rack = %s
                # """, (item.item_code, item.warehouse, item.rack))[0][0] or 0
                total_qty=frappe.db.get_value("Stock Ledger Entry", {"item_code": item.item_code, "warehouse": item.warehouse, "rack": item.rack, "is_cancelled": 0}, "qty_after_transaction") or 0
                available_qty = flt(total_qty)
                required_qty = flt(item.qty)

                if doc.is_return == 0:
                    if available_qty < required_qty:
                        shortage = required_qty - available_qty

                        frappe.throw(
                            _(
                                "Row {0}: Quantity not available for Rack {1} , Kindly duplicate the row with same item and warehouse but different rack"
                            ).format(
                                item.idx,
                                frappe.bold(item.rack)
                            )
                            + "<br><br>"
                            + _(
                                "Available Quantity: {0}<br>Required Quantity: {1}<br>Shortage: {2}"
                            ).format(
                                frappe.bold(available_qty),
                                frappe.bold(required_qty),
                                frappe.bold(shortage)
                            ),
                            title=_("Insufficient Stock")
                        )

				
# @frappe.whitelist()
# def get_rack_details(doctype, txt, searchfield, start, page_len, filters):
#     item_code = filters.get("item_code")
#     warehouse = filters.get("warehouse")

#     return frappe.db.sql("""
#         SELECT 
#             sle.rack AS name,
#             CONCAT("Available Qty: ", SUM(sle.actual_qty)) AS description
#         FROM `tabStock Ledger Entry` sle
#         WHERE sle.item_code = %s
#         AND sle.warehouse = %s
#         AND sle.is_cancelled = 0
#         AND sle.rack IS NOT NULL
#         GROUP BY sle.rack
#         HAVING SUM(sle.actual_qty) > 0
#         ORDER BY sle.rack
#         LIMIT %s OFFSET %s
#     """, (item_code, warehouse, page_len, start))

@frappe.whitelist()
def check_rack_qty_stock_entry(doc, method):
    if doc.company == "Norden Communication Middle East FZE":
        for item in doc.items:
            if item.rack:
                total_qty = frappe.db.sql("""
                    SELECT SUM(actual_qty)
                    FROM `tabStock Ledger Entry`
                    WHERE item_code = %s
                    AND warehouse = %s
                    AND is_cancelled = 0
                    AND rack = %s
                """, (item.item_code, item.s_warehouse, item.rack))[0][0] or 0
                if float(total_qty) < float(item.qty):
                    shortage = item.qty - total_qty
                    frappe.throw(
                        _(
                            "Row {0}: Quantity not available for Rack {1} , Kindly duplicate the row with same item and warehouse but different rack"
                        ).format(
                            item.idx,
                            frappe.bold(item.rack)
                        )
                        + "<br><br>"
                        + _(
                            "Available Quantity: {0}<br>Required Quantity: {1}<br>Shortage: {2}"
                        ).format(
                            frappe.bold(total_qty),
                            frappe.bold(item.qty),
                            frappe.bold(shortage)
                        ),
                        title=_("Insufficient Stock")
                    )




@frappe.whitelist()
def update_sales_person():
    sales_order = "F-Q-NCMET-2025-03782-4"
    frappe.db.set_value("Quotation",{'name':sales_order},'sales_person_user', 'Suresh Chandran Puthumana')
    frappe.db.set_value("Quotation",{'name':sales_order},'sale_person','suresh@nordenco.ae')
    frappe.db.set_value("Quotation",{'name':sales_order},'sales_person_name','Suresh Chandran Puthumana')

import frappe
import csv
import io
from frappe.utils.file_manager import save_file
@frappe.whitelist()
def export_dn_has_rack_sle_missing_rack():
    data = []
    dn_list = frappe.db.sql("""
        SELECT DISTINCT parent
        FROM `tabDelivery Note Item`
        WHERE IFNULL(rack, '') != ''
        AND parent IN (
            SELECT name FROM `tabDelivery Note`
            WHERE docstatus = 1
        )
    """, as_dict=True)

    for dn in dn_list:

        dn_name = dn.parent
        dn_items = frappe.db.sql("""
            SELECT item_code, rack
            FROM `tabDelivery Note Item`
            WHERE parent = %s
            AND IFNULL(rack, '') != ''
        """, dn_name, as_dict=True)

        dn_map = {(d.item_code): d.rack for d in dn_items}
        sle_list = frappe.db.sql("""
            SELECT name, item_code, warehouse, actual_qty, IFNULL(rack, '') as rack
            FROM `tabStock Ledger Entry`
            WHERE voucher_no = %s
        """, dn_name, as_dict=True)
        for sle in sle_list:
            dn_rack = dn_map.get(sle.item_code)
            if dn_rack and (not sle.rack):
                data.append([
                    dn_name,
                    sle.name,
                    sle.item_code,
                    sle.warehouse,
                    sle.actual_qty,
                    dn_rack,
                    sle.rack
                ])
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Delivery Note",
        "Stock Ledger Entry",
        "Item Code",
        "Warehouse",
        "Qty",
        "DN Rack",
        "SLE Rack"
    ])

    writer.writerows(data)
    csv_content = output.getvalue()
    file_doc = save_file(
        fname="dn_has_rack_sle_missing_rack.csv",
        content=csv_content,
        dt=None,
        dn=None,
        is_private=0
    )

    return {
        "message": "CSV generated successfully",
        "file_url": file_doc.file_url
    }


@frappe.whitelist()
def get_stock_details_manufacture(doc):
    item_details = frappe.db.sql(""" select item_code,description, sum(qty)as qty from `tabStock Entry Detail` where parent = '%s' group by item_code order by idx """%(doc.name),as_dict = 1)
    data = ''
    data += '<h4><center><b>STOCK DETAILS</b></center></h4>'
    data += '<table class="table table-bordered">'
    data += '<tr>'
    data += '<td colspan=3 style="width:13%;padding:1px;border:1px solid black;font-size:14px;background-color:#e20026;color:white;text-align:center">PRODUCT</td>'
    data += '<td colspan=3 style="width:70px;padding:1px;border:1px solid black;font-size:14px;background-color:#e20026;color:white;text-align:center">DESCRIPTION</td>'
    data += '<td colspan=3 style="width:70px;padding:1px;border:1px solid black;font-size:14px;background-color:#e20026;color:white;text-align:center">QTY</td>'
    data += '<td colspan=3 style="width:70px;padding:1px;border:1px solid black;font-size:14px;background-color:#e20026;color:white;text-align:center">WAREHOUSE</td>'
    data += '<td colspan=3 style="width:70px;padding:1px;border:1px solid black;font-size:14px;background-color:#e20026;color:white;text-align:center">RACK</td></tr>'
    for j in item_details:
        qty = 0
        av_qty = j.qty
        if av_qty > 0:
            qty = av_qty
        available_qty = 0
        warehouse=[]
        rack_name = []
        ware = frappe.db.get_list("Warehouse",{"company":doc.company,"custom_is_pick_list":0},['name'])
        for w in ware:
            bin = frappe.get_all("Bin",{"item_code":j.item_code,"warehouse":w.name},['actual_qty','reserved_stock'])
            sto = sum([value.get("actual_qty", 0) for value in bin])
            if sto and sto>0:
                warehouse.append(w.name)
                # reserve = frappe.db.sql("""
                #     SELECT (sum(reserved_qty) - sum(delivered_qty)) as reserved_qty 
                #     FROM `tabStock Reservation Entry` 
                #     WHERE voucher_no = %s 
                #     AND item_code = %s 
                #     AND docstatus != 2
                # """, (doc.name, j.item_code), as_dict=1)
        
                stock = sum([value.get("actual_qty", 0) for value in bin]) - sum([value.get("reserved_stock", 0) for value in bin])
                # if reserve:
                #     reser_qty = reserve[0]['reserved_qty']
                # else:
                #     reser_qty = 0
                # if reser_qty and reser_qty > 0:
                #     available_qty = reser_qty
                # else:
                if stock and qty >= stock:
                    available_qty = stock
                elif stock and qty < stock:
                    available_qty = qty
            
            racks = frappe.db.sql("""
                SELECT 
                    rack,
                    SUM(actual_qty) AS balance_qty
                FROM `tabStock Ledger Entry`
                WHERE item_code = %s
                AND warehouse = %s
                AND is_cancelled = 0
                AND rack IS NOT NULL
                GROUP BY rack
                HAVING SUM(actual_qty) > 0
            """, (j.item_code, w.name), as_dict=1)
            for r in racks:
                if r.balance_qty > 0:
                    # rack_name.append(r.rack)
                    rack_name.append(f"{r.rack} - {r.balance_qty}")
        if available_qty > 0:
            data += '<tr><td style="text-align:center;border: 1px solid black" colspan=3>%s</td>' %(j.item_code)
            data += '<td style="text-align:center;border: 1px solid black" colspan=3>%s</td>' %(j.description)
            data += '<td style="text-align:center;border: 1px solid black;text-align:right" colspan=3>%s</td>' %(available_qty)
            if warehouse:
                data += '<td style="text-align:center;border: 1px solid black" colspan=3>%s</td>' %(', '.join(map(str, warehouse)))
            else:
                data += '<td style="text-align:center;border: 1px solid black" colspan=3></td>'
            if rack_name:
                data += '<td style="text-align:center;border: 1px solid black" colspan=3>%s</td>' %(', '.join(map(str, rack_name)))
            else:
                data += '<td style="text-align:center;border: 1px solid black" colspan=3></td>'
    data += '</tr>'
    data += '</table>'
    return data

@frappe.whitelist()
def get_stock_details_popup(item_code,company,description):
    data = ''
    data += '<h4><center><b>STOCK DETAILS</b></center></h4>'
    data += '<table class="table table-bordered">'
    data += '<tr>'
    data += '<td colspan=3 style="width:13%;padding:1px;border:1px solid black;font-size:14px;background-color:#e20026;color:white;text-align:center">PRODUCT</td>'
    data += '<td colspan=3 style="width:70px;padding:1px;border:1px solid black;font-size:14px;background-color:#e20026;color:white;text-align:center">DESCRIPTION</td>'
    data += '<td colspan=3 style="width:70px;padding:1px;border:1px solid black;font-size:14px;background-color:#e20026;color:white;text-align:center">QTY</td>'
    data += '<td colspan=3 style="width:70px;padding:1px;border:1px solid black;font-size:14px;background-color:#e20026;color:white;text-align:center">WAREHOUSE</td>'
    data += '<td colspan=3 style="width:70px;padding:1px;border:1px solid black;font-size:14px;background-color:#e20026;color:white;text-align:center">RACK</td></tr>'
    
    # qty = 0
    # av_qty = j.qty
    # if av_qty > 0:
    #     qty = av_qty
    available_qty = 0
    warehouse=[]
    rack_name = []
    ware = frappe.db.get_list("Warehouse",{"company":company,"custom_is_pick_list":0},['name'])
    for w in ware:
        bin = frappe.get_all("Bin",{"item_code":item_code,"warehouse":w.name},['actual_qty','reserved_stock'])
        sto = sum([value.get("actual_qty", 0) for value in bin])
        if sto and sto>0:
            warehouse.append(w.name)
            stock = sum([value.get("actual_qty", 0) for value in bin]) - sum([value.get("reserved_stock", 0) for value in bin])
            available_qty = stock
                
            
        racks = frappe.db.sql("""
            SELECT 
                rack,
                SUM(actual_qty) AS balance_qty
            FROM `tabStock Ledger Entry`
            WHERE item_code = %s
            AND warehouse = %s
            AND is_cancelled = 0
            AND rack IS NOT NULL
            GROUP BY rack
            HAVING SUM(actual_qty) > 0
        """, (item_code, w.name), as_dict=1)
        for r in racks:
            if r.balance_qty > 0:
                # rack_name.append(r.rack)
                rack_name.append(f"{r.rack} - {r.balance_qty}")
    if available_qty > 0:
        data += '<tr><td style="text-align:center;border: 1px solid black" colspan=3>%s</td>' %(item_code)
        data += '<td style="text-align:center;border: 1px solid black" colspan=3>%s</td>' %(description)
        data += '<td style="text-align:center;border: 1px solid black;text-align:right" colspan=3>%s</td>' %(available_qty)
        if warehouse:
            data += '<td style="text-align:center;border: 1px solid black" colspan=3>%s</td>' %(', '.join(map(str, warehouse)))
        else:
            data += '<td style="text-align:center;border: 1px solid black" colspan=3></td>'
        if rack_name:
            data += '<td style="text-align:center;border: 1px solid black" colspan=3>%s</td>' %(', '.join(map(str, rack_name)))
        else:
            data += '<td style="text-align:center;border: 1px solid black" colspan=3></td>'
    data += '</tr>'
    data += '</table>'
    return data

@frappe.whitelist()
def getcreated_person():
    created_by = frappe.db.get_value("Quotation", "F-Q-NCMET-2026-00023", "price_list")
    print(created_by)

@frappe.whitelist()
def empty_item_desc():
    doc = frappe.get_doc("Item", "3134-31288OS2CL-CT")
    doc.description = ""
    doc.save(ignore_permissions=True)

    # frappe.db.commit()
    print("Description cleared successfully.")

@frappe.whitelist()
def empty_item_desc_quot():
    row = frappe.get_value(
        "Quotation Item",
        {
            "parent": "F-Q-NCME-2026-01553-1",
            "item_code": "3134-31288OS2CL-CT"
        },
        "name"
    )

    frappe.db.set_value(
        "Quotation Item",
        row,
        "description",
        "144 Core SM OS2 Duct Blown Unarmoured Fibre Optic Cable"
    )

    frappe.db.commit()

    print("Description updated successfully.")



@frappe.whitelist()
def get_electra_details_without_cost_test(): 
    data = ''
    data1 = ''
    data2=''
    i = 0
    
    
    item = frappe.get_value('Item', {'item_code': "122-31T180WH"}, 'item_code')
    if item:
        item = frappe.get_value('Item', {'item_code': "122-31T180WH"}, 'item_code')
        group = frappe.get_value('Item', {'item_code': "122-31T180WH"}, 'item_group')
        des = frappe.get_value('Item', {'item_code': "122-31T180WH"}, 'description')
        
        cou = 0
        p_po = 0
        p_so = 0
        tot = 'Total'
        uom = 'Nos'

        stocks_query = frappe.db.sql("""
            SELECT 
                (SUM(`tabBin`.actual_qty) - SUM(reserved_stock)) AS actual_qty,
                warehouse,
                stock_uom,
                stock_value
            FROM tabBin
            WHERE item_code = %s 
            GROUP BY warehouse
        """, (item,), as_dict=True)

        if stocks_query:
            data += '''
                <table class="table table-bordered" style="width:75%">
                    <tr>
                        <th style="padding:1px;border: 1px solid black;background-color:#fe3f0c;color:white" colspan=10><center>NORDEN PRODUCT SEARCH</center></th>
                    </tr>
                    <tr>
                        <td colspan=2 style="padding:1px;border: 1px solid black;color:white;background-color:#6f6f6f;text-align: left"><b>Item Code</b></td>
                        <td colspan=8 style="padding:1px;border: 1px solid black;text-align: left"><b>{}</b></td>
                    </tr>
                    <tr>
                        <td colspan=2 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;text-align: left"><b>Item Name</b></td>
                        <td colspan=8 style="padding:1px;border: 1px solid black;text-align: left"><b>{}</b></td>
                    </tr>
                    <tr>
                        <td colspan=2 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;text-align: left"><b>Item Group</b></td>
                        <td colspan=8 style="padding:1px;border: 1px solid black;text-align: left"><b>{}</b></td>
                    </tr>
                    <tr>
                        <td colspan=2 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;text-align: left"><b>Description</b></td>
                        <td colspan=8 style="padding:1px;border: 1px solid black;text-align: left"><b>{}</b></td>
                    </tr>
                    <tr>
                        <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Company</b></center></td>
                        <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Warehouse</b></center></td>
                        <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>QTY</b></center></td>
                        <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>UOM</b></center></td>
                        <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Selling Rate</b></center></td>
                        <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Currency</b></center></td>
                        <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Pending PO</b></center></td>
                        <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Pending SO</b></center></td>
                    </tr>
                '''.format(item, frappe.db.get_value('Item', item, 'item_name'), group, des)

            for stock in stocks_query:
                if stock.actual_qty >= 0:
                    stock_company = frappe.db.sql("""
                        SELECT company 
                        FROM tabWarehouse 
                        WHERE name = %s
                    """, (stock.warehouse,), as_dict=True)

                    for com in stock_company:
                        psoc_query = frappe.db.sql("""
                            SELECT SUM(`tabSales Order Item`.qty) AS qty 
                            FROM `tabSales Order`
                            LEFT JOIN `tabSales Order Item` ON `tabSales Order`.name = `tabSales Order Item`.parent
                            WHERE `tabSales Order Item`.item_code = %s 
                            AND `tabSales Order`.docstatus = 1 
                            AND `tabSales Order`.company = %s
                        """, ("122-31T180WH", com.company), as_dict=True)[0]
                        
                        if not psoc_query["qty"]:
                            psoc_query["qty"] = 0
                            
                        deliver = frappe.db.sql("""
                            SELECT SUM(`tabDelivery Note Item`.qty) AS qty 
                            FROM `tabDelivery Note`
                            LEFT JOIN `tabDelivery Note Item` ON `tabDelivery Note`.name = `tabDelivery Note Item`.parent
                            WHERE `tabDelivery Note Item`.item_code = %s 
                            AND `tabDelivery Note`.docstatus = 1 
                            AND `tabDelivery Note`.company = %s
                        """, ("122-31T180WH", com.company), as_dict=True)[0]
                        
                        if not deliver["qty"]:
                            deliver['qty'] = 0
                            
                        del_total = psoc_query['qty'] - deliver['qty']
                        
                        ppoc_query = frappe.db.sql("""
                            SELECT SUM(`tabPurchase Order Item`.qty) AS qty 
                            FROM `tabPurchase Order`
                            LEFT JOIN `tabPurchase Order Item` ON `tabPurchase Order`.name = `tabPurchase Order Item`.parent
                            WHERE `tabPurchase Order Item`.item_code = %s 
                            AND `tabPurchase Order`.docstatus != 2 
                            AND `tabPurchase Order`.company = %s
                        """, ("122-31T180WH", com.company), as_dict=True)[0]
                        
                        if not ppoc_query["qty"]:
                            ppoc_query["qty"] = 0
                            
                        ppoc_receipt = frappe.db.sql("""
                            SELECT SUM(`tabPurchase Receipt Item`.qty) AS qty 
                            FROM `tabPurchase Receipt`
                            LEFT JOIN `tabPurchase Receipt Item` ON `tabPurchase Receipt`.name = `tabPurchase Receipt Item`.parent
                            WHERE `tabPurchase Receipt Item`.item_code = %s 
                            AND `tabPurchase Receipt`.status = "Completed" 
                            AND `tabPurchase Receipt`.company = %s
                        """, ("122-31T180WH", com.company), as_dict=True)[0]
                        
                        if not ppoc_receipt["qty"]:
                            ppoc_receipt["qty"] = 0
                            
                        ppoc_total = ppoc_query["qty"] - ppoc_receipt["qty"]
                        
                        country, default_currency = frappe.get_value("Company", {"name": com.company}, ["country", "default_currency"])
                        
                        if country == "United Arab Emirates":
                            cost = frappe.get_value("Item Price", {"item_code": item, "price_list": "Electra Qatar - NCMEF"}, ["price_list_rate"])
                        else:
                            cost = frappe.get_value("Item Price", {"item_code": item, "price_list": "STANDARD BUYING-USD"}, ["price_list_rate"])
                            
                        pricelist = country + ' ' + "Sales Price"
                        
                        if country == "United Arab Emirates":
                            sp = frappe.get_value("Item Price", {"item_code": item, "price_list": "Internal - NCMEF"}, ["price_list_rate"])
                        else:
                            sp = frappe.get_value("Item Price", {"item_code": item, "price_list": pricelist}, ["price_list_rate"])
                        sp = sp if sp else 0.0		
                        data += '''
                            <tr>
                                <td colspan=1 style="padding:1px;border: 1px solid black">{}</td>
                                <td colspan=1 style="padding:1px;border: 1px solid black">{}</td>
                                <td colspan=1 style="padding:1px;border: 1px solid black"><center><b>{}</b></center></td>
                                <td colspan=1 style="padding:1px;border: 1px solid black"><center><b>{}</b></center></td>
                                <td colspan=1 style="padding:1px;border: 1px solid black"><center><b>{}</b></center></td>
                                <td colspan=1 style="padding:1px;border: 1px solid black"><center><b>{}</b></center></td>
                                <td colspan=1 style="padding:1px;border: 1px solid black"><center><b>{}</b></center></td>
                                <td colspan=1 style="padding:1px;border: 1px solid black"><center><b>{}</b></center></td>
                            </tr>
                        '''.format(
                            com.company,
                            stock.warehouse,
                            int(stock.actual_qty) or 0,
                            stock.stock_uom or '-',
                            "{:.2f}".format(sp),
                            default_currency,
                            ppoc_total or 0,
                            int(del_total) or 0
                        )
                        
                        i += 1
                        cou += stock.actual_qty
                        p_po += ppoc_total
                        p_so += del_total

            data += '''
                <tr>
                    <td align="right" colspan=2 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><b>{}</b></td>
                    <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>{}</b></center></td>
                    <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>{}</b></center></td>
                    <td colspan=2 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b></b></center></td>
                    <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>{}</b></center></td>
                    <td colspan=1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>{}</b></center></td>
                </tr>
            '''.format(tot or 0, int(cou) or 0, uom, int(p_po) or 0, int(p_so) or 0)
            
            data += '</table>'
        else:
            i += 1
            data2 += '''
                <table width="75%">
                    <tr>
                        <td align="center" colspan=10 style="padding:1px;border: 1px solid black;background-color:#fe3f0c;color:white;"><b>NORDEN PRODUCT SEARCH</b></td>
                    </tr>
                    <tr>
                        <td align="center" colspan=10 style="padding:1px;border: 1px solid black";><b>No Stock Available</b></td>
                    </tr>
                </table>
            '''
            data += data2

    else:
        i += 1
        data1 += '''
            <table width="75%">
                <tr>
                    <td align="center" colspan=10 style="padding:1px;border: 1px solid black;background-color:#fe3f0c;color:white;"><b>NORDEN PRODUCT SEARCH</b></td>
                </tr>
                <tr>
                    <td align="center" colspan=10 style="padding:1px;border: 1px solid black";><b>No Stock Available</b></td>
                </tr>
            </table>
        '''
        data += data1

    if i > 0:
        return data


