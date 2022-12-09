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

def execute(filters=None):
	columns, data = [] ,[]
	columns = get_columns(filters)
	frappe.errprint(columns)
	data = get_data(filters)
	return columns, data


def get_columns(filters):
	nspl_column = [
		_('Item') + ':Data:180',
		_('Item Name') + ':Data:300',
		_('Freight') + ':Currency:100',
		_('Internal Cost') + ':Currency:100',
		_('Sales price') + ':Currency:100',
		# _('Selling Price') + ':Currency:150',
		# _('Internal_cost') + ':Currency:100',
		# # _('Warehouse') + ':Data:120',
		# _('Stock UOM') + ':Data:150',
		# _('Balance') + ':Data:150',
	]

	ncpl_column = [
		_('Item') + ':Data:180',
		_('Item Name') + ':Data:300',
		_('India landing') + ':float:100',
		_('India SPC') + ':float:100',
		_('India STP') + ':float:100',
		_('India DTP') + ':float:100',
		_('India LTP') + ':float:100',
		_('India MOP') + ':float:100',
		_('India MRP') + ':float:100',
		# _('Selling Price') + ':Currency:150',
		# _('Internal_cost') + ':Currency:100',
		# # _('Warehouse') + ':Data:120',
		# _('Stock UOM') + ':Data:150',
		# _('Balance') + ':Data:150',
	]

	ncmef_column = [
		_('Item') + ':Data:180',
		_('Item Name') + ':Data:300',
		_('Landing') + ':float:100',
		_('Incentive') + ':float:100',
		_('Internal') + ':float:100',
		_('Distributor') + ':float:100',
		_('Saudi') + ':float:100',
		_('Project') + ':float:100',
		_('Retail') + ':float:100',
		_('Electra') + ':float:100',
		# _('Selling Price') + ':Currency:150',
		# _('Internal_cost') + ':Currency:100',
		# # _('Warehouse') + ':Data:120',
		# _('Stock UOM') + ':Data:150',
		# _('Balance') + ':Data:150',
	]

	ncul_column = [
		_('Item') + ':Data:180',
		_('Item Name') + ':Data:300',
		_('Freight') + ':float:100',
		_('Destination') + ':float:100',
		_('Installer') + ':float:100',
		_('Distributor') + ':float:100',
		# _('Saudi') + ':float:100',
		# _('Project') + ':float:100',
		# _('Selling Price') + ':Currency:150',
		# _('Internal_cost') + ':Currency:100',
		# # _('Warehouse') + ':Data:120',
		# _('Stock UOM') + ':Data:150',
		# _('Balance') + ':Data:150',
	]

	v_column = [
		_('Item') + ':Data:180',
		_('Item Name') + ':Data:300',
		_('Freight') + ':Currency:100',
		_('Internal Cost') + ':Currency:100',
		_('Sales price') + ':Currency:100',
		# _('Selling Price') + ':Currency:150',
		# _('Internal_cost') + ':Currency:100',
		# # _('Warehouse') + ':Data:120',
		# _('Stock UOM') + ':Data:150',
		# _('Balance') + ':Data:150',
	]

	i_column = [
		_('Item') + ':Data:180',
		_('Item Name') + ':Data:300',
		_('Freight') + ':Currency:100',
		_('Internal Cost') + ':Currency:100',
		_('Sales price') + ':Currency:100',
		# _('Selling Price') + ':Currency:150',
		# _('Internal_cost') + ':Currency:100',
		# # _('Warehouse') + ':Data:120',
		# _('Stock UOM') + ':Data:150',
		# _('Balance') + ':Data:150',
	]

	m_column = [
		_('Item') + ':Data:180',
		_('Item Name') + ':Data:300',
		_('Freight') + ':Currency:100',
		_('Internal Cost') + ':Currency:100',
		_('Sales price') + ':Currency:100',
		# _('Selling Price') + ':Currency:150',
		# _('Internal_cost') + ':Currency:100',
		# # _('Warehouse') + ':Data:120',
		# _('Stock UOM') + ':Data:150',
		# _('Balance') + ':Data:150',
	]

	b_column = [
		_('Item') + ':Data:180',
		_('Item Name') + ':Data:300',
		_('Freight') + ':Currency:100',
		_('Internal Cost') + ':Currency:100',
		_('Sales price') + ':Currency:100',
		# _('Selling Price') + ':Currency:150',
		# _('Internal_cost') + ':Currency:100',
		# # _('Warehouse') + ':Data:120',
		# _('Stock UOM') + ':Data:150',
		# _('Balance') + ':Data:150',
	]

	s_column = [
		_('Item') + ':Data:180',
		_('Item Name') + ':Data:300',
		_('Freight') + ':Currency:100',
		_('Internal Cost') + ':Currency:100',
		_('Sales price') + ':Currency:100',
		# _('Selling Price') + ':Currency:150',
		# _('Internal_cost') + ':Currency:100',
		# # _('Warehouse') + ':Data:120',
		# _('Stock UOM') + ':Data:150',
		# _('Balance') + ':Data:150',
	]

	p_column = [
		_('Item') + ':Data:180',
		_('Item Name') + ':Data:300',
		_('Freight') + ':Currency:100',
		_('Internal Cost') + ':Currency:100',
		_('Sales price') + ':Currency:100',
		# _('Selling Price') + ':Currency:150',
		# _('Internal_cost') + ':Currency:100',
		# # _('Warehouse') + ':Data:120',
		# _('Stock UOM') + ':Data:150',
		# _('Balance') + ':Data:150',
	]

	a_column = [
		_('Item') + ':Data:180',
		_('Item Name') + ':Data:300',
		_('Landing') + ':Currency:100',
		_('Margin') + ':Currency:100',
		_('Dealer') + ':Currency:100',
		_('Customer') + ':Currency:100',
		# _('Selling Price') + ':Currency:150',
		# _('Internal_cost') + ':Currency:100',
		# # _('Warehouse') + ':Data:120',
		# _('Stock UOM') + ':Data:150',
		# _('Balance') + ':Data:150',
	]

	if filters.territory == "Singapore":
		return nspl_column
	if filters.territory == "India":
		return ncpl_column
	if filters.territory == "Dubai":
		return ncmef_column
	if filters.territory == "United Kingdom":
		return ncul_column
	if filters.territory == "Vietnam":
		return v_column
	if filters.territory == "Indonesia":
		return i_column
	if filters.territory == "Malaysia":
		return m_column
	if filters.territory == "Bangladesh":
		return b_column
	if filters.territory == "Srilanka":
		return s_column
	if filters.territory == "Philippines":
		return p_column
	if filters.territory == "Africa":
		return a_column



