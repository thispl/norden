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
		data +='<tr><td style="padding:1px;border: 1px solid black"><b>item Code</b></td><td style="padding:1px;border: 1px solid black"><b>description</b></td><td style="padding:1px;border: 1px solid black"><b>B2B</b></td><td style="padding:1px;border: 1px solid black"><b>For Stock</b></td><td style="padding:1px;border: 1px solid black"><b>FOC</b></td><td style="padding:1px;border: 1px solid black"><b>Rate</b></td><td style="padding:1px;border: 1px solid black"><b>Amount</b></td><td style="padding:1px;border: 1px solid black"><b>Rate</b></td><td style="padding:1px;border: 1px solid black"><b>Amount</b></td><td style="padding:1px;border: 1px solid black"><b>Margin%</b></td><td style="padding:1px;border: 1px solid black"><b>STOCK</b></td><td style="padding:1px;border: 1px solid black"><b>PO</b></td><td style="padding:1px;border: 1px solid black"><b>Total</b></td><td style="padding:1px;border: 1px solid black"><b>Last 3month transaction</b></td><td style="padding:1px;border: 1px solid black"><b>Last Unit Purchase</b></td><td style="padding:1px;border: 1px solid black"><b>Remark</b></td></tr>'
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
					frappe.throw("Not allowed to submit")

			if doc.work_flow == "Pending for COO":
				if "COO" in frappe.get_roles(frappe.session.user):
					frappe.validated = True
				else:
					frappe.validated = False
					frappe.throw("Not allowed to submit")
				
			if doc.work_flow == "Pending for HOD":
				if "HOD" in frappe.get_roles(frappe.session.user):
					frappe.validated = True
				else:
					frappe.validated = False
					frappe.throw("Not allowed to submit")
				
			if doc.work_flow == "Pending for Sales Manager":
				if "Sales Manager" in frappe.get_roles(frappe.session.user):
					frappe.validated = True
				else:
					frappe.validated = False
					frappe.throw("Not allowed to submit")
		



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

						if doc.internal_cost_margin < 10 and doc.grand_total <= 250000 and doc.company == "Norden Communication Middle East FZE" and doc.work_flow == "Pending for Sales Manager" and "Sales Manager" in frappe.get_roles(frappe.session.user) and doc.currency == "AED":
							frappe.validated = False
							frappe.throw("Not allowed to submit ,the profit percentage is less than the allowed limit to submit. Click the Button Send to Operation Director")

						if doc.grand_total > 250000 and doc.company == "Norden Communication Middle East FZE" and doc.work_flow == "Pending for Sales Manager" and "Sales Manager" in frappe.get_roles(frappe.session.user) and doc.currency == "AED":
							frappe.validated = False
							frappe.throw("Not allowed to submit ,the profit percentage is less than the allowed limit to submit. Click the Button Send to Operation Director")

						if doc.internal_cost_margin < 10 and doc.company == "Norden Communication Middle East FZE" and doc.work_flow == "Pending for Sales Manager" and "Sales Manager" in frappe.get_roles(frappe.session.user) and doc.currency == "AED":
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
		unit_price_document_currency = unit_price * get_exchange_rate(frappe.get_value("Item Price",{"item_code":item_code,"price_list":price_list},["currency"]),doc_currency)
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
	doc.batch = doc.abbr +"-"+ doc.name[-10:]
	if doc.amended_from:
		doc.batch = doc.abbr +"-"+ doc.name[-12:]
	# doc.batch = batch

	# batch_id = frappe.new_doc('Batch')
	# po_items = doc.items
	# for item in po_items:
	#     batch_id.update({
	#         "item":item.item_code,
	#         "batch_id": batch,
	#         "purchase_order_no":doc.purchase_order_no,
	#         "reference_doctype":"Purchase Order",
	#         "reference_name":doc.name
	#     })
	#     batch_id.save(ignore_permissions=True)
		

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
	if not doc.file_number:
		if doc.company == "Norden Communication Middle East FZE" or doc.company == "Norden Communication UK Limited":
			code = 'F-Q-' + doc.abbr + '-23'
		else:
			code = 'F-Q-' + doc.abbr
		doc_no = doc.name[-5:]
		file_no = code + '-' + doc_no
		doc.file_number = file_no

@frappe.whitelist()
def create_opp_file_number(doc,method):    
	code = 'F-O-' + doc.abbr
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

