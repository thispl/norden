import frappe
from frappe import throw, _, scrub
from frappe.utils import get_url_to_form, today, add_days, nowdate
import datetime
from datetime import datetime

def opportunity_creation_alert(doc,method):
    url = get_url_to_form("Opportunity", doc.name)
    frappe.sendmail(
		recipients='nickil.ca@groupteampro.com',
		subject=_("Request for Quotation"),
		header=_("Opportunity Created"),
        message = """<p style='font-size:18px'>New Enquiry has been created for the %s - (<b>%s</b>).</p><br><p style='font-size:18px'>Requesting you to create Quotation for the Opportunity.</p><br><br>
        <form action="%s">
        <input type="submit" value="Open Opportunity" />
        </form>
        """%(doc.opportunity_from,doc.customer_name,url)
	)

def quotation_creation_alert(doc,method):
    if doc.workflow_state == 'Approved':
        url = get_url_to_form("Quotation", doc.name)
        frappe.log_error(message=url)
        frappe.sendmail(
            recipients='nikil.ca@groupteampro.com',
            subject=_("Quotation Created"),
            header=_("Quotation Created"),
            message = """<p style='font-size:18px'>As requested Quotation has been created for the %s - (<b>%s</b>).</p><br><br>
            <form action="%s">
            <input type="submit" value="View Quotation" />
            </form>
            """%(doc.quotation_to,doc.customer_name,url)
        )

def send_birthday_alert(doc,method):
    day = add_days(nowdate(),1)
    day = datetime.strptime(day,'%Y-%m-%d')
    date = day.strftime('%d')
    month = day.strftime('%m')
    emps = frappe.db.sql("""select name,date_of_birth,employee_name from `tabEmployee` where day(date_of_birth) = %s and month(date_of_birth) = %s """%(date,month),as_dict=True)
    content = """Dear Sir/Madam,<br><br>Kindly find the List of Employees having birthday Tomorrow.<br><br>"""
    table = "<table class='table table-bordered'><tr><th>S.No</th><th>Employee ID</th><th>Employee Name</th></tr>"
    i = 1
    for emp in emps:
        table += "<tr><td>%s</td><td>%s</td><td>%s</td></tr>"%(i,emp.name,emp.employee_name)
        i += 1
    content += table + "</table><br><br>Thanks & Regards,<br>ERP"
    # print(content)
    frappe.sendmail(
            recipients=['hrd@nordencommunucation.com'],
            subject=_("Birthday Remainder"),
            header=_("Birthday Remainder"),
            message = content
        )


@frappe.whitelist()
def appraisal_remainder_mail():
    role_name = "HOD"
    user_list = frappe.get_list("Has Role", fields=["parent"], filters={"role": role_name})
    for user in user_list:
        # print(user.parent)
        header = """<p>Dear Sir/Mam, <br> Please find the below list of Application pending for your Approval.</p><table class='table table-bordered'> """
        regards = "Thanks & Regards,<br>hrPRO"
        # table_html = ''
        emp = frappe.get_value("Employee",{'user_id':user.parent},['employee'])
        user_per = frappe.get_list("User Permission",{'user':user.parent,'allow':"Employee"},['for_value'])
    
        # table_html += '<table class="table table-bordered" style="width:100% ; background-color:steelblue;color:white"><tr><td colspan = 4 style="border: 1px solid black">Leave Application ID</td><td colspan = 4 style="border: 1px solid black">Employee Id</td><td colspan = 4 style="border: 1px solid black">Employee Name</td><td colspan = 4 style="border: 1px solid black">From Date</td><td colspan = 4 style="border: 1px solid black">To Date</td><td colspan = 4 style="border: 1px solid black">Leave Type</td></tr>'         
        for user_per_list in user_per:
            if user_per_list.for_value != emp:
                empl = frappe.get_list("Employee", {'employee': user_per_list.for_value},['*'])
                for emplo in empl:
                    print("hii")
                    if emplo.employment_type == "Full Time":
                        print(emplo.employment_type)
                        emp_doj = frappe.get_list('Employee' ,{'employee': emplo},["date_of_joining"])
                        print(emp_doj)

            
