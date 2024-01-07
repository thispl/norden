# Copyright (c) 2022, TEAMPRO and contributors
# For license information, please see license.txt

import frappe
from frappe import msgprint, _
from frappe.utils import formatdate


def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    columns = []
    columns += [
         _("Item Code") + ":Data/:150",
         _("Item Name") + ":Data/:150",
         _("Item Group") + ":Data/:180",
         _("Item Sub Group") + ":Data/:150",
         _("Norden Singapore PTE LTD") + ":Data/:150",
         _("Norden Communication Middle East FZE") + ":Data/:200",
         _("Test Norden Company") + ":Data/:100",
         _("Norden Communication Pvt Ltd") + ":Data/:100",
         _("Norden Communication UK Limited") + ":Data/:100",
         _("Sparcom Ningbo Telecom Ltd") + ":Data/:100",
         _("Norden research and Innovation Centre  Pvt. Ltd") + ":Data/:150",
         _("Norden Africa") + ":Data/:150",
         _("Norden Communication India") + ":Data/:150",
         _("NCPL -Bangalore") + ":Data/:150",
         _("Norden Singapore PTE LTD-SAARC") + ":Data/:150",
         _("Northen Communication TR LLC - Sole Proprietorship") + ":Data/:150"
    ]
    return columns

def get_data(filters):
    data = []
   
    
    item = frappe.db.sql("""select item_code,item_name,item_sub_group,item_group from `tabItem` """,as_dict = 1)
    
    # company = frappe.db.sql("""select company from `tabWarehouse` """,as_dict = 1)
    for i in item:
        
        company_stock_ns = frappe.db.sql("""
            select sum(b.actual_qty) as qty from `tabBin` b 
            join `tabWarehouse` wh on wh.name = b.warehouse
            join `tabCompany` c on c.name = wh.company
            where item_code = '%s' and wh.company = 'Norden Singapore PTE LTD'
            """%(i.item_code) ,as_dict=True)
            
        ns = []
        for cs in company_stock_ns:
            frappe.errprint('-')
        # ns.append(cs.qty)
        company_stock_me = frappe.db.sql("""
            select sum(b.actual_qty) as qty from `tabBin` b 
            join `tabWarehouse` wh on wh.name = b.warehouse
            join `tabCompany` c on c.name = wh.company
            where item_code = '%s' and wh.company = 'Norden Communication Middle East FZE'
            """%(i.item_code) ,as_dict=True)
        me =[]
        for c in company_stock_me:
            frappe.errprint('-')
        # me.append(c.qty)
        ompany_stock_tn = frappe.db.sql("""
            select sum(b.actual_qty) as qty from `tabBin` b 
            join `tabWarehouse` wh on wh.name = b.warehouse
            join `tabCompany` c on c.name = wh.company
            where item_code = '%s' and wh.company = 'Test Norden Company'
            """%(i.item_code) ,as_dict=True)
        tnc =[]
        for tn in ompany_stock_tn:
            frappe.errprint('-')
        # tnc.append(tn.qty)
        ompany_stock_nc = frappe.db.sql("""
            select sum(b.actual_qty) as qty from `tabBin` b 
            join `tabWarehouse` wh on wh.name = b.warehouse
            join `tabCompany` c on c.name = wh.company
            where item_code = '%s' and wh.company = 'Norden Communication Pvt Ltd'
            """%(i.item_code) ,as_dict=True)
        nc =[]
        for n in ompany_stock_nc:
            frappe.errprint('-')
        # nc.append(n.qty)
        ompany_stock_uk = frappe.db.sql("""
            select sum(b.actual_qty) as qty from `tabBin` b 
            join `tabWarehouse` wh on wh.name = b.warehouse
            join `tabCompany` c on c.name = wh.company
            where item_code = '%s' and wh.company = 'Norden Communication UK Limited'
            """%(i.item_code) ,as_dict=True)
        uk =[]
        for k in ompany_stock_uk:
            frappe.errprint('-')
        # uk.append(k.qty)
        ompany_stock_sn = frappe.db.sql("""
            select sum(b.actual_qty) as qty from `tabBin` b 
            join `tabWarehouse` wh on wh.name = b.warehouse
            join `tabCompany` c on c.name = wh.company
            where item_code = '%s' and wh.company = 'Sparcom Ningbo Telecom Ltd'
            """%(i.item_code) ,as_dict=True)
        sn =[]
        for s in ompany_stock_sn:
            frappe.errprint('-')
        # sn.append(s.qty)
        company_stock_nsi = frappe.db.sql("""
            select sum(b.actual_qty) as qty from `tabBin` b 
            join `tabWarehouse` wh on wh.name = b.warehouse
            join `tabCompany` c on c.name = wh.company
            where item_code = '%s' and wh.company = 'Norden Research and Innovation Centre (OPC) Pvt. Ltd'
            """%(i.item_code) ,as_dict=True)
        nsi =[]
        for si in company_stock_nsi:
            frappe.errprint('-')
        # nsi.append(si.qty)
        company_stock_na = frappe.db.sql("""
            select sum(b.actual_qty) as qty from `tabBin` b 
            join `tabWarehouse` wh on wh.name = b.warehouse
            join `tabCompany` c on c.name = wh.company
            where item_code = '%s' and wh.company = 'Norden Africa'
            """%(i.item_code) ,as_dict=True)
        na =[]
        for a in company_stock_na:
            frappe.errprint('-')
        # na.append(a.qty)
        company_stock_nci = frappe.db.sql("""
            select sum(b.actual_qty) as qty from `tabBin` b 
            join `tabWarehouse` wh on wh.name = b.warehouse
            join `tabCompany` c on c.name = wh.company
            where item_code = '%s' and wh.company = 'Norden Communication India'
            """%(i.item_code) ,as_dict=True)
        nci =[]
        for ci in company_stock_nci:
            frappe.errprint('-')
        # nci.append(ci.qty)
        company_stock_ncpl = frappe.db.sql("""
        select sum(b.actual_qty) as qty from `tabBin` b 
        join `tabWarehouse` wh on wh.name = b.warehouse
        join `tabCompany` c on c.name = wh.company
        where item_code = '%s' and wh.company = 'NCPL -Bangalore'
        """%(i.item_code) ,as_dict=True)
        ncpl =[]
        for pl in company_stock_ncpl:
            frappe.errprint('-')
        # ncpl.append(pl.qty)
        company_stock_nspl = frappe.db.sql("""
        select sum(b.actual_qty) as qty from `tabBin` b 
        join `tabWarehouse` wh on wh.name = b.warehouse
        join `tabCompany` c on c.name = wh.company
        where item_code = '%s' and wh.company = 'Norden Singapore PTE LTD-SAARC'
        """%(i.item_code) ,as_dict=True)
        nspl =[]
        for saarc in company_stock_nspl:
            frappe.errprint('-')
        # nspl.append(saarc.qty)
        company_stock_nctr = frappe.db.sql("""
        select sum(b.actual_qty) as qty from `tabBin` b 
        join `tabWarehouse` wh on wh.name = b.warehouse
        join `tabCompany` c on c.name = wh.company
        where item_code = '%s' and wh.company = 'Northen Communication TR LLC - Sole Proprietorship'
        """%(i.item_code) ,as_dict=True)
        nctr =[]
        for tr in company_stock_nctr:
            
            frappe.errprint(tr)
        # nctr.append(tr.qty)
                    
                    

    
        data.append([i.item_code or '-',i.item_name or '-',i.item_group or '-',i.item_sub_group or '-',cs.qty or '-',c.qty or '-',tn.qty or '-',n.qty or '-',k.qty or '-',s.qty or '-',si.qty or '-',a.qty or '-',ci.qty or '-',pl.qty or '-',saarc.qty or '-',tr.qty or '-'])
        
        # data.append([i.item_code,i.item_name,i.item_group,i.item_sub_group,str(ns),str(me),str(tnc),str(nc),str(uk),str(sn),str(nsi),str(na),str(nci),str(ncpl),str(nspl),str(nctr)])
    return data