@frappe.whitelist()
def create_file_number_mr(doc,method):
	if not doc.sales_order_number:
		code = 'F-MR-' + doc.abbr
		doc_no = doc.name[-5:]
		file_no = code + '-' + doc_no
		doc.file_number = file_no

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
			select sum(b.actual_qty) as qty from `tabBin` b 
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
	po = frappe.db.sql("""update `tabPurchase Order` set workflow_state = 'Cancelled' where name ='PUR-ORD-NCPLP-2022-00009' """)


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
	contact.email_id_ = email
	contact.mobile_no = mobile
	contact.append('email_ids',{
		'email_id': email		
	})
	contact.append('phone_nos',{
		'phone':mobile,
	})
	contact.append('links',{
		'link_doctype':'Customer',
		"link_name": customer
	})
	contact.save(ignore_permissions=True)

# @frappe.whitelist()
# def update_ce_so():
#     so = frappe.db.sql(""" update `tabDelivery Note` set conversion_rate = '1.32' where name = '%s' """%("DN-NSPL-2022-00098"))

   

@frappe.whitelist()
def get_electra_details(**args): 
	data = ''
	data1 = ''
	aa = args['item']
	item = frappe.get_value('Item',{'item_code':args['item']},'item_code')
	rate = frappe.get_value('Item',{'item_code':args['item']},'valuation_rate')
	group = frappe.get_value('Item',{'item_code':args['item']},'item_group')
	des = frappe.get_value('Item',{'item_code':args['item']},'description')
	price = frappe.get_value('Item Price',{'item_code':args['item'],'price_list':'Cost'},'price_list_rate')
	c_s_p = frappe.get_value('Item Price',{'item_code':args['item'],'price_list':'Standard Selling'},'price_list_rate') or 0
	csp = 'Current Selling Price'
	cpp = 'Current Purchase Price'
	cost = 'COST'
	pso = 'Pending Sales order'
	po ='Total Purchase Order'
	ppo = 'Pending Purchase order'
	cspp_rate = 0
	cppp_rate = 0
	psoc = 0
	ppoc = 0
	ppoc_total = 0
	i = 0
	cou = 0
	p_po = 0
	p_so = 0
	tot = 'Total'
	uom = 'Nos'

	stocks_query = frappe.db.sql("""select actual_qty,warehouse,stock_uom,stock_value from tabBin
			where item_code = '%s' """%(item),as_dict=True)
	if stocks_query:
		stocks = stocks_query
	if ppoc_total > 0 :
		ppoc_date_query = frappe.db.sql("""select `tabPurchase Order Item`.schedule_date  as date from `tabPurchase Order`
		left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
		where `tabPurchase Order Item`.item_code = '%s' """ % (args['item']), as_dict=True)[0]
		if ppoc_date_query:
			po_date = ppoc_date_query['date']

	data += '<table class="table table-bordered" style="width:70%"><tr><th style="padding:1px;border: 1px solid black;background-color:#fe3f0c;color:white" colspan=10><center>NORDEN PRODUCT SEARCH</center></th></tr>'
	data += '<tr><td colspan = 2 style="padding:1px;border: 1px solid black;color:white;background-color:#6f6f6f;text-align: left"><b>Item Code</b></td><td colspan = 8 style="padding:1px;border: 1px solid black;text-align: left"><b>%s</b></td></tr>'%(item)
	data += '<tr><td colspan = 2 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;text-align: left"><b>Item Name</b></td><td colspan = 8 style="padding:1px;border: 1px solid black;text-align: left"><b>%s</b></td></tr>'%(frappe.db.get_value('Item',item,'item_name'))
	data += '<tr><td colspan = 2 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;text-align: left"><b>Item Group</b></td><td colspan = 8 style="padding:1px;border: 1px solid black;text-align: left"><b>%s</b></td></tr>'%(group)
	data += '<tr><td colspan = 2 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;text-align: left"><b>Description</b></td><td colspan = 8 style="padding:1px;border: 1px solid black;text-align: left"><b>%s</b></td></tr>'%(des)
	
	if stocks_query:
		data += '<tr><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Company</b></center></td>'
		data += '<td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Warehouse</b></center></td>'
		data += '<td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>QTY</b></center></td>'
		data += '<td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>UOM</b></center></td>'
		data += '<td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Cost</b></center></td>'
		data += '<td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Selling Rate</b></center></td>'
		data += '<td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Currency</b></center></td>'
		data += '<td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Pending PO</b></center></td>'
		data += '<td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Pending SO</b></center></td>'
		data += '</tr>'
		for stock in stocks_query:
			if stock.actual_qty >= 0:
				stock_company = frappe.db.sql("""select company from tabWarehouse where name = '%s' """%(stock.warehouse),as_dict=True)
				for com in stock_company:
					psoc_query = frappe.db.sql("""select sum(`tabSales Order Item`.qty) as qty from `tabSales Order`
					left join `tabSales Order Item` on `tabSales Order`.name = `tabSales Order Item`.parent
					where `tabSales Order Item`.item_code = '%s' and `tabSales Order`.docstatus = 1 and `tabSales Order`.company = '%s' """ % (args['item'],com.company), as_dict=True)[0]
					if not psoc_query["qty"]:
						psoc_query["qty"] = 0
					deliver = frappe.db.sql("""select sum(`tabDelivery Note Item`.qty) as qty from `tabDelivery Note`
					left join `tabDelivery Note Item` on `tabDelivery Note`.name = `tabDelivery Note Item`.parent
					where `tabDelivery Note Item`.item_code = '%s' and `tabDelivery Note`.docstatus = 1 and `tabDelivery Note`.company = '%s'  """%(args['item'],com.company), as_dict=True)[0]
					if not deliver["qty"]:
						deliver['qty'] = 0
					del_total = psoc_query['qty'] - deliver['qty']
					ppoc_query = frappe.db.sql("""select sum(`tabPurchase Order Item`.qty) as qty from `tabPurchase Order`
					left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
					where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 and `tabPurchase Order`.company = '%s' """ % (args['item'],com.company), as_dict=True)[0]
					if not ppoc_query["qty"]:
						ppoc_query["qty"] = 0
					ppoc_receipt = frappe.db.sql("""select sum(`tabPurchase Receipt Item`.qty) as qty from `tabPurchase Receipt`
					left join `tabPurchase Receipt Item` on `tabPurchase Receipt`.name = `tabPurchase Receipt Item`.parent
					where `tabPurchase Receipt Item`.item_code = '%s' and `tabPurchase Receipt`.status = "Completed" and `tabPurchase Receipt`.company = '%s'  """%(args['item'],com.company),as_dict=True)[0]
					if not ppoc_receipt["qty"]:
						ppoc_receipt["qty"] = 0
					ppoc_total = ppoc_query["qty"] - ppoc_receipt["qty"]
					country,default_currency = frappe.get_value("Company",{"name":com.company},["country","default_currency"])
					if country == "United Arab Emirates":
						cost = frappe.get_value("Item Price",{"item_code":item,"price_list":"Electra Qatar - NCMEF"},["price_list_rate"])
					else:
						cost = frappe.get_value("Item Price",{"item_code":item,"price_list":"STANDARD BUYING-USD"},["price_list_rate"])
					pricelist = country + ' ' + "Sales Price"
					if country == "United Arab Emirates":
						sp = frappe.get_value("Item Price",{"item_code":item,"price_list":"Internal - NCMEF"},["price_list_rate"])
					else:
						sp = frappe.get_value("Item Price",{"item_code":item,"price_list":pricelist},["price_list_rate"])
					data += '<tr><td colspan = 1 style="padding:1px;border: 1px solid black">%s</td><td colspan = 1 style="padding:1px;border: 1px solid black">%s</td><td colspan = 1 style="padding:1px;border: 1px solid black"><center><b>%s</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black"><center><b>%s</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black"><center><b>%s</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black"><center><b>%s</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black"><center><b>%s</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black"><center><b>%s</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black"><center><b>%s</b></center></td></tr>'%(com.company,stock.warehouse,int(stock.actual_qty) or 0,stock.stock_uom or '-',cost or 0,sp or 0,default_currency,ppoc_total or 0,del_total or 0)
					i += 1
					cou += stock.actual_qty
					p_po += ppoc_total
					p_so += del_total
		data += '<tr><td align="right" colspan = 2 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><b>%s</b></td><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>%s</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>%s</b></center></td><td colspan = 3 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b></b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>%s</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>%s</b></center></td></tr>'%(tot or 0,int(cou) or 0,uom,p_po or 0,p_so or 0)
		data += '</table>'
	else:
		i += 1
		data1 += '<tr><td align="center" colspan = 10 style="padding:1px;border: 1px solid black;background-color:#fe3f0c;color:white;"><b>No Stock Available</b></td></tr>'
		data1 += '</table>'
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

