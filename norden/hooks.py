# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "norden"
app_title = "Norden"
app_publisher = "Teampro"
app_description = "Norden"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "sarumathy.d@groupteampro.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/norden/css/norden.css"
# app_include_js = "/assets/norden/js/norden.js"

# include js, css files in header of web template
# web_include_css = "/assets/norden/css/norden.css"
# web_include_js = "/assets/norden/js/norden.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "norden/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "norden.install.before_install"
# after_install = "norden.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "norden.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Leave Application":"norden.overrides.CustomLeaveApplication",
	"Expense Claim":"norden.overrides.CustomExpenseClaim",
	"Attendance Request":"norden.overrides.CustomAttendanceRequest",
    "Salary Slip":"norden.overrides.CustomSalarySlip"
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Item Inspection":{
		"on_submit": ["norden.custom.update_qc_status","norden.custom.update_qc_status_stock","norden.custom.to_reserve_on_inspection"],
	
		# "on_update": "norden.custom.item_ins_serial"
	},
	"Item":{
		"after_insert": "norden.utils.item_default_wh",
	},
	"Item Price":{
		"validate":'norden.custom.validate_item_price_list'
	},
	"Stock Reservation Entry":{
		"after_insert": "norden.utils.update_reserve_status",
		"on_cancel": "norden.utils.revert_reserve_status"
	},

	"Stock Entry":{
		"on_submit": ["norden.utils.create_sti","norden.utils.update_sn"],
		"before_submit":["norden.utils.add_itemwise_additional_cost","norden.custom.check_rack_qty_stock_entry"],
		"before_cancel":"norden.utils.reversing_se",
		# "on_cancel":"norden.custom.cancel_stock_entry_name"
	},
    "Work From Home Request":{
		"on_submit": "norden.utils.wfh_approval_mail",
	},

	# "Serial No":{
	# 	"after_insert":[
	# 	"norden.utils.update_sn",],
		# "validate": "norden.custom.get_foc_item",
		
	# },
	
	"Opportunity": {
		# "after_insert": "norden.email_alerts.opportunity_creation_alert",
		# "validate" : "norden.custom.create_opp_file_number",
        "on_submit":"norden.custom.get_file_number",
	},
	# "Quotation": {
		# "on_update": "norden.email_alerts.quotation_creation_alert",
	# },
	
	# "Landed Cost Voucher": {
	# 	"on_submit": "norden.custom.create_lcv_je",
	# },
    "Purchase Invoice":{
        "on_trash": "norden.utility.pe_on_trash",
        # "after_insert":"norden.custom.set_discount_value",
	},
     "Rack Transfer":{
		"on_submit": "norden.custom.create_stock_entry",

	},
	"Purchase Receipt": {
		# "on_update_after_submit":"norden.utils.create_stock_transfer_india",
		"after_submit": ["norden.custom.create_lcv",
		],
        # "on_submit": "norden.custom.to_reserve_on_pr",
        # "on_update": "norden.custom.hide_inspect_button",
    
		# 'on_submit':'norden.utils.create_stock_transfer_india',
		# "on_submit": "norden.custom.update_sn_pr",

		# "on_submit": "norden.custom.check_pr",
		# 'validate':'norden.utils.create_product_testing',
		
		"on_submit": [
      	# "norden.custom.check_item_inspection",
       	# "norden.custom.pr_create",
		"norden.custom.get_foc_item_pr",
		"norden.utils.update_sn_pr", 
		"norden.custom.create_mrb",
		"norden.utils.create_stock_transfer_india",
        "norden.custom.automate_inspect_creation",
        # "norden.custom.to_reserve_on_pr",
		
		],
        "before_cancel":"norden.utils.reverse_sti_pr"
	},
	"Logistics Request": {
		"on_submit": "norden.custom.create_landed_cost_voucher",
		# "after_insert":"norden.utils.set_requester_name"
	},

	# "MRB": {
	# 	"on_update":"norden.custom.mrb_create"
	# 	# "validate": "norden.utils.transfer_to_scrap",
	# },

	"Material Request": {
		# "validate": "norden.custom.create_file_number_mr",
        "on_submit":"norden.custom.get_file_number",
	},
	"Employee Promotion": {
		"on_update": "norden.custom.update_appraisal_template",
	},
	"Sales Order": {
		"on_submit": ["norden.custom.update_marcom",
        "norden.custom.update_base_rate_new"
                ],
		"validate":"norden.utils.check_credit_limit"

	},
	"Sales Person":{
		"after_insert":"norden.custom.create_cluster_and_update_up"
	},
	"Sales Invoice": {
        "after_insert":"norden.custom.update_invoice_number",
        "on_trash": "norden.utility.pe_on_trash",
		"validate":'norden.custom.validate_taxes_presence',
        "on_cancel":'norden.custom.invoice_cancel',
        "before_insert":'norden.utils.update_si_naming_series'
	},
	"Travel Request":{
		"on_submit": "norden.custom.create_employee_advance",

	},
	# "Appraisal Template":{
	# 	"on_update": "norden.custom.get_appraisal_kra"
	# },
	"Appraisal":{
		"on_update": "norden.custom.get_appraisal"
	},
    
    "Appraisal Template":{
		"on_update": "norden.custom.get_appraisal_template"
		# "validate": "norden.custom.get_appraisal_kra"
	},

	"Quotation": {

		"before_submit":[
		"norden.custom.check_discount_percent",
		"norden.custom.check_internal_cost",
		"norden.custom.check_user_roles"
		],
		# "before_save":[
		
		# ],

		"validate":[
			"norden.custom.internal_margin_calculation",
			# "norden.custom.create_file_number",
			"norden.utils.quotation_workflow_alert",
			# "norden.utils.item_allocation",
			
		],
        # "on_submit":"norden.custom.get_file_number",
},
# "Customer":{
# 	"validate":[
# 		"norden.utils.get_customer_det",
# 		"norden.utils.get_address_det"
# ]
# },

	"Purchase Order": {
        "on_submit": ["norden.custom.batch_number","norden.custom.create_pi"],
		
		"after_insert": [
			"norden.custom.get_po_no",
            "norden.custom.batch_number",
		]
},
    "Batch":{
        "after_insert":[
            "norden.custom.update_company",
            "norden.custom.update_lot_no"
		]
	},
    "ToDo":{
        "after_insert":[
            "norden.custom.update_todo",
		]
	},

	"Delivery Note": {
		# "on_submit": "norden.custom.dn_status",
        "validate":"norden.custom.on_dn_submission",
		"on_submit":["norden.utils.check_item_inspection_dn",
		"norden.custom.get_foc_item_dn",
		],
  		"before_submit":"norden.custom.check_rack_qty",
		"on_cancel":'norden.custom.update_rack'
	},
	"Pick List":{
        "on_submit":["norden.custom.check_qc_completion","norden.custom.validate_reserved_stock_in_pick_list"]
	},
	

