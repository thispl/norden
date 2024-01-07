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

}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Item Inspection":{
		"on_submit": ["norden.custom.update_qc_status","norden.custom.update_qc_status_stock"],
	
		# "on_update": "norden.custom.item_ins_serial"
	},
	"Item":{
		"after_insert": "norden.utils.item_default_wh",
	},
	"Stock Reservation Entry":{
		"after_insert": "norden.utils.update_reserve_status",
		"on_cancel": "norden.utils.revert_reserve_status"
	},

	"Stock Entry":{
		"on_submit": ["norden.utils.create_sti","norden.utils.update_sn"],
		"before_submit":"norden.utils.add_itemwise_additional_cost",
		"before_cancel":"norden.utils.reversing_se",
		# "on_cancel":"norden.custom.cancel_stock_entry_name"
	},

	# "Serial No":{
	# 	"after_insert":[
	# 	"norden.utils.update_sn",],
		# "validate": "norden.custom.get_foc_item",
		
	# },
	
	"Opportunity": {
		# "after_insert": "norden.email_alerts.opportunity_creation_alert",
		"validate" : "norden.custom.create_opp_file_number",
	},
	# "Quotation": {
	# 	"on_update": "norden.email_alerts.quotation_creation_alert",
	# },
	
	"Landed Cost Voucher": {
		"on_submit": "norden.custom.create_lcv_je",
	},
	"Purchase Receipt": {
		"on_update_after_submit":"norden.utils.create_stock_transfer_india",
		"after_submit": ["norden.custom.create_lcv",
		],
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
		"validate": "norden.custom.create_file_number_mr",
	},
	"Employee Promotion": {
		"on_update": "norden.custom.update_appraisal_template",
	},
	"Sales Order": {
		"on_submit": "norden.custom.update_marcom",
	},
	"Sales Invoice": {
        "after_insert":"norden.custom.update_invoice_number"
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
			"norden.custom.create_file_number",
			"norden.utils.quotation_workflow_alert",
			# "norden.utils.item_allocation",
			
		],
},
# "Customer":{
# 	"validate":[
# 		"norden.utils.get_customer_det",
# 		"norden.utils.get_address_det"
# ]
# },

	"Purchase Order": {
		"after_insert": [
			"norden.custom.batch_number",
			"norden.custom.get_po_no",
		],

		"validate": "norden.custom.batch_number",
		# "validate": "norden.utils.check_uom",
},
    "Batch":{
        "after_insert":[
            "norden.custom.update_company",
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


		
	],
# 	"hourly": [
# 		"norden.tasks.hourly"
# 	],
# 	"weekly": [
# 		"norden.tasks.weekly"
# 	]
	"monthly": [
		# "norden.utils.update_previous_leave_allocation_manually",
# 		"norden.tasks.monthly"

	],
"cron":{
	"0 9 * * *":[
		"norden.email_alerts.send_birthday_alert"
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
        "norden.custom.return_tax_html"
	]

}

fixtures = ["Client Script","Print Format","Report","Custom Field"]