# @frappe.whitelist()
# def delete_pr():
#     pr = frappe.db.sql(""" delete from `tabItem Inspection`  where name = "IS-NCMEF-2023-00002"  """)

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
		

# Quote to stock entry creation process
@frappe.whitelist()
def create_new_stock_entry(name):
	doc_quote = frappe.get_doc("Quotation",name)
	if doc_quote.stock_entry:
		frappe.throw(_("Stock Entry Already Created Against this Quotation"))
	else:
		quote_item = doc_quote.items
		source_warehouse = frappe.db.sql(""" select name from `tabWarehouse` where default_for_stock_transfer = '1' and company = '%s' """%(doc_quote.company),as_dict=1)[0]
		target_warehouse = frappe.db.sql(""" select name from `tabWarehouse` where is_allocate = '1' and company = '%s' """%(doc_quote.company),as_dict=1)[0]
		cost_center = frappe.db.sql("""select cost_center from `tabCompany` where name = '%s' """%(doc_quote.company),as_dict=1)[0]
		stock = frappe.new_doc("Stock Entry")
		stock.company = doc_quote.company
		stock.stock_entry_type = "Material Transfer"
		stock.linked_quotation = doc_quote.name
		stock.from_warehouse = source_warehouse['name']
		stock.to_warehouse = target_warehouse['name']
		for i in quote_item:
			stock.append('items',{
				'item_code':i.item_code,
				'qty':i.qty,
				'uom':i.uom,
				's_warehouse': source_warehouse['name'],
				't_warehouse': target_warehouse['name'],
				'cost_center': cost_center['cost_center']
			})
		stock.save(ignore_permissions=True)
		frappe.db.commit()
		frappe.msgprint("Stock Entry Has been created Kindly refresh the page")

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
 

