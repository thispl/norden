import frappe
import urllib.parse
from frappe.utils import (
	add_days,
	add_months,
	cint,
	date_diff,
	flt,
	get_first_day,
	get_last_day,
	get_link_to_form,
	getdate,
	rounded,
	today,
)

@frappe.whitelist()
def update_stock_qty(rack,item_code,stockQty,physical_qty,stock_analysis):
    # warehouse = urllib.parse.unquote(warehouse)
    rack = urllib.parse.unquote(rack)
    qty=physical_qty-stockQty
    # company=frappe.db.get_value("Warehouse",{'name':"warehouse"},['company'])
    company='Norden Communication Middle East FZE'
    message=''
    if qty==0.0:
        message="No changes happend"
    else:
        sr=frappe.new_doc("ERP Stock Reconciliation Tool")
        sr.posting_date=today()
        sr.company=company
        sr.warehouse="Main Stores - NCME"
        sr.rack=rack
        sr.item=item_code
        sr.stock_qty=stockQty
        sr.physical_qty=physical_qty
        sr.qty_addedremoved=qty
        sr.stock_analysis=stock_analysis
        sr.save(ignore_permissions=True)
        message="Qty has been updated in ERP"
    # elif qty>0.0:
    #     se=frappe.new_doc("Stock Entry")
    #     se.company=company
    #     se.stock_entry_type='Material Issue'
    #     se.append('items',{
    #         's_warehouse':warehouse,
    #         'item_code':item_code,
    #         'qty':qty
    #     })
    #     se.save(ignore_permissions=True)
    #     message=str(qty)+" has been issued from the warehouse : "+str(warehouse) +" for the Item: "+str(item_code)
    # elif qty<0.0:
    #     se=frappe.new_doc("Stock Entry")
    #     se.company=company
    #     se.stock_entry_type='Material Receipt'
    #     se.append('items',{
    #         't_warehouse':warehouse,
    #         'item_code':item_code,
    #         'qty':-(qty)
    #     })
    #     se.save(ignore_permissions=True)
    #     message=str(-(qty))+" has been inwarded to the warehouse : "+str(warehouse) +" for the Item: "+str(item_code)

    return message

@frappe.whitelist()
def delete_route_history():
    delete_route_history=frappe.get_all("Activity Log",{'user':'habib@nordenco.ae'},['name'])
    for d in delete_route_history:
        dele=frappe.get_doc("Activity Log",d.name)
        dele.delete()