import frappe

def get_spec():
    powers = frappe.db.sql("""select specification from `tabDS General` where title like 'power consumption%'""",as_dict=True)
    for power in powers:
        spec = "".join(power.specification.split())
        print(spec)

@frappe.whitelist()
def clear_default_warehouse():
    items = frappe.get_all('Item')
    for doc in items:
        item_defaults = frappe.get_all('Item Default',{'parent':doc['name']},['name','default_warehouse'])
        for it_df in item_defaults:
            default_warehouse = frappe.db.get_value('Item Default',{'name':it_df['name']},'default_warehouse')
            if default_warehouse:
                frappe.db.set_value('Item Default',{'name':it_df['name']},'default_warehouse',None)
                frappe.db.commit()
