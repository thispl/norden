import frappe
from frappe import _
from frappe.utils import flt, today, add_days, nowdate
from erpnext.stock.stock_balance import get_balance_qty_from_sle


def get_context(context):
    """Page context — permissions check."""
    if not frappe.has_permission("Stock Ledger Entry", "read"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)


@frappe.whitelist()
def get_inventory_data_old():
    data = frappe.db.sql(
        """
        SELECT
            b.item_code,
            i.item_name,
            i.stock_uom,
            i.item_group,
            b.warehouse,
            COALESCE(b.actual_qty, 0) AS actual_qty,
            COALESCE(b.valuation_rate, 0) AS valuation_rate,
            COALESCE(b.actual_qty, 0) * COALESCE(b.valuation_rate, 0) AS value
        FROM
            `tabBin` b
            JOIN `tabItem` i ON i.name = b.item_code
            JOIN `tabWarehouse` wh ON wh.name = b.warehouse
            JOIN `tabItem Group` ig ON ig.name = i.item_group
        WHERE
            i.disabled = 0
            AND wh.disabled = 0
            AND wh.company = 'Norden Communication Pvt Ltd'
        ORDER BY
            i.item_group,
            i.item_name,
            b.warehouse
        """,
        as_dict=True,
    )
    return data


# @frappe.whitelist()
# def get_inventory_data(company=None, warehouse=None):

#     conditions = ["sle.is_cancelled = 0"]
#     values = {"to_date": nowdate()}

#     if company:
#         conditions.append("wh.company = %(company)s")
#         values["company"] = company

#     if warehouse:
#         conditions.append("sle.warehouse = %(warehouse)s")
#         values["warehouse"] = warehouse

#     data = frappe.db.sql(
#         f"""
#         SELECT
#             sle.item_code,
#             i.item_name,
#             i.stock_uom,
#             i.item_group,
#             sle.warehouse,
#             wh.company,

#             SUM(sle.actual_qty) AS actual_qty,

#             (
#                 SELECT sle2.valuation_rate
#                 FROM `tabStock Ledger Entry` sle2
#                 WHERE
#                     sle2.item_code = sle.item_code
#                     AND sle2.warehouse = sle.warehouse
#                     AND sle2.is_cancelled = 0
#                     AND sle2.posting_date <= %(to_date)s
#                 ORDER BY sle2.posting_date DESC,
#                          sle2.posting_time DESC,
#                          sle2.creation DESC
#                 LIMIT 1
#             ) AS valuation_rate

#         FROM `tabStock Ledger Entry` sle

#         INNER JOIN `tabItem` i
#             ON i.name = sle.item_code
            

#         INNER JOIN `tabWarehouse` wh
#             ON wh.name = sle.warehouse

#         WHERE
#             sle.posting_date <= %(to_date)s
#             AND {" AND ".join(conditions)}

#         GROUP BY
#             sle.item_code,
#             sle.warehouse

#         ORDER BY
#             sle.posting_date
            
#         """,
#         values,
#         as_dict=True,
#     )

#     # compute stock value
#     result = []
#     for row in data:
#         row.actual_qty = flt(row.actual_qty)

#         if row.actual_qty != 0:
#             row.stock_value = row.actual_qty * flt(row.valuation_rate)
#             result.append(row)

#     return result    

import frappe
from frappe.utils import nowdate, flt
from collections import defaultdict


@frappe.whitelist()
def get_inventory_data(company=None, warehouse=None):

    conditions = ["sle.is_cancelled = 0"]
    values = {"to_date": nowdate()}

    if company:
        conditions.append("sle.company = %(company)s")
        values["company"] = company

    if warehouse:
        conditions.append("sle.warehouse = %(warehouse)s")
        values["warehouse"] = warehouse

    sle_entries = frappe.db.sql(
        f"""
        SELECT
            sle.item_code,
            sle.warehouse,
            sle.company,
            sle.posting_date,
            sle.actual_qty,
            sle.qty_after_transaction,
            sle.stock_value_difference,
            sle.valuation_rate,
            sle.voucher_type,
            sle.batch_no,
            sle.serial_no,

            item.item_name,
            item.item_group,
            item.stock_uom

        FROM `tabStock Ledger Entry` sle
        INNER JOIN `tabItem` item
            ON item.name = sle.item_code

        WHERE
            {" AND ".join(conditions)}
            AND sle.posting_date <= %(to_date)s
            AND sle.warehouse != 'Stores - NCPL'

        ORDER BY
            sle.item_code,
            sle.warehouse,
            sle.posting_date,
            sle.posting_time,
            sle.creation
        """,
        values,
        as_dict=1,
    )

    item_warehouse_map = {}

    for entry in sle_entries:

        key = (entry.company, entry.item_code, entry.warehouse)

        if key not in item_warehouse_map:
            item_warehouse_map[key] = {
                "item_code": entry.item_code,
                "item_name": entry.item_name,
                "item_group": entry.item_group,
                "stock_uom": entry.stock_uom,
                "warehouse": entry.warehouse,
                "company": entry.company,
                "actual_qty": 0,
                "stock_value": 0,
                "valuation_rate": 0,
            }

        row = item_warehouse_map[key]

        # Same logic used in Stock Balance Report
        if (
            entry.voucher_type == "Stock Reconciliation"
            and (not entry.batch_no or entry.serial_no)
        ):
            qty_diff = flt(entry.qty_after_transaction) - flt(row["actual_qty"])
        else:
            qty_diff = flt(entry.actual_qty)

        row["actual_qty"] += qty_diff
        row["stock_value"] += flt(entry.stock_value_difference)
        row["valuation_rate"] = flt(entry.valuation_rate)

    result = []

    for row in item_warehouse_map.values():

        if flt(row["actual_qty"]) == 0:
            continue

        # Stock Balance report final valuation
        row["stock_value"] = row["actual_qty"] * row["valuation_rate"]

        result.append(row)

    return result


