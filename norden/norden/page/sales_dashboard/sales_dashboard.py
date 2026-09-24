import frappe
from frappe.utils import today, formatdate

def build_date_range_text(from_date, to_date):
    if from_date and to_date:
        if from_date == to_date:
            return formatdate(from_date)
        return f"{formatdate(from_date)} to {formatdate(to_date)}"
    elif from_date:
        return f"From {formatdate(from_date)}"
    elif to_date:
        return f"Up to {formatdate(to_date)}"
    else:
        return formatdate(today())

@frappe.whitelist()
def get_sales_dashboard_data(from_date=None, to_date=None):
    from_date = from_date or today()
    to_date = to_date or today()
    companies = ["Norden Communication UK Limited","Norden Communication Middle East FZE"]

    # Submitted invoices - sales person & company wise
    invoices_by_sp = frappe.db.sql("""
        SELECT sp.sales_person, si.company,
               COUNT(si.name) AS count,
               SUM(si.base_grand_total) AS value,
               si.posting_date AS date
        FROM `tabSales Invoice` si
        LEFT JOIN `tabSales Team` sp ON sp.parent = si.name
        WHERE si.posting_date BETWEEN %s AND %s
          AND si.company in ({company_placeholders})
          AND si.docstatus = 1
        GROUP BY si.posting_date, sp.sales_person, si.company
        ORDER BY si.posting_date, sp.sales_person, si.company
    """.format(company_placeholders=",".join(["%s"]*len(companies))),
    tuple([from_date, to_date] + companies), as_dict=True)

    # Submitted invoices - date & company wise
    invoices_by_date = frappe.db.sql("""
        SELECT si.posting_date AS date, si.company,
               COUNT(si.name) AS count,
               SUM(si.base_grand_total) AS value
        FROM `tabSales Invoice` si
        WHERE si.posting_date BETWEEN %s AND %s
          AND si.company in ({company_placeholders})
          AND si.docstatus = 1
        GROUP BY si.posting_date, si.company
        ORDER BY si.posting_date, si.company
    """.format(company_placeholders=",".join(["%s"]*len(companies))),
    tuple([from_date, to_date] + companies), as_dict=True)

    total_count = sum(r.count for r in invoices_by_date)
    total_value = sum(r.value for r in invoices_by_date)

    # Cancelled invoices - sales person & company wise
    cancelled_by_sp = frappe.db.sql("""
        SELECT sp.sales_person, si.company,
               COUNT(si.name) AS count,
               SUM(si.base_grand_total) AS value,
               si.posting_date AS date
        FROM `tabSales Invoice` si
        LEFT JOIN `tabSales Team` sp ON sp.parent = si.name
        WHERE si.posting_date BETWEEN %s AND %s
          AND si.company in ({company_placeholders})
          AND (si.docstatus = 2 OR si.return_against IS NOT NULL)
        GROUP BY si.posting_date, sp.sales_person, si.company
        ORDER BY si.posting_date, sp.sales_person, si.company
    """.format(company_placeholders=",".join(["%s"]*len(companies))),
    tuple([from_date, to_date] + companies), as_dict=True)

    # Cancelled invoices - date & company wise
    cancelled_by_date = frappe.db.sql("""
        SELECT si.posting_date AS date, si.company,
               COUNT(si.name) AS count,
               SUM(si.base_grand_total) AS value
        FROM `tabSales Invoice` si
        WHERE si.posting_date BETWEEN %s AND %s
          AND si.company in ({company_placeholders})
          AND (si.docstatus = 2 OR si.return_against IS NOT NULL)
        GROUP BY si.posting_date, si.company
        ORDER BY si.posting_date, si.company
    """.format(company_placeholders=",".join(["%s"]*len(companies))),
    tuple([from_date, to_date] + companies), as_dict=True)

    cancel_count = sum(r.count for r in cancelled_by_date)
    cancel_value = sum(r.value for r in cancelled_by_date)

    # Fetch company currencies
    company_currency = {c.name: c.default_currency for c in frappe.get_all("Company", fields=["name", "default_currency"])}

    # Add currency to each row
    for row in invoices_by_date + invoices_by_sp + cancelled_by_date + cancelled_by_sp:
        row.currency = company_currency.get(row.company)

    return {
        "date_range": build_date_range_text(from_date, to_date),
        "invoices": {
            "total_count": total_count,
            "total_value": total_value,
            "by_date": invoices_by_date,
            "sales_person": invoices_by_sp,
            "cancelled_by_date": cancelled_by_date,
            "cancelled_by_sp": cancelled_by_sp,
            "cancel_total_count": cancel_count,
            "cancel_total_value": cancel_value
        }
    }

