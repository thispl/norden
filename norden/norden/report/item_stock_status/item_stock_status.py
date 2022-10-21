# Copyright (c) 2013, Teampro and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from six import string_types
import frappe
import json
from frappe.utils import (getdate, cint, add_months, date_diff, add_days,
    nowdate, get_datetime_str, cstr, get_datetime, now_datetime, format_datetime)
from frappe.utils import get_first_day, today, get_last_day, format_datetime, add_years, date_diff, add_days, getdate, cint, format_date,get_url_to_form
from frappe.utils import add_months, add_days, format_time, today, nowdate, getdate, format_date
from datetime import datetime, time, timedelta
import datetime
from calendar import monthrange
from frappe import _, msgprint
from frappe.utils import flt
from frappe.utils import cstr, cint, getdate
import pandas as pd
from dateutil.relativedelta import relativedelta

def execute(filters=None):
    columns, data = [], []
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    column = [
        _('Item') + ':Data:180',
        _('Description') + ':Data:280',
        _('Unit') + ':Data:80',
        _('Norden India') + ':Data:180',
        _('UK') + ':Data:180',
        _('UAE') + ':Data:180',
        _('Singapore') + ':Data:180',
        _('Norden India Stock Value') + ':Data:180'
    ]
    return column

def get_data(filters):
    data = []
    item = frappe.get_all("Item",["*"])
    country = ["India","United Kingdom","United Arab Emirates","Singapore"]
    for i in item[:50]:
        row = [i.name,i.description,i.stock_uom]
        for c in country:
            query = """
                select sum(b.actual_qty) as qty from `tabBin` b 
                join `tabWarehouse` wh on wh.name = b.warehouse
                join `tabCompany` c on c.name = wh.company
                where c.country = '%s' and b.item_code = '%s'
                """ % (c,i.item_code)
            bins = frappe.db.sql(query,as_dict=1)[0]
            if bins['qty']:
                row += [bins['qty']]
            else:
                row += [0]
            pr = frappe.get_value("Item Price",{"price_list":"STANDARD BUYING-USD","item_code":i.item_code},["price_list_rate"])
            if not pr:
                pr = 0
            if not bins['qty']:
                bins['qty'] = 0
            st_value = pr*bins['qty']
            frappe.errprint(st_value)
            row += [st_value]
            
        # for c in country:
        #     company = frappe.get_all("Company",{"country":c},["name"])
        #     for com in company:
        #         warehouse = frappe.get_all("Warehouse",{"company":com.name},["name"])
        #         for w in warehouse:
        #             qty = frappe.get_all("Bin",{"warehouse":w.name,"item_code":i.name},['actual_qty'])
        #             for q in qty:
        #                 if q.actual_qty:
        #                     row += [q.actual_qty]
        #                 else:
        #                     row += [0]
        data.append(row)
            # if c == "India":
            #     company = frappe.get_all("Company",{"country":c},["name"])
            #     for com in company:
            #         warehouse = frappe.get_all("Warehouse",{"company":com.name},["name"])
            #         for w in warehouse:
            #             qty = frappe.get_all("Bin",{"warehouse":w.name,"item_code":i.name},['actual_qty'])
            #             for q in qty:
            #                 if q.actual_qty:
            #                     row += [q.actual_qty]
            #                 else:
            #                     row += [0]


            # if c == "United Kingdom":
            #     company = frappe.get_all("Company",{"country":c},["name"])
            #     for com in company:
            #         warehouse = frappe.get_all("Warehouse",{"company":com.name},["name"])
            #         for w in warehouse:
            #             qty = frappe.get_all("Bin",{"warehouse":w.name,"item_code":i.name},['actual_qty'])
            #             for q in qty:
            #                 if q.actual_qty:
            #                     console.log('hi')
            #                     row += [q.actual_qty]
            #                 else:
            #                     row += [0]
            
    return data
    
    
