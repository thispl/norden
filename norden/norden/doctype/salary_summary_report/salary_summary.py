# import frappe
# import pandas as pd
# from frappe.utils import flt, getdate, formatdate
# from frappe.utils.xlsxutils import make_xlsx
# from openpyxl import load_workbook
# from io import BytesIO

# @frappe.whitelist()
# def export_payroll_to_excel(from_date, to_date, company):
#     # --- Step 1: Fetch categories and components ---
#     payroll_categories = [c.name for c in frappe.get_all("Payroll Category", fields=["name"])]
#     earning_components = [c.name for c in frappe.get_all(
#         "Salary Component", filters={"type": "Earning", "disabled": 0}, fields=["name"]
#     )]
#     deduction_components = [c.name for c in frappe.get_all(
#         "Salary Component", filters={"type": "Deduction", "disabled": 0}, fields=["name"]
#     )]

#     all_components = earning_components + deduction_components
#     columns = ["Payroll Category", "No. of Employees"] + all_components
#     df = pd.DataFrame(columns=columns)

#     # --- Step 2: Prepare data per category ---
#     for category in payroll_categories:
#         slips = frappe.get_all(
#             "Salary Slip",
#             filters={
#                 "start_date": ["between", [from_date, to_date]],
#                 "company": company
#             },
#             fields=["name", "employee"],
#         )

#         # Count employees from Employee Doc (Active only)
#         employee_count = frappe.db.count("Employee", filters={"payroll_category": category, "status": "Active"})
#         row = {"Payroll Category": category, "No. of Employees": employee_count}

#         slip_names = [s.name for s in slips] if slips else []

#         # Sum components
#         for comp in all_components:
#             if slip_names:
#                 total = frappe.db.sql("""
#                     SELECT SUM(sd.amount) as total
#                     FROM `tabSalary Detail` sd
#                     INNER JOIN `tabSalary Slip` ss ON sd.parent = ss.name
#                     INNER JOIN `tabEmployee` e ON ss.employee = e.name
#                     WHERE e.payroll_category = %s
#                         AND ss.name IN %s
#                         AND sd.salary_component = %s
#                 """, (category, tuple(slip_names), comp), as_dict=True)
#                 row[comp] = flt(total[0].total) if total and total[0].total else 0
#             else:
#                 row[comp] = 0

#         df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

#     # --- Step 2b: Add Grand Total row ---
#     grand_total = {"Payroll Category": "Grand Total", "No. of Employees": df["No. of Employees"].sum()}
#     for comp in all_components:
#         grand_total[comp] = df[comp].sum()
#     df = pd.concat([df, pd.DataFrame([grand_total])], ignore_index=True)

#     # --- Step 3: Convert DataFrame to Excel ---
#     data_for_excel = [list(df.columns)] + df.fillna('').values.tolist()
#     xlsx = make_xlsx(data_for_excel, sheet_name="Payroll Summary")

#     # --- Step 4: Add merged headers using openpyxl ---
#     wb = load_workbook(filename=BytesIO(xlsx.getvalue()))
#     ws = wb.active

#     # Insert 2 rows at top for Month-Year and Earnings/Deductions headings
#     ws.insert_rows(1, amount=2)

#     # Row 1 - Month-Year title
#     month_year = formatdate(from_date, "MMMM YYYY")
#     ws.cell(row=1, column=1, value=f"Payroll Summary - {month_year}")
#     ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(columns))
#     ws.cell(row=1, column=1).alignment = ws.cell(row=1, column=1).alignment.copy(horizontal="center", vertical="center")
#     ws.cell(row=1, column=1).font = ws.cell(row=1, column=1).font.copy(bold=True)

#     # Row 2 - Earnings and Deductions headings
#     earning_start = 3  # Payroll Category, No. of Employees = first 2 columns
#     earning_end = earning_start + len(earning_components) - 1
#     deduction_start = earning_end + 1
#     deduction_end = deduction_start + len(deduction_components) - 1

