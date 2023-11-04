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
)

@frappe.whitelist()
def attendance():
    to_date = today()
    first_date = get_first_day(today())
    print(to_date)
    print(first_date)

    # user = frappe.db.get_list("User",{'att_mark':1})
    # for i in user:
    #     user_id = i.name
    #     # print(i.name)
    #     today = nowdate()
    #     date_obj = datetime.strptime(today, '%Y-%m-%d').date()
    #     previous_date = date_obj - timedelta(days=1)
    #     sp = str(previous_date).split("-")

    #     url = "https://nordencommunications.org:54321/person/uNameAttendance"

    #     payload={}
    #     headers = {
    #     'Content-Type': 'application/json',
    #     'dd': sp[2],
    #     'mm': sp[1],
    #     'yyyy': sp[0],
    #     'uName': user_id,
    #     'Authorization': 'Bearer eyJhbGciOiJIUzUxMiJ9.eyJyb2xlIjpbIlNVUEVSX0FETUlOIl0sInV1aWQiOiIjI2ExYjIzMjczLTUxYTktNGM2MS1hMmYzLTNiYmMwMDk1MTg4ZSMjIiwic3ViIjoidGVzdElkIiwiaWF0IjoxNjg0NDkxNDU1LCJleHAiOjE2ODcwODM0NTV9.ds7OIWyey95sRlLfvpq1KCLQthTZhSNu6fgJEW-0liemPHfZW6gaYPTLiKm9RllE5HRaExczYu9B-x19oM7tuA'
    #     }

    #     response = requests.request("GET", url, headers=headers, data=payload,verify = False)
        
    #     if response is None:
    #         print("No data was returned from the API.")
    #     res = json.loads(response.text)
    #     input_dict = json.loads(response.text.replace("'", "\""))

    #     output_dict = {}
    #     for key, value in input_dict.items():
    #         if key == 'assignedScheduleName':
    #             output_dict['assignedScheduleName'] = value
    #         elif key == 'assignedScheduleUuid':
    #             output_dict['assignedScheduleUuid'] = value
    #         elif key == 'attendance':
    #             output_dict['attendance'] = value
    #         elif key == 'fromTimeHour':
    #             output_dict['fromTimeHour'] = value
    #         elif key == 'toTimeHour':
    #             output_dict['toTimeHour'] = value
    #         elif key == 'fromTimeMinute':
    #             output_dict['fromTimeMinute'] = value
    #         elif key == 'toTimeMinute':
    #             output_dict['toTimeMinute'] = value

    #     if output_dict['attendance'] == "PRESENT":
    #         intime = str(output_dict['fromTimeHour'])+':'+str(output_dict['fromTimeMinute'])
    #         in_time = datetime.strptime(intime, '%H:%M').time()
    #         in_t = datetime.combine(previous_date, in_time)
    #         in_result = in_t + timedelta(hours=5, minutes=30)
    #         # print(in_result)

    #         outtime = str(output_dict['toTimeHour'])+':'+str(output_dict['toTimeMinute'])
    #         out_time = datetime.strptime(outtime, '%H:%M').time()
    #         out = datetime.combine(previous_date, out_time)
    #         out_result = out + timedelta(hours=5, minutes=30)
    #         # print(out_result)
    #         # print(output_dict['attendance'])


    #         emp = frappe.db.get_value("Employee",{'user_id':user_id},['name'])
    #         att = frappe.new_doc("Attendance")
    #         att.employee = emp
    #         att.attendance_date = previous_date
    #         if output_dict['attendance'] == "PRESENT":
    #             att.status = "Present"
    #         att.in_time = in_result
    #         att.out_time = out_result
    #         att.save(ignore_permissions=True)








    

    