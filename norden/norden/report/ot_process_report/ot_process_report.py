# Copyright (c) 2023, Teampro and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.utils import time_diff

def execute(filters=None):
	columns=get_columns(filters)
	data = get_data(filters) 
	return columns, data

def get_columns(filters):
	columns = []
	columns += [
		_("ID") + ":Link/OT Process:110",
		_("Employee") + ":Link/Employee:200",
		_("Date of Overtime")+":Date :110",
		_("Day") + ":Data:100",
		_("From Time") + ":Time:200",
		_("To Time") + ":To:200",
		_("Payable Per Hour") + ":Data:200",
		_("Total Hours") + ":Data:200",
		_("Total Amount") + ":Data:200",
	]
	return columns
def get_conditions(filters):
	conditions = ""
	if filters.get("from_date") and filters.get("to_date"):
		conditions += "  date_of_overtime between %(from_date)s and %(to_date)s"
	if filters.employee:
		conditions += " and employee= %(employee)s"
	return conditions, filters

def get_data(filters):
	data = []
	conditions, filters = get_conditions(filters)
	sa = []
	value = 0
	total_amount_sum = 0
	total_hours_sum = 0
	hours = 0
	minute = 0
	minutes = 0
	sa = frappe.db.sql("""select * from `tabOT Process` where %s """%conditions, filters,as_dict=True)
	if sa:
		for i in sa:
			row=[i.name,i.employee_name,i.date_of_overtime,i.day,i.over_time,i.from_time,i.to_time,i.total_hours,i.total_amount]
			data.append(row)
			amount =float(i.total_amount)
			total_amount_sum += amount
			value_single = time_diff(i.to_time,i.from_time)
			val = value_single.total_seconds() / 60
			total_hours = int(val // 60)
			remaining_minutes = int(val % 60)
			hours += total_hours
			minute += remaining_minutes
		# frappe.errprint(type(minute))
		if minute > 59 :
			mini = int(minute) / 60
			frappe.errprint(mini)
			m = float(mini) - int(mini)
			mm = m * 60
			minutes =int(mm) 
			tot_hou = hours + int(mini)
		else:
			tot_hou = hours
			minutes = minute
		
		total_row = ["Total", "", "", "", "", "", "",f"{tot_hou} hours {minutes} minutes",total_amount_sum]
		data.append(total_row)
	return data
	