#     if earning_components:
#         ws.merge_cells(start_row=2, start_column=earning_start, end_row=2, end_column=earning_end)
#         ws.cell(row=2, column=earning_start, value="Earnings")
#         ws.cell(row=2, column=earning_start).alignment = ws.cell(row=2, column=earning_start).alignment.copy(horizontal="center", vertical="center")
#         ws.cell(row=2, column=earning_start).font = ws.cell(row=2, column=earning_start).font.copy(bold=True)

#     if deduction_components:
#         ws.merge_cells(start_row=2, start_column=deduction_start, end_row=2, end_column=deduction_end)
#         ws.cell(row=2, column=deduction_start, value="Deductions")
#         ws.cell(row=2, column=deduction_start).alignment = ws.cell(row=2, column=deduction_start).alignment.copy(horizontal="center", vertical="center")
#         ws.cell(row=2, column=deduction_start).font = ws.cell(row=2, column=deduction_start).font.copy(bold=True)

#     # --- Step 5: Save to response ---
#     output = BytesIO()
#     wb.save(output)

#     frappe.response.filename = f"Payroll_Summary_{month_year}.xlsx"
#     frappe.response.filecontent = output.getvalue()
#     frappe.response.type = "download"



import frappe
import pandas as pd
from frappe.utils import flt, formatdate
from frappe.utils.xlsxutils import make_xlsx
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font
from io import BytesIO
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side


