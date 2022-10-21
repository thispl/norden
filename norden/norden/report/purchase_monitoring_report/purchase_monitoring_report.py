# Copyright (c) 2013, Teampro and contributors
# For license information, please see license.txt

import frappe
from frappe import msgprint, _


def execute(filters=None):
	columns, data = [], []
	row = []
	columns = get_columns()
	purchase_orders = frappe.get_all('Purchase Order',['*'])
	for po in purchase_orders:
		row = [
			po.name,po.transaction_date,po.supplier,po.company,
			po.name,po.consignment_type,po.proforma_invoice,
			po.cargo_type,po.item_group,po.currency,po.total,po.payment_status,
			po.production_finish,po.shipment_departure_date,po.doc_,
			po.shipment_arrival_date,po.goods_receipt,po.purchase_entry_no,
			po.purchase_entry_date,po.completed_status,po.remarks,
			]
		data.append(row)
	return columns, data

def get_columns():
	columns = []
	columns += [
		_('PO NO') + ':Link/Purchase Order:120',
		_('Date') + ':Date/:120',
		_('Supplier') + ':Link/Supplier:120',_('Company') + ':Link/Company:120',
		_('PRQ') + ':Link/Material Request:120',_('Proj/Stock') + ':Data:120',
		_('PL') + ':Data:120',_('ShipmentType') + ':Data:120',_('Category') + ':Link/Item Group:120',
		_('Currency') + ':Data:120',_('PO Value') + ':Data:120',
		_('Payment Status') + ':Data:120',_('Production Finish') + ':Date:120',
		_('Shipment Departure Date') + ':Date:120',_('Doc') + ':Data:120',
		_('Shipment Arrival Date') + ':Date:120',_('Goods Receipt') + ':Data:120',
		_('Purchase Entry No') + ':Data:120',_('Purchase Entry Date') + ':Date:120',
		_('Completed Status') + ':Data:120',_('Remarks') + ':Data:120'

		]
	return columns

