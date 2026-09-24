import frappe
# @frappe.whitelist()
# def check_wfh_non_tech(fd,emp):
# 	date_string = str(fd)
# 	date_obj = datetime.strptime(date_string, "%Y-%m-%d")
# 	month = date_obj.month
# 	start_date, end_date = get_start_end_dates(2023, month)
# 	sd = start_date.strftime("%Y-%m-%d")
# 	ed = end_date.strftime("%Y-%m-%d")
# 	c = frappe.get_all("Work From Home Request",{"docstatus":1,"employee":emp,'work_from_date': ['between', (sd,ed)]},["*"])
# 	count = 0
# 	if c:
# 		for i in c:
# 			count = i.total_working_days + count
# 	return count


# @frappe.whitelist()
# def check_wfh_tech(fd,emp):
# 	date_string = str(fd)
# 	date_obj = datetime.strptime(date_string, "%Y-%m-%d")
# 	month = date_obj.month
# 	start_date, end_date = get_start_end_dates(2023, month)
# 	sd = start_date.strftime("%Y-%m-%d")
# 	ed = end_date.strftime("%Y-%m-%d")
# 	c = frappe.get_all("Work From Home Request",{"docstatus":1,"employee":emp,'work_from_date': ['between', (sd,ed)]},["*"])
# 	count = 0
# 	if c:
# 		for i in c:
# 			count = i.total_working_days + count
# 	return count