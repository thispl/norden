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
    columns, data = [] ,[]
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    column = [
        _('Item') + ':Data:180',
        _('Description') + ':Data:300',
        _('Item Group') + ':Data:200',
        _('Item Price') + ':Data:150',
        _('Singapore') + ':Data:150',
        _('Vietnam') + ':Data:150',
        _('Combodia') + ':Data:150',
        _('Bangladesh') + ':Data:150',
        _('Philippines') + ':Data:150',
        _('Malaysia') + ':Data:150',
        _('Indonesia') + ':Data:150',
        _('Srilanka') + ':Data:150',
        
    ]
    return column

def get_data(filters):
    data = []
    if filters.item_code:
        item = frappe.get_all("Item",{'name':filters.item_code},['*'])
    elif filters.item_group:
        item = frappe.get_all("Item",{'item_group':filters.item_group},['*'])
    else:
        item = frappe.get_all("Item",['*'])
    # sales_price = frappe.get_value("Country Margin Price",{"item_group":"Fibre Cables - Cut Piece",'country':"Singapore"},["sales"])
    # frappe.errprint(sales_price)
    country = ["Singapore","Vietnam","Combodia","Bangladesh","Philippines","Malaysia","Indonesia","Srilanka"]
    for i in item:
        item_price = frappe.get_value("Item Price",{"item_code":i.name},["price_list_rate"])
        row = [i.name,i.item_name,i.item_sub_group,item_price]
        for c in country:
            all_prices = frappe.get_value("Country Margin Price",{"item_group":i.item_sub_group,'country':c},["freight","internal","sales"])
            if not item_price:
                item_price = 0
            if all_prices:    
                freight = round(all_prices[0]/100 * item_price) + item_price
                internal = round(all_prices[1]/100 * freight) + freight
                sp = round(all_prices[2]/100 * internal) + internal
                margin_price = sp 
                if margin_price:
                    row += [round(margin_price,2)]
                else:
                    row += [0]
            else:
                row += [0]
            data.append(row)
    return data	