@frappe.whitelist()
def set_sp():
	sl = frappe.db.sql(""" select name from `tabSales Order` where transaction_date between "2022-07-12" and "2022-12-12" and docstatus != 2 """,as_dict=True)
	for sale in sl:
		sp = frappe.get_doc("Sales Order",sale.name)
		print(sale.name)
		name = frappe.db.get_value("Employee",{'user_id':sp.sale_person},['name'])
		sale_person = frappe.db.get_value("Sales Person",{'employee':name},['name'])
		if sale_person:
			sp.set('sales_team', [])
			sp.append("sales_team",{
				'sales_person': sale_person,
				'allocated_percentage': 100,
				'allocated_amount':sp.net_total,
			})
			sp.flags.ignore_mandatory = True
			sp.flags.ignore_validate_update_after_submit = True
			sp.save(ignore_permissions = True)


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
	no_item = ["HI"]
	for ip in ips:
		if frappe.db.exists('Item Price', {'item_code': ip[0]}):
			if frappe.db.exists('Item Price', {'item_code': ip[0], 'price_list': "Cost Rate - NCMEF"}):
				rate = frappe.get_doc('Item Price', {'item_code': ip[0], 'price_list': "Cost Rate - NCMEF"})
				print(rate.price_list_rate)
				rate.price_list_rate = ip[2]
				rate.save(ignore_permissions=True)
				frappe.db.commit() 

			if frappe.db.exists('Item Price', {'item_code': ip[0], 'price_list': "Landing - NCMEF"}):
				rate = frappe.get_doc(
					'Item Price', {'item_code': ip[0], 'price_list': "Landing - NCMEF"})
				print(rate.price_list_rate)
				rate.price_list_rate = ip[3]
				rate.save(ignore_permissions=True)
				frappe.db.commit() 

			if frappe.db.exists('Item Price', {'item_code': ip[0], 'price_list': "Incentive - NCMEF"}):
				rate = frappe.get_doc('Item Price', {'item_code': ip[0], 'price_list': "Incentive - NCMEF"})
				print(rate.price_list_rate)
				rate.price_list_rate = ip[4]
				rate.save(ignore_permissions=True)
				frappe.db.commit() 

			if frappe.db.exists('Item Price', {'item_code': ip[0], 'price_list': "Internal - NCMEF"}):
				rate = frappe.get_doc('Item Price', {'item_code': ip[0], 'price_list': "Internal - NCMEF"})
				print(rate.price_list_rate)
				rate.price_list_rate = ip[5]
				rate.save(ignore_permissions=True)
				frappe.db.commit() 

			if frappe.db.exists('Item Price', {'item_code': ip[0], 'price_list': "Base Sales Price - NCMEF"}):
				rate = frappe.get_doc('Item Price', {'item_code': ip[0], 'price_list': "Base Sales Price - NCMEF"})
				print(rate.price_list_rate)
				rate.price_list_rate = ip[6]
				rate.save(ignore_permissions=True)
				frappe.db.commit() 

			if frappe.db.exists('Item Price', {'item_code': ip[0], 'price_list': "Retail - NCMEF"}):
				rate = frappe.get_doc('Item Price', {'item_code': ip[0], 'price_list': "Retail - NCMEF"})
				print(rate.price_list_rate)
				rate.price_list_rate = ip[7]
				rate.save(ignore_permissions=True)
				frappe.db.commit() 

			if frappe.db.exists('Item Price', {'item_code': ip[0], 'price_list': "Dist. Price - NCMEF"}):
				rate = frappe.get_doc('Item Price', {'item_code': ip[0], 'price_list': "Dist. Price - NCMEF"})
				print(rate.price_list_rate)
				rate.price_list_rate = ip[8]
				rate.save(ignore_permissions=True)
				frappe.db.commit() 

			if frappe.db.exists('Item Price', {'item_code': ip[0], 'price_list': "Electra Qatar - NCMEF"}):
				rate = frappe.get_doc('Item Price', {'item_code': ip[0], 'price_list': "Electra Qatar - NCMEF"})
				print(rate.price_list_rate)
				rate.price_list_rate = ip[9]
				rate.save(ignore_permissions=True)
				frappe.db.commit() 

			if frappe.db.exists('Item Price', {'item_code': ip[0], 'price_list': "Project Group - NCMEF"}):
				rate = frappe.get_doc('Item Price', {'item_code': ip[0], 'price_list': "Project Group - NCMEF"})
				print(rate.price_list_rate)
				rate.price_list_rate = ip[10]
				rate.save(ignore_permissions=True)
				frappe.db.commit() 

			if frappe.db.exists('Item Price', {'item_code': ip[0], 'price_list': "Saudi Dist. - NCMEF"}):
				rate = frappe.get_doc('Item Price', {'item_code': ip[0], 'price_list': "Saudi Dist. - NCMEF"})
				print(rate.price_list_rate)
				rate.price_list_rate = ip[11]
				rate.save(ignore_permissions=True)
				frappe.db.commit() 
		else:
			no_item.append(ip[0])

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