def get_data(filters):
	data = []
	item = frappe.get_all("Item",["item_code","item_name"])	
	for i in item:
		if filters.territory == "Singapore":
			Singapore_freight = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Singapore Freight"},["price_list_rate"])
			Singapore_internal_cost = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Singapore Internal Cost"},["price_list_rate"])
			Singapore_sales_price = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Singapore Sales Price"},["price_list_rate"])
			row = [i.item_code,i.item_name,Singapore_freight,Singapore_internal_cost,Singapore_sales_price]

		if filters.territory == "India":
			india_landing = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"India Landing"},["price_list_rate"])
			india_spc = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"India SPC"},["price_list_rate"])
			india_stp = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"India STP"},["price_list_rate"])
			india_dtp = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"India DTP"},["price_list_rate"])
			india_ltp = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"India LTP"},["price_list_rate"])
			india_mop = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"India MOP"},["price_list_rate"])
			india_mrp = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"India MRP"},["price_list_rate"])
			row = [i.item_code,i.item_name,india_landing,india_spc,india_stp,india_dtp,india_ltp,india_mop,india_mrp]

		
		if filters.territory == "Dubai":
			landing = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Landing - NCMEF"},["price_list_rate"])
			incentive = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Incentive - NCMEF"},["price_list_rate"])
			internal = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Internal - NCMEF"},["price_list_rate"])
			dist = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Dist. Price - NCMEF"},["price_list_rate"])
			saudi = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Saudi Dist. - NCMEF"},["price_list_rate"])
			project = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Project Group - NCMEF"},["price_list_rate"])
			retail = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Retail - NCMEF"},["price_list_rate"])
			electra = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Electra Qatar - NCMEF"},["price_list_rate"])
			cost_rate = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Cost Rate - NCMEF"},["price_list_rate"])
			base_sales_price = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Base Sales Price - NCMEF"},["price_list_rate"])
			row = [i.item_code,i.item_name,landing,incentive,internal,dist,saudi,project,retail,electra]
		
		if filters.territory == "United Kingdom":
			uk_freight= frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"UK Freight Cost"},["price_list_rate"])
			uk_desitination = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"UK Destination Charges"},["price_list_rate"])
			uk_installer = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"UK Installer Price"},["price_list_rate"])
			uk_distributor = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"UK Distributor Price"},["price_list_rate"])
			row = [i.item_code,i.item_name,uk_freight,uk_desitination,uk_installer,uk_distributor]

		if filters.territory == "Vietnam":
			v_freight = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Vietnam Freight"},["price_list_rate"])
			v_internal_cost = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Vietnam Internal Cost"},["price_list_rate"])
			v_sales_price = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Vietnam Sales Price"},["price_list_rate"])
			row = [i.item_code,i.item_name,v_freight,v_internal_cost,v_sales_price]

		if filters.territory == "Indonesia":
			i_freight = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Indonesia Freight"},["price_list_rate"])
			i_internal_cost = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Indonesia Internal Cost"},["price_list_rate"])
			i_sales_price = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Indonesia Sales Price"},["price_list_rate"])
			row = [i.item_code,i.item_name,i_freight,i_internal_cost,i_sales_price]

		if filters.territory == "Malaysia":
			m_freight = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Malaysia Freight"},["price_list_rate"])
			m_internal_cost = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Malaysia Internal Cost"},["price_list_rate"])
			m_sales_price = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Malaysia Sales Price"},["price_list_rate"])
			row = [i.item_code,i.item_name,m_freight,m_internal_cost,m_sales_price]

		if filters.territory == "Bangladesh":
			b_freight = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Bangladesh Freight"},["price_list_rate"])
			b_internal_cost = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Bangladesh Internal Cost"},["price_list_rate"])
			b_sales_price = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Bangladesh Sales Price"},["price_list_rate"])
			row = [i.item_code,i.item_name,b_freight,b_internal_cost,b_sales_price]

		if filters.territory == "Srilanka":
			s_freight = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Srilanka Freight"},["price_list_rate"])
			s_internal_cost = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Srilanka Internal Cost"},["price_list_rate"])
			s_sales_price = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Srilanka Sales Price"},["price_list_rate"])
			row = [i.item_code,i.item_name,s_freight,s_internal_cost,s_sales_price]

		if filters.territory == "Philippines":
			p_freight = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"philippines Freight"},["price_list_rate"])
			p_internal_cost = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"philippines Internal Cost"},["price_list_rate"])
			p_sales_price = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"philippines Sales Price"},["price_list_rate"])
			row = [i.item_code,i.item_name,p_freight,p_internal_cost,p_sales_price]

		if filters.territory == "Africa":
			a_landing = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Africa Landing Cost"},["price_list_rate"])
			a_margin = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Africa Sales Price"},["price_list_rate"])
			a_dealer = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Africa Dealer Price"},["price_list_rate"])
			a_customer = frappe.get_value("Item Price",{"item_code":i.item_code,"price_list":"Africa Customer Price"},["price_list_rate"])

			row = [i.item_code,i.item_name,a_landing,a_margin,a_dealer,a_customer]
		
		data.append(row)
	return data	

	 