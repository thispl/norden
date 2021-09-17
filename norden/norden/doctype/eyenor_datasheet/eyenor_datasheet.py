# -*- coding: utf-8 -*-
# Copyright (c) 2021, Teampro and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class EyenorDatasheet(Document):
	pass

@frappe.whitelist()
def get_header(doc):
	data = ''
	data += '<tr><td style="background-color:#7dba33;font-family:Frutiger Bold;" rowspan="2"><svg height="28" width="10"><text font-size="8px" fill="white" transform="translate(10,28) rotate(-90)">MODEL</text></svg></td>'
	data += '<td style="background-color:#C6C6C6;border-bottom: 0.5px solid #E8E8E8;" ><b style="color:#404040;font-family:Frutiger Bold;">Model No.</b></td><td colspan="8" style="background-color:#7dba33;color:#505050;font-family:Frutiger Bold;border-bottom: 0.5px solid #898989;">%s</td></tr>'%(doc.ds_item_no)
	data += '<tr><td style="background-color:#C6C6C6; border-bottom: 0.5px solid #E8E8E8;border-top: 0.5px solid #E8E8E8;">Type</td><td colspan="8" style="border-bottom: 0.5px solid #E8E8E8;border-top: 0.5px solid #E8E8E8;">%s</td></tr>'%(doc.ds_item_name)
	return data

@frappe.whitelist()
def get_specification(doc,spec_tables):
	data = ''
	clr = "1"
	cl1 = "C8C8C8"
	cl2 = "808080"
	txtcl1 = "303030"
	txtcl2 = "FFFFFF"
	b1 = "#FFFFFF"
	for spec in spec_tables:
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
			data += '<tr><td style="background-color:#%s;font-family:Frutiger Bold;width:2px" rowspan="%s"><svg height="%s" width="10px"><text font-weight="bold" font-size="10px" fill=#%s transform="translate(10,%s) rotate(-90)">%s</text></svg></td>'%(cl1,len(spec[0]),svg_height,txtcl1,svg_translate,svg_title)
			for s in spec[0]:
				if clr == "1":
					data += '<td style="background-color:#%s; border: 0.5px solid %s;color:#%s;width:150px">%s</td><td style="border: 0.5px solid #E8E8E8;background-color:#F5F5F5">%s</td></tr><tr>'%(cl2,b1,txtcl2,s.title,s.specification)
					clr = "2"
				else:
					data += '<td style="background-color:#%s; border: 0.5px solid %s;color:#%s">%s</td><td style="border: 0.5px solid #E8E8E8;">%s</td></tr><tr>'%(cl2,b1,txtcl2,s.title,s.specification)
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
				data += '</table><p style="page-break-before: always;">&nbsp;</p><table class="table-condensed specifictd" style="width:100%">'
				data += '<tr><td  style="background-color:#7dba33;width:15px;font-family:Frutiger Bold;" rowspan="2"><svg height="30" width="10"><text font-size="9px" fill="white" transform="translate(10,30) rotate(-90)">MODEL</text></svg></td>'
				data += '<td style="background-color:#C6C6C6;border-bottom: 0.5px solid #E8E8E8;" ><b style="color:#404040;font-family:Frutiger Bold;">Model No.</b></td><td style="background-color:#7dba33;color:#505050;font-family:Frutiger Bold;border-bottom: 0.5px solid #898989;;">%s</td></tr>'%(doc.ds_item_no)
				data += '<tr><td style="background-color:#C6C6C6; border-bottom: 0.5px solid #E8E8E8;border-top: 0.5px solid #E8E8E8;">Type</td><td style="border-bottom: 0.5px solid #E8E8E8;border-top: 0.5px solid #E8E8E8;">%s</td></tr>'%(doc.ds_item_name)
				clr = "1"
				cl1 = "C8C8C8"
				cl2 = "808080"
				txtcl1 = "303030" #566573
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
	data += '<tr><td><b style="color:#505050">Part Number</p></b></td><td colspan="1"><b style="color:#505050">Description</b></td> <td style="white-space: nowrap;"><b style="color:#505050">Standard Quantity</b></td></tr><tr>'
	for d in doc.ds_order:
		if d.part_number == "br":
			data += '</tr></table><br><table><tr>'
		else:
			data += '<td style="font-family:Frutiger-Light;">%s</td><td colspan="1" style="word-wrap: break-all;font-family:Frutiger-Light;">%s</td> <td style="font-family:Frutiger-Light;">%s</td></tr>'%(d.part_number,d.description,d.standard_quantity)
	return data

@frappe.whitelist()
def get_pack_info(doc):
	data = ''
	data += '<tr><td colspan="3"><b style="color:#505050">Part Number</b></td><td colspan="3"><b style="color:#505050">Packing Mode</b></td><td colspan="3"><b style="color:#505050">Gross weight(Kg)</b></td><td colspan="3"><b style="color:#505050">Dimension(mm)</b></td></tr><tr>'
	for d in doc.table_15:
		if d.part_number == "br":
			data += '</tr></table><br><table><tr>'
		else:
			data += '<td colspan="3">%s</td><td colspan="3">%s</td> <td colspan="3">%s</td><td colspan="3">%s</td></tr>'%(d.part_number,d.packing_number,d.gross_weight,d.dimension)
	return data

@frappe.whitelist()
def get_samplecontent(doc):
	data = ''
	data += '<tr><td colspan="3"><b style="color:#505050">Part Number</b></td><td colspan="3"><b style="color:#505050">Packing Mode</b></td><td colspan="3"><b style="color:#505050">Gross weight(Kg)</b></td><td colspan="3"><b style="color:#505050">Dimension</b></td></tr><tr>'
	for d in doc.sample_content:
		if d.part_number == "br":
			data += '</tr></table><br><table><tr>'
		else:
			data += '<td colspan="3">%s</td><td colspan="3">%s</td> <td colspan="3">%s</td><td colspan="3">%s</td></tr>'%(d.part_number,d.packing_number,d.gross_weight,d.dimension)
	return data	


@frappe.whitelist()
def get_datasheet_icons(icons):
	data = '<div align="right">'
	d = 0
	for i in icons:
		if d >= 8:
			data += '</div><div align="right">'
			d = 0
		data += '<img class="icons" src="%s" width="60px">'%i.icon_image
	data += '</div>'
	return data