@frappe.whitelist()
def all_stock(item_code,company):
	w_house = frappe.db.get_all("Warehouse",{"is_allocate":1,"company":company},["name"])
	allocation_details = []
	for wh in w_house:
		parent = frappe.db.get_all("Stock Entry Detail",{'item_code':item_code,"t_warehouse":wh.name},['parent','qty','uom'])
		for p in parent:
			if p.parent:
				quotation = frappe.get_value("Stock Entry",{"name":p.parent,'docstatus':1},['linked_quotation'])
				if quotation:
					customer,transaction_date,file_number,status,company = frappe.get_value("Quotation",quotation,['party_name','transaction_date','file_number','status','company'])
					doctype = "Quotation"
					doc_name = quotation
					allocation_details.append(frappe._dict({"stock_entry":p.parent,"customer":customer,"qty":p.qty,"uom":p.uom,"company":company,"type":doctype,"doc_name":doc_name,"transaction_date": transaction_date,"file_number": file_number,"status": status}))
					print(allocation_details)
				sales_order = frappe.get_value("Stock Entry",{"name":p.parent,'docstatus':1},['linked_sales_order'])
				if sales_order:
					customer,transaction_date,file_number,status,company = frappe.get_value("Sales Order",sales_order,['customer','transaction_date','file_number','status','company'])
					doctype = "Sales Order"
					doc_name = sales_order
					allocation_details.append(frappe._dict({"stock_entry":p.parent,"customer":customer,"qty":p.qty,"uom":p.uom,"company":company,"type":doctype,"doc_name":doc_name,"transaction_date": transaction_date,"file_number": file_number,"status": status}))
					print(allocation_details)
		return allocation_details
	
