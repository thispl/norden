import frappe
from frappe.utils import today, add_months, getdate
from datetime import datetime
@frappe.whitelist()
def calc_trainee_period(joining_date):
    joining_date = (datetime.strptime(joining_date, '%Y-%m-%d')).date()
    pb_end_date = add_months(joining_date, 6)
    return pb_end_date



@frappe.whitelist()
def update_employee_no(name,employee_number):
    emp = frappe.get_doc("Employee",name)
    emps=frappe.get_all("Employee",{"status":"Active"},['*'])
    for i in emps:
        if emp.employee_number == employee_number:
            pass
        elif i.employee_number == employee_number:
            frappe.throw(f"Employee Number already exists for {i.name}")
        else:
            frappe.db.set_value("Employee",name,"employee_number",employee_number)
            frappe.rename_doc("Employee", name, employee_number, force=1)
            return employee_number


@frappe.whitelist()
def get_emp_code(code):
    emps = frappe.get_all('Employee', {'name': ('like', code+'%')}, ['name'])
    print(emps)
    emp_list = []
    for emp in emps:
        emp_list.append(emp["name"].replace(code, ''))
    if not emp_list:    
        emp_code = str(code) + "101"
    else:
        emp_code = str(code) + str(int(max(emp_list))+1)
    return emp_code



@frappe.whitelist()
def create_sales_person(emp):
    if not frappe.db.exists("Sales Person", {'employee': emp}):
        employee = frappe.get_doc('Employee', emp)
        if employee.department in ('Sales - NC', 'Sales - NCMEFD', 'Sales - NCPLB', 'Sales - NCPLP', 'Sales - NCUL', 'Sales - NSPL', 'Sales - SNTL'):
            doc = frappe.new_doc("Sales Person")
            doc.employee = emp
            doc.sales_person_name = employee.employee_name
            doc.parent_sales_person = 'Sales Team'
            if employee.reports_to:
                parent = frappe.db.get_value(
                    'Sales Person', {'is_group': 1, 'employee': employee.reports_to})
                if parent:
                    doc.parent_sales_person = parent
                else:
                    frappe.db.set_value(
                        'Sales Person', {'employee': employee.reports_to}, 'is_group', 1)
                    parent = frappe.db.get_value(
                        'Sales Person', {'is_group': 1, 'employee': employee.reports_to})
                    doc.parent_sales_person = parent
            doc.save(ignore_permissions=True)
            frappe.db.commit()



@frappe.whitelist()
def allow_holiday_list_to_user(holiday_list, user):
    user_permission = frappe.get_doc({
        'doctype': 'User Permission',
        'user': user,
        'allow': 'Holiday List',
        'for_value': holiday_list,
    })
    user_permission.insert()

    frappe.db.commit()
    return user_permission.name