@frappe.whitelist()
def export_payroll_to_excel(from_date, to_date, company):
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    header_fill = PatternFill(start_color="D7BDE2", end_color="D7BDE2", fill_type="solid")
    grand_total_fill = PatternFill(start_color="2471A3", end_color="2471A3", fill_type="solid")  # orange


    # --- Step 1: Fetch categories and components ---
    payroll_categories = [c.name for c in frappe.get_all("Payroll Category", fields=["name"])]
    earning_components = [c.name for c in frappe.get_all(
        "Salary Component", filters={"type": "Earning", "disabled": 0}, fields=["name"]
    )]
    deduction_components = [c.name for c in frappe.get_all(
        "Salary Component", filters={"type": "Deduction", "disabled": 0}, fields=["name"]
    )]

    all_components = earning_components + deduction_components
    columns = ["Particulars", "No. of Staffs", "Gross"] + all_components
    df = pd.DataFrame(columns=columns)

    # --- Step 2: Prepare data per category ---
    for category in payroll_categories:
        # Fetch active employees in category
        employees = frappe.get_all(
            "Employee",
            filters={"payroll_category": category, "status": "Active"},
            fields=["name", "gross_pay"]
        )
        employee_count = len(employees)
        total_gross = sum(flt(emp.gross_pay) for emp in employees)

        row = {
            "Particulars": category,
            "No. of Staffs": employee_count,
            "Gross": total_gross
        }

        # Fetch Salary Slips in date range
        slips = frappe.get_all(
            "Salary Slip",
            filters={
                "start_date": ["between", [from_date, to_date]],
                "company": company
            },
            fields=["name", "employee"],
        )
        slip_names = [s.name for s in slips] if slips else []

        # Sum each component from Salary Detail
        for comp in all_components:
            if slip_names:
                total = frappe.db.sql("""
                    SELECT SUM(sd.amount) as total
                    FROM `tabSalary Detail` sd
                    INNER JOIN `tabSalary Slip` ss ON sd.parent = ss.name
                    INNER JOIN `tabEmployee` e ON ss.employee = e.name
                    WHERE e.payroll_category = %s
                        AND ss.name IN %s
                        AND sd.salary_component = %s
                """, (category, tuple(slip_names), comp), as_dict=True)
                row[comp] = flt(total[0].total) if total and total[0].total else 0
            else:
                row[comp] = 0

        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

    # --- Step 2b: Add Grand Total row ---
    grand_total = {"Particulars": "Grand Total", "No. of Staffs": df["No. of Staffs"].sum(), "Gross": df["Gross"].sum()}
    for comp in all_components:
        grand_total[comp] = df[comp].sum()
    df = pd.concat([df, pd.DataFrame([grand_total])], ignore_index=True)

    component_columns = all_components.copy()
    for comp in component_columns:
        # skip 'Gross' since it's already separate
        if df[comp].sum() == 0:
            df.drop(columns=[comp], inplace=True)
            all_components.remove(comp)

    columns = ["Particulars", "No. of Staffs", "Gross"] + all_components

    # --- Step 3: Convert DataFrame to Excel ---
    data_for_excel = [list(df.columns)] + df.fillna('').values.tolist()
    xlsx = make_xlsx(data_for_excel, sheet_name="Summary")

    # --- Step 4: Open with openpyxl and format ---
    wb = load_workbook(filename=BytesIO(xlsx.getvalue()))
    ws = wb.active

    # Insert 2 rows at top for Month-Year and Earnings/Deductions headings
    ws.insert_rows(1, amount=2)

    # Row 1 - Month-Year title
    month_year = formatdate(from_date, "MMMM YYYY")
    ws.cell(row=1, column=1, value=f"{month_year}")
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(columns))
    ws.cell(row=1, column=1).alignment = Alignment(horizontal="center", vertical="center")
    ws.cell(row=1, column=1).font = Font(bold=True)

    # Recalculate components that still exist after dropping zero-only columns
    earning_components = [c for c in earning_components if c in df.columns]
    deduction_components = [c for c in deduction_components if c in df.columns]

    earning_start = 4  # Particulars, No. of Staffs, Gross = first 3 columns
    earning_end = earning_start + len(earning_components) - 1
    deduction_start = earning_end + 1
    deduction_end = deduction_start + len(deduction_components) - 1


    if earning_components:
        ws.merge_cells(start_row=2, start_column=earning_start, end_row=2, end_column=earning_end)
        ws.cell(row=2, column=earning_start, value="Additions")
        ws.cell(row=2, column=earning_start).alignment = Alignment(horizontal="center", vertical="center")
        ws.cell(row=2, column=earning_start).font = Font(bold=True)

    if deduction_components:
        ws.merge_cells(start_row=2, start_column=deduction_start, end_row=2, end_column=deduction_end)
        ws.cell(row=2, column=deduction_start, value="Deductions")
        ws.cell(row=2, column=deduction_start).alignment = Alignment(horizontal="center", vertical="center")
        ws.cell(row=2, column=deduction_start).font = Font(bold=True)

    # Make Grand Total row bold
    last_row_idx = ws.max_row
    for col in range(1, len(columns)+1):
        ws.cell(row=last_row_idx, column=col).font = Font(bold=True)
 
    header_idx = 3
    for col in range(1, len(columns)+1):
        ws.cell(row=header_idx, column=col).font = Font(bold=True)

    
    for row in range(1, 4): 
        for col in range(1, len(columns)+1):
            cell = ws.cell(row=row, column=col)
            cell.fill = header_fill
            cell.border = thin_border

    for row in range(4, ws.max_row): 
        for col in range(1, len(columns)+1):
            cell = ws.cell(row=row, column=col)
            cell.border = thin_border

    last_row_idx = ws.max_row
    for col in range(1, len(columns)+1):
        cell = ws.cell(row=last_row_idx, column=col)
        cell.font = Font(bold=True)
        cell.fill = grand_total_fill
        cell.border = thin_border




    # --- Set column widths ---
    column_widths = {
        "A": 20,  # Payroll Category
        "B": 15,  # No. of Employees
        "C": 15   # Gross
    }
    for idx, col in enumerate(all_components, start=4):
        letter = ws.cell(row=3, column=idx).column_letter
        column_widths[letter] = 15

    for col_letter, width in column_widths.items():
        ws.column_dimensions[col_letter].width = width

    # --- Step 5: Save to response ---
    output = BytesIO()
    wb.save(output)

    frappe.response.filename = f"Summary Test Report.xlsx"
    frappe.response.filecontent = output.getvalue()
    frappe.response.type = "download"
