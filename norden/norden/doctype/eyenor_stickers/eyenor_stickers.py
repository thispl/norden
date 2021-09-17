# -*- coding: utf-8 -*-
# Copyright (c) 2021, Teampro and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document


class EyenorStickers(Document):
    pass


def generate_stickers(doc):
    data = """<body><center>
	<table class="table table-condensed" style="border:1px black solid;">
	<tr>
	<td ><img src="%s" width="65" height="23"> <th><h style="font-size:7px;text-align:center">%s</h>	</th></td>
	</tr>
	<tr>
    <td colspan="2">Model:%s</td>
    <td> </td>
    </tr>
	<tr>
    <td>Power Supply:%s</td>
    <td>user:%s</td>  
    </tr>
    <tr>
    <td>SN:%s</td>
    <td>password:%s</td>
    </tr>
	<tr>
    <td>Batch No:%s</td>
    <td>IP:%s</td>
	</tr>
	<tr>
	<td width="40px" colspan="2">%s</td>
    </tr>
	<th>
	
	<img src="%s" width="60" height="30"></th>
	<th><img src="%s" class="id"width="30" height="35"></th>
	</table>
	
    </center>
	</body>""" % (doc.header, doc.subtittle, doc.model, doc.power_supply, doc.user, doc.sn, doc.password, doc.batch_no, doc.ip, doc.company_name, doc.image, doc.qr_code)

    table = '<table><tr>'
    d = 0
    for i in range(50):
        if d < 5:
            table += '<td>%s</td>' % (data)
            d += 1
        else:
            d = 0
            table += '</tr><tr>'
    table += '</tr></table>'
    return table