@frappe.whitelist()
def get_detail_so(item_code,company):
	so_details = []
	pending_qty = 0
	sa = frappe.db.sql(""" select `tabSales Order Item`.parent as parent,`tabSales Order Item`.qty as qty,`tabSales Order Item`.delivered_qty as delivered_qty from `tabSales Order`
	left join `tabSales Order Item` on `tabSales Order`.name = `tabSales Order Item`.parent
	where `tabSales Order Item`.item_code = '%s' and `tabSales Order`.docstatus != 2 and `tabSales Order`.company = '%s' order by `tabSales Order`.transaction_date """ %(item_code,company),as_dict=True)
	for i in sa:
		if not i.qty:
			i.qty = 0
		if not i.delivered_qty:
			i.delivered_qty = 0
		pending_qty = i.qty - i.delivered_qty
		sb = frappe.get_doc("Sales Order", i.parent)
		so_details.append(frappe._dict({"parent":i.parent,"qty":i.qty,"pending_qty":pending_qty,"rate":i.rate,"delivered_qty":i.delivered_qty,"transaction_date":sb.transaction_date,"customer":sb.customer,"po_no":sb.po_no}))
	return so_details


	
	
@frappe.whitelist()
def get_detail_po(item_code,company):
	po_details = []
	bal_qty = 0
	# pending_qty = 0
	sa = frappe.db.sql(""" select `tabPurchase Order Item`.parent as parent,`tabPurchase Order Item`.qty as qty from `tabPurchase Order`
	left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
	where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 and `tabPurchase Order`.company = '%s' order by transaction_date""" %(item_code,company),as_dict=True)
	for i in sa:
	# 	pending_qty = i.qty - i.delivered_qty
		pos = frappe.db.sql("""select `tabPurchase Receipt Item`.received_qty as received_qty from `tabPurchase Receipt`
		left join `tabPurchase Receipt Item` on `tabPurchase Receipt`.name = `tabPurchase Receipt Item`.parent
		where `tabPurchase Receipt Item`.item_code = '%s' and `tabPurchase Receipt Item`.purchase_order = '%s' and `tabPurchase Receipt`.company = '%s'  and `tabPurchase Receipt`.docstatus != 2 """ % (item_code,i.parent,company), as_dict=True)
		req=0
		for j in pos:
			req=j.received_qty
		po = frappe.db.get_value("Item Inspection",{"po_number":i.parent,"item_code":item_code},["sample"])
		if not po:
			po = 0
		if not req:
			req =0
		bal_qty = i.qty - req
		sb = frappe.get_doc("Purchase Order", i.parent)
		po_details.append(frappe._dict({"mr":req,"qc":po,"parent":i.parent,"qty":i.qty,"bal_qty":bal_qty,"transaction_date":sb.transaction_date,"supplier":sb.supplier}))
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
	sales_order = frappe.get_doc("Sales Order",so_no)
	return sales_order.items

@frappe.whitelist()
def get_allocate_qty(so_no):
	se = frappe.db.get_value("Stock Entry",{'linked_sales_order':so_no})
	if se:
		stock = frappe.db.sql("""SELECT SUM(`tabStock Entry Detail`.qty) as qty, `tabStock Entry Detail`.item_code FROM `tabStock Entry` left join `tabStock Entry Detail` on `tabStock Entry`.name = `tabStock Entry Detail`.parent where `tabStock Entry`.name = '%s' group by `tabStock Entry Detail`.item_code """ % (se), as_dict=True)

		# stock = frappe.get_doc("Stock Entry",se)
		return stock
	

@frappe.whitelist()
def get_po_qty(item,company):
	new_po = frappe.db.sql("""select sum(`tabPurchase Order Item`.qty) as qty,sum(`tabPurchase Order Item`.received_qty) as d_qty from `tabPurchase Order` left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus = 1 and `tabPurchase Order`.company = '%s' """ % (item,company), as_dict=True)[0]
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
	item_group = frappe.db.sql("""select sum(actual_qty) as actual_qt from `tabBin` left join `tabItem` where `tabItem`.item_sub_group = %s """ % ("Telephone Cables"), as_dict=True)
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

