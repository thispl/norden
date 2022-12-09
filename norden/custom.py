from datetime import datetime
from lib2to3.pytree import convert
import frappe
import erpnext
from frappe.utils import date_diff, add_months, today, add_days, nowdate,formatdate
from frappe.utils.csvutils import read_csv_content
from frappe.utils.file_manager import get_file
import json
from forex_python.converter import CurrencyRates
from frappe.model.document import Document
import pandas as pd
from frappe.model.rename_doc import rename_doc
from frappe.model.naming import make_autoname
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions
# from erpnext.accounts.doctype.gl_entry.gl_entry import rename_gle_sle_docs


@frappe.whitelist()
def create_material_request(item_table, company):
    item_table = json.loads(item_table)
    for item in item_table:
        stocks = frappe.db.sql("""select actual_qty,warehouse,stock_uom,stock_value from tabBin
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
        stocks = frappe.db.sql("""select actual_qty,warehouse,stock_uom,stock_value from tabBin
            where item_code = '%s' """ % (item["item_code"]), as_dict=True)
        item_name = frappe.db.get_value('Item',{'item_code':item['item_code']},['item_name'])
        for stock in stocks:
            if stock.actual_qty > 0:
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
    stocks = frappe.db.sql("""select actual_qty,warehouse,stock_uom,stock_value from tabBin
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
    frappe.errprint(item)
    data = ''
    data_1 = ''
    pos = frappe.db.sql("""select `tabPurchase Order Item`.item_code as item_code,`tabPurchase Order Item`.item_name as item_name,`tabPurchase Order`.supplier as supplier,`tabPurchase Order Item`.qty as qty,`tabPurchase Order Item`.amount as amount,`tabPurchase Order`.transaction_date as date,`tabPurchase Order`.name as po,`tabPurchase Order`.company as company from `tabPurchase Order`
    left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
    where `tabPurchase Order`.company = '%s' and `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.name != '%s' and `tabPurchase Order`.docstatus != 2 order by date desc """ % (company,item,name), as_dict=True)
    data += '<table class="table table-bordered"><tr><th style="padding:1px;border: 1px solid black" colspan=6><center>Previous Purchase Order</center></th></tr>'
    data += '<tr><td style="padding:1px;border: 1px solid black"><b>Item Code</b></td><td style="padding:1px;border: 1px solid black"><b>PO Number</b></td><td style="padding:1px;border: 1px solid black"><b>Supplier</b></td><td style="padding:1px;border: 1px solid black"><b>QTY</b></td><td style="padding:1px;border: 1px solid black"><b>PO Date</b></td><td style="padding:1px;border: 1px solid black"><b>Amount</b></td></tr>'
    frappe.errprint(pos)
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
    frappe.log_error(message=doc)
    lcv = frappe.new_doc('Landed Cost Voucher')
    lcv.company = doc.company
    lcv.append('purchase_receipts', {
        'receipt_document_type': 'Purchase Receipt',
        'receipt_document': doc.name,
    })
    lcv.items = doc.items
    lcv.taxes = doc.landed_taxes
    lcv.save(ignore_permissions=True)
    frappe.log_error(message=lcv)
    frappe.db.commit()


@frappe.whitelist()
def get_sales_person(converted_by):
    if converted_by:
        emp = frappe.db.exists('Employee', {'user_id': converted_by})
        if emp:
            sp = frappe.db.exists('Sales Person', {'employee': emp})
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

#         frappe.log_error(title='',message=item_not_exists)
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
        stocks = frappe.db.sql("""select actual_qty from tabBin
            where item_code = '%s' """ % (item["item_code"]), as_dict=True)
        pos = frappe.db.sql("""select `tabPurchase Order Item`.item_code as item_code,`tabPurchase Order Item`.item_name as item_name,`tabPurchase Order`.supplier as supplier,`tabPurchase Order Item`.qty as qty,`tabPurchase Order Item`.rate as rate,`tabPurchase Order Item`.amount as amount,`tabPurchase Order`.transaction_date as date,`tabPurchase Order`.name as po from `tabPurchase Order`
            left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
            where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 """ % (item["item_code"]), as_dict=True)    
        sal = frappe.db.sql("""select `tabSales Order Item`.item_code as item_code,`tabSales Order Item`.item_name as item_name,`tabSales Order`.customer as customer,`tabSales Order Item`.qty as qty,`tabSales Order Item`.amount as amount,`tabSales Order`.transaction_date as date,`tabSales Order`.name as po from `tabSales Order`
            left join `tabSales Order Item` on `tabSales Order`.name = `tabSales Order Item`.parent
            where `tabSales Order Item`.item_code = '%s' and `tabSales Order`.docstatus != 2 """ % (item["item_code"]), as_dict=True)        
        data +='<table class="table table-bordered"><tr><th style="padding:1px;border: 1px solid black" colspan=17><center>Approval</center></th></tr>'
        data +='<tr><td colspan="2" style="padding:1px;border: 1px solid black"><b></b></td><td colspan="3" style="padding:1px;border: 1px solid black"><b>Ordering QTY</b></td><td Colspan="2" style="padding:1px;border: 1px solid black"><b>Sales Order</b></td><td colspan="2" style="padding:1px;border: 1px solid black"><b>Purchase Order</b></td><td colpsan="1" style="padding:1px;border: 1px solid black"><b></b></td><td colspan="3" style="padding:1px;border: 1px solid black"><b>Stock Available Now</b></td><td colspan="3" style="padding:1px;border: 1px solid black"><b></b></td></tr>'
        data +='<tr><td style="padding:1px;border: 1px solid black"><b>item Code</b></td><td style="padding:1px;border: 1px solid black"><b>description</b></td><td style="padding:1px;border: 1px solid black"><b>B2B</b></td><td style="padding:1px;border: 1px solid black"><b>For Stock</b></td><td style="padding:1px;border: 1px solid black"><b>FOC</b></td><td style="padding:1px;border: 1px solid black"><b>Rate</b></td><td style="padding:1px;border: 1px solid black"><b>Amount</b></td><td style="padding:1px;border: 1px solid black"><b>Rate</b></td><td style="padding:1px;border: 1px solid black"><b>Amount</b></td><td style="padding:1px;border: 1px solid black"><b>Margin%</b></td><td style="padding:1px;border: 1px solid black"><b>In Warehouse</b></td><td style="padding:1px;border: 1px solid black"><b>In Transit</b></td><td style="padding:1px;border: 1px solid black"><b>Total</b></td><td style="padding:1px;border: 1px solid black"><b>Last 3month transaction</b></td><td style="padding:1px;border: 1px solid black"><b>Last Unit Purchase</b></td><td style="padding:1px;border: 1px solid black"><b>Remark</b></td></tr>'
        i = 0
        for s in item_details:
            if s["type"] == 'STOCK':
                res1 = s["qty"]
                stocks = frappe.db.sql("""select actual_qty,warehouse from tabBin
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
                stocks = frappe.db.sql("""select actual_qty,warehouse from tabBin
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
    stocks = frappe.db.sql("""select `tabBin`.actual_qty as actual_qty,`tabBin`.warehouse as warehouse,`tabBin`.stock_uom as stock_uom,`tabBin`.stock_value as stock_value from `tabBin`
                            join `tabWarehouse` on `tabWarehouse`.name = `tabBin`.warehouse
                            join `tabCompany` on `tabCompany`.name = `tabWarehouse`.company
                            where `tabBin`.item_code = '%s' and `tabWarehouse`.company = '%s' """ % (item,company), as_dict=True)
    
    data += '<table class="table table-bordered"><tr><th style="padding:1px;border: 1px solid black" colspan=6><center>Stock Availability</center></th></tr>'
    data += '<tr><td style="padding:1px;border: 1px solid black"><b>Item Code</b></td><td style="padding:1px;border: 1px solid black"><b>Item Name</b></td><td style="padding:1px;border: 1px solid black"><b>Warehouse</b></td><td style="padding:1px;border: 1px solid black"><b>QTY</b></td><td style="padding:1px;border: 1px solid black"><b>UOM</b></td></tr>'
    if stocks:
        for stock in stocks:
            if stock["actual_qty"] > 0:
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
    att = frappe.db.sql(""" update  `tabAttendance`  set docstatus = 1 where attendance_date between '2022-04-01' and '2022-04-30'  """)
    print(att)
    
@frappe.whitelist()
def sales_order():
    sales = frappe.get_all("Sales Order",{"name":"SAL-ORD-2022-00010"},['*'])
    print(sales)


@frappe.whitelist()
def leave():
    emp = frappe.db.get('Quotation',{"name":"SAL-QTN-NC-2022-00005-1"},['*'])
    print(emp)

# @frappe.whitelist()
# def ordered_qty(po_no):
#     data = []
#     qty = frappe.db.sql(""" select `tabPurchase Order Item`.qty from `tabPurchase Order` left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent 
#     where `tabPurchase Order`.name = '%s' """ %(po_no),as_dict=True)
#     for i in qty:
#         data.append(i.qty)
#     return data

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
    customer = frappe.get_value("Sales Order",{"file_number":file},["customer","prepared_by"])
    return customer

@frappe.whitelist()
def get_margin_details(item_details,company,exchange_rate,currency,name):
    item_details = json.loads(item_details)
    data_4 = ''
    if "Sales Manager" in frappe.get_roles(frappe.session.user):
        data_4 += '<table class="table"><tr><th style="padding:1px;border: 1px solid black;font-size:14px;background-color:#32CD32;color:white;" colspan=20><center><b>STOCK STATUS  &  INTERNAL COST</b></center></th></tr>'
    
        data_4+='<tr><td colspan=5 style="border: 0.5px solid black;font-size:11px;"><b>ITEM</b></td><td colspan=2 style="border: 0.5px solid black;font-size:11px;width:50%;"><b>ITEM NAME</b><td colspan=3 style="border: 0.5px solid black;font-size:11px;"><b><center>IN WAREHOUSE</center></b></td><td colspan=3 style="border: 0.5px solid black;font-size:11px;"><b><center>IN TRANSIT</center></b></td><td colspan=3 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td></td><td colspan=3 style="border: 0.5px solid black;font-size:11px;"><b><center>QTY</center></b></td><td colspan=3 style="border: 0.5px solid black;font-size:11px;"><b><center>INTERNAL COST</center></b></td></tr>'
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
        from erpnext.setup.utils import get_exchange_rate
        if not currency == "USD":
            if not company == "Norden Communication Middle East FZE":
                ep = get_exchange_rate('USD',currency)
                i["rate"] = round(i["rate"]/ep,1)

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
    frappe.errprint(total_internal_cost)
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
            data_5+='<tr><td colspan=4 style="border:1px solid black;font-size:11px;"><b>ITEM</b></td><td colspan=2 style="border: 1px solid black;font-size:11px;width:40%;"><b>ITEM NAME</b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>IN WAREHOUSE</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>IN TRANSIT</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SELLING PRICE</b></td></tr>'
        else:
            data_5+='<tr><td colspan=4 style="border:1px solid black;font-size:11px;"><b>ITEM</b></td><td colspan=2 style="border: 1px solid black;font-size:11px;width:40%;"><b>ITEM NAME</b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>IN WAREHOUSE</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>IN TRANSIT</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SPECIAL PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SELLING PRICE</b></td></tr>'

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
        # from erpnext.setup.utils import get_exchange_rate
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
            from erpnext.setup.utils import get_exchange_rate
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
        from erpnext.setup.utils import get_exchange_rate
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
    #     from erpnext.setup.utils import get_exchange_rate
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
    # data_2+='<tr><td colspan=1 style="border: 1px solid black;font-size:12px;"><center><b>IN WAREHOUSE</b><center></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><center><b>IN TRANSIT</b><center></td><td colspan=1 style="border: 1px solid black;font-size:12px;"><center><b>TOTAL</b><center></td></tr>'
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
    frappe.errprint(sale_no)
    if sale_no:
        so_no = frappe.get_value("Sales Order",{"name":sale_no},["delivery"])
        frappe.errprint(so_no)
        return so_no
    elif mat_no: 
        so = frappe.get_value("Material Request",{"name":mat_no},["sales_order_number"])
        if so:
            po = frappe.get_value("Sales Order",{"name":so},["delivery"])
            frappe.errprint(po)


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
    
        data_4+='<tr><td colspan=3 style="border: 0.5px solid black;font-size:11px;"><b>ITEM</b></td><td colspan=3 style="border: 0.5px solid black;font-size:11px;width:30%;"><b>ITEM NAME</b><td colspan=3 style="border: 0.5px solid black;font-size:11px;"><b><center>IN WAREHOUSE</center></b></td><td colspan=3 style="border: 0.5px solid black;font-size:11px;"><b><center>IN TRANSIT</center></b></td><td colspan=3 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td></td><td colspan=3 style="border: 0.5px solid black;font-size:11px;"><b><center>QTY</center></b></td><td colspan=3 style="border: 0.5px solid black;font-size:11px;"><b><center>INTERNAL COST</center></b></td></tr>'
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
        from erpnext.setup.utils import get_exchange_rate
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
        frappe.errprint(total_internal_cost)
        frappe.errprint(total_selling_price)
        if "Sales Manager" in frappe.get_roles(frappe.session.user):
            data_4+='<tr style="height:5px;"><td colspan=3 style="border: 1px solid black;font-size:11px;padding:0px; margin:0px;"><center>%s</center></td><td colspan=3 style="border: 1px solid black;font-size:11px;">%s</td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=3 align = "right"style="border: 1px solid black;font-size:11px;">%s</td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],round((i["internal_cost"]*i["qty"]),2))      
    if total_internal_cost == 0:
        total_margin_internal = (total_selling_price - total_internal_cost)/100
        # total_margin_internal = ((total_selling_price - total_internal_cost )/ total_internal_cost)*100
    else:
        total_margin_internal = (total_selling_price - total_internal_cost )/(total_selling_price)*100
    frappe.errprint(total_margin_internal)

    if "Sales Manager" in frappe.get_roles(frappe.session.user):
        data_4 += '<tr style="line-height:0.4;"><th style="padding-top:12px;border: 1px solid black;font-size:12px" colspan=6><center><b>TOTAL MARGIN BASED ON INTERNAL COST: %s </b></center></th><td align = "right" colspan=7 style="border: 1px solid black;font-size:12px;"><b>%s</b></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:12px;"><b>%s</b></td><td colspan=3 align = "right" style="border: 1px solid black;font-size:12px;"><b>%s</b></td></tr>'%(round(total_margin_internal,2),'',total_qty,round(total_internal_cost,2))
    data_4+='</table>'

    data_5 = ''
    if "CFO" in frappe.get_roles(frappe.session.user) or "COO" in frappe.get_roles(frappe.session.user) or "HOD" in frappe.get_roles(frappe.session.user) or "Accounts User" in frappe.get_roles(frappe.session.user):
        data_5 += '<table class="table"><tr><th style="padding:1px;border: 1px solid black;font-size:14px;background-color:#FF4500;color:white;" colspan=18><center><b>MARGIN BY VALUE & MARGIN BY PERCENTAGE</b></center></th></tr>'
        spl = 0
        for i in item_details:
            if i["special_cost"] > 0:
                spl = spl + 1
        if spl == 0:
            data_5+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=2 style="border: 1px solid black;font-size:11px;width:30%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>IN WAREHOUSE</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>IN TRANSIT</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SELLING PRICE</b></td></tr>'
        else:
            data_5+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=2 style="border: 1px solid black;font-size:11px;width:30%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>IN WAREHOUSE</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>IN TRANSIT</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SPECIAL PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SELLING PRICE</b></td></tr>'

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
        frappe.errprint(i["rate"])
        frappe.errprint("------------")
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
        # from erpnext.setup.utils import get_exchange_rate
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
            from erpnext.setup.utils import get_exchange_rate
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
        from erpnext.setup.utils import get_exchange_rate
        base_cost_conversion = get_exchange_rate("USD",currency)
        if not standard_buying_usd:
            standard_buying_usd = 0
        else:
            standard_buying_usd =  base_cost_conversion * standard_buying_usd
        cost_total = standard_buying_usd*i["qty"] + cost_total
        country = frappe.get_value("Company",{"name":company},["country"])
        
        total_internal_cost = i["internal_cost"]*i["qty"] + total_internal_cost
        total_special_price =(i["special_cost"] * i["qty"]) + total_special_price

        if "CFO" in frappe.get_roles(frappe.session.user) or "COO" in frappe.get_roles(frappe.session.user) or "HOD" in frappe.get_roles(frappe.session.user) or "Accounts User" in frappe.get_roles(frappe.session.user):
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
    if "CFO" in frappe.get_roles(frappe.session.user) or "COO" in frappe.get_roles(frappe.session.user) or "HOD" in frappe.get_roles(frappe.session.user) or "Accounts User" in frappe.get_roles(frappe.session.user):
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
    # data_2+='<tr><td colspan=1 style="border: 1px solid black;font-size:11px;"><center><b>ITEM</b><center></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><center><b>IN WAREHOUSE</b><center></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><center><b>IN TRANSIT</b><center></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><center><b>TOTAL</b><center></td></tr>'
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
def check_internal_cost(doc,method):
    if not doc.internal_cost_margin:
        doc.internal_cost_margin = 0

    if not doc.currency == "INR" and doc.grand_total >= 100000 and doc.work_flow == 'Draft':
        frappe.validated = False
        frappe.throw("Not allowed to submit,Grand total exceed the limit,Please click the button Send to CFO")

    if doc.currency == "INR" and doc.grand_total >= 10000000 and doc.work_flow == 'Draft':
        frappe.validated = False
        frappe.throw("Not allowed to submit,Grand total exceed the limit,Please click the button Send to CFO")

    if doc.internal_cost_margin < 40 and doc.work_flow == 'Draft':
        frappe.validated = False
        frappe.throw("Not allowed to submit,click the Button Send to Sales Manager")

    if not doc.company == "Norden Communication Middle East FZE" and doc.internal_cost_margin < 30  and doc.work_flow == "Pending for Sales Manager" and "Sales Manager" in frappe.get_roles(frappe.session.user):
        frappe.validated = False
        frappe.throw("Not allowed to submit,click the Button Send to HOD")
    
    if doc.internal_cost_margin < 25  and doc.work_flow == "Pending for HOD" and "HOD" in frappe.get_roles(frappe.session.user):
        frappe.validated = False
        frappe.throw("Not allowed to submit,click the Button Send to COO")

    if doc.internal_cost_margin < 10 and doc.work_flow == "Pending for COO" and "COO" in frappe.get_roles(frappe.session.user):
        frappe.validated = False
        frappe.throw("Not allowed to submit,click the Button Send to CFO")

    if doc.grand_total >= 10000000 and doc.work_flow == "Pending for CFO" and "CFO" in frappe.get_roles(frappe.session.user):
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

    if doc.internal_cost_margin < 10 and doc.grand_total <= 100000 and doc.company == "Norden Communication Middle East FZE" and doc.work_flow == "Pending for Sales Manager" and "Sales Manager" in frappe.get_roles(frappe.session.user) and doc.currency == "AED":
        frappe.validated = False
        frappe.throw("Not allowed to submit,click the Button Send to Operation Manager")

   

    



@frappe.whitelist()
def currency_conversion(currency,price):
    from erpnext.setup.utils import get_exchange_rate
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
def get_item_rate(item_code,price_list):
    rate = frappe.get_value("Item Price",{"item_code":item_code,"price_list":price_list},["price_list_rate"])
    return rate

@frappe.whitelist()
def internal_margin_calculation(doc,method):
    if doc.total_selling_price_in_usd:
        if doc.internal_cost == 0:
            doc.internal_cost_margin = doc.internal_cost
        else:
            margin = ((doc.total_selling_price_in_usd - doc.internal_cost)/doc.total_selling_price_in_usd)*100
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
    part_no = frappe.db.sql(""" select `tabItem Supplier`.supplier as supplier from `tabItem` left join `tabItem Supplier` on `tabItem`.name =`tabItem Supplier`.parent where `tabItem`.name = '%s' """%(item_code),as_dict = True)[0]
    return part_no

@frappe.whitelist()
def check_altair(name):
    altair = frappe.db.exists("Purchase Order",{"original_po_number":name})
    if altair:
        return "Yes"
    else:
        return "No"

@frappe.whitelist()
def batch_number(doc,method):
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

@frappe.whitelist()
def create_file_number(doc,method):
    
    code = 'F-Q-' + doc.abbr
    doc_no = doc.name[-5:]
    file_no = code + '-' + doc_no
    doc.file_number = file_no

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
            frapper.msgprint("----")
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
            # frappe.log_error(title = )
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

@frappe.whitelist()
def create_file_number_mr(doc,method):
    if not doc.sales_order_number:
        code = 'F-MR-' + doc.abbr
        doc_no = doc.name[-5:]
        file_no = code + '-' + doc_no
        doc.file_number = file_no

# @frappe.whitelist()
# def get_sub_heading(item_detail):
#     item_detail = json.loads(item_detail)
#     l1 = []
#     l2 = []
#     for i in item_detail:
#         if i['item_sub_heading'] not in l1:
#             l1.append(i["item_sub_heading"])
#         else:
#             l2.append(i["item_sub_heading"])
#     return l1



@frappe.whitelist()
def get_item_heading(item_details):
    item_details = json.loads(item_details)
    l1 = []
    l2 = []
    for i in item_details:
        if i['item_heading'] not in l1:
            l1.append(i["item_heading"])
        else:
            l2.append(i["item_heading"])
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
    data+='<table class = table table-bordered >' 
    data += '<table class="table table-bordered"><tr rowspan = 2 ><th style="padding:1px;border: 1px solid black;width:100%;" colspan=16><center><b>Item Details</b></center></th></tr>'
    so_cust = frappe.get_value("Sales Order",{"name":so_no},["customer_name"])
    so_pt = frappe.get_value("Sales Order",{"name":so_no},["payment_terms_template"])
    po_pt = frappe.get_value("Purchase Order",{"name":name},["payment_terms_template"])
    data += '<tr rowspan = 2 ><td style="padding:1px;border: 1px solid black;" colspan=3><b>Customer</b></td><td style="padding:1px;border: 1px solid black;" colspan=4>%s</td><td style="padding:1px;border: 1px solid black;" colspan = 3><b>Supplier</b></td><td style="padding:1px;border: 1px solid black;" colspan=5 >%s</td></tr>'%(so_cust,supplier)
    data += '<tr rowspan = 2 ><td style="padding:1px;border: 1px solid black;" colspan=3><b>Payment Terms</b></td><td style="padding:1px;border: 1px solid black;" colspan=4>%s</td><td style="padding:1px;border: 1px solid black;" colspan = 3><b>Payment Terms</b></td><td style="padding:1px;border: 1px solid black;" colspan=5 >%s</td></tr>'%(so_pt,po_pt or '')
    data += '<tr rowspan = 2 ><td style="padding:1px;border: 1px solid black;width:100px;" colspan=2><b>Item Code</b></td><td style="padding:1px;border: 1px solid black;" colspan=2><b>Description</b></td><td style="padding:1px;border: 1px solid black;" colspan=1><b>Qty</b></td><td style="padding:1px;border: 1px solid black;" colspan=1><b>Rate</b></td><td style="padding:1px;border: 1px solid black;" colspan=1><b>Prv PO</b></td><td style="padding:1px;border: 1px solid black;" colspan=1><b>Selling Rate</b></td><td style="padding:1px;border: 1px solid black;" colspan=2><b>Margin%</b></td><td style="padding:1px;border: 1px solid black;" colspan=2><b>Stock</b></td><td style="padding:1px;border: 1px solid black;" colspan=2><b>In transit</b></td><td style="padding:1px;border: 1px solid black;" colspan=2><b>Currency</b></td></tr>'
    for i in item_details:
        frappe.errprint(i["item_code"])
        from erpnext.setup.utils import get_exchange_rate
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
        ppo = 0
        if pos:
            from erpnext.setup.utils import get_exchange_rate
            pos_ex = get_exchange_rate(pos[0]["currency"],so_currency)
            pos[0]["rate"] = pos_ex * pos[0]["rate"]
            pos[0]["rate"] = round(pos[0]["rate"],3)
            ppo = pos[0]["rate"]
        # frappe.errprint(pos[0]["rate"])
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
            select sum(b.actual_qty) as qty from `tabBin` b 
            join `tabWarehouse` wh on wh.name = b.warehouse
            join `tabCompany` c on c.name = wh.company
            where c.country = '%s' and b.item_code = '%s' and wh.company = '%s'
            """ % (country,i["item_code"],company),as_dict=True)[0]
        if not warehouse_stock["qty"]:
            warehouse_stock["qty"] = 0
        # if pos:
        #     data += '<tr rowspan = 2 ><td style="padding:1px;border: 1px solid black;" colspan=1>%s</td><td style="padding:1px;border: 1px solid black;" colspan=3>%s</td><td style="padding:1px;border: 1px solid black;" colspan=1>%s</td><td style="padding:1px;border: 1px solid black;" colspan=1>%s</td><td style="padding:1px;border: 1px solid black;" colspan=1 >%s</td><td style="padding:1px;border: 1px solid black;" colspan=1 >%s</td><td style="padding:1px;border: 1px solid black;" colspan=2 >%s</td><td style="padding:1px;border: 1px solid black;" colspan=2 >%s</td><td style="padding:1px;border: 1px solid black;" colspan=2 >%s</td><td style="padding:1px;border: 1px solid black;" colspan=2 >%s</td></tr>'%(i["item_code"],i["description"],i["qty"],i["rate"],pos["amount"]/pos["qty"],s_rate["rate"],round(margin,2),warehouse_stock["qty"],in_transit,currency)
        # else:
        data += '<tr rowspan = 2 ><td style="padding:1px;border: 1px solid black;width:150px;" colspan=2>%s</td><td style="padding:1px;border: 1px solid black;width:150px;" colspan=2>%s</td><td style="padding:1px;border: 1px solid black;" colspan=1>%s</td><td style="padding:1px;border:1px solid black;width:80px;" colspan=1>%s</td><td style="padding:1px;border: 1px solid black;" colspan=1>%s</td><td style="padding:1px;border: 1px solid black;" colspan=1 >%s</td><td style="padding:1px;border: 1px solid black;" colspan=2 >%s</td><td style="padding:1px;border: 1px solid black;" colspan=2 >%s</td><td style="padding:1px;border: 1px solid black;" colspan=2 >%s</td><td style="padding:1px;border: 1px solid black;" colspan=2 >%s</td></tr>'%(i["item_code"],i["description"],i["qty"],i["rate"],ppo,s_rate[0]["rate"],round(margin,2),warehouse_stock["qty"],in_transit,so_currency)   
    data+='</table>'
    return data


@frappe.whitelist()
def get_item_details_frm_mr(mat_rq,company,name,currency,item_details,supplier):
    if mat_rq:
        item_details = json.loads(item_details)
        # mr = frappe.get_doc("Material Request",mat_rq)
        mr_currency = frappe.get_value("Material Request",{"name":mat_rq},["project_currency"])
        data = ''
        data+='<table class = table table-bordered >' 
        data += '<table class="table table-bordered"><tr rowspan = 2 ><th style="padding:1px;border: 1px solid black;width:100%;" colspan=18><center><b>Item Details</b></center></th></tr>'
        mr_cust = frappe.get_value("Material Request",{"name":mat_rq},["customers"])
        po_pt = frappe.get_value("Purchase Order",{"name":name},["payment_terms_template"])
        data += '<tr rowspan = 2 ><td style="padding:1px;border: 1px solid black;" colspan=4><b>Customer</b></td><td style="padding:1px;border: 1px solid black;" colspan=4>%s</td><td style="padding:1px;border: 1px solid black;" colspan = 4><b>Supplier</b></td><td style="padding:1px;border: 1px solid black;" colspan=5 >%s</td></tr>'%(mr_cust,supplier)
        data += '<tr rowspan = 2 ><td style="padding:1px;border: 1px solid black;" colspan=4><b>Payment Terms</b></td><td style="padding:1px;border: 1px solid black;" colspan=4>%s</td><td style="padding:1px;border: 1px solid black;" colspan = 4><b>Payment Terms</b></td><td style="padding:1px;border: 1px solid black;" colspan=5 >%s</td></tr>'%('',po_pt or '')
        data += '<tr rowspan = 2 ><td style="padding:1px;border: 1px solid black;" colspan=3><b>Item Code</b></td><td style="padding:1px;border: 1px solid black;" colspan=2><b>Description</b></td><td style="padding:1px;border: 1px solid black;" colspan=1><b>Qty</b></td><td style="padding:1px;border: 1px solid black;" colspan=1><b>Rate</b></td><td style="padding:1px;border: 1px solid black;" colspan=2><b>Prv Po</b></td><td style="padding:1px;border: 1px solid black;" colspan=1><b>Selling Rate</b></td><td style="padding:1px;border: 1px solid black;" colspan=2><b>Margin%</b></td><td style="padding:1px;border: 1px solid black;" colspan=2><b>Stock</b></td><td style="padding:1px;border: 1px solid black;" colspan=2><b>In transit</b></td><td style="padding:1px;border: 1px solid black;" colspan=2><b>Currency</b></td></tr>'
        for i in item_details:
            frappe.errprint(i["item_code"])
            from erpnext.setup.utils import get_exchange_rate
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
                frappe.errprint(pos[0]["rate"])
                from erpnext.setup.utils import get_exchange_rate
                pos_ex = get_exchange_rate(pos[0]["currency"],mr_currency)
                pos[0]["rate"] = pos_ex * pos[0]["rate"]
                pos[0]["rate"] = round(pos[0]["rate"],3)
                ppo = pos[0]["rate"]
            frappe.errprint(ppo)
            # if not pos:
            #     pos = 123
            # if pos:
            #     frappe.errprint(pos)
                # from erpnext.setup.utils import get_exchange_rate
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
            data += '<tr rowspan = 2 ><td colspan=3 style="padding:1px;border: 1px solid black;";>%s</td><td style="padding:1px;border: 1px solid black;" colspan=2>%s</td><td style="padding:1px;border: 1px solid black;" colspan=1>%s</td><td style="padding:1px;border: 1px solid black;" colspan=1>%s</td><td style="padding:1px;border: 1px solid black;" colspan=1 >%s</td><td style="padding:1px;border: 1px solid black;" colspan=2 >%s</td><td style="padding:1px;border: 1px solid black;" colspan=2 >%s</td><td style="padding:1px;border: 1px solid black;" colspan=2 >%s</td><td style="padding:1px;border: 1px solid black;" colspan=2 >%s</td><td style="padding:1px;border: 1px solid black;" colspan=2 >%s</td></tr>'%(i["item_code"],i["description"],i["qty"],round(i["rate"],2),ppo,m_rate["sales_price"],round(margin,2),warehouse_stock["qty"],in_transit,mr_currency)
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
#     frappe.errprint(item)
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
def margin(item_details,company,currency,exchange_rate,user,price_list):
    item_details = json.loads(item_details)
    data = ''
    if "CFO" in frappe.get_roles(frappe.session.user) or "COO" in frappe.get_roles(frappe.session.user) or "HOD" in frappe.get_roles(frappe.session.user) or "Accounts User" in frappe.get_roles(frappe.session.user):
        data+= '<table class="table"><tr><th style="padding:1px;border: 1px solid black;font-size:14px;" colspan=18><center><b>MARGIN BY VALUE & MARGIN BY PERCENTAGE</b></center></th></tr>'
        spl = 0
        for i in item_details:
            if i["special_cost"] > 0:
                spl = spl + 1
        if spl == 0:
            if price_list == "Internal Cost":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=2 style="border: 1px solid black;font-size:11px;width:30%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>IN WAREHOUSE</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>IN TRANSIT</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SELLING PRICE</b></td></tr>'
            if price_list == "Freight":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=2 style="border: 1px solid black;font-size:11px;width:30%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>IN WAREHOUSE</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>IN TRANSIT</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>FREIGHT %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SELLING PRICE</b></td></tr>'
            if price_list == "Sales Price":
                data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=2 style="border: 1px solid black;font-size:11px;width:30%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>IN WAREHOUSE</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>IN TRANSIT</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SALES PRICE %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SELLING PRICE</b></td></tr>'
        else:
            data+='<tr><td colspan=3 style="border:1px solid black;font-size:11px;width:20%;"><center><b>ITEM</b></center></td><td colspan=2 style="border: 1px solid black;font-size:11px;width:30%;"><center><b>ITEM NAME</b></center></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>IN WAREHOUSE</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>IN TRANSIT</center></b></td><td colspan=1 style="border: 0.5px solid black;font-size:11px;"><b><center>TOTAL</center></b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>QTY</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>COST %</b></td></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>INTERNAL COST %</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SPECIAL PRICE</b></td><td colspan=1 style="border: 1px solid black;font-size:11px;"><b>SELLING PRICE</b></td></tr>'

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
        frappe.errprint(i["rate"])
        frappe.errprint("------------")
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

        sbu = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':'STANDARD BUYING-USD'},["price_list_rate"])
        value = frappe.db.get_value("Margin Price Tool")
        frappe.errprint(value)
        # for i in ic.singapore:
        #     frappe.errprint(i)

        
        if "CFO" in frappe.get_roles(frappe.session.user) or "COO" in frappe.get_roles(frappe.session.user) or "HOD" in frappe.get_roles(frappe.session.user) or "Accounts User" in frappe.get_roles(frappe.session.user):
            if i["special_cost"] > 0:
                data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=2 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,i["qty"],total_stock,'','','','','','')
            else:
                data+='<tr><td colspan=3 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=2 align = "right" style="border: 1px solid black;font-size:11px;"><center>%s<center></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1  align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;">%s</td></tr>'%(i["item_code"],i["description"],warehouse_stock["qty"],in_transit,total_stock,i["qty"],sbu,'','','','')
   
    if "CFO" in frappe.get_roles(frappe.session.user) or "COO" in frappe.get_roles(frappe.session.user) or "HOD" in frappe.get_roles(frappe.session.user) or "Accounts User" in frappe.get_roles(frappe.session.user):
        if spcl == 0:
            data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=5><center><b>TOTAL MARGIN BASED ON INTERNAL COST : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%('','','','','','','')
        else:
            data += '<tr style="line-height:0.6;"><th style="padding-top:12px;border: 1px solid black;font-size:11px" colspan=5><center><b>TOTAL MARGIN BASED ON INTERNAL COST : %s</b></center></th><td colspan=4 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s<b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td><td colspan=1 align = "right" style="border: 1px solid black;font-size:11px;"><b>%s</b></td></tr>'%('','','','','')
    data+='</table>'
    return data


        
   
