# Copyright (c) 2021, Teampro and contributors
# For license information, please see license.txt

import frappe
from frappe import throw, _, scrub
from frappe.model.document import Document
from frappe.utils import get_url_to_form, today, add_days, nowdate

class LogisticsRequest(Document):
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