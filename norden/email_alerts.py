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
            recipients=['hrd@nordencommunucation.com','kareem@nordencommunication.com'],
            subject=_("Birthday Remainder"),
            header=_("Birthday Remainder"),
            message = content
        )