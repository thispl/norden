import frappe

def get_spec():
    powers = frappe.db.sql("""select specification from `tabDS General` where title like 'power consumption%'""",as_dict=True)
    for power in powers:
        spec = "".join(power.specification.split())
        print(spec)