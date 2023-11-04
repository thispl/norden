# Copyright (c) 2023, Teampro and contributors
# For license information, please see license.txt

import frappe
from frappe import _
# from frappe.utils import date_diff
from datetime import datetime
from datetime import datetime
from datetime import date, timedelta
import frappe
from frappe import _
from frappe.utils import date_diff


def execute(filters=None, consolidated=False):
	data, columns = DelayedItemReport(filters).run()
	return data, columns


class DelayedItemReport(object):
	def __init__(self, filters=None):
		self.filters = frappe._dict(filters or {})

	def run(self):
		return self.get_columns(), self.get_data() or []

	def get_data(self, consolidated=False):
		doctype = self.filters.get("based_on")
		sales_order_field = "sales_order" if doctype == "Sales Invoice" else "against_sales_order"
		parent = frappe.qb.DocType(doctype)
		child = frappe.qb.DocType(f"{doctype} Item")
		query = (
			frappe.qb.from_(child)
			.from_(parent)
			.select(
				child.item_code,
				child.item_name,
				child.item_group,
				child.qty,
				child.rate,
				child.amount,
				# child[sales_order_field].as_("sales_order"),
				parent.shipping_address,
				# parent.po_no,
				parent.purchase_order_no,
				parent.supplier,
				parent.posting_date,
				parent.name,
				parent.grand_total,
			)
			.where(
				(child.parent == parent.name)
				& (parent.docstatus == 1)
				& (parent.posting_date.between(self.filters.get("from_date"), self.filters.get("to_date")))
				# & (child[sales_order_field].notnull())
				# & (child[sales_order_field] != "")
			)
		)

		
		# if doctype == "Sales Invoice":
		# 	query = query.where((parent.update_stock == 1) & (parent.is_pos == 0))
		# 	frappe.errprint(query)
	# 	if self.filters.get("item_group"):
	# 		query = query.where(child.item_group == self.filters.get("item_group"))

	# 	if self.filters.get("sales_order"):
	# 		query = query.where(child[sales_order_field] == self.filters.get("sales_order"))

		# for field in ("customer", "customer_group", "company"):
		# 	if self.filters.get(field):
		# 		query = query.where(parent[field] == self.filters.get(field))

		self.transactions = query.run(as_dict=True)
		# frappe.errprint(self.transactions)

		if self.transactions:
			self.filter_transactions_data(consolidated)

			return self.transactions

	def filter_transactions_data(self, consolidated=False):
		purchase_orders = [d.purchase_order_no for d in self.transactions]
		doctype = "Purchase Order"
		filters = {"name": ("in", purchase_orders)}

	# 	if not consolidated:
	# 		sales_order_items = [d.so_detail for d in self.transactions]
	# 		doctype = "Sales Order Item"
	# 		filters = {"parent": ("in", sales_orders), "name": ("in", sales_order_items)}

		po_data = {}
		for d in frappe.get_all(doctype, filters=filters, fields=["schedule_date", "parent", "name"]):
			key = d.name if consolidated else (d.parent, d.name)
			if key not in po_data:
				po_data.setdefault(key, d.schedule_date)
		
		frappe.errprint(self.transactions)
		for row in self.transactions:
			key = row.purchase_order_no if consolidated else (row.purchase_order_no)
			schedule_date = frappe.get_value("Purchase Order",{"name":key},["schedule_date"])
			# date = datetime.strptime(schedule_date, '%Y-%m-%d')
			# frappe.errprint(type(date))
			frappe.errprint(type(schedule_date))
			row.update(
				{
					"delivery_date": schedule_date,
					"delayed_days": date_diff(row.posting_date,schedule_date),
				}
			)
		return self.transactions

	def get_columns(self):
		based_on = self.filters.get("based_on")

		return [
			{
				"label": _(based_on),
				"fieldname": "name",
				"fieldtype": "Link",
				"options": based_on,
				"width": 100,
			},
			{
				"label": _("Supplier"),
				"fieldname": "supplier",
				"fieldtype": "Link",
				"options": "Supplier",
				"width": 200,
			},
			{
				"label": _("Shipping Address"),
				"fieldname": "shipping_address",
				"fieldtype": "Link",
				"options": "Address",
				"width": 120,
			},
			{
				"label": _("Expected Delivery Date"),
				"fieldname": "delivery_date",
				"fieldtype": "Date",
				"width": 100,
			},
			{
				"label": _("Actual Delivery Date"),
				"fieldname": "posting_date",
				"fieldtype": "Date",
				"width": 100,
			},
			{
				"label": _("Item Code"),
				"fieldname": "item_code",
				"fieldtype": "Link",
				"options": "Item",
				"width": 100,
			},
			{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 100},
			{"label": _("Quantity"), "fieldname": "qty", "fieldtype": "Float", "width": 100},
			{"label": _("Rate"), "fieldname": "rate", "fieldtype": "Currency", "width": 100},
			{"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 100},
			{"label": _("Delayed Days"), "fieldname": "delayed_days", "fieldtype": "Int", "width": 100},
			{
				"label": _("Purchase Order"),
				"fieldname": "purchase_order_no",
				"fieldtype": "Link",
				"options": "Purchase Order",
				"width": 100,
			},
			{"label": _("Customer PO"), "fieldname": "po_no", "fieldtype": "Data", "width": 100},
		]

