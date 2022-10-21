from curses import is_term_resized
import email
import frappe 
from frappe.utils.pdf import get_pdf,cleanup
from frappe import _
import json
from frappe.utils.background_jobs import enqueue
from norden.custom import employee

@frappe.whitelist(allow_guest=True)
def download_pdf(doctype, name, format=None, doc=None, no_letterhead=0):
    html = frappe.get_print(doctype, name, format, doc=doc, no_letterhead=no_letterhead)
    frappe.local.response.filename = "{name}.pdf".format(name=name.replace(" ", "-").replace("/", "-"))
    frappe.local.response.filecontent = get_pdf(html)
    frappe.local.response.type = "pdf"

@frappe.whitelist()
def get_series(company,doctype):
    company_series = frappe.db.get_value("Company Series",{'company':company,'document_type':doctype},'series')
    return company_series
    
@frappe.whitelist()
def email_salary_slip():
    ss = frappe.get_all("Salary Slip",{'start_date':'2022-09-01'},['employee','name'])
    for s in ss:
        doc = frappe.get_doc("Salary Slip",s['name'])
        # receiver = 'hrd@nordencommunication.com'
        receiver = frappe.db.get_value("Employee", doc.employee, "company_email")
        # receiver = 'jagadeesan.a@groupteampro.com'
        payroll_settings = frappe.get_single("Payroll Settings")
        message = "Please Find the attachment"
        password = None

        if receiver:
            email_args = {
                "sender": "hrd@nordencommunication.com",
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
                # 'api@groupteampro.com','hrd@nordencommunication.com','aiswarya@nordencommunication.com','kareem@nordencommunication.com'],
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
           stock_qty = frappe.db.sql(""" select actual_qty from `tabBin` where item_code = '%s' and warehouse = '%s' """%(s['item_code'],w),as_dict=1)
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
    stocks = frappe.db.sql("""select actual_qty,warehouse,stock_uom,stock_value from tabBin
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
    from erpnext.setup.utils import get_exchange_rate
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