# 	"Sales Invoice": {
# 		"on_submit": "norden.custom.si_status",
# },



}
# Scheduled Tasks
# ---------------

scheduler_events = {
# 	"all": [
# 		"norden.tasks.all"
# 	],
	"daily": [
		"norden.norden.doctype.logistics_request.logistics_request.pending_for_payments",
		"norden.utils.return_blocked_items",
		"norden.custom.internship_end_date",
		"norden.custom.date_of_joining",
		"norden.custom.request_for_sample",
		"norden.custom.get_valuation_rate_from_sle",
        "norden.utils.passport_expire",
        # "norden.utils.work_anniversary_remainder",
        # "norden.utils.probation_to_confirmation",
        # "norden.utils.probation.email_probation_emp",
        # "norden.utils.probation.annual_leave_expiry",
        # "norden.utils.probation.annual_leave_due",
    ],
# 	"hourly": [
# 		"norden.tasks.hourly"
# 	],
# 	"weekly": [
# 		"norden.tasks.weekly"
# 	]
	"monthly": [
		"norden.utils.update_previous_leave_allocation_manually",
        "norden.utils.create_update_leave_allocation",
        "norden.utils.annual_leave_expired",
# 		"norden.tasks.monthly"

	],
"cron":{
	"0 9 * * *":[
		"norden.email_alerts.send_birthday_alert"
	],
    "00 00 * * *":[
		"norden.custom.annual_leave_expiry_alert_mail"
	],
    "30 00 * * *":[
		"norden.utils.annual_leave_expired"
	],
    "0 9 * * *":[
		"norden.utils.passport_expire"
	],
    "01 00 * * *":[
		"norden.email_alerts.work_anniversary_reminder_to_shoba"
	],
    "05 00 * * *":[
		"norden.email_alerts.work_anniversary_reminder_to_employees"
	],
	# "0 0 */15 * *":[
	# 	"norden.utils.return_blocked_items"
	# ]
}
}