@frappe.whitelist()
def get_so_dashboard_data(from_date=None, to_date=None):
    from_date = from_date or today()
    to_date = to_date or today()
    companies = ["Norden Communication UK Limited","Norden Communication Middle East FZE"]

    # Submitted Sales Orders - sales person & company wise
    orders_by_sp = frappe.db.sql("""
        SELECT sp.sales_person, so.company,
               COUNT(so.name) AS count,
               SUM(so.base_grand_total) AS value,
               so.transaction_date AS date
        FROM `tabSales Order` so
        LEFT JOIN `tabSales Team` sp ON sp.parent = so.name
        WHERE so.transaction_date BETWEEN %s AND %s
          AND so.company in ({company_placeholders})
          AND so.docstatus = 1
        GROUP BY so.transaction_date, sp.sales_person, so.company
        ORDER BY so.transaction_date, sp.sales_person, so.company
    """.format(company_placeholders=",".join(["%s"]*len(companies))),
    tuple([from_date, to_date] + companies), as_dict=True)

    # Submitted Sales Orders - date & company wise
    orders_by_date = frappe.db.sql("""
        SELECT so.transaction_date AS date, so.company,
               COUNT(so.name) AS count,
               SUM(so.base_grand_total) AS value
        FROM `tabSales Order` so
        WHERE so.transaction_date BETWEEN %s AND %s
          AND so.company in ({company_placeholders})
          AND so.docstatus = 1
        GROUP BY so.transaction_date, so.company
        ORDER BY so.transaction_date, so.company
    """.format(company_placeholders=",".join(["%s"]*len(companies))),
    tuple([from_date, to_date] + companies), as_dict=True)

    total_count = sum(r.count for r in orders_by_date)
    total_value = sum(r.value for r in orders_by_date)

    # Cancelled Sales Orders - sales person & company wise
    cancelled_by_sp = frappe.db.sql("""
        SELECT sp.sales_person, so.company,
               COUNT(so.name) AS count,
               SUM(so.base_grand_total) AS value,
               so.transaction_date AS date
        FROM `tabSales Order` so
        LEFT JOIN `tabSales Team` sp ON sp.parent = so.name
        WHERE so.transaction_date BETWEEN %s AND %s
          AND so.company in ({company_placeholders})
          AND so.docstatus = 2
        GROUP BY so.transaction_date, sp.sales_person, so.company
        ORDER BY so.transaction_date, sp.sales_person, so.company
    """.format(company_placeholders=",".join(["%s"]*len(companies))),
    tuple([from_date, to_date] + companies), as_dict=True)

    # Cancelled Sales Orders - date & company wise
    cancelled_by_date = frappe.db.sql("""
        SELECT so.transaction_date AS date, so.company,
               COUNT(so.name) AS count,
               SUM(so.base_grand_total) AS value
        FROM `tabSales Order` so
        WHERE so.transaction_date BETWEEN %s AND %s
          AND so.company in ({company_placeholders})
          AND so.docstatus = 2
        GROUP BY so.transaction_date, so.company
        ORDER BY so.transaction_date, so.company
    """.format(company_placeholders=",".join(["%s"]*len(companies))),
    tuple([from_date, to_date] + companies), as_dict=True)

    cancel_count = sum(r.count for r in cancelled_by_date)
    cancel_value = sum(r.value for r in cancelled_by_date)

    # Fetch company currencies
    company_currency = {c.name: c.default_currency for c in frappe.get_all("Company", fields=["name", "default_currency"])}

    # Add currency to each row
    for row in orders_by_date + orders_by_sp + cancelled_by_date + cancelled_by_sp:
        row.currency = company_currency.get(row.company)

    return {
        "date_range": build_date_range_text(from_date, to_date),
        "orders": {
            "total_count": total_count,
            "total_value": total_value,
            "by_date": orders_by_date,
            "sales_person": orders_by_sp,
            "cancelled_by_date": cancelled_by_date,
            "cancelled_by_sp": cancelled_by_sp,
            "cancel_total_count": cancel_count,
            "cancel_total_value": cancel_value
        }
    }
