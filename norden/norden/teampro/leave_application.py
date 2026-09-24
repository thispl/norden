import frappe
from datetime import datetime
from calendar import monthrange
# @frappe.whitelist()
# def check_leave(fd,emp):
# 	date_string = str(fd)
# 	date_obj = datetime.strptime(date_string, "%Y-%m-%d")
# 	month = date_obj.month
# 	start_date, end_date = get_start_end_dates(2023, month)
# 	sd = start_date.strftime("%Y-%m-%d")
# 	ed = end_date.strftime("%Y-%m-%d")
# 	# c = frappe.db.sql(""" select name from `tabLeave Application` where from_date between '2023-09-01' and '2022-09-30' and docstatus = 1 """ ,as_dict=1)
# 	c = frappe.get_all("Leave Application",{"docstatus":1,"employee":emp,'from_date': ['between', (sd,ed)]},["*"])
# 	count = 0
# 	if c:
# 		for i in c:
# 			count = i.total_leave_days + count
# 	return count

# def get_start_end_dates(year, month):
# 	# Create the first day of the month
# 	start_date = datetime(year, month, 1)

# 	# Get the number of days in the month
# 	_, last_day = monthrange(year, month)

# 	# Create the last day of the month
# 	end_date = datetime(year, month, last_day)

# 	return start_date, end_date