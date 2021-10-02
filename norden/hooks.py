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

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"norden.tasks.all"
# 	],
# 	"daily": [
# 		"norden.tasks.daily"
# 	],
# 	"hourly": [
# 		"norden.tasks.hourly"
# 	],
# 	"weekly": [
# 		"norden.tasks.weekly"
# 	]
# 	"monthly": [
# 		"norden.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "norden.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "norden.event.get_events"
# }
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

jenv = {
	"methods": [
		"get_specification:norden.norden.doctype.eyenor_datasheet.eyenor_datasheet.get_specification",
		"get_header:norden.norden.doctype.eyenor_datasheet.eyenor_datasheet.get_header",
		"get_order_info:norden.norden.doctype.eyenor_datasheet.eyenor_datasheet.get_order_info",
		"get_pack_info:norden.norden.doctype.eyenor_datasheet.eyenor_datasheet.get_pack_info",	
		"get_datasheet_icons:norden.norden.doctype.eyenor_datasheet.eyenor_datasheet.get_datasheet_icons",
		"get_nvs_specification:norden.norden.doctype.nvs.nvs.get_nvs_specification",
		"get_nvs_header:norden.norden.doctype.nvs.nvs.get_nvs_header",
		"get_category_alignment:norden.norden.doctype.nvs.nvs.get_category_alignment",
		"generate_stickers:norden.norden.doctype.eyenor_stickers.eyenor_stickers.generate_stickers",
		"get_technical_parameter:norden.norden.doctype.nac_datasheet.nac_datasheet.get_technical_parameter",
		"get_samplecontent:norden.norden.doctype.eyenor_datasheet.eyenor_datasheet.get_samplecontent",
		"get_product_info:norden.norden.doctype.cable_datasheet.cable_datasheet.get_product_info",
		"get_material_info:norden.norden.doctype.cable_datasheet.cable_datasheet.get_material_info",
		"get_electrical_mechanical_info:norden.norden.doctype.cable_datasheet.cable_datasheet.get_electrical_mechanical_info",
		"ordering_guide:norden.norden.doctype.cable_datasheet.cable_datasheet.ordering_guide",
		"get_nordata_desc:norden.norden.doctype.cable_datasheet.cable_datasheet.get_nordata_desc",
		"get_optidata_desc:norden.norden.doctype.cable_datasheet.cable_datasheet.get_optidata_desc",
	]
}

fixtures = ["Client Script","Print Format"]