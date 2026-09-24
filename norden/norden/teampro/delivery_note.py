import frappe
@frappe.whitelist()
def dn_contact_details(name,email,mobile,customer):
    contact = frappe.new_doc("Contact")
    contact.first_name = name
    if email:
        contact.email_id_ = email
        contact.append('email_ids',{
            'email_id': email		
        })
    if mobile:
        contact.mobile_no = mobile
        contact.append('phone_nos',{
            'phone':mobile,
        })
    contact.custom_delivery_note = 1
    contact.append('links',{
        'link_doctype':'Customer',
        "link_name": customer
    })
    contact.save(ignore_permissions=True)
    return contact.name



@frappe.whitelist()
def get_del_base_cost(name, item):
    items = frappe.db.get_all("Sales Order Item", {"parent": name, 'item_code': item}, ['*'])
    val = items[0].custom_base_rate
    landing_cost = items[0].custom_landing_rate
    incentive_cost = items[0].custom_incentive_rate
    internal_cost = items[0].custom_internal_rate
    return [val, landing_cost, incentive_cost, internal_cost]



@frappe.whitelist()
def return_dn_qty(name):
    dn_qty = frappe.db.sql(""" select delivered_qty from `tabSales Order Item` where name = '%s' """%(name),as_dict=True)[0]
    return dn_qty


@frappe.whitelist()
def get_country_name(company):
    country = frappe.db.sql("""select country from `tabCompany` where name ='%s' """%(company),as_dict=1)[0]
    return country['country']