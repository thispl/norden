import frappe
from frappe.utils import time_diff
@frappe.whitelist()
def time_difference(to_time,from_time):
    value = time_diff(to_time,from_time)
    val = value.total_seconds() / 60
    total_hours = int(val // 60)
    remaining_minutes = int(val % 60)
    return f"{total_hours} hours {remaining_minutes} minutes"


@frappe.whitelist()
def minutes_calculate(to_time,from_time,amount,over_time):
    value = time_diff(to_time,from_time)
    val = value.total_seconds() / 60
    total_value=float(over_time)/60
    total_amount =float(total_value) * val
    return round(total_amount,2)


@frappe.whitelist()
def amount_calculate(total_amount):
    value=total_amount
    amount = int(value) * 12
    val = int(amount) / 365
    amt =float(val)
    cal = float(amt) / 9
    overtime = round(cal,2)
    return overtime