from datetime import datetime, timedelta
from frappe.utils.background_jobs import enqueue
@frappe.whitelist()
def work_anniversary_reminder_to_shoba():
	message = _("Dear Mam,<br><br>A friendly reminder of future important dates for our team.<br><br>Let’s congratulate them on their work anniversary!<br><br>")
	employees = frappe.db.sql("""SELECT name, employee_name, department, date_of_joining
	FROM `tabEmployee`
	WHERE status = 'Active'
	AND company = "Norden Communication Middle East FZE"
	ORDER BY date_of_joining""", as_dict=True)
	emp_set = set()
	today = datetime.now().date()
	future_date = today + timedelta(days=14)
	for emp in employees:
		employee_hire_date = emp.date_of_joining
		upcoming_anniversary = datetime(today.year, employee_hire_date.month, employee_hire_date.day).date()
		if today <= upcoming_anniversary <= future_date:
			diff_years = today.year - employee_hire_date.year - ((today.month, today.day) < (employee_hire_date.month, employee_hire_date.day))
			if diff_years in [5.0, 10.0, 15.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0, 30.0, 31.0, 32.0, 33.0, 34.0, 35.0]:
				emp_tuple = (emp["name"], emp["employee_name"], emp["department"], emp["date_of_joining"], diff_years)
				emp_set.add(emp_tuple)
		half_year_anniversary = employee_hire_date + timedelta(days=183)
		if today <= half_year_anniversary <= future_date:
			emp_tuple_half_year = (emp["name"], emp["employee_name"], emp["department"], emp["date_of_joining"], 0.5 )
			emp_set.add(emp_tuple_half_year)
	if emp_set:
		sorted_emp_set = sorted(emp_set, key=lambda x: (x[3], x[0]))
		message += '<table class="table table-bordered"><tr><th>Employee ID</th><th>Employee Name</th><th>Department</th><th>Date of Joining</th><th>Work Anniversary Completed</th></tr>'
		for emp_tuple in sorted_emp_set:
			message += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s years</td></tr>'%(emp_tuple[0], emp_tuple[1], emp_tuple[2], format_date(emp_tuple[3]), emp_tuple[4])
		message += '</table>'
		email_args = {
			"message": message,
			"recipients": ["veeramayandi.p@groupteampro.com","sobha@nordenco.ae"],
			"subject": "Work Anniversary Reminder"
		}
		enqueue(method=frappe.sendmail, queue='short', timeout=300, is_async=True, **email_args)

@frappe.whitelist()
def work_anniversary_reminder_to_employees():
	message = _("Dear Mam/Sir,<br><br>A friendly reminder of future important dates for our team.<br><br>Let’s congratulate them on their work anniversary!<br><br>")
	employees = frappe.db.sql("""SELECT *
		FROM `tabEmployee`
		WHERE status = 'Active'
		AND company = "Norden Communication Middle East FZE"
		ORDER BY date_of_joining""", as_dict=True)
	emp_set = set()
	today = datetime.now().date()  # Assuming you want today's date
	future_date = today + timedelta(days=14)
	for emp in employees:
		employee_hire_date = emp.date_of_joining
		upcoming_anniversary = datetime(today.year, employee_hire_date.month, employee_hire_date.day).date()
		if today <= upcoming_anniversary <= future_date:
			diff_years = today.year - employee_hire_date.year - ((today.month, today.day) < (employee_hire_date.month, employee_hire_date.day))
			if diff_years in [5.0, 10.0, 15.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0, 30.0, 31.0, 32.0, 33.0, 34.0, 35.0]:
				emp_tuple = (emp["name"], emp["employee_name"], emp["department"], emp["date_of_joining"], diff_years)
				emp_set.add(emp_tuple)
		half_year_anniversary = employee_hire_date + timedelta(days=183)
		if today <= half_year_anniversary <= future_date:
			emp_tuple_half_year = (emp["name"], emp["employee_name"], emp["department"], emp["date_of_joining"], 0.5 )
			emp_set.add(emp_tuple_half_year)
	if len(emp_set) > 1:
		sorted_emp_set = sorted(emp_set, key=lambda x: (x[3], x[0]))
		for emp in employees:
			recipients = emp.user_id or emp.company_email or emp.personal_email
			if recipients:
				message += '<table class="table table-bordered"><tr><th>Employee ID</th><th>Employee Name</th><th>Department</th><th>Date of Joining</th><th>Work Anniversary Completed</th></tr>'
				for emp_tuple in sorted_emp_set:
					if emp["name"] != emp_tuple[0]:
						message += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s years</td></tr>'%(emp_tuple[0], emp_tuple[1], emp_tuple[2], format_date(emp_tuple[3]), emp_tuple[4])
				message += '</table>'
				email_args = {
					"message": message,
					"recipients": [recipients],
					"subject": "Work Anniversary Reminder"
				}
				enqueue(method=frappe.sendmail, queue='short', timeout=300, is_async=True, **email_args)
	elif len(emp_set) == 1:
		sorted_emp_set = sorted(emp_set, key=lambda x: (x[3], x[0]))
		for emp in employees:
			recipients = emp.user_id or emp.company_email or emp.personal_email
			if recipients:
				message += '<table class="table table-bordered"><tr><th>Employee ID</th><th>Employee Name</th><th>Department</th><th>Date of Joining</th><th>Work Anniversary Completed</th></tr>'
				for emp_tuple in sorted_emp_set:
					if emp["name"] != emp_tuple[0]:
						message += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s years</td></tr>'%(emp_tuple[0], emp_tuple[1], emp_tuple[2], format_date(emp_tuple[3]), emp_tuple[4])
						message += '</table>'
						email_args = {
							"message": message,
							"recipients": [recipients],
							"subject": "Work Anniversary Reminder"
						}
						enqueue(method=frappe.sendmail, queue='short', timeout=300, is_async=True, **email_args)
	  