# Testing
# -------

# before_tests = "norden.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
	"frappe.utils.pdf.get_pdf":"norden.pdf_overrides.get_pdf"
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "norden.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

jinja = {
	"methods": [
		"norden.norden.doctype.eyenor_datasheet.eyenor_datasheet.get_specification",
  		"norden.norden.doctype.eyenor_datasheet.eyenor_datasheet.get_specification_test",
		"norden.norden.doctype.eyenor_datasheet.eyenor_datasheet_html.get_html_specification",
		"norden.norden.doctype.eyenor_datasheet.eyenor_datasheet_html.get_html_header",
		"norden.norden.doctype.eyenor_datasheet.eyenor_datasheet.get_header",
		"norden.norden.doctype.eyenor_datasheet.eyenor_datasheet.get_header_test",
		"norden.norden.doctype.eyenor_datasheet.eyenor_datasheet_html.get_html_order_info",
		"norden.norden.doctype.eyenor_datasheet.eyenor_datasheet.get_order_info",
  		"norden.norden.doctype.eyenor_datasheet.eyenor_datasheet.get_order_info_test",

		"norden.norden.doctype.eyenor_datasheet.eyenor_datasheet.get_pack_info",
  		"norden.norden.doctype.eyenor_datasheet.eyenor_datasheet.get_pack_info_test",	
	
		"norden.norden.doctype.eyenor_datasheet.eyenor_datasheet.get_thermal_image",	
		"norden.norden.doctype.eyenor_datasheet.eyenor_datasheet.get_datasheet_icons",
		"norden.norden.doctype.nvs.nvs.get_nvs_specification",
		"norden.norden.doctype.nvs.nvs.get_nvs_header",
        "norden.norden.doctype.nac_datasheet.nac_datasheet.get_secnor_header",
        "norden.norden.doctype.nvs.nvs.get_nvs_header_old",
		"norden.norden.doctype.nvs.nvs.get_category_alignment",
		"norden.norden.doctype.eyenor_stickers.eyenor_stickers.generate_stickers",
		"norden.norden.doctype.nac_datasheet.nac_datasheet.get_technical_parameter",
		"norden.norden.doctype.eyenor_datasheet.eyenor_datasheet.get_samplecontent",
		"norden.norden.doctype.cable_datasheet.cable_datasheet.get_product_info",
		"norden.norden.doctype.cable_datasheet.cable_datasheet.get_material_info",
		"norden.norden.doctype.cable_datasheet.cable_datasheet.get_electrical_mechanical_info",
		"norden.norden.doctype.cable_datasheet.cable_datasheet.ordering_guide",
		"norden.norden.doctype.cable_datasheet.cable_datasheet.get_nordata_desc",
		"norden.norden.doctype.cable_datasheet.cable_datasheet.get_optidata_desc",
        "norden.norden.doctype.eyenor_datasheet.eyenor_datasheet.get_dori_distance",
		"norden.norden.doctype.eyenor_datasheet.eyenor_datasheet.get_dori_distance_test",
        "norden.custom.get_leave_balance",
		"norden.utils.get_visual",
		"norden.utils.get_dimensional",
		"norden.utils.get_material",
		"norden.utils.get_functional",
		"norden.utils.india_quotation",
		"norden.utils.opportunity_india",
        "norden.custom.return_total_amt",
        "norden.custom.get_stock_details",
        "norden.custom.get_stock",
        "norden.utils.stock_detail",
        "norden.custom.return_tax_html",
        "norden.custom.returntaxhtml",
        "norden.custom.return_tax_invoice",
        "norden.custom.serial_number_check",
		"norden.custom.get_stock_details_manufacture"
	]

}

fixtures = ["Client Script","Print Format","Report","Custom Field"]