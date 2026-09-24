import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
	data = get_data(filters)
	columns = get_columns()
	return columns, data

def get_columns():
	return [
		_("Product") + ":Link/Item:190",
		_("Description") + ":Data:660",
		_("Stock Qty") + ":Int:120",
		_("Physical Qty") + ":Int:120",
		_("Difference") + ":Int:120",
	]
def get_data(filters):
	conditions = "WHERE docstatus < 2 AND warehouse = 'Main Stores - NCME'"
	if filters and filters.get("item"):
		conditions += " AND item = %(item)s"

	items = frappe.db.sql("""
		SELECT name
		FROM `tabItem`
		WHERE is_stock_item = 1 AND disabled = 0
	""", filters, as_dict=True)

	data = []
	ind = 0
	for item in items:
		if item:
			stock_qty = fetch_stock_qty(item["name"])
			physical_qty = fetch_physical_qty(item["name"], filters)
			if stock_qty > 0 or physical_qty > 0:
				data.append([
					item["name"],
					fetch_item_name(item["name"]),
					stock_qty,
					physical_qty,
					stock_qty - physical_qty
				])
				ind += 1
	frappe.log_error("Message", ind)
	return data

frappe.whitelist()
def fetch_item_name(item):
	doc = frappe.get_doc("Item", item)
	return doc.item_name

frappe.whitelist()
def fetch_stock_qty(item):
	stock_qty = frappe.db.get_value("Bin", {"item_code": item, "warehouse": "Main Stores - NCME"}, "actual_qty")
	return stock_qty if stock_qty else 0

def fetch_physical_qty(item_name, filters=None):
    conditions = ""
    values = [item_name]

    if filters and filters.get("stock_analysis"):
        conditions += " AND stock_analysis = %s"
        values.append(filters.get("stock_analysis"))

    result = frappe.db.sql(f"""
        SELECT SUM(physical_qty) AS p
        FROM `tabERP Stock Reconciliation Tool`
        WHERE item = %s
          AND docstatus != 2
          {conditions}
    """, tuple(values), as_dict=True)

    return result[0]["p"] or 0