@frappe.whitelist()
def get_stock_details(doc):
	item_details = doc.items
	data = ''
	data += '<h4><center><b>PICKING LIST</b></center></h4>'
	data += '<table class="table table-bordered">'
	data += '<tr>'
	data += '<td colspan=1 style="width:13%;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e20026;color:white;"><center><b>PRODUCT</b></center></td>'
	data += '<td colspan=1 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e20026;color:white;"><center><b>DESCRIPTION</b></center></td>'
	data += '<td colspan=1 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e20026;color:white;"><center><b>QTY</b></center></td>'
	data += '<td colspan=1 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e20026;color:white;"><center><b>WAREHOUSE</b></center></td></tr>'
	for j in item_details:
		warehouse=[]
		st = 0
		ware = frappe.db.get_list("Warehouse",{"company":doc.company},['name'])
		for w in ware:
			sto = frappe.db.get_value("Bin",{"item_code":j.item_code,"warehouse":w.name},['actual_qty'])
			if sto and sto>0:
				st+=sto
				warehouse.append(w.name)
		data += '<tr><td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' %(j.item_code)
		data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' %(j.description)
		data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' %(j.qty-j.delivered_qty)
		if st >= (j.qty-j.delivered_qty):
			data += '<td style="text-align:center;border: 1px solid black" colspan=1>%s</td>' %(', '.join(map(str, warehouse)))
		else:
			data += '<td style="text-align:center;border: 1px solid black" colspan=1></td>'

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
	SELECT W.company,I.item_sub_group, SUM(B.actual_qty) AS qty
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
	item_details = doc.items
	data = ''
	data += '<h4><center><b>PICKING LIST</b></center></h4>'
	data += '<table class="table table-bordered">'
	data += '<tr>'
	data += '<td colspan=3 style="width:13%;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e20026;color:white;"><center><b>PRODUCT</b></center></td>'
	data += '<td colspan=3 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e20026;color:white;"><center><b>DESCRIPTION</b></center></td>'
	data += '<td colspan=3 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e20026;color:white;"><center><b>QTY</b></center></td>'
	data += '<td colspan=3 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e20026;color:white;"><center><b>WAREHOUSE</b></center></td></tr>'
	
	for j in item_details:
		available_qty = 0
		nonavailable_qty = 0
		warehouse=[]
		st = 0
		ware = frappe.db.get_list("Warehouse",{"company":doc.company},['name'])
		for w in ware:
			sto = frappe.db.get_value("Bin",{"item_code":j.item_code,"warehouse":w.name},['actual_qty'])
			if sto and sto>0:
				st+=sto
				warehouse.append(w.name)
				
				if sto and j.qty > sto:
					available_qty = sto
					
				elif sto and j.qty < sto:
					available_qty = j.qty
		nonavailable_qty = j.qty - available_qty
		if available_qty > 0:
			data += '<tr><td style="text-align:center;border: 1px solid black" colspan=3>%s</td>' %(j.item_code)
			data += '<td style="text-align:center;border: 1px solid black" colspan=3>%s</td>' %(j.description)
			data += '<td style="text-align:center;border: 1px solid black" colspan=3>%s</td>' %(available_qty)
			if warehouse:
				data += '<td style="text-align:center;border: 1px solid black" colspan=3>%s</td>' %(', '.join(map(str, warehouse)))
			else:
				data += '<td style="text-align:center;border: 1px solid black" colspan=3></td>'
	data += '</tr>'
	data += '</table>'
	return data

@frappe.whitelist()
def get_stock(doc):
	item_details = doc.items
	data = ''
	data += '<h4><center><b>NON AVAILABLE QTY</b></center></h4>'
	data += '<table class="table table-bordered">'

	data += '<tr>'
	data += '<td colspan=4 style="width:13%;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e20026;color:white;"><center><b>PRODUCT</b></center></td>'
	data += '<td colspan=4 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e20026;color:white;"><center><b>DESCRIPTION</b></center></td>'
	data += '<td colspan=4 style="width:70px;padding:1px;border:1px solid black;font-size:14px;font-size:12px;background-color:#e20026;color:white;"><center><b>QTY</b></center></td>'	
	for j in item_details:
		available_qty = 0
		nonavailable_qty = 0
		warehouse=[]
		st = 0
		ware = frappe.db.get_list("Warehouse",{"company":doc.company},['name'])
		for w in ware:
			sto = frappe.db.get_value("Bin",{"item_code":j.item_code,"warehouse":w.name},['actual_qty'])
			if sto and sto>0:
				st+=sto
				warehouse.append(w.name)
				if sto and j.qty > sto:
					available_qty = sto
					
				elif sto and j.qty < sto:
					available_qty = j.qty
		nonavailable_qty = j.qty - available_qty
		if nonavailable_qty > 0:
			data += '<tr><td style="text-align:center;border: 1px solid black" colspan=4>%s</td>' %(j.item_code)
			data += '<td style="text-align:center;border: 1px solid black" colspan=4>%s</td>' %(j.description)
			data += '<td style="text-align:center;border: 1px solid black" colspan=4>%s</td>' %(nonavailable_qty)
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

