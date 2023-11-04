# Copyright (c) 2013, Teampro and contributors
# For license information, please see license.txt

from dataclasses import dataclass
from logging import basicConfig
import frappe
from datetime import date, timedelta
from frappe import get_request_header, msgprint, _
from frappe.utils import cstr, cint, getdate
from frappe.utils import cstr, add_days, date_diff, getdate, get_last_day,get_first_day
from datetime import date, timedelta, datetime


def execute(filters=None):
	columns,data = [],[]
	columns = get_columns()
	data = get_data(filters)
	return columns,data 

def get_columns():
	columns = [
		_('Employee') +':Data:100',_('Employee Name') + ':Data:100',_('Date of Joining') + ':Data:100',_('Date of Birth') + ':Data:100',

		_('Designation') + ':Data:100',_('Region') + ':Data:100',_('Company') + ':Data:100',_('Start Date') + ':Data:100',_('End Date') + ':Data:100',

		_('Basic') + ':Data:100',_('HRA') + ':Data:100',_('Conveyance') +':Data:100',_('Vehicel & Fuel Allowance')  +':Data:100',

		_('Special Allowance') +':Data:100',_('CTC') +':Data:100',_('Arrears') +':Data:100',_('Overtime') +':Data:100',_('Gift') +':Data:100',_('Leave Encashemet') +':Data:100',

		_('Internet') + ':Data:100',_('Gross Pay') +':Data:100',_('Professional Tax') +':Data:100',_('EPF') +':Data:100',_('ESI') +':Data:100',

		_('Advance Deduction') +':Dataa:100',_('TDS') +':Data:100',_('Loss Of Pay') +':Data:100',_('Total Deduction') +':Data:100',_('Net Pay') +':Data:100',

		_('Working Days') +':Data:100',_('Payment  Days') +':Data:100',_('Lop Days') +':Data:100'
	]
	return columns

def get_data(filters):
	data = []
	if filters.employee:
		salary_slip = frappe.db.get_all('Salary Slip',{'employee':filters.employee,'start_date':filters.from_date},['*'])
	else:
		salary_slip = frappe.db.get_all('Salary Slip',{'start_date':filters.from_date},['*'])
	if filters.company:
		salary_slip = frappe.db.get_all('Salary Slip',{'company':filters.company,'start_date':filters.from_date},['*'])
	else:
		salary_slip = frappe.db.get_all('Salary Slip',{'start_date':filters.from_date},['*'])

	for ss in salary_slip:
		emp = frappe.get_doc('Employee',{'employee':ss.employee},['*'])
		frappe.errprint(emp)
		basic = frappe.db.get_value('Salary Detail',{'abbr':'B','parent':ss.name},'amount')
		hra = frappe.db.get_value('Salary Detail',{'abbr':'HRA','parent':ss.name},'amount')
		conveyance = frappe.db.get_value('Salary Detail',{'abbr':'CNV','parent':ss.name},'amount')	
		vfa = frappe.db.get_value('Salary Detail',{'abbr':'VFA','parent':ss.name},'amount')	
		sa = frappe.db.get_value('Salary Detail',{'abbr':'SA','parent':ss.name},'amount')
		ctc = frappe.db.get_value('Salary Detail',{'abbr':'CTC','parent':ss.name},'amount')
		arrears = frappe.db.get_value('Salary Detail',{'abbr':'A','parent':ss.name},'amount')
		ot = frappe.db.get_value('Salary Detail',{'abbr':'OT','parent':ss.name},'amount')
		gift = frappe.db.get_value('Salary Detail',{'abbr':'G','parent':ss.name},'amount')
		leave_encashment  = frappe.db.get_value('Salary Detail',{'abbr':'LE','parent':ss.name},'amount')	
		internet = frappe.db.get_value('Salary Detail',{'abbr':'I','parent':ss.name},'amount')	
		professional_tax = frappe.db.get_value('Salary Detail',{'abbr':'PT','parent':ss.name},'amount')
		epf = frappe.db.get_value('Salary Detail',{'abbr':'PF','parent':ss.name},'amount')
		esi = frappe.db.get_value('Salary Detail',{'abbr':'ESI','parent':ss.name},'amount')
		ad = frappe.db.get_value('Salary Detail',{'abbr':'AD','parent':ss.name},'amount')
		tds = frappe.db.get_value('Salary Detail',{'abbr':'TDS','parent':ss.name},'amount')
		lop = frappe.db.get_value('Salary Detail',{'abbr':'LOP','parent':ss.name},'amount')

		row = [
			ss.employee,frappe.get_value('Employee',ss.employee,"employee_name"),emp.date_of_joining,emp.date_of_birth,ss.designation,ss.region,ss.company,ss.start_date,ss.end_date,
			basic,hra,conveyance,vfa,sa,ctc,arrears,ot,gift,leave_encashment,internet,ss.gross_pay,professional_tax,epf,esi,ad,tds,lop,
			ss.total_deduction,ss.net_pay,ss.total_working_days,ss.payment_days,ss.leave_without_pay
		]	
		data.append(row)
	return data
