# Copyright (c) 2021, Teampro and contributors
# For license information, please see license.txt

import frappe
from frappe import throw, _, scrub
from frappe.model.document import Document
from erpnext.setup.utils import get_exchange_rate
from frappe.utils import get_url_to_form, today, add_days, nowdate, flt, getdate
from frappe.core.api.file import zip_files
import json
from frappe.model.mapper import get_mapped_doc

class LogisticsRequest(Document):
	def validate(self):
		total = 0
		for row in self.product_description:
			total += row.amount
		self.grand_total = total
		

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
			multiple_pos_list = [po.strip() for po in self.multiple_pos.split(',')] if self.multiple_pos else []
			net_weight = 0
			gross_weight = 0
			for item in self.product_description:
				if multiple_pos_list:
					actual_qty = frappe.db.get_value('Purchase Order Item',{'parent':('in',multiple_pos_list),'item_code':item.item_code,'material_request':item.material_request},'qty')
					utilized_qty = frappe.db.sql("""select `tabPurchase Order Item`.qty as qty from `tabLogistics Request`
					left join `tabPurchase Order Item` on `tabLogistics Request`.name = `tabPurchase Order Item`.parent where `tabPurchase Order Item`.material_request = '%s' and `tabPurchase Order Item`.item_code = '%s' and `tabLogistics Request`.name != '%s' and `tabPurchase Order Item`.parent = '%s' and `tabLogistics Request`.docstatus != 2 """%(item.material_request,item.item_code,self.name,item.parent),as_dict=True)
				else:
					actual_qty = frappe.db.get_value('Purchase Order Item',{'parent':self.order_no,'item_code':item.item_code,'material_request':item.material_request},'qty')
					utilized_qty = frappe.db.sql("""select `tabPurchase Order Item`.qty as qty from `tabLogistics Request`
					left join `tabPurchase Order Item` on `tabLogistics Request`.name = `tabPurchase Order Item`.parent where `tabPurchase Order Item`.material_request = '%s' and `tabPurchase Order Item`.item_code = '%s' and `tabLogistics Request`.name != '%s' and `tabLogistics Request`.order_no = '%s' and `tabLogistics Request`.docstatus != 2 """%(item.material_request,item.item_code,self.name,self.order_no),as_dict=True)
				
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
	def update_gross_net(self):
		net_weight = 0
		gross_weight = 0
		for item in self.product_description:
			nw, gw = frappe.db.get_value("Item",{'name':item.item_code},['nw','gw'])
			net_weight += (nw*item.qty)
			gross_weight += (gw*item.qty)
		self.net_wt = net_weight
		self.gross_wt = gross_weight

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

@frappe.whitelist()
def make_purchase_order(source_name, target_doc=None, args=None):
	pos=[]
	if args is None:
		args = {}
	if isinstance(args, str):
		args = json.loads(args)

	def postprocess(source, target_doc):
		
		if frappe.flags.args and frappe.flags.args.default_supplier:
			# items only for given default supplier
			supplier_items = []
			for d in target_doc.items:
				default_supplier = get_item_defaults(d.item_code, target_doc.company).get("default_supplier")
				if frappe.flags.args.default_supplier == default_supplier:
					supplier_items.append(d)
			target_doc.items = supplier_items
		
		target_doc.logistic_type='Import'
		target_doc.po_so='Purchase Order'
		if target_doc.multiple_pos:
			# If there are already values, append a separator (comma, for example)
			target_doc.multiple_pos += ", " + source.name
		else:
			# If no values, just set it to the first PO name
			target_doc.multiple_pos = source.name

	def select_item(d):
		filtered_items = args.get("filtered_children", [])
		child_filter = d.name in filtered_items if filtered_items else True

		return d.ordered_qty < d.stock_qty and child_filter
	# current_date = datetime.strptime(nowdate(), "%Y-%m-%d").date()
	# frappe.errprint(type(current_date))
	doclist = get_mapped_doc(
		"Purchase Order",
		source_name,
		{
			"Purchase Order": {
				"doctype": "Purchase Order",
				"validation": {"docstatus": ["=", 1]},
			},
			"Purchase Order Item": {
				"doctype": "Purchase Order Item",
				"field_map": [
					["name", "purchase_order_item"],
					["parent", "purchase_order"],
					["uom", "stock_uom"],
					["uom", "uom"],
					["sales_order", "sales_order"],
					["sales_order_item", "sales_order_item"],
					["wip_composite_asset", "wip_composite_asset"],
					["material_request", "material_request"],
					["material_request_item", "material_request_item"],
					['schedule_date','schedule_date']
				],
				"postprocess": update_item,
				"condition": select_item,
			},
		},
		target_doc,
		postprocess,
	)

	return doclist

def update_item(obj, target, source_parent):
	target.conversion_factor = obj.conversion_factor
	target.qty = flt(flt(obj.stock_qty) - flt(obj.ordered_qty)) / target.conversion_factor
	target.stock_qty = target.qty * target.conversion_factor
	if getdate(target.schedule_date) < getdate(nowdate()):
		target.schedule_date = getdate(nowdate())