# ── Warehouse Performance KPIs ─────────────────────────────────────────────────
@frappe.whitelist()
def get_warehouse_performance(
    custom_picking_start_time=None,
    custom_picking_end_time=None
):
    previous_day = add_days(today(), -1)

    # Total Orders
    total_submitted_orders = frappe.db.count(
        "Sales Order",
        filters={
            "docstatus": 1,
        },
    )

    # today_submitted_orders
    today_submitted_orders = frappe.db.count(
        "Sales Order",
        filters={
            "docstatus": 1,
            "transaction_date": previous_day,
        },
    )

    picking_accuracy = (
        round((today_submitted_orders / total_submitted_orders) * 100, 2)
        if total_submitted_orders else 0
    )

    # Order Fulfillment Rate
    invoiced_orders = frappe.db.sql("""
    SELECT COUNT(DISTINCT so.name)
    FROM `tabSales Order` so
    INNER JOIN `tabSales Invoice Item` sii
        ON sii.sales_order = so.name
    INNER JOIN `tabSales Invoice` si
        ON si.name = sii.parent
       AND si.docstatus = 1
    WHERE so.docstatus = 1
      AND so.transaction_date = %(prev_day)s
""", {
    "prev_day": previous_day
})[0][0] or 0

    fulfillment_rate = (
        round((invoiced_orders / total_submitted_orders) * 100, 2)
        if total_submitted_orders else 0
    )

    # Avg Picking Time using passed values

    previous_day = add_days(today(), -1)

    avg_picking_time = frappe.db.sql("""
        SELECT AVG(
            TIMESTAMPDIFF(
                MINUTE,
                custom_picking_start_time,
                custom_picking_end_time
            )
        ) AS avg_minutes
        FROM `tabSales Order`
        WHERE docstatus = 1
        AND transaction_date = %(prev_day)s
        AND custom_picking_start_time IS NOT NULL
        AND custom_picking_end_time IS NOT NULL
    """, {
        "prev_day": previous_day
    })[0][0]

    avg_picking_time = round(float(avg_picking_time), 1) if avg_picking_time else 0

    return {
        "picking_accuracy": picking_accuracy,
        "fulfillment_rate": fulfillment_rate,
        "avg_picking_time": avg_picking_time,
    }


# ── Order Management ───────────────────────────────────────────────────────────
@frappe.whitelist()
def get_order_management():
    previous_day = add_days(today(), -1)

    # Orders Received Today — Sales Orders created on previous date
    orders_received = frappe.db.count(
        "Sales Order",
        filters={
            "workflow_state": "Draft",
            "transaction_date": previous_day,
        },
    )
    # Orders Processed — Sales Orders from previous date that have a linked
    # Sales Invoice posted on the same previous date
    orders_processed = frappe.db.count(
        "Sales Order",
        filters={
            "docstatus": "1",
            "transaction_date": previous_day,
            "status":["in",["Completed"]]
        },
    )
    # orders_processed = frappe.db.sql(
    #     """
    #     SELECT COUNT(DISTINCT so.name)
    #     FROM `tabSales Order` so
    #     INNER JOIN `tabSales Invoice Item` sii
    #         ON sii.sales_order = so.name
    #     INNER JOIN `tabSales Invoice` si
    #         ON si.name = sii.parent
    #        AND si.docstatus = 1
    #        AND DATE(si.posting_date) = %(prev_day)s
    #     WHERE
    #         so.docstatus = 1
    #         AND so.transaction_date = %(prev_day)s
    #     """,
    #     {"prev_day": previous_day},
    # )[0][0] or 0

    # Pending for QC — distinct Sales Orders from previous date that have a
    # linked Purchase Order whose set_warehouse contains 'Pending for QC'
    pending_qc = frappe.db.sql(
        """
        SELECT COUNT(DISTINCT poi.sales_order)
        FROM `tabPurchase Order Item` poi
        INNER JOIN `tabPurchase Order` po
            ON po.name = poi.parent
           AND po.docstatus = 1
        INNER JOIN `tabSales Order` so
            ON so.name = poi.sales_order
           AND so.docstatus = 1
           AND so.transaction_date = %(prev_day)s
        WHERE
            po.set_warehouse LIKE '%%Pending for QC%%'
        """,
        {"prev_day": previous_day},
    )[0][0] or 0

    # Orders Pending — derived value, floored at 0
    orders_pending = max(orders_received - orders_processed - pending_qc, 0)

    return {
        "orders_received": orders_received,
        "orders_processed": orders_processed,
        "pending_qc": pending_qc,
        "orders_pending": orders_pending,
    }


