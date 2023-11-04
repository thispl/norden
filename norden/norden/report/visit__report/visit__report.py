import frappe
from frappe import _

def execute(filters=None):
	columns, data = get_columns(filters), get_data(filters)
	return columns, data

def get_columns(filters=None):
	columns = []
	columns += [
		_("Country") + ":Link/Country:200",
		_("Date") + ":Date:95",
		_("Sales Person") + ":Link/Sales Person:200",
		_("Customer") + ":Link/Customer:200",
		_("Vertical/Industry") + ":Data:100",
		_("Solution") + ":Table Multiselect/Solution:100",
		_("Key Win Factors") + ":Small Text:100",
		_("Total Revenue") + ":Currency:100",
		_("Total Gross Margin") + ":Currency:100",
		_("Gross Margin") + ":Percentage:100",
		_("Expected Closing Date") + ":Date:100",
		_("Percentage of Close Deal") + ":Percentage:100",
		_("Remarks") + ":Small Text:200"
	]
	return columns

def get_conditions(filters):
	conditions = ""
	if filters.date_of_visit and filters.expected_closing_date:
		conditions += " AND date_of_visit BETWEEN %(date_of_visit)s AND %(expected_closing_date)s"
	if filters.get("sales_person"):
		conditions += " and sales_person = %(sales_person)s"
	if filters.get("region"):
		conditions += " and region = %(region)s"
	if filters.get("name_of_the_customer__distributor__si__eu__consultant"):
		conditions += " and name_of_the_customer__distributor__si__eu__consultant = %(name_of_the_customer__distributor__si__eu__consultant)s"
	return conditions, filters

def get_data(filters):
	data = []
	conditions, filters = get_conditions(filters)
	visit = []	
	visit = frappe.db.sql(f"""SELECT * FROM `tabVisit Report` WHERE 1 {conditions}""", filters, as_dict=True)
	if visit:
		for i in visit:
			value=frappe.get_doc("Visit Report",{"name":i.name})
			values = [j.item_sub_group for j in value.product_categories]
			value_str = ', '.join(values)
			row = [
				i.region, i.date_of_visit, i.sales_person, i.name_of_the_customer__distributor__si__eu__consultant,
				i.verticalindustry,value_str, i.key_win_factors, i.total_revenue, i.total_gross_margin,
				i.gross_margin, i.expected_closing_date, i.percentage_of_conversion, i.remarks
			]
			data.append(row)
	return data
