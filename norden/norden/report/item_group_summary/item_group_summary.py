import frappe
from frappe import _
from frappe.utils import flt
from frappe import qb
from frappe.query_builder import Order


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "label": _("Item Group"),
            "fieldname": "item_group",
            "fieldtype": "Link",
            "options": "Item Group",
            "width": 200
        },
        {
            "label": _("Selling Amount"),
            "fieldname": "amount",
            "fieldtype": "Currency",
            "options": "currency",
            "width": 150
        },
        {
            "label": _("Cost"),
            "fieldname": "cost",
            "fieldtype": "Currency",
            "options": "currency",
            "width": 150
        },
        {
            "label": _("Gross Profit"),
            "fieldname": "gross_profit",
            "fieldtype": "Currency",
            "options": "currency",
            "width": 150
        },
        {
            "label": _("GP %"),
            "fieldname": "gp_percent",
            "fieldtype": "Percent",
            "width": 120
        },
        {
            "label": _("Currency"),
            "fieldname": "currency",
            "fieldtype": "Data",
            "hidden": 1
        }
    ]


def get_conditions(filters):
    conditions = ""

    if filters.get("from_date"):
        conditions += " AND si.posting_date >= %(from_date)s"

    if filters.get("to_date"):
        conditions += " AND si.posting_date <= %(to_date)s"

    if filters.get("company"):
        conditions += " AND si.company = %(company)s"

    if filters.get("item_group"):
        conditions += " AND sii.item_group = %(item_group)s"

    return conditions


def get_data(filters):
    conditions = get_conditions(filters)

    company = filters.get("company") or frappe.defaults.get_user_default("Company")
    company_currency = frappe.get_cached_value("Company", company, "default_currency")

    items = frappe.db.sql(f"""
        SELECT
            sii.name,
            sii.parent,
            sii.item_code,
            sii.item_group,
            sii.qty,
            sii.base_net_amount,
            sii.warehouse,
            sii.delivery_note,
            sii.dn_detail,
            si.company,
            si.update_stock
        FROM `tabSales Invoice Item` sii
        JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE si.docstatus = 1 {conditions}
    """, filters, as_dict=1)

    grouped_data = {}

    for i in items:
        item_sub_group = frappe.db.get_value("Item",{'name':i.item_code},['item_sub_group'])
        base_cost = 0
        landing_cost = 0

        landing_per = frappe.db.get_value(
            "Margin Dubai",
            {"item_group": item_sub_group},
            "landing"
        ) or 0

        if i.delivery_note:
            base_cost = calculate_buying_amount_from_sle(
                i.company, i.item_code, i.warehouse,
                i.delivery_note, i.dn_detail, i.qty
            )

        elif i.update_stock:
            base_cost = calculate_buying_amount_from_sle_si(
                i.company, i.item_code, i.warehouse,
                i.parent, i.name, i.qty
            )

        else:
            valuation_rate = frappe.db.sql("""
                SELECT incoming_rate
                FROM `tabStock Ledger Entry`
                WHERE item_code = %s
                AND voucher_no = %s
                ORDER BY creation DESC
                LIMIT 1
            """, (i.item_code, i.parent), as_list=True)

            if valuation_rate:
                base_cost = flt(valuation_rate[0][0]) * i.qty

        landing_cost = base_cost * landing_per

        if filters.get("cost_type") == "Landing Cost":
            cost = landing_cost
        else:
            cost = base_cost

        if i.item_group not in grouped_data:
            grouped_data[i.item_group] = {
                "item_group": i.item_group,
                "amount": 0,
                "cost": 0
            }

        grouped_data[i.item_group]["amount"] += flt(i.base_net_amount)
        grouped_data[i.item_group]["cost"] += flt(cost)

    result = []
    for g in grouped_data.values():
        gross_profit = g["amount"] - g["cost"]
        gp_percent = (gross_profit / g["amount"] * 100) if g["amount"] else 0

        result.append({
            "item_group": g["item_group"],
            "amount": g["amount"],
            "cost": g["cost"],
            "gross_profit": gross_profit,
            "gp_percent": round(gp_percent, 3),
            "currency": company_currency
        })

    return result



@frappe.whitelist()
def calculate_buying_amount_from_sle(company, item_code, warehouse, delivery_note, dn_detail,qty):
		res = []
		if item_code and warehouse:
			sle = qb.DocType("Stock Ledger Entry")
			res = (
				qb.from_(sle)
				.select(
					sle.item_code,
					sle.voucher_type,
					sle.voucher_no,
					sle.voucher_detail_no,
					sle.stock_value,
					sle.warehouse,
					sle.actual_qty.as_("qty"),
				)
				.where(
					(sle.company == company)
					& (sle.item_code == item_code)
					& (sle.warehouse == warehouse)
					& (sle.is_cancelled == 0)
				)
				.orderby(sle.item_code)
				.orderby(sle.warehouse, sle.posting_date, sle.posting_time, sle.creation, order=Order.desc)
				.run(as_dict=True)
			)
		for i, sle in enumerate(res):
			if (
				sle.voucher_type == "Delivery Note"
				and sle.voucher_no == delivery_note
				and sle.voucher_detail_no == dn_detail
			):
				previous_stock_value = len(res) > i + 1 and flt(res[i + 1].stock_value) or 0.0

				if previous_stock_value:
					return abs(previous_stock_value - flt(sle.stock_value)) * flt(qty) / abs(flt(sle.qty))
		return 0.0

@frappe.whitelist()
def calculate_buying_amount_from_sle_si(company, item_code, warehouse, name, si_name,qty):
		res = []
		if item_code and warehouse:
			sle = qb.DocType("Stock Ledger Entry")
			res = (
				qb.from_(sle)
				.select(
					sle.item_code,
					sle.voucher_type,
					sle.voucher_no,
					sle.voucher_detail_no,
					sle.stock_value,
					sle.warehouse,
					sle.actual_qty.as_("qty"),
				)
				.where(
					(sle.company == company)
					& (sle.item_code == item_code)
					& (sle.warehouse == warehouse)
					& (sle.is_cancelled == 0)
				)
				.orderby(sle.item_code)
				.orderby(sle.warehouse, sle.posting_date, sle.posting_time, sle.creation, order=Order.desc)
				.run(as_dict=True)
			)
		for i, sle in enumerate(res):
			if (
				sle.voucher_type == "Sales Invoice"
				and sle.voucher_no == name
				and sle.voucher_detail_no == si_name
			):
				previous_stock_value = len(res) > i + 1 and flt(res[i + 1].stock_value) or 0.0

				if previous_stock_value:
					return abs(previous_stock_value - flt(sle.stock_value)) * flt(qty) / abs(flt(sle.qty))
		return 0.0