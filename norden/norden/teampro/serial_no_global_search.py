import frappe
@frappe.whitelist()
def get_data(serial_no):
    data = '<table border="1" style="width: 100%;">'
    if serial_no:
        serial_no_value = frappe.db.get_value("Serial and Batch Entry", {'serial_no': serial_no}, ['parent'])
        if serial_no_value:
            value = frappe.get_all('Serial and Batch Bundle', {'name': serial_no_value}, ['voucher_no', 'voucher_type', 'item_code'])
            dn_date = frappe.db.get_value("Delivery Note", {'name': value[0]['voucher_no']}, ['posting_date'])
            data += '<tr style="background-color:#D9E2ED;">'
            data += '<td colspan="2" style="text-align:center;"><b>Item Code</b></td>'
            if value and value[0].get('voucher_type') == 'Delivery Note':
                si_parent = frappe.get_value("Sales Invoice Item", {'delivery_note': value[0]['voucher_no']}, ['parent'])
                si_date = frappe.db.get_value("Sales Invoice", {'name': si_parent}, ['posting_date']) if si_parent else None
                data += '<td colspan="2" style="text-align:center;"><b>Delivery Note</b></td>'
                if si_parent:
                    data += '<td colspan="2" style="text-align:center;"><b>Sales Invoice</b></td>'
                if dn_date:
                    data += '<td colspan="2" style="text-align:center;"><b>Delivery Date</b></td>'
                    if si_date:
                        data += '<td colspan="2" style="text-align:center;"><b>Invoiced Date</b></td>'
            pr = frappe.db.get_value("Serial and Batch Bundle",{"item_code":format(value[0]['item_code']),"voucher_type":"Purchase Receipt"},["voucher_type"])
            if pr:
                data += '<td colspan="2" style="text-align:center;"><b>Purchase Receipt</b></td>'
            stock = frappe.db.get_value("Serial and Batch Bundle",{"item_code":format(value[0]['item_code']),"voucher_type":"Stock Entry"},["voucher_type"])
            if stock:
                data += '<td colspan="2" style="text-align:center;"><b>Stock Entry</b></td>'
            data += '<td colspan="2" style="text-align:center;"><b>Warranty Terms</b></td>'
            data += '</tr>'
            data += '<tr>'
            data += '<td colspan="2" style="text-align:center;"><b>{}</b></td>'.format(value[0]['item_code'])
            if value and value[0].get('voucher_type') == 'Delivery Note':
                data += '<td colspan="2" style="text-align:center;"><b>{}</b></td>'.format(value[0]['voucher_no'])
                if si_parent:
                    data += '<td colspan="2" style="text-align:center;"><b>{}</b></td>'.format(si_parent)
                if dn_date:
                    data += '<td colspan="2" style="text-align:center;"><b>{}</b></td>'.format(dn_date)
                    if si_date:
                        data += '<td colspan="2" style="text-align:center;"><b>{}</b></td>'.format(si_date)
            pr_value = frappe.db.get_value("Serial and Batch Bundle",{"item_code":format(value[0]['item_code']),"voucher_type":"Purchase Receipt"},["voucher_no"])
            if pr_value:
                data += '<td colspan="2" style="text-align:center;"><b>{}</b></td>'.format(pr_value)
            stock_entry = frappe.db.get_value("Serial and Batch Bundle",{"item_code":format(value[0]['item_code']),"voucher_type":"Stock Entry"},["voucher_no"])
            if stock_entry:
                data += '<td colspan="2" style="text-align:center;"><b>{}</b></td>'.format(stock_entry)
            data += '<td colspan="2" style="text-align:center;"><b>Not Disclosure</b></td>'
            data += '</tr>'
        else:
            item_code = frappe.db.get_value("Serial No", {'name': serial_no}, ['item_code'])
            dn = frappe.db.get_value("Delivery Note Item", {'item_code': item_code}, ['parent'])			
            if dn:
                dn_date = frappe.db.get_value("Delivery Note", {'name': dn}, ['posting_date'])
                si_parent = frappe.get_value("Sales Invoice Item", {'delivery_note': dn}, ['parent'])
                si_date = frappe.db.get_value("Sales Invoice", {'name': si_parent}, ['posting_date']) if si_parent else None
                
                data += '<tr style="background-color:#D9E2ED;">'
                data += '<td colspan="2" style="text-align:center;"><b>Item Code</b></td>'
                data += '<td colspan="2" style="text-align:center;"><b>Delivery Note</b></td>'
                
                if si_parent:
                    data += '<td colspan="2" style="text-align:center;"><b>Sales Invoice</b></td>'
                
                if dn_date:
                    data += '<td colspan="2" style="text-align:center;"><b>Delivery Date</b></td>'
                    if si_date:
                        data += '<td colspan="2" style="text-align:center;"><b>Invoiced Date</b></td>'
                
                data += '<td colspan="2" style="text-align:center;"><b>Warranty Terms</b></td>'
                data += '</tr>'
                data += '<tr>'
                data += '<td colspan="2" style="text-align:center;"><b>{}</b></td>'.format(item_code)
                data += '<td colspan="2" style="text-align:center;"><b>{}</b></td>'.format(dn)
                
                if si_parent:
                    data += '<td colspan="2" style="text-align:center;"><b>{}</b></td>'.format(si_parent)
                
                if dn_date:
                    data += '<td colspan="2" style="text-align:center;"><b>{}</b></td>'.format(dn_date)
                    if si_date:
                        data += '<td colspan="2" style="text-align:center;"><b>{}</b></td>'.format(si_date)
                
                data += '<td colspan="2" style="text-align:center;"><b>Not Disclosure</b></td>'
                data += '</tr>'
            else:
                data += '<tr><td colspan="10" style="text-align:center;"><b>Not Delivered Yet</b></td></tr>'

    data += '</table>'
    return data




