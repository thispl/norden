import frappe
from frappe.utils import today, formatdate


@frappe.whitelist()
def so_details(from_date=None, to_date=None):
    from_date = from_date or today()
    to_date = to_date or today()
    
    data = frappe.db.sql("""
                         SELECT sales_person_user , SUM(base_grand_total) AS value
                         FROM `tabSales Order`
                         WHERE company = "Norden Communication Middle East FZE"
                         AND transaction_date BETWEEN %s AND %s 
                         AND docstatus = 1 
                         AND status != "Closed"
                         GROUP BY sales_person_user
                         
                         """,[from_date,to_date], as_dict=True)
    
    return data



@frappe.whitelist()
def si_details(from_date=None, to_date=None):
    from_date = from_date or today()
    to_date = to_date or today()
    
    data = frappe.db.sql("""
        SELECT 
            si.sales_person_user, SUM(si.base_grand_total) AS value
        FROM `tabSales Invoice` si
        LEFT JOIN `tabSales Order` so 
            ON si.so_no = so.name
        WHERE 
            si.company = %s
            AND si.posting_date BETWEEN %s AND %s
            AND si.docstatus = 1
            AND (so.status IS NULL OR so.status != "Closed")
        GROUP BY si.sales_person_user
    """, ["Norden Communication Middle East FZE", from_date, to_date], as_dict=True)
    
    return data