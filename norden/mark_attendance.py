from curses import is_term_resized
import email
import frappe
import requests
import json
from frappe.utils.data import format_date, today 
from frappe.utils.pdf import get_pdf,cleanup
from frappe import _
import json
import datetime
from frappe.utils import (getdate, cint, add_months, date_diff, add_days,getdate,get_first_day,
	nowdate, get_datetime_str, cstr, get_datetime, now_datetime, format_datetime)
from frappe.utils.background_jobs import enqueue
from norden.custom import employee
from datetime import date, timedelta,time,datetime
from frappe.utils import flt
from frappe.utils.csvutils import read_csv_content
from frappe.utils.file_manager import get_file
from erpnext.setup.utils import get_exchange_rate
from frappe.utils import (
	add_days,
	add_months,
	add_years,
	cint,
	cstr,
	date_diff,
	flt,
	formatdate,
	get_last_day,
	get_timestamp,
	getdate,
	nowdate,
	today,
	get_first_day,
)

@frappe.whitelist()
def attendance():
	to_date = nowdate()
	first_date = get_first_day(nowdate())

	user = frappe.db.get_list("User",{'custom_att_mark':1})
	for i in user:
		user_id = i.name
		print(i.name)
		today = nowdate()
		date_obj = datetime.strptime(today, '%Y-%m-%d').date()
		previous_date = date_obj - timedelta(days=1)
		sp = str(previous_date).split("-")
		# print(sp[0])

		url = "https://nordencommunications.org:54321/person/uNameAttendance"
		

		payload={}
		headers = {
		'Content-Type': 'application/json',
		'dd': sp[2],
		'mm': sp[1],
		'yyyy': sp[0],
		'uName': user_id,
		'Authorization': 'Bearer eyJhbGciOiJIUzUxMiJ9.eyJyb2xlIjpbIlNVUEVSX0FETUlOIl0sInV1aWQiOiIjI2ExYjIzMjczLTUxYTktNGM2MS1hMmYzLTNiYmMwMDk1MTg4ZSMjIiwic3ViIjoidGVzdElkIiwiaWF0IjoxNzMwOTczNTIzLCJleHAiOjE3MzM1NjU1MjN9.GN6KjHHOLStsNkig10fu2vCTCXLWzuxIE9hXQUJ7jFoPwUJRmhkhQCWCJp54TqFrvAudSoDFf-7waxYi6aSbnQ'
		}

		response = requests.request("GET", url, headers=headers, data=payload,verify = False)
		print(response.status_code)
		print(response.headers)
		if response.status_code != 200:
			print("No data was returned from the API.")
		else:
			res = json.loads(response.text)
			input_dict = json.loads(response.text.replace("'", "\""))
			print(input_dict)
			output_dict = {}
			for key, value in input_dict.items():
				if key == 'present':
					output_dict['present']=value
				if key == 'totalAsString':
					output_dict['totalAsString']=value
				if key == 'productiveAsString':
					output_dict['productiveAsString']=value
				if key == 'taskComments':
					output_dict['taskComments']=value
					first_comment = output_dict['taskComments'][0]
					hour = first_comment.get("hour", 0)
					minute = first_comment.get("minute", 0)
					second = first_comment.get("second", 0)
					in_time = time(hour, minute, second)
					last_comment = output_dict['taskComments'][-1]
					hour = last_comment.get("hour", 0)
					minute = last_comment.get("minute", 0)
					second = last_comment.get("second", 0)
					out_time = time(hour, minute, second)
				if key == 'present':
					output_dict['present']=value
				if key == 'assignedScheduleName':
					output_dict['assignedScheduleName'] = value
				elif key == 'assignedScheduleUuid':
					output_dict['assignedScheduleUuid'] = value
				elif key == 'attendance':
					output_dict['attendance'] = value
				elif key == 'fromTimeHour':
					output_dict['fromTimeHour'] = value
				elif key == 'toTimeHour':
					output_dict['toTimeHour'] = value
				elif key == 'fromTimeMinute':
					output_dict['fromTimeMinute'] = value
				elif key == 'toTimeMinute':
					output_dict['toTimeMinute'] = value
			print(out_time)
			# if output_dict['attendance'] == "NOT_DEFINED":
			emp = frappe.db.get_value("Employee",{'user_id':user_id},['name'])
			emp_company = frappe.db.get_value("Employee",{'user_id':user_id},['company'])
			if output_dict['present'] == True:
				print(output_dict['present'])
				# print(output_dict['fromTimeHour'])
				# intime = str(output_dict['fromTimeHour'])+':'+str(output_dict['fromTimeMinute'])
				# in_time = datetime.strptime(intime, '%H:%M').time()
				# in_t = datetime.combine(previous_date, in_time)
				# in_result = str(previous_date) +" " +intime
				# # print(in_result)

				# outtime = str(output_dict['toTimeHour'])+':'+str(output_dict['toTimeMinute'])
				# out_time = datetime.strptime(outtime, '%H:%M').time()
				# out = datetime.combine(previous_date, out_time)
				# out_result = str(previous_date) +' '+ outtime
				# # print(out_result)
				# # print(output_dict['attendance'])


				
				
				if emp and emp_company:
					if frappe.db.exists("Attendance",{"employee":emp,'attendance_date':previous_date,'docstatus':('!=',2)}):
						att=frappe.get_doc("Attendance",{"employee":emp,'attendance_date':previous_date,'docstatus':('!=',2)})
						if (att.status=='On Leave' and att.leave_application) or att.status=='Work From Home':
							pass
						elif (att.status=='Half Day' and att.leave_application):
							att.custom_total_working_hours = output_dict['totalAsString']
							att.custom_productivity_hours = output_dict['productiveAsString']
							if in_time:
								att.in_time = str(previous_date) +" " +str(in_time)
							if out_time:
								att.out_time = str(previous_date) +" " +str(out_time)
							att.save(ignore_permissions=True)
						else:					
							att.status = "Present"
							if in_time:
								att.in_time = str(previous_date) +" " +str(in_time)
							if out_time:
								att.out_time = str(previous_date) +" " +str(out_time)
							att.custom_total_working_hours = output_dict['totalAsString']
							att.custom_productivity_hours = output_dict['productiveAsString']
							att.save(ignore_permissions=True)
					else:
						att = frappe.new_doc("Attendance")
						att.employee = emp
						att.attendance_date = previous_date
						att.status = "Present"
						att.company = emp_company
						if in_time:
							att.in_time = str(previous_date) +" " +str(in_time)
						if out_time:
							att.out_time = str(previous_date) +" " +str(out_time)
						att.save(ignore_permissions=True)
			elif output_dict['present'] == False:
				if emp and emp_company:
					if frappe.db.exists("Attendance",{"employee":emp,'attendance_date':previous_date}):
						pass
					else:
						att = frappe.new_doc("Attendance")
						att.employee = emp
						att.attendance_date = previous_date
						att.status = "Absent"
						att.custom_total_working_hours = output_dict['totalAsString']
						att.custom_productivity_hours = output_dict['productiveAsString']
						att.company = emp_company
						if in_time:
							att.in_time = str(previous_date) +" " +str(in_time)
						if out_time:
							att.out_time = str(previous_date) +" " +str(out_time)
						att.save(ignore_permissions=True)








		

		