# @frappe.whitelist()
# def get_serial_no_details(serial_no):
# # def get_serial_no_details():
# # 	serial_no = "EN-210235U29E322C000006"
# 	sl = '%'+serial_no+'%'
# 	data = ''
# 	data += '<table  border= 1px solid black width = 100%>'
    
# 	pos = frappe.db.sql("""select `tabDelivery Note Item`.item_code as item_code,`tabDelivery Note Item`.against_sales_order as sales_order,`tabDelivery Note Item`.parent as parent,`tabDelivery Note Item`.warranty_terms as warranty_terms from `tabDelivery Note`
# 	left join `tabDelivery Note Item` on `tabDelivery Note`.name = `tabDelivery Note Item`.parent
# 	where `tabDelivery Note Item`.serial_no like '%s' and `tabDelivery Note`.docstatus != 2 """ % (sl), as_dict=True)
# 	if pos:
# 		for i in pos:
# 			if not i.warranty_terms:
# 				i.warranty_terms = "Not Disclosed"
# 			data += '<tr style = "background-color:#D9E2ED"><td colspan =2 style = "text-align:center"><b>Item Code</b></td><td style = "text-align:center"><b>Delivery Note</b></td><td colspan =2 style = "text-align:center"><b>Sales Invoice</b></td><td colspan =2 style = "text-align:center"><b>Delivery Date</b></td><td colspan =2 style = "text-align:center"><b>Invoiced Date</b></td><td colspan =2 style = "text-align:center"><b>Warranty Terms</b></td></tr>'
# 			date = frappe.db.get_value("Delivery Note",i.parent,'posting_date')
# 			si = frappe.db.sql("""select parent from `tabSales Invoice Item` where delivery_note = '%s' """%(i.parent),as_dict=1)[0]
# 			si_date = frappe.db.get_value("Sales Invoice",si['parent'],'posting_date')
# 			data += '<tr><td colspan =2 style = "text-align:center"><b>%s</b></td><td style="border: 1px solid black;font-weight:bold"><center><a href="https://erp.nordencommunication.com/app/delivery-note/%s">%s</a></center></td><td style="border: 1px solid black;font-weight:bold"><center><a href="https://erp.nordencommunication.com/app/sales-invoice/%s">%s</a></center></td><td colspan =2 style = "text-align:center"><b>%s</b></td><td colspan =2 style = "text-align:center"><b>%s</b></td><td colspan =2 style = "text-align:center"><b>%s</b></td></tr>'%(i.item_code,i.parent,i.parent,si['parent'],si['parent'],format_date(date),format_date(si_date),i.warranty_terms or '')
# 	else:
# 		data += '<tr style = "background-color:#D9E2ED"><td colspan =8 style = "text-align:center"><b>Not Delivered Yet</b></td></tr>'
    
# 	data += '</table>' 
# 	return data