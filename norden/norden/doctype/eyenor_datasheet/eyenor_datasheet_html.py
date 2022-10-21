# -*- coding: utf-8 -*-
# Copyright (c) 2021, Teampro and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.utils import scrub_urls, cstr
from frappe.model.document import Document
import requests
from requests import request


class EyenorDatasheet(Document):
    pass


@frappe.whitelist()
def datasheet_api(doc):
    doc = json.loads(doc)
    eyenor_doc = frappe.get_doc('Eyenor Datasheet', doc['name'])
    url = "https://www.nordencommunication.com/api/products/save"
    # specs = frappe.get_print(doc['doctype'], doc['name'], doc=eyenor_doc, print_format='Eyenor Datasheet Specification HTML').replace('\n',"").replace('\t',""),
    specs = frappe.render_template(
        "norden/norden/doctype/eyenor_datasheet/eyenor_ds_specification.html", {"doc": doc})
    ordering_info = frappe.render_template(
        "norden/norden/doctype/eyenor_datasheet/eyenor_ds_ordering_information.html", {"doc": doc})
    # download = frappe.get_print(doc['doctype'], doc['name'], doc=eyenor_doc, print_format='Datasheet 2').replace('\n',"").replace('\t',""),
    payload = {
        "name": doc['ds_item_name'],
        "overview": doc['overview'],
        "specification": specs,
        "ordering_information": ordering_info,
        "purchase_informations": "Integer posuere at tellus vitae luctus. Sed non molestie nunc. Sed faucibus orci a magna blandit vestibulum. Quisque augue ante, tincidunt sit amet suscipit a, pharetra vitae magna.",
        "category_id": doc['category_id'],
        "default_part_number": doc['ds_item_no'],
        "part_numbers": doc['ds_item_no'],
        "image": 'https://erp.nordencommunication.com' + doc['file_upload'],
        "data_sheet": "https://erp.nordencommunication.com/api/method/norden.utils.download_pdf?doctype=Eyenor%20Datasheet&name=ENC-HDO8M-50R-94-None&trigger_print=1&format=Datasheet%202&no_letterhead=0"
    }
    # frappe.errprint(specs)
    headers = {
        'Authorization': 'Bearer qhMbf0bCwdUVysowooeGdQoz8BTI4nv5iZgWj8CM',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.request("POST", url, data=payload, headers=headers)
    frappe.errprint(response.content)


@frappe.whitelist()
def get_html_header(doc):
    data = ''
    data += '<tr><td style="background-color:#7dba33;font-family:Frutiger Bold;" rowspan="2" colspan="1"><svg height="28" width="30"><text font-size="10px" fill="white" transform="translate(10,28) rotate(-90)">MODEL</text></svg></td>'
    data += '<td style="background-color:#C6C6C6;border-bottom: 0.5px solid #E8E8E8;" ><b style="color:#404040;font-family:Frutiger Bold;font-size:20px">Model No.</b></td><td colspan="8" style="background-color:#7dba33;color:#505050;font-family:Frutiger Bold;border-bottom: 0.5px solid #898989;font-size:20px">%s</td></tr>' % (
        doc['ds_item_no'])
    data += '<tr><td style="background-color:#C6C6C6; border-bottom: 0.5px solid #E8E8E8;border-top: 0.5px solid #E8E8E8;">Type</td><td colspan="8" style="border-bottom: 0.5px solid #E8E8E8;border-top: 0.5px solid #E8E8E8;">%s</td></tr>' % (
        doc['ds_item_name'])

    return data

@frappe.whitelist()
def get_html_specification(doc, spec_tables):
    data = ''
    clr = "1"
    cl1 = "C8C8C8"
    cl2 = "808080"
    txtcl1 = "303030"
    txtcl2 = "FFFFFF"
    b1 = "#FFFFFF"
    for spec in spec_tables:
        spec_len = 0
        if spec[0]:
            spec_len = get_length(spec[0])
            if spec_len > 6:
                svg_height = svg_translate = spec_len * 9
            else:
                svg_height = svg_translate = spec_len * 11

            svg_title = spec[1]
            # specs1 = get_svg_text_count(spec[1])
            # if len(specs1) > 1:
            # 	frappe.errprint(specs1[0])
            # 	data += '<tr><td style="background-color:#%s;font-family:Frutiger Bold;width:2px" rowspan="%s"><svg height="%s" width="10px"><text font-weight="bold" font-size="10px" fill=#%s transform="translate(10,%s) rotate(-90)"><tspan x="0" dy="1em">Hello</tspan><tspan x="0" dy="1em">World</tspan></text></svg></td>'%(cl1,len(spec[0]),svg_height,txtcl1,svg_translate)
            # else:
            data += '<tr><td style="background-color:#%s;font-family:Frutiger Bold;width:2px" rowspan="%s"><center><svg height="%s" width="10px"><text font-weight="bold" font-size="10px" fill=#%s transform="translate(10,%s) rotate(-90)">%s</center></text></svg></td>' % (
                cl1, len(spec[0]), svg_height, txtcl1, svg_translate, svg_title)
            for s in spec[0]:
                if clr == "2":
                    data += '</tr><tr><td style="background-color:#%s; border: 0.5px solid %s;color:#%s;width:170px;font-size:15px">%s</td><td>%s</td></tr><tr>' % (
                        cl2, b1, txtcl2, s['title'], str(s['specification']))
                    clr = "2"
                else:
                    data += '<td style="background-color:#%s; border: 0.5px solid %s;color:#%s;font-size:15px">%s</td><td>%s</td></tr><tr>' % (
                        cl2, b1, txtcl2, s['title'], str(s['specification']))
                    clr = "1"
            if cl1 == "C8C8C8":
                cl1 = "7dba33"
                txtcl1 = "FFFFFF"
            elif cl1 == "7dba33":
                cl1 = "C8C8C8"
                txtcl1 = "303030"
            if txtcl2 == "585858":
                txtcl2 = "FFFFFF"
            elif txtcl2 == "FFFFFF":
                txtcl2 = "585858"
            if cl2 == "808080":
                cl2 = "C8C8C8"
            elif cl2 == "C8C8C8":
                cl2 = "808080"
            if b1 == "#FFFFFF":
                b1 = "#F5F5F5"
            elif b1 == "#F5F5F5":
                b1 = "#FFFFFF"

            if spec[2] == 1:
                # data += '<tr><td  style="background-color:#7dba33;width:15px;font-family:Frutiger Bold;" rowspan="2"><svg height="30" width="10"><text font-size="9px" fill="white" transform="translate(10,30) rotate(-90)">MODEL</text></svg></td>'
                # data += '<td style="background-color:#C6C6C6;border-bottom: 0.5px solid #E8E8E8;" ><b style="color:#404040;font-family:Frutiger Bold;">Model No.</b></td><td style="background-color:#7dba33;color:#505050;font-family:Frutiger Bold;border-bottom: 0.5px solid #898989;;">%s</td></tr>' % (
                #     doc['ds_item_no'])
                # data += '<tr><td style="background-color:#C6C6C6; border-bottom: 0.5px solid #E8E8E8;border-top: 0.5px solid #E8E8E8;">Type</td><td style="border-bottom: 0.5px solid #E8E8E8;border-top: 0.5px solid #E8E8E8;">%s</td></tr>' % (
                #     doc['ds_item_name'])
                clr = "1"
                cl1 = "C8C8C8"
                cl2 = "808080"
                txtcl1 = "303030"  # 566573
                txtcl2 = "FFFFFF"
    return data


def get_length(spec):
    spec_len = 0
    for s in spec:
        sp = s['specification']
        if sp:
            l = sp.count('\n')
            spec_len = spec_len + (l+1)
    return spec_len


def get_svg_text_count(spec1):
    svg_text_count = spec1.split(" ")
    return svg_text_count


@frappe.whitelist()
def get_html_order_info(doc):
    data = ''
    data += '<tr><td><b style="color:#505050">Part Number</p></b></td><td colspan="1"><b style="color:#505050">Description</b></td> <td style="white-space: nowrap;"><b style="color:#505050">Standard Quantity</b></td></tr><tr>'
    for d in doc['ds_order']:
        if d['part_number'] == "br":
            data += '</tr></table><br><table><tr>'
        else:
            data += '<td style="font-family:Frutiger-Light;">%s</td><td colspan="1" style="word-wrap: break-all;font-family:Frutiger-Light;">%s</td> <td style="font-family:Frutiger-Light;">%s</td></tr>' % (
                d['part_number'], d['description'], d['standard_quantity'])
    return data


@frappe.whitelist()
def get_pack_info(doc):
    data = ''
    data += '<tr><td colspan="3"><b style="color:#505050">Part Number</b></td><td colspan="3"><b style="color:#505050">Packing Mode</b></td><td colspan="3"><b style="color:#505050">Gross weight(Kg)</b></td><td colspan="3"><b style="color:#505050">Dimension(mm)</b></td></tr><tr>'
    for d in doc.table_15:
        if d.part_number == "br":
            data += '</tr></table><br><table><tr>'
        else:
            data += '<td colspan="3">%s</td><td colspan="3">%s</td> <td colspan="3">%s</td><td colspan="3">%s</td></tr>' % (
                d.part_number, d.packing_number, d.gross_weight, d.dimension)
    return data


@frappe.whitelist()
def get_samplecontent(doc):
    data = ''
    data += '<tr><td colspan="3"><b style="color:#505050">Part Number</b></td><td colspan="3"><b style="color:#505050">Packing Mode</b></td><td colspan="3"><b style="color:#505050">Gross weight(Kg)</b></td><td colspan="3"><b style="color:#505050">Dimension</b></td></tr><tr>'
    for d in doc.sample_content:
        if d.part_number == "br":
            data += '</tr></table><br><table><tr>'
        else:
            data += '<td colspan="3">%s</td><td colspan="3">%s</td> <td colspan="3">%s</td><td colspan="3">%s</td></tr>' % (
                d.part_number, d.packing_number, d.gross_weight, d.dimension)
    return data


@frappe.whitelist()
def get_datasheet_icons(icons):
    data = '<div align="right">'
    d = 0
    for i in icons:
        if d >= 8:
            data += '</div><div align="right">'
            d = 0
        data += '<img class="icons" src="%s" width="60px">' % i.icon_image
    data += '</div>'
    return data