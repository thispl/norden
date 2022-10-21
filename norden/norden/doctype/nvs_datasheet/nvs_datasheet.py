# -*- coding: utf-8 -*-
# Copyright (c) 2021, Teampro and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe,json
from frappe.utils import cstr
from frappe.model.document import Document
import requests

class NVSDatasheet(Document):
	pass

@frappe.whitelist()
def datasheet_api(doc):
    doc = json.loads(doc)
    nvs_doc = frappe.get_doc('NVS', doc['name'])
    url = "https://www.nordencommunication.com/api/products/save"
    # specs = frappe.get_print(doc['doctype'], doc['name'], doc=nvs_doc, print_format='NVS Datasheet Specification HTML').replace('\n',"").replace('\t',""),
    specs = frappe.render_template("norden/norden/doctype/nvs_datasheet/nvs_ds_specification.html",{"doc": doc})
    ordering_info = frappe.render_template("norden/norden/doctype/nvs_datasheet/nvs_ds_ordering_information.html",{"doc": doc})
    payload = {
        "name": doc['model_no'],
        "overview": doc['description'],
        "specification": specs,
        "ordering_information": ordering_info,
        "purchase_informations": "Integer posuere at tellus vitae luctus. Sed non molestie nunc. Sed faucibus orci a magna blandit vestibulum. Quisque augue ante, tincidunt sit amet suscipit a, pharetra vitae magna.",
        "category_id": doc['category_id'],
        "default_part_number": doc['type'],
		"part_numbers": doc['type'],
		"status":1,
        "image": 'https://erp.nordencommunication.com/doc' + doc['image_upload'],
        "data_sheet": "https://samplewebsite/documents/data-sheet.pdf"
    }
    # frappe.errprint(specs)
    headers = {
        'Authorization': 'Bearer qhMbf0bCwdUVysowooeGdQoz8BTI4nv5iZgWj8CM',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.request("POST", url, data=payload,headers=headers)
    frappe.errprint(response.content)
