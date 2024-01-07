# -*- coding: utf-8 -*-
# Copyright (c) 2021, Teampro and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from email.mime import image
import frappe
import json
from frappe.utils import scrub_urls, cstr
from frappe.model.document import Document
import requests
from requests import request
from frappe.utils.pdf import get_pdf



class EyenorDatasheet(Document):
    def after_save(self):
        doctype = 'Eyenor Datasheet'
        format = 'Datasheet 2'
        name = self.name
        html = frappe.get_print(doctype, name, format, doc=None, no_letterhead='no_letterhead')
        ret = frappe.get_doc({
            "doctype": "File",
            "attached_to_name": '',
            "attached_to_doctype": 'Eyenor Datasheet',
            "attached_to_field": '',
            "file_name": 'data_sheet.pdf',
            "is_private": 0,
            "content": get_pdf(html),
            "decode": False
        })
        ret.save(ignore_permissions=True)
        frappe.db.commit()
        attached_file = frappe.get_doc("File", ret.name)
        # frappe.log_error(message=[attached_file.file_url,name])
        self.generated_pdf = attached_file.file_url

@frappe.whitelist()
def datasheet_api(doc):
    from requests.utils import requote_uri
    doc = json.loads(doc)
    image_path = 'https://erp.nordencommunication.com' + requote_uri(doc['file_upload'])
    frappe.errprint(image_path)
    eyenor_doc = frappe.get_doc('Eyenor Datasheet', doc['name'])
    url = "https://www.nordencommunication.com/api/products/save"
    # specs = frappe.get_print(doc['doctype'], doc['name'], doc=eyenor_doc, print_format='Eyenor Datasheet Specification HTML').replace('\n',"").replace('\t',""),
    specs = frappe.render_template(
        "norden/norden/doctype/eyenor_datasheet/eyenor_ds_specification.html", {"doc": doc})
    ordering_info = frappe.render_template(
        "norden/norden/doctype/eyenor_datasheet/eyenor_ds_ordering_information.html", {"doc": doc})
    payload = {
        "name": doc['ds_item_name'],
        "overview": doc['overview'],
        "status": "Enabled",
        "specification": specs,
        "ordering_information": ordering_info,
        "purchase_informations": "Integer posuere at tellus vitae luctus. Sed non molestie nunc. Sed faucibus orci a magna blandit vestibulum. Quisque augue ante, tincidunt sit amet suscipit a, pharetra vitae magna.",
        "category_id": doc['category_id'],
        "default_part_number": doc['ds_item_no'],
        "part_numbers": doc['ds_item_no'],
        "image": 'https://erp.nordencommunication.com' + image_path,
        "data_sheet": 'https://erp.nordencommunication.com' + doc['generated_pdf']
    }
    headers = {
        'Authorization': 'Bearer qhMbf0bCwdUVysowooeGdQoz8BTI4nv5iZgWj8CM',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.request("POST", url, data=payload, headers=headers)
    frappe.msgprint("Datasheet has been Uploaded to the website successfully")

@frappe.whitelist()
def get_header(doc):
    data = ''
    data += '<tr><td style="background-color:#7dba33;font-family:Frutiger Bold;" rowspan="2"><svg height="26" width="10"><text font-size="8px" fill="white" transform="translate(10,28) rotate(-90)">MODEL</text></svg></td>'
    data += '<td style="background-color:#C6C6C6;border-bottom: 0.5px solid #E8E8E8;" ><b style="color:#404040;font-family:Frutiger Bold;">Model No.</b></td><td colspan="8" style="background-color:#7dba33;color:#505050;font-family:Frutiger Bold;border-bottom: 0.5px solid #898989;">%s</td></tr>' % (
        doc.ds_item_no)
    data += '<tr><td style="background-color:#C6C6C6; border-bottom: 0.5px solid #E8E8E8;border-top: 0.5px solid #E8E8E8;">Type</td><td colspan="8" style="border-bottom: 0.5px solid #E8E8E8;border-top: 0.5px solid #E8E8E8;">%s</td></tr>' % (
        doc.ds_item_name)
    return data


@frappe.whitelist()
def get_header_test(doc):
    data = ''
    data += '<tr><td style="background-color:#FF0000;font-family:Frutiger Bold;" rowspan="2"><svg height="26" width="10"><text font-size="8px" fill="white" transform="translate(10,28) rotate(-90)">MODEL</text></svg></td>'
    data += '<td style="background-color:#C6C6C6;border-bottom: 0.5px solid #E8E8E8;" ><b style="color:#404040;font-family:Frutiger Bold;">Model No.</b></td><td colspan="8" style="background-color:#FF0000;color:#505050;font-family:Frutiger Bold;border-bottom: 0.5px solid #898989;">%s</td></tr>' % (
        doc.ds_item_no)
    data += '<tr><td style="background-color:#C6C6C6; border-bottom: 0.5px solid #E8E8E8;border-top: 0.5px solid #E8E8E8;">Type</td><td colspan="8" style="border-bottom: 0.5px solid #E8E8E8;border-top: 0.5px solid #E8E8E8;">%s</td></tr>' % (
        doc.ds_item_name)
    return data


@frappe.whitelist()
def get_specification(doc, spec_tables):
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
        
            data += '<tr><td style="background-color:#%s;font-family:Frutiger Bold;width:2px" rowspan="%s"><svg height="%s" width="10px"><text font-weight="bold" font-size="10px" fill=#%s transform="translate(10,%s) rotate(-90)">%s</text></svg></td>' % (
                cl1, len(spec[0]), svg_height, txtcl1, svg_translate, svg_title)
            for s in spec[0]:
                if clr == "1":
                    data += '<td style="background-color:#%s; border: 0.5px solid %s;color:#%s;width:150px">%s</td><td style="border: 0.5px solid #E8E8E8;background-color:#F5F5F5;">%s</td></tr><tr>' % (
                        cl2, b1, txtcl2, s.title, s.specification)
                    clr = "2"
                                        
                # elif s.page_break == 1:
                #     # data += '<tr><td style="background-color:#%s;font-family:Frutiger Bold;width:2px" rowspan="%s"><svg height="%s" width="10px"><text font-weight="bold" font-size="10px" fill=#%s transform="translate(10,%s) rotate(-90)">%s</text></svg></td>' % (
                #     #     cl1, len(spec[0]), svg_height, txtcl1, svg_translate, svg_title)
                #     data += '</table><table class="table-condensed specifictd" style="width:100%">'
                #     data += '<tr><td style="background-color:#7dba33;font-family:Frutiger Bold;" rowspan="2"><svg height="28" width="10"><text font-size="8px" fill="white" transform="translate(10,28) rotate(-90)">MODEL</text></svg></td>'
                #     data += '<td style="background-color:#C6C6C6;border-bottom: 0.5px solid #E8E8E8;" ><b style="color:#404040;font-family:Frutiger Bold;">Model No.</b></td><td colspan="8" style="background-color:#7dba33;color:#505050;font-family:Frutiger Bold;border-bottom: 0.5px solid #898989;">%s</td></tr>' % (
                #         doc.ds_item_no)
                #     data += '<tr><td style="background-color:#C6C6C6; border-bottom: 0.5px solid #E8E8E8;border-top: 0.5px solid #E8E8E8;">Type</td><td colspan="8" style="border-bottom: 0.5px solid #E8E8E8;border-top: 0.5px solid #E8E8E8;">%s</td></tr>' % (
                #         doc.ds_item_name)
                #     data += '<td style="background-color:#%s; border: 0.5px solid %s;color:#%s;width:150px">%s</td><td style="border: 0.5px solid #E8E8E8;background-color:#F5F5F5;">%s</td></tr><tr>' % (
                #         cl2, b1, txtcl2, s.title, s.specification)
            
                else:
                    data += '<td style="background-color:#%s; border: 0.5px solid %s;color:#%s">%s</td><td style="border: 0.5px solid #E8E8E8;">%s</td></tr><tr>' % (
                            cl2, b1, txtcl2, s.title, s.specification)

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
                data += '</table><p style="page-break-before: always;"></p><table class="table-condensed specifictd" style="width:100%">'
                data += '<tr><td style="background-color:#7dba33;font-family:Frutiger Bold;" rowspan="2"><svg height="28" width="10"><text font-size="8px" fill="white" transform="translate(10,28) rotate(-90)">MODEL</text></svg></td>'
                data += '<td style="background-color:#C6C6C6;border-bottom: 0.5px solid #E8E8E8;" ><b style="color:#404040;font-family:Frutiger Bold;">Model No.</b></td><td colspan="8" style="background-color:#7dba33;color:#505050;font-family:Frutiger Bold;border-bottom: 0.5px solid #898989;">%s</td></tr>' % (
                    doc.ds_item_no)
                data += '<tr><td style="background-color:#C6C6C6; border-bottom: 0.5px solid #E8E8E8;border-top: 0.5px solid #E8E8E8;">Type</td><td colspan="8" style="border-bottom: 0.5px solid #E8E8E8;border-top: 0.5px solid #E8E8E8;">%s</td></tr>' % (
                    doc.ds_item_name)
                     
                clr = "2"
                clr = "1"
                cl1 = "C8C8C8"
                cl2 = "808080"
                txtcl1 = "303030"  # 566573
                txtcl2 = "FFFFFF"
    return data


@frappe.whitelist()
def get_specification_test(doc, spec_tables):
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
        
            data += '<tr><td style="background-color:#%s;font-family:Frutiger Bold;width:2px" rowspan="%s"><svg height="%s" width="10px"><text font-weight="bold" font-size="10px" fill=#%s transform="translate(10,%s) rotate(-90)">%s</text></svg></td>' % (
                cl1, len(spec[0]), svg_height, txtcl1, svg_translate, svg_title)
            for s in spec[0]:
                if clr == "1":
                    data += '<td style="background-color:#%s; border: 0.5px solid %s;color:#%s;width:150px">%s</td><td style="border: 0.5px solid #E8E8E8;background-color:#F5F5F5;">%s</td></tr><tr>' % (
                        cl2, b1, txtcl2, s.title, s.specification)
                    clr = "2"
            
                else:
                    data += '<td style="background-color:#%s; border: 0.5px solid %s;color:#%s">%s</td><td style="border: 0.5px solid #E8E8E8;">%s</td></tr><tr>' % (
                            cl2, b1, txtcl2, s.title, s.specification)

                    clr = "1"
            if cl1 == "C8C8C8":
                cl1 = "FF0000" 
                
                txtcl1 = "FFFFFF"
            elif cl1 == "FF0000":
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
                data += '</table><p style="page-break-before: always;"></p><table class="table-condensed specifictd" style="width:100%">'
                data += '<tr><td style="background-color:#FF0000;font-family:Frutiger Bold;" rowspan="2"><svg height="28" width="10"><text font-size="8px" fill="white" transform="translate(10,28) rotate(-90)">MODEL</text></svg></td>'
                data += '<td style="background-color:#C6C6C6;border-bottom: 0.5px solid #E8E8E8;" ><b style="color:#404040;font-family:Frutiger Bold;">Model No.</b></td><td colspan="8" style="background-color:#FF0000;color:#505050;font-family:Frutiger Bold;border-bottom: 0.5px solid #898989;">%s</td></tr>' % (
                    doc.ds_item_no)
                data += '<tr><td style="background-color:#C6C6C6; border-bottom: 0.5px solid #E8E8E8;border-top: 0.5px solid #E8E8E8;">Type</td><td colspan="8" style="border-bottom: 0.5px solid #E8E8E8;border-top: 0.5px solid #E8E8E8;">%s</td></tr>' % (
                    doc.ds_item_name)
                     
                clr = "2"
                clr = "1"
                cl1 = "C8C8C8"
                cl2 = "808080"
                txtcl1 = "303030"  # 566573
                txtcl2 = "FFFFFF"
    return data

def get_length(spec):
    spec_len = 0
    for s in spec:
        sp = s.specification
        if sp:
            l = sp.count('\n')
            spec_len = spec_len + (l+1)
    return spec_len


def get_svg_text_count(spec1):
    svg_text_count = spec1.split(" ")
    return svg_text_count


@frappe.whitelist()
def get_order_info(doc):
    data = ''
    data += '<tr><td><b style="color:#505050;white-space: nowrap;">Part Number</p></b></td><td colspan="3"><b style="color:#505050">Description</b></td> <td style="white-space: nowrap;"><b style="color:#505050">Standard Quantity</b></td></tr><tr>'
    for d in doc.ds_order:
        if d.part_number == "br":
            data += '</tr></table><br><table><tr>'
        else:
            data += '<td style="font-family:Frutiger-Light;white-space: nowrap;">%s</td><td colspan="3" style="overflow-wrap:break-word;font-family:Frutiger-Light;">%s</td> <td style="font-family:Frutiger-Light;word-wrap: break-all;">%s</td></tr>' % (
                d.part_number, d.description, d.standard_quantity)
    return data

@frappe.whitelist()
def get_order_info_test(doc):
    data = ''
    data += '<tr><td style = background-color:#e03636><b style="color:white;white-space: nowrap;">Part Number</p></b></td><td colspan="3" style = background-color:#e03636><b style="color:white">Description</b></td> <td style="white-space: nowrap;background-color:#e03636"><b style="color:white">Standard Quantity</b></td></tr><tr>'
    for d in doc.ds_order:
        if d.part_number == "br":
            data += '</tr></table><br><table><tr>'
        else:
            data += '<td style="font-family:Frutiger-Light;white-space: nowrap;">%s</td><td colspan="3" style="overflow-wrap:break-word;font-family:Frutiger-Light;">%s</td> <td style="font-family:Frutiger-Light;word-wrap: break-all;">%s</td></tr>' % (
                d.part_number, d.description, d.standard_quantity)
    return data


@frappe.whitelist()
def get_pack_info(doc):
    data = ''
    data += '<tr><td colspan="2"><b style="color:white">Part Number</b></td><td colspan="3"><b style="color:white">Packing Mode</b></td><td colspan="3"><b style="color:white">Gross weight(Kg)</b></td><td colspan="3"><b style="color:white">Dimension(mm)</b></td></tr><tr>'
    for d in doc.table_15:
        if d.part_number == "br":
            data += '</tr></table><br><table><tr>'
        else:
            data += '<td colspan="2">%s</td><td colspan="3">%s</td> <td colspan="3">%s</td><td colspan="3">%s</td></tr>' % (
                d.part_number, d.packing_number, d.gross_weight, d.dimension)
    return data



@frappe.whitelist()
def get_pack_info_test(doc):
    data = ''
    data += '<tr><td colspan=2 style = background-color:#e03636><b style="color:white;white-space: nowrap;">Part Number</b></td><td colspan = 3 style = background-color:#e03636><b style="color:white;white-space: nowrap;">Packing Mode</b></td><td style = background-color:#e03636 colspan = 3><b style="color:white;white-space: nowrap;">Gross weight(Kg)</b></td><td colspan = 3 style = background-color:#e03636><b style="color:white;white-space: nowrap;">Dimension(mm)</b></td></tr><tr>'
    for d in doc.table_15:
        if d.part_number == "br":
            data += '</tr></table><br><table><tr>'
        else:
            data += '<td colspan="2">%s</td><td colspan="3">%s</td> <td colspan="3">%s</td><td colspan="3">%s</td></tr>' % (
                d.part_number, d.packing_number, d.gross_weight, d.dimension)
    return data

# @frappe.whitelist()
# def get_order_info_test(doc):
#     data = '<table style="width:100%; border: 1px solid #d3d3d3;">'
#     data += '<tr><td><b colspan="3" style="color:white;background-color:#FF0000">Part Number</p></b></td><td colspan="3"><b style="color:white;background-color:#FF0000">Description</b></td><b colspan="3" style="color:white;background-color:#FF0000">Standard Quantity</b></td></tr>'
#     clr = "1"
#     for d in doc.ds_order:
#         if d.part_number == "br":
#             data += '</tr><tr>'
#         else:
#             data += '<td colspan="3" style="border: 1px solid #d3d3d3;">{}</td><td colspan="3" style="border: 1px solid #d3d3d3;">{}</td><td colspan="3" style="border: 1px solid #d3d3d3;">{}</td>'.format(
#                 d.part_number, d.description, d.standard_quantity)
#     data += '</tr></table>'
#     return data








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

@frappe.whitelist()
def get_dori_distance(doc,dori_distance):
    data = ''
    clr = "1"
    cl1 = "C8C8C8"
    cl2 = "808080"
    txtcl1 = "303030"
    txtcl2 = "FFFFFF"
    b1 = "#FFFFFF"
    for d in dori_distance:
        if d[0]:
            d_len = get_length(d[0])
            if d_len > 6:
                svg_height = svg_translate = d_len * 9
            else:
                svg_height = svg_translate = d_len * 11

            svg_title = d[1]
            # specs1 = get_svg_text_count(spec[1])
            # if len(specs1) > 1:
            # 	frappe.errprint(specs1[0])
            # 	data += '<tr><td style="background-color:#%s;font-family:Frutiger Bold;width:2px" rowspan="%s"><svg height="%s" width="10px"><text font-weight="bold" font-size="10px" fill=#%s transform="translate(10,%s) rotate(-90)"><tspan x="0" dy="1em">Hello</tspan><tspan x="0" dy="1em">World</tspan></text></svg></td>'%(cl1,len(spec[0]),svg_height,txtcl1,svg_translate)
            # else:
            data += '<tr><td style="background-color:#%s;font-family:Frutiger Bold;width:2px" rowspan="%s"><svg height="%s" width="10px"><text font-weight="bold" font-size="10px" fill=#%s transform="translate(10,%s) rotate(-90)">%s</text></svg></td>' % (
                cl1, len(d[0]), svg_height, txtcl1, svg_translate, svg_title)
            for s in d[0]:
                if clr == "1":
                    data += '<td style="background-color:#%s; border: 0.5px solid %s;color:#%s;width:150px">%s</td><td style="border: 0.5px solid #E8E8E8;background-color:#F5F5F5">%s</td></tr><tr>' % (
                        cl2, b1, txtcl2, s.lens, s.detect,s.observe,s.recognize,s.identyfy)
                    clr = "2"
                else:
                    data += '<td style="background-color:#%s; border: 0.5px solid %s;color:#%s">%s</td><td style="border: 0.5px solid #E8E8E8;">%s</td></tr><tr>' % (
                        cl2, b1, txtcl2, s.lens, s.detect,s.observe,s.recognize,s.identyfy)
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

            if d[2] == 1:
                # data += '</table><p style="page-break-before: always;">&nbsp;</p><table class="table-condensed specifictd" style="width:100%">'
                data += '<tr><td  style="background-color:#e03636 ;width:15px;font-family:Frutiger Bold;" rowspan="2"><svg height="30" width="10"><text font-size="9px" fill="white" transform="translate(10,30) rotate(-90)">MODEL</text></svg></td>'
                data += '<td style="background-color:#C6C6C6;border-bottom: 0.5px solid #E8E8E8;" ><b style="color:#404040;font-family:Frutiger Bold;">Model No.</b></td><td style="background-color:#e03636;color:#505050;font-family:Frutiger Bold;border-bottom: 0.5px solid #898989;;">%s</td></tr>' % (
                    doc.ds_item_no)
                # data += '<tr><td style="background-color:#C6C6C6; border-bottom: 0.5px solid #E8E8E8;border-top: 0.5px solid #E8E8E8;">Type</td><td style="border-bottom: 0.5px solid #E8E8E8;border-top: 0.5px solid #E8E8E8;">%s</td></tr>' % (
                #     doc.ds_item_name)
                clr = "1"
                cl1 = "C8C8C8"
                cl2 = "808080"
                txtcl1 = "303030"  # 566573
                txtcl2 = "FFFFFF"
    return data

@frappe.whitelist()
def get_dori_distance_test(doc,dori_distance):
    data = ''
    clr = "1"
    cl1 = "C8C8C8"
    cl2 = "808080"
    txtcl1 = "303030"
    txtcl2 = "FFFFFF"
    b1 = "#FFFFFF"
    for d in dori_distance:
        if d[0]:
            d_len = get_length(d[0])
            if d_len > 6:
                svg_height = svg_translate = d_len * 9
            else:
                svg_height = svg_translate = d_len * 11

            svg_title = d[1]
            # specs1 = get_svg_text_count(spec[1])
            # if len(specs1) > 1:
            # 	frappe.errprint(specs1[0])
            # 	data += '<tr><td style="background-color:#%s;font-family:Frutiger Bold;width:2px" rowspan="%s"><svg height="%s" width="10px"><text font-weight="bold" font-size="10px" fill=#%s transform="translate(10,%s) rotate(-90)"><tspan x="0" dy="1em">Hello</tspan><tspan x="0" dy="1em">World</tspan></text></svg></td>'%(cl1,len(spec[0]),svg_height,txtcl1,svg_translate)
            # else:
            data += '<tr><td style="background-color:#%s;font-family:Frutiger Bold;width:2px" rowspan="%s"><svg height="%s" width="10px"><text font-weight="bold" font-size="10px" fill=#%s transform="translate(10,%s) rotate(-90)">%s</text></svg></td>' % (
                cl1, len(d[0]), svg_height, txtcl1, svg_translate, svg_title)
            for s in d[0]:
                if clr == "1":
                    data += '<td style="background-color:#%s; border: 0.5px solid %s;color:#%s;width:150px">%s</td><td style="border: 0.5px solid #E8E8E8;background-color:#F5F5F5">%s</td></tr><tr>' % (
                        cl2, b1, txtcl2, s.lens, s.detect,s.observe,s.recognize,s.identyfy)
                    clr = "2"
                else:
                    data += '<td style="background-color:#%s; border: 0.5px solid %s;color:#%s">%s</td><td style="border: 0.5px solid #E8E8E8;">%s</td></tr><tr>' % (
                        cl2, b1, txtcl2, s.lens, s.detect,s.observe,s.recognize,s.identyfy)
                    clr = "1"
            if cl1 == "C8C8C8":
                cl1 = "FF0000"
                txtcl1 = "FFFFFF"
            elif cl1 == "FF0000":
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

            if d[2] == 1:
                # data += '</table><p style="page-break-before: always;">&nbsp;</p><table class="table-condensed specifictd" style="width:100%">'
                data += '<tr><td  style="background-color:#FF0000;width:15px;font-family:Frutiger Bold;" rowspan="2"><svg height="30" width="10"><text font-size="9px" fill="white" transform="translate(10,30) rotate(-90)">MODEL</text></svg></td>'
                data += '<td style="background-color:#C6C6C6;border-bottom: 0.5px solid #E8E8E8;" ><b style="color:#404040;font-family:Frutiger Bold;">Model No.</b></td><td style="background-color:#FF0000;color:#505050;font-family:Frutiger Bold;border-bottom: 0.5px solid #898989;;">%s</td></tr>' % (
                    doc.ds_item_no)
                # data += '<tr><td style="background-color:#C6C6C6; border-bottom: 0.5px solid #E8E8E8;border-top: 0.5px solid #E8E8E8;">Type</td><td style="border-bottom: 0.5px solid #E8E8E8;border-top: 0.5px solid #E8E8E8;">%s</td></tr>' % (
                #     doc.ds_item_name)
                clr = "1"
                cl1 = "C8C8C8"
                cl2 = "808080"
                txtcl1 = "303030"  # 566573
                txtcl2 = "FFFFFF"
    return data


@frappe.whitelist()
def get_thermal_image(doc):
    data = ''
    data += '<tr><td><b style="color:#505050;white-space: nowrap;">Part Number</p></b></td><td colspan="3"><b style="color:#505050">Description</b></td> <td style="white-space: nowrap;"><b style="color:#505050">Standard Quantity</b></td></tr><tr>'
    data += '<tr><td><b style="color:#505050;white-space: nowrap;">Part Number</p></b></td><td colspan="3"><b style="color:#505050">Description</b></td> <td style="white-space: nowrap;"><b style="color:#505050">Standard Quantity</b></td></tr><tr>'
    # for d in thermal_imaging_object:
    #     data += '<td style="font-family:Frutiger-Light;white-space: nowrap;">%s</td><td colspan="3" style="overflow-wrap:break-word;font-family:Frutiger-Light;">%s</td> <td style="font-family:Frutiger-Light;word-wrap: break-all;">%s</td></tr>' % (
    #     d.object, d.detection, d.recognition)
    return data