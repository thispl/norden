import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	columns = [
		{"label": _("Item"), "fieldtype": "Link", "options": "Item", "width": 150},
		{"label": _("Item Name"), "fieldtype": "Data", "width": 200},
	]

	
	warehouses = frappe.get_all("Warehouse", filters={"company": filters.company, "disabled": 0,"name":('!=', 'Stores - NCPL')}, pluck="name")
	for ware in warehouses:
		columns.append({
			"label": _(ware),
			"fieldtype": "Float",
			"width": 100
		})

	return columns

def get_data(filters):
	data = []

	
	items = frappe.get_all("Item", filters={"item_group": filters.item_group, "disabled": 0}, fields=["item_code", "item_name"])

	
	stock_data = frappe.db.sql("""
		SELECT
			b.item_code,
			b.warehouse,
			SUM(b.actual_qty) AS qty
		FROM `tabBin` b
		JOIN `tabWarehouse` wh ON wh.name = b.warehouse
		WHERE wh.company = %s AND wh.disabled = 0 AND b.item_code IN (%s) AND wh.name != 'Stores - NCPL'
		GROUP BY b.item_code, b.warehouse
	""" % ("%s", ",".join(["%s"] * len(items))),
		[filters.company] + [item["item_code"] for item in items],
		as_dict=True
	)


	stock_dict = {}
	for entry in stock_data:
		stock_dict.setdefault(entry.item_code, {})[entry.warehouse] = entry.qty or 0


	for item in items:
		row = [item.item_code, item.item_name]
		for ware in frappe.get_all("Warehouse", filters={"company": filters.company, "disabled": 0,"name":('!=', 'Stores - NCPL')}, pluck="name"):
			row.append(stock_dict.get(item.item_code, {}).get(ware, 0))
		data.append(row)

	return data
