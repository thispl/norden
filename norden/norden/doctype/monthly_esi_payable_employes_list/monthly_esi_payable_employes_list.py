# Copyright (c) 2022, Teampro and contributors
# For license information, please see license.txt

import frappe

from frappe.model.document import Document
from datetime import date, timedelta
from frappe.utils import flt


class MonthlyESIPayableEmployesList(Document):
    def validate(self):
        
        sps = frappe.get_all('Salary Slip',{'start_date':self.select_payroll_date})
        # frappe.errprint(total_num_of_employees)
        eesi = 0
        empsi=0
        for sp in sps:
            amt = frappe.db.sql(""" select count(`tabSalary Detail`.salary_component) as count from `tabSalary Slip` left join `tabSalary Detail` on `tabSalary Slip`.name=`tabSalary Detail`.parent where `tabSalary Detail`.salary_component='Employer Employee State Insurance' """,as_dict=True)[0]
            self.total_no_of_employees = amt["count"]
            gross = frappe.db.sql(""" select sum(`tabSalary Slip`.gross_pay) as sum from `tabSalary Slip` left join `tabSalary Detail` on `tabSalary Slip`.name=`tabSalary Detail`.parent where `tabSalary Detail`.salary_component='Employer Employee State Insurance' """,as_dict=True)[0]
            self.total_wages = gross["sum"]
            # frappe.errprint(gross["sum"])

            eesi_amt = frappe.db.sql("""select amount from `tabSalary Detail` where salary_component = 'Employer Employee State Insurance' and parent = '%s'  """ % sp['name'],as_dict=1)
            if eesi_amt:
                eesi += flt(eesi_amt[0]['amount'])
                self.employers_contribution =eesi
        
            esi_amt = frappe.db.sql("""select amount from `tabSalary Detail` where salary_component = 'Employee State Insurance' and parent = '%s'  """ % sp['name'],as_dict=1)
            if esi_amt:
                empsi += flt(esi_amt[0]['amount'])
                # frappe.errprint(esi_amt[0])
                self.employees_contribution =empsi

                self.total= self.employees_contribution + self.employers_contribution
                # frappe.errprint(self.total)
        
        