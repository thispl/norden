import frappe
from frappe import _
from frappe.utils import flt
import erpnext

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    columns = [
        {
            "label": _("Item"),
            "fieldname": "item",
            "fieldtype": "Link",
            "options": "Item",
        },
        {
            "label": _("Company"),
            "fieldname": "company",
            "fieldtype": "Link",
            "options": "Company",
            "hidden":1
        },
        {
            "label": _("Item Name"),
            "fieldname": "item_name",
            "fieldtype": "Data",
        },
        {
            "label": _("Total Qty"),
            "fieldname": "total_qty",
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "label": _("Reserved Qty"),
            "fieldname": "reserved_qty",
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "label": _("Free Qty"),
            "fieldname": "free_qty",
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "label": _("Non Sale Qty"),
            "fieldname": "non_sale_qty",
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "label": _("Demo Qty"),
            "fieldname": "demo_qty",
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "label": _("PO Qty"),
            "fieldname": "po_qty",
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "label": _("SO Pending Qty"),
            "fieldname": "so_qty",
            "fieldtype": "Data",
            "width": 160,
        },
        {
            "label": _("Unit"),
            "fieldname": "unit",
            "fieldtype": "Data",
            "width": 130,
        },

    ]
    
    return columns

def get_data(filters):
    date = frappe.db.get_value("Custom Settings","Custom Settings","date")
    data = []
    if filters.item:
        item = frappe.get_all("Item",{"name":filters.item},["*"])

    if filters.like:
        like_filter = "%"+filters.like+"%"
        item = frappe.get_all("Item",{"name":["like",like_filter]},["*"])
    for i in item:
        # stocks = frappe.db.sql("""select (sum(`tabBin`.actual_qty) - sum(reserved_stock)) as actual_qty from `tabBin`
        #                     join `tabWarehouse` on `tabWarehouse`.name = `tabBin`.warehouse
        #                     join `tabCompany` on `tabCompany`.name = `tabWarehouse`.company
        #                     where `tabBin`.item_code = '%s' and `tabWarehouse`.company = '%s' and disabled = 0 """ % (i.name,filters.company), as_dict=True)[0]
        stocks = frappe.db.sql("""
            select (sum(`tabBin`.actual_qty) - sum(reserved_stock)) as actual_qty from `tabBin`
            join `tabWarehouse` on `tabWarehouse`.name = `tabBin`.warehouse
            join `tabCompany` on `tabCompany`.name = `tabWarehouse`.company
            where `tabBin`.item_code = %s
            and `tabWarehouse`.company = %s
            and `tabWarehouse`.disabled = 0
            and `tabWarehouse`.custom_is_service_stock = 0
        """, (i.name, filters.company), as_dict=True)[0]
        
        
        total_reserved_qty = 0

        # Get entries with status "Reserved" and "Partially Reserved"
        stock_entries = frappe.get_all(
            "Stock Reservation Entry",
            filters={
                "company": filters.company,
                "item_code": i.name,
                "status": ["in", ["Reserved", "Partially Reserved"]]
            },
            fields=["reserved_qty"]
        )

        # Sum reserved quantities
        for entry in stock_entries:
            total_reserved_qty += entry.reserved_qty or 0

        # Get partially delivered quantities using parameterized SQL
        prq = frappe.db.sql("""
            SELECT (reserved_qty - delivered_qty) AS partially_delivered
            FROM `tabStock Reservation Entry`
            WHERE item_code = %s AND company = %s AND status = 'Partially Delivered'
        """, (i.name, filters.company), as_dict=True)

        # Sum partially delivered values
        for prq_ in prq:
            total_reserved_qty += flt(prq_['partially_delivered']) or 0

        if not stocks['actual_qty']:
            stocks['actual_qty'] = 0
        


        # mrb_qty = frappe.db.sql("""select (sum(`tabBin`.actual_qty) - sum(reserved_stock)) as actual_qty from `tabBin`
        #                     join `tabWarehouse` on `tabWarehouse`.name = `tabBin`.warehouse
        #                     join `tabCompany` on `tabCompany`.name = `tabWarehouse`.company
        #                     where `tabBin`.item_code = '%s' and `tabWarehouse`.company = '%s' and `tabWarehouse`.custom_is_non_sale = 1 """ % (i.name,filters.company), as_dict=True)[0]
        mrb_qty = frappe.db.sql("""
            select (sum(`tabBin`.actual_qty) - sum(reserved_stock)) as actual_qty from `tabBin`
            join `tabWarehouse` on `tabWarehouse`.name = `tabBin`.warehouse
            join `tabCompany` on `tabCompany`.name = `tabWarehouse`.company
            where `tabBin`.item_code = %s
            and `tabWarehouse`.company = %s
            and `tabWarehouse`.custom_is_non_sale = 1
            and `tabWarehouse`.custom_is_service_stock = 0
        """, (i.name, filters.company), as_dict=True)[0]
        
        if not mrb_qty['actual_qty']:
            mrb_qty['actual_qty'] = 0


        # demo_qty = frappe.db.sql("""select (sum(`tabBin`.actual_qty) - sum(reserved_stock)) as actual_qty from `tabBin`
        #                     join `tabWarehouse` on `tabWarehouse`.name = `tabBin`.warehouse
        #                     join `tabCompany` on `tabCompany`.name = `tabWarehouse`.company
        #                     where `tabBin`.item_code = '%s' and `tabWarehouse`.company = '%s' and `tabWarehouse`.custom_is_demo = 1 """ % (i.name,filters.company), as_dict=True)[0]
        demo_qty = frappe.db.sql("""
            select (sum(`tabBin`.actual_qty) - sum(reserved_stock)) as actual_qty from `tabBin`
            join `tabWarehouse` on `tabWarehouse`.name = `tabBin`.warehouse
            join `tabCompany` on `tabCompany`.name = `tabWarehouse`.company
            where `tabBin`.item_code = %s
            and `tabWarehouse`.company = %s
            and `tabWarehouse`.custom_is_demo = 1
            and `tabWarehouse`.custom_is_service_stock = 0
        """, (i.name, filters.company), as_dict=True)[0]
            
        if not demo_qty['actual_qty']:
            demo_qty['actual_qty'] = 0

        new_po = frappe.db.sql("""select sum(`tabPurchase Order Item`.qty) as qty,sum(`tabPurchase Order Item`.received_qty) as d_qty from `tabPurchase Order`
        left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
        where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus = 1 and `tabPurchase Order`.company = '%s' and `tabPurchase Order Item`.qty >= `tabPurchase Order Item`.received_qty and `tabPurchase Order`.transaction_date >= '%s' """ % (i.name,filters.company,date), as_dict=True)[0]
        if not new_po['qty']:
            new_po['qty'] = 0
        if not new_po['d_qty']:
            new_po['d_qty'] = 0
        ppoc_total = new_po['qty'] - new_po['d_qty']

        sa = frappe.db.sql("""
            SELECT `tabSales Order Item`.parent AS parent,
                SUM(`tabSales Order Item`.qty) AS qty,
                `tabSales Order Item`.delivered_qty AS delivered_qty
            FROM `tabSales Order`
            LEFT JOIN `tabSales Order Item` ON `tabSales Order`.name = `tabSales Order Item`.parent
            WHERE `tabSales Order Item`.item_code = '%s'
            AND `tabSales Order`.docstatus != 2
            AND `tabSales Order`.company = '%s'
            AND `tabSales Order`.per_delivered != 100
            AND `tabSales Order`.status != 'Closed'            
            AND `tabSales Order`.transaction_date >= '%s'
            GROUP BY `tabSales Order Item`.parent
            ORDER BY `tabSales Order`.transaction_date
        """ % (i.name, filters.company,date), as_dict=True)
        psoc_total=0
        for j in sa:	
            if not j.qty:
                j.qty = 0
            if not j.delivered_qty:
                j.delivered_qty = 0
            psoc_total += j.qty - j.delivered_qty
        if stocks["actual_qty"] > 0:
            ware = frappe.db.sql(""" SELECT name FROM `tabWarehouse` WHERE is_scrap = 1 AND disabled = 0 AND company = %s """, (filters.company), as_dict=True)
            total_scrap_qty = 0
            for house in ware:
                sc_qty = frappe.get_value("Bin", {"warehouse": house.name,"item_code":i.name}, ['actual_qty']) or 0
                total_scrap_qty += sc_qty
            row = {'company':filters.company,'item':i.name,'item_name':i.item_name,'total_qty':stocks["actual_qty"] - total_scrap_qty +total_reserved_qty ,'reserved_qty':total_reserved_qty or 0,'free_qty':stocks["actual_qty"] - total_scrap_qty - demo_qty['actual_qty']-mrb_qty['actual_qty'],'non_sale_qty':mrb_qty['actual_qty'] or 0,'po_qty':ppoc_total or 0,'so_qty':psoc_total or 0,'unit':i.stock_uom,'demo_qty':demo_qty['actual_qty']}
        else:
            row = {'company':filters.company,'item':i.name,'item_name':i.item_name,'total_qty':0+total_reserved_qty ,'reserved_qty':total_reserved_qty or 0,'free_qty':0,'non_sale_qty':mrb_qty['actual_qty'] or 0,'po_qty':ppoc_total or 0,'so_qty':psoc_total or 0,'unit':i.stock_uom,'demo_qty':demo_qty['actual_qty']}
        data.append(row)
    return data