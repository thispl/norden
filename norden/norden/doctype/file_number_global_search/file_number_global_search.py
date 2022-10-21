# Copyright (c) 2022, Teampro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.xlsxutils import read_xlsx_file_from_attached_file
from frappe.utils.file_manager import get_file

from datetime import date, timedelta, datetime
import openpyxl
from openpyxl import Workbook


import openpyxl
import xlrd
import re
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import GradientFill, PatternFill
from six import BytesIO, string_types
from frappe.utils import (
    flt,
    cint,
    cstr,
    get_html_format,
    get_url_to_form,
    gzip_decompress,
    format_duration,
)


class FileNumberGlobalSearch(Document):
    @frappe.whitelist()
    def get_data(self):
        quotation = frappe.get_value('Quotation',{'file_number':self.file_number},['name','party_name','grand_total'])
        sales_order = frappe.get_value('Sales Order',{'file_number':self.file_number},['name','customer','grand_total'])
        delivery_note = frappe.get_value('Delivery Note',{'file_number':self.file_number},['name','customer','grand_total'])
        sales_invoice = frappe.get_value('Sales Invoice',{'file_number':self.file_number},['name','customer','grand_total'])
        material_request = frappe.get_value('Material Request',{'file_number':self.file_number},['name'])
        purchase_order = frappe.get_value('Purchase Order',{'file_number':self.file_number},['name','supplier','grand_total'])
        data = ''
        data+='<table class = table table-bordered >' 
        data += '<table class="table table-bordered"><tr rowspan = 2 ><th style="padding:1px;border: 1px solid black;" colspan=6><center>Linked Documents</center></th></tr>'
        data+='<tr><th style="border: 1px solid black;"><center>DOCUMENT</center></th><th style="border: 1px solid black;"><center>DOCUMENT NAME</center></th><th style="border: 1px solid black;"><center>PARTY</center></th><th style="border: 1px solid black;"><center>TOTAL</center></th></tr>'
        if quotation:
            data+='<tr><td style="border: 1px solid black;"><center><b>QUOTATION</b></center></td><td style="border: 1px solid black;"><center><a href="https://erp.nordencommunication.com/app/quotation/%s">%s</a></center></td><td style="border: 1px solid black;"><center>%s</center></td><td style="border: 1px solid black;"><center>%s</center></td></tr>'%(quotation[0],quotation[0],quotation[1],quotation[2])
        if sales_order:
            data+='<tr><td style="border: 1px solid black;"><center><b>SALES ORDER</b></center></td><td style="border: 1px solid black;"><center><a href="https://erp.nordencommunication.com/app/sales-order/%s">%s</a></center></td><td style="border: 1px solid black;"><center>%s</center></td><td style="border: 1px solid black;"><center>%s</center></td></tr>'%(sales_order[0],sales_order[0],sales_order[1],sales_order[2])
        if delivery_note:
            data+='<tr><td style="border: 1px solid black;"><center><b>DELIVERY NOTE</b></center></td><td style="border: 1px solid black;"><center><a href="https://erp.nordencommunication.com/app/delivery-note/%s">%s</a></center></td><td style="border: 1px solid black;"><center>%s</center></td><td style="border: 1px solid black;"><center>%s</center></td></tr>'%(delivery_note[0],delivery_note[0],delivery_note[1],delivery_note[2])
        if sales_invoice:
            data+='<tr><td style="border: 1px solid black;"><center><b>SALES INVOICE</b></center></td><td style="border: 1px solid black;"><center><a href="https://erp.nordencommunication.com/app/sales-invoice/%s">%s</a><center></td><td style="border: 1px solid black;"><center>%s</center></td><td style="border: 1px solid black;"><center>%s</center></td></tr>'%(sales_invoice[0],sales_invoice[0],sales_invoice[1],sales_invoice[2])
        if material_request:
            data+='<tr><td style="border: 1px solid black;"><center><b>MATERIAL REQUEST</b></center></td><td style="border: 1px solid black;"><center><a href="https://erp.nordencommunication.com/app/material-request/%s">%s</a><center></td><td style="border: 1px solid black;"><center></center></td><td style="border: 1px solid black;"><center></center></td></tr>'%( material_request, material_request)
        if purchase_order:
            data+='<tr><td style="border: 1px solid black;"><center><b>PURCHASE ORDER</b></center></td><td style="border: 1px solid black;"><center><a href="https://erp.nordencommunication.com/app/purchase-order/%s">%s</a><center></td><td style="border: 1px solid black;"><center>%s</center></td><td style="border: 1px solid black;"><center>%s</center></td></tr>'%(purchase_order[0],purchase_order[0],purchase_order[1],purchase_order[2])
        data+='</table>'
        return data
