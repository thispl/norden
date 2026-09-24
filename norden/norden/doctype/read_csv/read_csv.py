import frappe
import pandas as pd
from frappe.model.document import Document
from frappe.utils.file_manager import get_file_path
from io import BytesIO
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
import json
from frappe.utils import (getdate, cint, add_months, date_diff, add_days,format_date,
	nowdate, get_datetime_str, cstr, get_datetime, now_datetime, format_datetime)

class ReadCSV(Document):
    pass

			
@frappe.whitelist()
def download():
	data = []
	attachments = frappe.get_single("Read CSV")
	file_doc = frappe.get_doc("File", {"file_url": attachments.attach})
	file_path = get_file_path(file_doc.file_url)  

	with open(file_path, "rb") as f:  
		file_content = f.read()  

	if file_doc.file_name.endswith(".csv"):  
		df = pd.read_csv(BytesIO(file_content))
	elif file_doc.file_name.endswith(".xlsx"):  
		df = pd.read_excel(BytesIO(file_content), engine="openpyxl")
	else:  
		frappe.throw("Unsupported file format.")  

	num_rows, num_cols = df.shape  
	s_no = 0
	for row in range(0, num_rows):
		for col in range(22, num_cols - 1):
			item = df.iloc[row, 0]
			rack = df.columns[col]
			qty = df.iloc[row, col]
			if pd.notna(qty) and qty != 0:
				s_no += 1
				frappe.msgprint(f"{s_no} | {item} | {rack} | {qty}")
				data.append([s_no, item, rack, qty])
	filename = 'RackWise Qty Item'
	build_xlsx_response(filename, data)

def make_xlsx(data, sheet_name="Sheet1", wb=None):
	if wb is None:
		wb = openpyxl.Workbook()
	
	ws = wb.active
	ws.title = sheet_name  
	ws.append(['S No', 'Item', 'Rack', 'Qty'])  
	for row in data:
		if isinstance(row, (list, tuple)):  
			ws.append(row)
		else:
			frappe.throw(f"Invalid row format: {row}")  

	xlsx_file = BytesIO()
	wb.save(xlsx_file)
	return xlsx_file

def build_xlsx_response(filename, data):
	xlsx_file = make_xlsx(data)
	frappe.response['filename'] = filename + '.xlsx'
	frappe.response['filecontent'] = xlsx_file.getvalue()
	frappe.response['type'] = 'binary'