@frappe.whitelist()
def update_so_wf():
	bn = frappe.db.sql(""" update  `tabSerial No`  set batch_no = "9BE47DA" where name = "NVS-DC900021CM-5"  """)
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
		data += "<td style ='border-color:#e20026;text-align:right'>%s</td>" % (frappe.db.get_value('Item',item.item,'gst_hsn_code'))
		# data += "".join(["<td style ='border-color:#e20026;text-align:right'>%s</td>" % i.gst_hsn_code for i in doc.items])
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
	stock = frappe.get_all('Stock Reservation Entry', {'voucher_no': so_no, 'docstatus': ('!=', '2')},
						   ['item_code', 'reserved_qty'])
	for entry in stock:
		item_code = entry.item_code
		reserved_qty = entry.reserved_qty
		if item_code in items_data:
			items_data[item_code] += reserved_qty
		else:
			items_data[item_code] = reserved_qty
	result = [{'item_code': item_code, 'reserved_qty': qty} for item_code, qty in items_data.items()]

	return result

@frappe.whitelist()
def get_data(serial_no):
	data = '<table border="1" style="width: 100%;">'
	if serial_no:
		serial_no_value = frappe.db.get_value("Serial and Batch Entry", {'serial_no': serial_no}, ['parent'])
		if serial_no_value:
			value = frappe.get_all('Serial and Batch Bundle', {'name': serial_no_value}, ['voucher_no', 'voucher_type', 'item_code'])
			dn_date = frappe.db.get_value("Delivery Note", {'name': value[0]['voucher_no']}, ['posting_date'])
			if value and value[0].get('voucher_type') == 'Delivery Note':
				si_parent = frappe.get_value("Sales Invoice Item", {'delivery_note': value[0]['voucher_no']}, ['parent'])
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
				data += '<td colspan="2" style="text-align:center;"><b>{}</b></td>'.format(value[0]['item_code'])
				data += '<td colspan="2" style="text-align:center;"><b>{}</b></td>'.format(value[0]['voucher_no'])
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

@frappe.whitelist()
def create_serial_nums(item_code, docname, batch, serial_numbers):
	doc = frappe.get_doc("Purchase Receipt", docname)
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
				"batch_no": batch,
				"company": doc.company
			}).insert(ignore_permissions=True)
		else:
			success = False
			frappe.msgprint(_("Serial Number {0} already exists.").format(cstr(individual_serial)))

	if success:
		frappe.msgprint(_("Serial Numbers are created successfully"))

	return success


# @frappe.whitelist()
# def po_order_doc():
# 	po_ord=frappe.db.sql(""" delete from `tabPurchase Order` where name = 'PO-NSPL-2023-00096-2' """,as_dict=1)
# 	print(po_ord)

@frappe.whitelist()
def update_target():
	target = frappe.db.get_value("Sales Person", {'name':"Le Minh The"}, ['target'])
	print(target)
	
	
@frappe.whitelist()
def request_for_sample():
	data = ''
	count = 0
	items = frappe.db.sql("""select * from `tabRequest for Sample Item` where workflow_state = 'Issued' """,as_dict= True)
	data += 'Dear Sir,<br><br>Kindly Find the List of Sample Items Not Returned<br><table class="table table-bordered">'
	data += '<table class="table table-bordered"><tr><th>Document Name</th><th>Item Code</th><th>Qty</th><th>Rate</th><th>Customer</th><th>Company</th><th>Source Warehouse</th><th>Target Warehouse</th></tr>'
	for i in items:
		start_date = add_days(i.submission_date,15)
		print(start_date)
		reminder_date = nowdate()
		item = frappe.db.get_value("Sample Items",{'parent':i.name},['item'])
		qty = frappe.db.get_value("Sample Items",{'parent':i.name},['quantity'])
		rate = frappe.db.get_value("Sample Items",{'parent':i.name},['rate'])
		if start_date == reminder_date and i.workflow_state == "Issued":
			count += 1
			data += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (i.name,item,qty,rate,i.customer,i.company,i.source_warehouse,i.target_warehouse)
	data += '</table>'
	if count > 0:
		frappe.sendmail(
			recipients=[i.user,'balamanikandan@nordencommunication.com','jeena.mary@nordencommunication.com','sahayasterwin17@gmail.com','sahayasterwin.a@groupteampro.com'],
			subject=('Sample Items Not Returned'),
			message=data
		)
		
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