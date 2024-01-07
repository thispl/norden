# # Copyright (c) 2022, Teampro and contributors
# # For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import today


class ProjectReference(Document):
    pass

@frappe.whitelist()
def create_project_reference(doc,method):
    pr_id = frappe.db.exists("Project Reference",doc.project_name)
    if pr_id:
        pr = frappe.get_doc("Project Reference",pr_id)
    else:
        pr = frappe.new_doc("Project Reference")
    pr.project_name = doc.project_name 
    pr.sale_order = doc.name
    # pr.project_reference_name = doc.project_reference_name
    pr.customer_contractor = doc.customer
    pr.consultant_company = doc.consultant_company
    pr.consultant_name = doc.consultant_name
    pr.customer_contractor = doc.customer__contractor
    pr.company = doc.company
    pr.sales_person_name = doc.sales_person_name
    pr.so_submitted_date = today()
    pr.so_status_live = doc.status
    pr.end_client_user_name = doc.end_client_user_name
    pr.end_client_user_industry = doc.end_client_user_industry
    # pr.sales_order = doc.name
    for i in doc.items:
        pr.append('items_table',{
        'items_name':i.item_name,
        'qty':i.qty,
        'item_group':i.item_group
        })
    pr.flags.ignore_mandatory = True
    pr.save(ignore_permissions = True)
    # frappe.errprint(doc)
    # if doc.project_name_reference:
    # project_reference = frappe.db.exists("Project Reference", {"sales_order": doc.name})
    # if project_reference:
    #     project_reference = frappe.get_doc("Project Reference", doc.name)
    # else:
    #     project_reference = frappe.new_doc("Project Reference")
    #     frappe.errprint(project_reference)
    #     project_reference.update({
    #     "sales_order": doc.name,
    #     "project_name": doc.project_name_reference,
    #     "end_client_user_name": doc.end_client_user_name,
    #     "end_client_user_industry": doc.end_client_user_industry,
    #     "project_name_reference": doc.project_name_reference,
    #     "customer_contractor": doc.customer,
    #     "consultant_company": doc.consultant_company,
    #     "consultant_name": doc.consultant_name, 
    #     "so_submitted_date": today(),
    #     "so_status_live":doc.status,
    #     "sales_person_name": doc.sales_person_name,
    #     "company": doc.company,
    #     })
    #     for so in doc.items:
    #         project_reference.append('items_table',{
    #             'items_name':so.item_name,
    #             'qty':so.qty,
    #             'item_group':so.item_group
    #         })
    #         project_reference.flags.ignore_mandatory = True
    #         project_reference.save(ignore_permissions=True)
    #         frappe.db.commit()
