# Copyright (c) 2021, Teampro and contributors
# For license information, please see license.txt

import frappe
from frappe import throw, _, scrub
from frappe.model.document import Document
from erpnext.setup.utils import get_exchange_rate
from frappe.utils import get_url_to_form, today, add_days, nowdate
from frappe.core.api.file import zip_files
import json

class LogisticsRequest(Document):
	def on_update(self):
		if self.workflow_state == "Pending for Confirmation":
			# day = formatdate(today())
			frappe.db.set_value("Logistics Request",self.name,"alert_date",today())
		# if self.workflow_state == "Logistics OPS":
			wa = frappe.get_doc("Workflow Approval","Logistics Request")
			for i in wa.workflow:
				if self.company == i.company and i.role == "Logistics User" and self.workflow_state == "Logistics OPS":
					frappe.sendmail(
						recipients=[i.user ],
						subject = 'Logistics Request- %s is Pending for Approval' %(self.name),
						message = """ Logistics Request - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/logistics-request/%s">Click here</a> to approve """ %(self.name,self.name)

					) 
		if self.workflow_state == "Pending for HOD":	
			wa = frappe.get_doc("Workflow Approval","Logistics Request")
			for i in wa.workflow:
				if self.company == i.company and i.role == "HOD" and self.workflow_state == "Pending for HOD":
					frappe.sendmail(
						recipients=[i.user ],
						subject = 'Logistics Request- %s is Pending for HOD Approval' %(self.name),
						message = """ Logistics Request - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/logistics-request/%s">Click here</a> to approve """ %(self.name,self.name)

					) 

		if self.workflow_state == "Pending for COO":	
			wa = frappe.get_doc("Workflow Approval","Logistics Request")
			for i in wa.workflow:
				if self.company == i.company and i.role == "COO" and self.workflow_state == "Pending for COO":
					frappe.sendmail(
						recipients=[i.user ],
						subject = 'Logistics Request- %s is Pending for COO Approval' %(self.name),
						message = """ Logistics Request - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/logistics-request/%s">Click here</a> to approve """ %(self.name,self.name)

					) 
		
		if self.workflow_state == "Pending for Confirmation":	
			wa = frappe.get_doc("Workflow Approval","Logistics Request")
			for i in wa.workflow:
				if self.company == i.company and i.role == "Accounts User" and self.workflow_state == "Pending for Confirmation":
					frappe.sendmail(
						recipients=[i.user ],
						subject = 'Logistics Request- %s is Pending for Accounts to confirm' %(self.name),
						message = """ Logistics Request - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/logistics-request/%s">Click here</a> to approve """ %(self.name,self.name)

					) 
		
		if self.workflow_state == "Pending for Logistics to Attach Documents":	
			wa = frappe.get_doc("Workflow Approval","Logistics Request")
			for i in wa.workflow:
				if self.company == i.company and i.role == "Logistics User	" and self.workflow_state == "Pending for Logistics to Attach Documents":
					frappe.sendmail(
						recipients=[i.user ],
						subject = 'Logistics Request- %s is Pending for Logistics to Attach Documents' %(self.name),
						message = """ Logistics Request - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/logistics-request/%s">Click here</a> to approve """ %(self.name,self.name)

					) 
		
		if self.workflow_state == "Document Review":	
			wa = frappe.get_doc("Workflow Approval","Logistics Request")
			for i in wa.workflow:
				if self.company == i.company and i.role == "Logistics User" and self.workflow_state == "Document Review":
					frappe.sendmail(
						recipients=[i.user ],
						subject = 'Logistics Request- %s is Pending for Logistics to review documents' %(self.name),
						message = """ Logistics Request - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/logistics-request/%s">Click here</a> to approve """ %(self.name,self.name)

					) 
					
		if self.workflow_state == "Payment & Customs Clearance":	
			wa = frappe.get_doc("Workflow Approval","Logistics Request")
			for i in wa.workflow:
				if self.company == i.company and i.role == "Accounts User" and self.workflow_state == "Payment & Customs Clearance":
					frappe.sendmail(
						recipients=[i.user ],
						subject = 'Logistics Request- %s is Pending for accounts to clear payments and customs' %(self.name),
						message = """ Logistics Request - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/logistics-request/%s">Click here</a> to approve """ %(self.name,self.name)

					) 

		if self.workflow_state == "Waiting for ID Submission":	
			wa = frappe.get_doc("Workflow Approval","Logistics Request")
			for i in wa.workflow:
				if self.company == i.company and i.role == "Accounts User" and self.workflow_state == "Waiting for ID Submission":
					frappe.sendmail(
						recipients=[i.user ],
						subject = 'Logistics Request- %s is Pending for accounts to submit ID' %(self.name),
						message = """ Logistics Request - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/logistics-request/%s">Click here</a> to approve """ %(self.name,self.name)

					) 

		

		if self.workflow_state == "Attach Supporting Document":	
			wa = frappe.get_doc("Workflow Approval","Logistics Request")
			for i in wa.workflow:
				if self.company == i.company and i.role == "Logistics User" and self.workflow_state == "Attach Supporting Document":
					frappe.sendmail(
						recipients=[i.user ],
						subject = 'Logistics Request- %s is Pending for Logistic user to attach documents ' %(self.name),
						message = """ Logistics Request - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/logistics-request/%s">Click here</a> to approve """ %(self.name,self.name)

					) 

		if self.workflow_state == "E-Way Bill":	
			wa = frappe.get_doc("Workflow Approval","Logistics Request")
			for i in wa.workflow:
				if self.company == i.company and i.role == "Accounts User" and self.workflow_state == "E-Way Bill":
					frappe.sendmail(
						recipients=[i.user ],
						subject = 'Logistics Request- %s is Pending for Accounts User to attach E-way bill documents' %(self.name),
						message = """ Logistics Request - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/logistics-request/%s">Click here</a> to approve """ %(self.name,self.name)

					) 

		if self.workflow_state == "Delivery":	
			wa = frappe.get_doc("Workflow Approval","Logistics Request")
			for i in wa.workflow:
				if self.company == i.company and i.role == "Logistics User" and self.workflow_state == "Delivery":
					frappe.sendmail(
						recipients=[i.user ],
						subject = 'Logistics Request- %s is Pending for Logistics User to fill delivery details' %(self.name),
						message = """ Logistics Request - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/logistics-request/%s">Click here</a> to approve """ %(self.name,self.name)

					) 

		if self.workflow_state == "Create Purchase Receipt":	
			wa = frappe.get_doc("Workflow Approval","Logistics Request")
			for i in wa.workflow:
				if self.company == i.company and i.role == "Stock User" and self.workflow_state == "Create Purchase Receipt":
					frappe.sendmail(
						recipients=[i.user ],
						subject = 'E-way bill is generated.Logistics Request- %s is Pending for Stock User to create Purchase receipt for the logistic request' %(self.name),
						message = """ Logistics Request - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/logistics-request/%s">Click here</a> to approve """ %(self.name,self.name)

					) 

				if self.company == i.company and i.role == "Logistics User" and self.workflow_state == "Create Purchase Receipt":
					frappe.sendmail(
						recipients=[i.user ],
						subject = 'E-way bill is generated.Logistics Request- %s is Pending for Stock User to create Purchase receipt for the logistic request' %(self.name),
						message = """ Logistics Request - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/logistics-request/%s">Click here</a> to approve """ %(self.name,self.name)

					) 
			
		if self.workflow_state == "Attach Bills":	
			wa = frappe.get_doc("Workflow Approval","Logistics Request")
			for i in wa.workflow:
				if self.company == i.company and i.role == "Logistics User" and self.workflow_state == "Attach Bills":
					frappe.sendmail(
						recipients=[i.user ],
						subject = 'Logistics Request- %s is Pending for logistic user to attach final bills and amount for the logistic request' %(self.name),
						message = """ Logistics Request - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/logistics-request/%s">Click here</a> to approve """ %(self.name,self.name)

					) 

		if self.workflow_state == "Accounts to Confirm":	
			wa = frappe.get_doc("Workflow Approval","Logistics Request")
			for i in wa.workflow:
				if self.company == i.company and i.role == "Accounts User" and self.workflow_state == "Accounts to Confirm":
					frappe.sendmail(
						recipients=[i.user ],
						subject = 'Logistics Request- %s is Pending for accounts user to approve the logistic request document' %(self.name),
						message = """ Logistics Request - %s is pending,waiting for your approval <a href = "https://erp.nordencommunication.com/app/logistics-request/%s">Click here</a> to approve """ %(self.name,self.name)

					) 




	@frappe.whitelist()
	def compare_po_items(self):
		if self.po_so == 'Purchase Order':
			for item in self.product_description:
				actual_qty = frappe.db.get_value('Purchase Order Item',{'parent':self.order_no,'item_code':item.item_code},'qty')
				utilized_qty = frappe.db.sql("""select `tabPurchase Order Item`.qty as qty from `tabLogistics Request`
				left join `tabPurchase Order Item` on `tabLogistics Request`.name = `tabPurchase Order Item`.parent where `tabPurchase Order Item`.item_code = '%s' and `tabLogistics Request`.name != '%s' and `tabLogistics Request`.order_no = '%s' and `tabLogistics Request`.docstatus != 2 """%(item.item_code,self.name,self.order_no),as_dict=True)
				if not utilized_qty:
					utilized_qty = 0
				else:
					utilized_qty = utilized_qty[0].qty
				remaining_qty = int(actual_qty) - utilized_qty
				if item.qty > remaining_qty:
					msg = """<table class='table table-bordered'><tr><th>Purchase Order Qty</th><td>%s</td></tr>
					<tr><th>Logistics Request Already raised for</th><td>%s</td></tr>
					<tr><th>Remaining Qty</th><td>%s</td></tr>
					</table><p><b>Requesting Qty should not go beyond Remaining Qty</b><p>"""%(actual_qty,utilized_qty,remaining_qty)
					return msg


	@frappe.whitelist()
	def pending_for_logistics(self):
		url = get_url_to_form("Logistics Request", self.name)
		frappe.sendmail(
			recipients='karthikeyan.s@groupteampro.com',
			subject=_("Logistics OPS Request"),
			header=_("Logistics OPS Request"),
			message = """<p style='font-size:18px'>Logistics OPS Request has been raised for Purchase Order - (<b>%s</b>).</p><br><br>
			<form action="%s">
			<input type="submit" value="Open Logistics Request" />
			</form>
			"""%(self.order_no,url)
		)

	@frappe.whitelist()
	def pending_for_accounts(self):
		url = get_url_to_form("Logistics Request", self.name)
		frappe.sendmail(
			recipients='karthikeyan.s@groupteampro.com',
			subject=_("Logistics OPS Request"),
			header=_("Logistics OPS Request"),
			message = """<p style='font-size:18px'>Logistics Request has been raised for Purchase Order - (<b>%s</b>).</p><br><br>
			<form action="%s">
			<input type="submit" value="Open Logistics Request" />
			</form>
			"""%(self.order_no,url)
		)

@frappe.whitelist()
def get_supporting_docs(selected_docs):
	selected_docs = json.loads(selected_docs)
	file_list = []
	for s in selected_docs:
		file_name = frappe.get_value("File", {"file_url": s['attach']},"name")
		file_list.append(file_name)
	return file_list