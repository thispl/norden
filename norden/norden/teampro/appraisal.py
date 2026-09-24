import frappe
@frappe.whitelist()
def get_appraisal(doc,method):
    emp = frappe.get_doc("Employee",{'employee_name':doc.employee_name})
    emp.set('goals',[])
    for i in doc.goals:
        emp.append("goals",{
            "kra":i.kra,
            "per_weightage":i.per_weightage,
            "req_output":i.req_output,
            "min_output":i.min_output,
            "actual_output":i.actual_output,
            "earned_score":i.score_earned
        })
        emp.save(ignore_permissions=True)




@frappe.whitelist()
def get_appraisal_template(doc,method):
    emp = frappe.get_doc("Employee",{'employee_name':doc.employee_name})
    emp.set('template',[])
    for i in doc.goals:
        emp.append("template",{
            "kra":i.kra,
            "req_output":i.req_output,
            "min_output":i.min_output,
            "per_weightage":i.per_weightage
        })
        emp.save(ignore_permissions=True)   