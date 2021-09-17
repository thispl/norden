# -*- coding: utf-8 -*-
# Copyright (c) 2021, Teampro and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class NVS(Document):
	pass

@frappe.whitelist()
def get_nvs_header(doc):
	data = '<tr><td style="background-color:#6e1f56;" colspan="3"><b style="color:white;font-size:14px">Specifications</b></td></tr>'
	data += '<tr><td style="background-color:#e9d8e2;" ><b>Model</b></td><td style="background-color:#e9d8e2;" colspan="3"><b style="font-size:11px;">%s</b></td></tr>'%(doc.type)
	return data

@frappe.whitelist()
def get_category_alignment(selected_ca,doc):
	if selected_ca == 'Left':
		category_alignment = '<div id="left-cat"><svg version="1.0" xmlns="http://www.w3.org/2000/svg" width="45px" height="250px"\
				viewBox="0 0 119.000000 855.000000" preserveAspectRatio="xMidYMid meet">\
				<g transform="translate(0.000000,855.000000) scale(0.100000,-0.100000)" fill="#7A1F5E" stroke="none">\
					<path d="M10 4280 c0 -2343 2 -4260 4 -4260 10 0 992 652 1045 693 35 27 67\
							64 86 98 l30 54 3 3390 c2 3072 1 3395 -14 3445 -27 93 -84 139 -633 500 -272\
							179 -500 329 -507 333 -12 7 -14 -666 -14 -4253z" /></g>\
				<text font-size="60px" font-weight="bold" fill="#FFFFFF" transform="translate(80,620) rotate(-90)">%s</text></svg></div>'%(doc.categories)
	else:
		category_alignment = '<div style="float:right; margin-right:-15px">\
        <div style="position: fixed;top:600px">\
            <svg version="1.0" xmlns="http://www.w3.org/2000/svg" width="45px" height="250px"\
                viewBox="0 0 118.000000 854.000000" preserveAspectRatio="xMidYMid meet">\
                <g transform="translate(0.000000,854.000000) scale(0.100000,-0.100000)" fill="#7A1F5E" stroke="none">\
                    <path d="M647 8181 c-279 -186 -526 -355 -548 -377 -21 -21 -49 -59 -62 -84\
                                l-22 -45 0 -3405 0 -3405 22 -47 c12 -26 41 -66 65 -88 24 -23 274 -194 556\
                                -380 l512 -339 0 4254 c0 2340 -3 4255 -7 4254 -5 0 -237 -152 -516 -338z" /></g>\
                <text font-size="60px" font-weight="bold" fill="#FFFFFF" transform="translate(75,650) rotate(-90)">%s</text></svg>\
        </div>\
    </div>'%(doc.categories)

	return category_alignment

@frappe.whitelist()
def get_nvs_specification(doc,child,label,pb):
	if len(child) > 0:
		data = '<tr><td rowspan=%s style="vertical-align: middle;">%s</td>'%(len(child),label)
		for c in child:
			data += '<td>%s</td><td><p style="font-size:11px">%s</p></td></tr><tr>'%(c.title,c.specification)
		data += '</tr>'
		if pb == 1:
			data += '</table><p style="page-break-before: always;">&nbsp;</p><table class="table table-condensed table-border">'
			data += '<tr><td style="background-color:#6e1f56;" colspan="3"><b style="color:white">Specifications</b></td></tr>'
			data += '<tr><td style="background-color:#e9d8e2;" >Model</td><td style="background-color:#e9d8e2;"colspan="3"><center>%s</center></td></tr>'%(doc.type)
		return data
	else:
		return ''

# @frappe.whitelist()
# def get_nvs_specification(doc,child,label,pb):
# 	if len(child) > 0:
# 		data = '<tr><td rowspan=%s style="border: 1px solid #4d004d"><center>%s</center></td>'%(len(child),label)
# 		for c in child:
# 			data += '<td style="border: 1px solid #4d004d">%s</td><td style="border: 1px solid #4d004d">%s</td></tr><tr>'%(c.title,c.specification)
# 		data += '</tr>'
# 		if pb == 1:
# 			data += '</table><p style="page-break-before: always;">&nbsp;</p><table class="table table-condensed">'
# 			data += '<tr><td style="background-color:#6e1f56;border:1px solid #4d004d;" colspan="3"><text color="white">Specifications</text></td></tr>'
# 			data += '<tr><td style="border: 1px solid #4d004d; background-color:#e9d8e2;" >Model</td><td style="border: 1px solid #4d004d; background-color:#DDA0DD;" colspan="2"><center>%s</center></td></tr>'%(doc.type)
# 		return data
# 	else:
# 		return ''