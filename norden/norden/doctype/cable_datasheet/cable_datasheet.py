# -*- coding: utf-8 -*-
# Copyright (c) 2021, Teampro and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe,json
from frappe.utils import cstr
from frappe.model.document import Document
import requests

class CableDatasheet(Document):
    pass

@frappe.whitelist()
def get_product_info(doc):
    cl1 = "#DFEDD8"
    cl2 = "#EFF6EC"
    data = ''
    for d in doc.product_classification:
        data += '<tr><td colspan="1" style="word-wrap: break-all;background-color:%s;color:#5B5B5B;">%s</td> <td colspan="1" style="word-wrap: break-all;background-color:%s;color:#5B5B5B;">%s</td></tr>'%(cl1,d.title,cl2,d.description)
        cl1 = "#EFF6EC"
        cl2 = "#DFEDD8"
    return data
@frappe.whitelist()
def get_material_info(doc):
    cl1 = "#DFEDD8"
    cl2 = "#EFF6EC"
    data = ''
    for d in doc.material_construction_and_design:
        data += '<tr><td colspan="1" style="word-wrap: break-all;background-color:%s;color:#5B5B5B;">%s</td> <td colspan="1" style="word-wrap: break-all;background-color:%s;color:#5B5B5B;">%s</td></tr>'%(cl1,d.title,cl2,d.description)
        if cl1 == "#EFF6EC":
            cl1 = "#DFEDD8"
            cl2 = "#EFF6EC"
        elif cl1 == "#DFEDD8":
            cl1 = "#EFF6EC"
            cl2 = "#DFEDD8"
    return data
@frappe.whitelist()
def get_electrical_mechanical_info(doc):
    cl1 = "#DFEDD8"
    cl2 = "#EFF6EC"
    data = ''
    for d in doc.electrical_and_mechanical_characteristics:
        data += '<tr><td colspan="1" style="word-wrap: break-all;background-color:%s;padding :1px;color:#5B5B5B;">%s</td> <td colspan="1" style="word-wrap: break-all;background-color:%s;color:#5B5B5B;">%s</td></tr>'%(cl1,d.title,cl2,d.description)
        if cl1 == "#EFF6EC":
            cl1 = "#DFEDD8"
            cl2 = "#EFF6EC"
        elif cl1 == "#DFEDD8":
            cl1 = "#EFF6EC"
            cl2 = "#DFEDD8"
    return data

@frappe.whitelist()
def ordering_guide(doc):
    data = ''
    fibre_type_fxx = ''
    fibre_tube = ''
    jacket = ''
    data += '<tr><td style="border:0.5px solid #E95328;border-right:0.5px solid white;padding :1px; background-color:#E95328;color:white;font-size:12px;font-weight:900;"><b style="color:white;">Cable Type</b></td>\
    <td style="border:0.5px solid #E95328;border-right:0.5px solid white;background-color:#E95328;color:white;font-size:12px;font-weight:900;"><b style="color:white;">Jacket</b></td>\
    <td style="border:0.5px solid #E95328;border-right:0.5px solid white;background-color:#E95328;color:white;font-size:12px;font-weight:900;"><b style="color:white;">Fibre Tube</b></td>\
    <td style="border:0.5px solid #E95328;border-right:0.5px solid white;background-color:#E95328;color:white;font-size:12px;font-weight:900;"><b style="color:white;">Fibre Count</b></td>\
    <td style="border:0.5px solid #E95328;border-right:0.5px solid white;background-color:#E95328;color:white;font-size:12px;font-weight:900;"><b style="color:white;">Fibre Type (FXX)</b></td>\
    <td style="border:0.5px solid #E95328;background-color:#E95328;color:white;font-size:12px;font-weight:900;"><b style="color:white;">Jacket Colour (CL)</b></td></tr><tr>'
    for d in doc.ordering_guide:   
        for i in d.fibre_tube:
            fibre_tube += '%s' %(i)
            if i == '\n':
                fibre_tube += '<br>'
        for i in d.jacket:
            jacket += '%s' %(i)
            if i == '\n':
                jacket += '<br>'
        for i in d.fibre_type_fxx:
            fibre_type_fxx += '%s' %(i)
            if i == '\n':
                fibre_type_fxx += '<br>'
        data += '<td style="border:0.5px solid #E95328;color:#5B5B5B;font-size:12px;padding :1px;">%s</td><td colspan="1" style="border:0.5px solid #E95328;color:#5B5B5B;font-size:10px;font-weight:500">%s</td><td style="border:0.5px solid #E95328;color:#5B5B5B;font-size:10px;font-weight:500">%s</td><td style="border:0.5px solid #E95328;color:#5B5B5B;font-size:10px;font-weight:500">%s</td><td style="border:0.5px solid #E95328;color:#5B5B5B;font-size:10px;font-weight:500;">%s</td><td style="border:0.5px solid #E95328;color:#5B5B5B;font-size:10px;font-weight:500">%s</td></tr>'%(d.cable_type,jacket,fibre_tube,d.fibre_count,fibre_type_fxx,d.jacket_colour)   
    return data
    
@frappe.whitelist()
def get_nordata_desc(doc):
    data = ''
    for d in doc.description:
        # frappe.errprint(d)
        data += d
        if d == '\n':
            data += '<br>'
    frappe.errprint(data)
    return data

@frappe.whitelist()
def get_optidata_desc(doc):
    data = ''
    for d in doc.description:
        # frappe.errprint(d)
        data += d
        if d == '\n':
            data += '<br>'
    frappe.errprint(data)
    return data

@frappe.whitelist()
def datasheet_api(doc):
    doc = json.loads(doc)
    nac_doc = frappe.get_doc('Cable Datasheet', doc['name'])
    url = "https://www.nordencommunication.com/api/products/save"
    # specs = frappe.get_print(doc['doctype'], doc['name'], doc=nac_doc, print_format='NAC Datasheet Specification HTML').replace('\n',"").replace('\t',"")
    specs = frappe.render_template("norden/norden/doctype/cable_datasheet/cable_ds_specification.html",{"doc": doc})
    ordering_info = frappe.render_template("norden/norden/doctype/cable_datasheet/cable_ds_ordering_information.html",{"doc": doc})
    payload = {
        "name": doc['type'],
        "overview": doc['description'],
        "specification": specs,
        "ordering_information": ordering_info,
        "purchase_informations": "Integer posuere at tellus vitae luctus. Sed non molestie nunc. Sed faucibus orci a magna blandit vestibulum. Quisque augue ante, tincidunt sit amet suscipit a, pharetra vitae magna.",
        "category_id": doc['category_id'],
        "default_part_number": doc['part_number'],
    	"part_numbers": doc['part_number'],
    	"status":1,
        "image": 'https://erp.nordencommunication.com/doc' + doc['compliance_image'],
        "data_sheet": "https://samplewebsite/documents/data-sheet.pdf"
    }
    # frappe.errprint(payload)
    headers = {
        'Authorization': 'Bearer qhMbf0bCwdUVysowooeGdQoz8BTI4nv5iZgWj8CM',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.request("POST", url, data=payload,headers=headers)
    frappe.errprint(response.content)
