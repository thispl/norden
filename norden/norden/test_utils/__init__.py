import frappe
from erpnext.stock.report.stock_balance.stock_balance import execute

def main():
    filters = frappe._dict({
        "company": "Norden Communication Middle East FZE",
        "from_date": "2023-01-01",
        "to_date": "2024-12-31",
        "valuation_field_type": "Currency",
        "ignore_closing_balance": 1
    })

    columns, data = execute(filters)

    total_val = 0
    total_bal_val = 0
    for row in data:
        if isinstance(row, dict):
            total_val += row.get("total_val", 0) or 0
            total_bal_val += row.get("bal_val", 0) or 0

    print(f"Total Value (total_val): {total_val}")
    print(f"Balance Value (bal_val): {total_bal_val}")
    print(f"Number of rows: {len(data)}")
