# -*- coding: utf-8 -*-
# Copyright (c) 2021, Teampro and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe,json
from frappe.utils import cstr
from frappe.model.document import Document
import requests

class NACDatasheet(Document):
    pass

@frappe.whitelist()
def get_technical_parameter(doc):
    data = ''
    data += '<tr><td><b style="color:#505050">Part Number</p></b></td><td colspan="1"><b style="color:#505050">Description</b></td> <td style="white-space: nowrap;"><b style="color:#505050">Standard Quantity</b></td></tr><tr>'
    for d in doc.technical_parameters:
        if d.part_number == "br":
            data += '</tr></table><br><table><tr>'
        else:
            data += '<td>%s</td></tr>'%(d.part_number,d.description,d.standard_quantity)
    return data

@frappe.whitelist()
def datasheet_api(doc):
    doc = json.loads(doc)
    nac_doc = frappe.get_doc('NAC Datasheet', doc['name'])
    url = "https://www.nordencommunication.com/api/products/save"
    # specs = frappe.get_print(doc['doctype'], doc['name'], doc=nac_doc, print_format='NAC Datasheet Specification HTML').replace('\n',"").replace('\t',"")
    specs = frappe.render_template("norden/norden/doctype/nac_datasheet/nac_ds_specification.html",{"doc": doc})
    ordering_info = frappe.render_template("norden/norden/doctype/nac_datasheet/nac_ds_ordering_information.html",{"doc": doc})
    payload = {
        "name": doc['type'],
        "overview": doc['description'],
        "specification": specs,
        "ordering_information": ordering_info,
        "purchase_informations": "Integer posuere at tellus vitae luctus. Sed non molestie nunc. Sed faucibus orci a magna blandit vestibulum. Quisque augue ante, tincidunt sit amet suscipit a, pharetra vitae magna.",
        "category_id": doc['category_id'],
        "default_part_number": doc['model'],
    	"part_numbers": doc['model'],
    	"status":1,
        "image": 'https://erp.nordencommunication.com/doc' + doc['item_image'],
        "data_sheet": "https://samplewebsite/documents/data-sheet.pdf"
    }
    # frappe.errprint(payload)
    headers = {
        'Authorization': 'Bearer qhMbf0bCwdUVysowooeGdQoz8BTI4nv5iZgWj8CM',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.request("POST", url, data=payload,headers=headers)
    frappe.errprint(response.content)