from frappe.utils import today
@frappe.whitelist()
def get_inbound_data():
    total_shipments_received = frappe.db.sql("""
        SELECT COALESCE(SUM(po.total_qty), 0)
        FROM `tabPurchase Order` po
        WHERE po.docstatus = 1
          AND po.transaction_date = %s
    """, (today(),))[0][0]

    

   
    # Orders Processed — Sales Orders from previous date that have a linked
    # Sales Invoice posted on the same previous date

    grn_pending = frappe.db.sql("""
    SELECT COALESCE(SUM(poi.qty), 0)
    FROM `tabPurchase Order Item` poi
    INNER JOIN `tabPurchase Order` po
        ON po.name = poi.parent
    WHERE po.docstatus = 1
      AND po.transaction_date = %s
      AND poi.received_qty = 0
""", (today(),))[0][0]
    

    pending_for_qc = frappe.db.sql("""
        SELECT COALESCE(SUM(poi.qty), 0)
        FROM `tabPurchase Order Item` poi
        INNER JOIN `tabPurchase Order` po
            ON po.name = poi.parent
        AND po.docstatus = 1
        INNER JOIN `tabSales Order` so
            ON so.name = poi.sales_order
        AND so.docstatus = 1
        WHERE po.transaction_date = %(today)s
        AND po.set_warehouse LIKE '%%Pending for QC%%'
    """, {
        "today": today()
    })[0][0]
    # pending_for_qc = frappe.db.sql("""
    #     SELECT COALESCE(SUM(poi.qty), 0)
    #     FROM `tabPurchase Order Item` poi
    #     INNER JOIN `tabPurchase Order` po
    #         ON po.name = poi.parent
    #     WHERE po.docstatus = 1
    #     AND po.transaction_date = %(today)s
    #     AND po.set_warehouse LIKE '%%Pending for QC%%'
    # """, {
    #     "today": previous_day
    # })[0][0]
    data = {
        "total_shipments_received": total_shipments_received,
        "grn_pending": grn_pending,
        "pending_for_qc": pending_for_qc,
    }
    return data
    


@frappe.whitelist()
def get_mrb_stock():
    previous_day = add_days(today(), -1)

    total_stock_sku_wise = frappe.db.sql("""
        SELECT COALESCE(SUM(sle.actual_qty), 0)
        FROM `tabStock Ledger Entry` sle
        WHERE sle.is_cancelled = 0
          AND sle.warehouse LIKE '%%MRB%%'
          AND sle.posting_date <= %(prev_day)s
    """, {
        "prev_day": previous_day
    })[0][0]
    return total_stock_sku_wise


@frappe.whitelist()
def get_dead_stock():
    previous_day = add_days(today(), -1)

    items = frappe.db.sql("""
        SELECT
            sle.warehouse,
            sle.item_code,
            MAX(sle.posting_date) AS last_movement_date
        FROM `tabStock Ledger Entry` sle
        INNER JOIN `tabItem` i
            ON i.name = sle.item_code
           AND i.disabled = 0
        WHERE
            sle.is_cancelled = 0
        GROUP BY
            sle.warehouse,
            sle.item_code
        HAVING
            MAX(sle.posting_date) <= DATE_SUB(%(prev_day)s, INTERVAL 180 DAY)
        ORDER BY
            sle.warehouse,
            sle.item_code
    """, {
        "prev_day": previous_day
    }, as_dict=True)

    data = []

    for row in items:
        qty = get_balance_qty_from_sle(
            row.item_code,
            row.warehouse
        )

        if qty > 0:
            data.append({
                "warehouse": row.warehouse,
                "item_code": row.item_code,
                "qty": qty,
                "last_movement_date": row.last_movement_date
            })

    return data