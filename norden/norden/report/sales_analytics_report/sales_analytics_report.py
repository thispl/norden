# Copyright (c) 2024, Teampro and contributors
# For license information, please see license.txt

import frappe
from datetime import datetime
from dateutil.relativedelta import relativedelta

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	from_date = datetime.strptime(filters.get('from_date'), '%Y-%m-%d')
	to_date = datetime.strptime(filters.get('to_date'), '%Y-%m-%d')

	num_months = (to_date.year - from_date.year) * 12 + to_date.month - from_date.month + 1

	columns = [
		{"label": "Territory", "fieldname": "territory", "fieldtype": "Data", "width": 180},
		{"label": "Total Sales", "fieldname": "total_sales", "fieldtype": "Float", "width": 160},
		{"label": "Total Quantity Sold", "fieldname": "total_qty_sold", "fieldtype": "Float", "width": 160,'hidden':1},
	]
	for i in range(num_months):
		month_year = from_date + relativedelta(months=i)
		month_label = month_year.strftime('%B %Y')
		fieldname = f"total_sales_{month_year.strftime('%B_%Y').lower().replace(' ', '_')}"
		columns.append({"label": f"{month_label}", "fieldname": fieldname, "fieldtype": "Float", "width": 160})

	return columns
def get_data(filters):
	if filters.doc_type == "Sales Invoice" or filters.doc_type == "Delivery Note" :
		field_name = 'posting_date'
	else:
		field_name = 'transaction_date'
	
	data = []
	query = """
		SELECT territory,
			SUM(base_net_total) AS total_sales,
			SUM(total_qty) AS total_qty_sold
		FROM `tab{table_name}`
		WHERE territory IS NOT NULL
		AND {field_name} BETWEEN %s AND %s
		AND company = %s
		AND docstatus = 1
		GROUP BY territory
	""".format(table_name=filters.doc_type,field_name=field_name)

	territories_data = frappe.db.sql(query, (filters.get('from_date'), filters.get('to_date'),filters.get('company')), as_dict=True)

	for territory_data in territories_data:
		territory_row = {
			"territory": territory_data.territory,
			"total_sales": territory_data.total_sales,
			"total_qty_sold": territory_data.total_qty_sold,
		}

		monthly_sales = get_monthly_sales(territory_data.territory, filters.get('from_date'), filters.get('to_date'),filters.get('company'),filters.doc_type,field_name)

		for month, sales in monthly_sales.items():
			fieldname = f"total_sales_{month.lower().replace(' ', '_')}"
			territory_row[fieldname] = sales

		data.append(territory_row)

		query = """
			SELECT customer, 
				SUM(base_net_total) AS total_sales,
				SUM(total_qty) AS total_qty_sold
			FROM `tab{table_name}`
			WHERE territory = %s
			AND company = %s
			AND docstatus = 1
			AND {field_name} BETWEEN %s AND %s
			GROUP BY customer
			""".format(table_name=filters.doc_type,field_name = field_name)
		customers = frappe.db.sql(query, (territory_data.territory,filters.get('company'),filters.get('from_date'), filters.get('to_date')), as_dict=True)

		for customer in customers:

			customer_monthly_sales = get_customer_monthly_sales(customer.customer, filters.get('from_date'), filters.get('to_date'),filters.get('company'),filters.doc_type,field_name)
			customer_row = {
				"territory": customer.customer,
				"total_sales": customer.total_sales,
				"total_qty_sold": customer.total_qty_sold,
				"indent": 1
			}

			for month, sales in customer_monthly_sales.items():
				fieldname = f"total_sales_{month.lower().replace(' ', '_')}"
				customer_row[fieldname] = sales

			data.append(customer_row)
			query = """
				SELECT item_group, 
					SUM(base_net_amount) AS total_sales,
					SUM(qty) AS total_qty_sold
				FROM `tab{table_name} Item`
				WHERE parent IN (
						SELECT name
						FROM `tab{table_name}`
						WHERE customer = %s
						AND territory = %s
						AND company = %s
						AND docstatus = 1
						AND {field_name} BETWEEN %s AND %s
					)
					GROUP BY item_group
				""".format(table_name=filters.doc_type,field_name=field_name)

			item_groups = frappe.db.sql(query, (customer.customer, territory_data.territory, filters.get('company'), filters.get('from_date'), filters.get('to_date')), as_dict=True)

			for item_group in item_groups:
				item_group_monthly_sales = get_item_group_monthly_sales(item_group.item_group, filters.get('from_date'), filters.get('to_date'),filters.get('company'),filters.doc_type,field_name,customer.customer)

				item_group_row = {
					"territory": item_group.item_group,
					"total_sales": item_group.total_sales,
					"total_qty_sold": item_group.total_qty_sold,
					"indent": 2
				}
				for month, sales in item_group_monthly_sales.items():
					fieldname = f"total_sales_{month.lower().replace(' ', '_')}"
					item_group_row[fieldname] = sales

				data.append(item_group_row)

	return data

def get_monthly_sales(territory, from_date, to_date,company,doc_type,field_name):
	monthly_sales = {}

	query = """
		SELECT 
			CONCAT(MONTHNAME({field_name}), ' ', YEAR({field_name})) AS month_year,
			SUM(base_net_total) AS total_sales
		FROM `tab{table_name}`
		WHERE territory = %s
		AND {field_name} BETWEEN %s AND %s
		AND company = %s
		AND docstatus = 1
		GROUP BY MONTH({field_name}), YEAR({field_name})
	""".format(table_name=doc_type,field_name=field_name)

	monthly_sales_data = frappe.db.sql(query, (territory, from_date, to_date,company), as_dict=True)

	for data in monthly_sales_data:
		monthly_sales[data.month_year] = data.total_sales

	return monthly_sales

def get_customer_monthly_sales(customer, from_date, to_date,company,doc_type,field_name):
	monthly_sales = {}

	query = """
		SELECT 
			CONCAT(MONTHNAME({field_name}), ' ', YEAR({field_name})) AS month_year,
			SUM(base_net_total) AS total_sales
		FROM `tab{table_name}`
		WHERE customer = %s
		AND {field_name} BETWEEN %s AND %s
		AND company = %s
		AND docstatus = 1
		GROUP BY MONTH({field_name}), YEAR({field_name})
	""".format(table_name=doc_type,field_name=field_name)

	monthly_sales_data = frappe.db.sql(query, (customer, from_date, to_date,company), as_dict=True)

	for data in monthly_sales_data:
		monthly_sales[data.month_year] = data.total_sales
	return monthly_sales

def get_item_group_monthly_sales(item_group, from_date, to_date, company, doc_type, field_name,customer):
    monthly_sales = {}

    query = """
        SELECT 
            CONCAT(MONTHNAME(si.{field_name}), ' ', YEAR(si.{field_name})) AS month_year,
            SUM(sii.base_net_amount) AS total_sales
        FROM `tab{table_name} Item` sii
        INNER JOIN `tab{table_name}` si ON si.name = sii.parent
        WHERE si.docstatus = 1
        AND sii.item_group = %s
        AND si.{field_name} BETWEEN %s AND %s
        AND si.company = %s
        AND si.customer = %s
        GROUP BY MONTH(si.{field_name}), YEAR(si.{field_name})
    """.format(table_name=doc_type, field_name=field_name)

    monthly_sales_data = frappe.db.sql(query, (item_group, from_date, to_date, company,customer), as_dict=True)

    for data in monthly_sales_data:
        monthly_sales[data.month_year] = data.total_sales

    return monthly_sales
