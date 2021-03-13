# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "finbyz"
app_title = "Finbyz"
app_publisher = "FinByz Tech Pvt. Ltd."
app_description = "Customizations"
app_icon = "octicon octicon-screen-normal"
app_color = "FF5733"
app_email = "info@finbyz.com"
app_license = "MIT"



# override for cc_field
from frappe.email.doctype.notification.notification import Notification
from finbyz.api import get_list_of_recipients
Notification.get_list_of_recipients = get_list_of_recipients
# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/finbyz/css/finbyz.css"
# app_include_js = "/assets/finbyz/js/finbyz.js"

# include js, css files in header of web template
# web_include_css = "/assets/finbyz/css/finbyz.css"
# web_include_js = "/assets/finbyz/js/finbyz.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}

doctype_js = {
	"Lead": "public/js/doctype_js/lead.js",
	"Sales Invoice": "public/js/doctype_js/sales_invoice.js"
}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "finbyz.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "finbyz.install.before_install"
# after_install = "finbyz.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "finbyz.notifications.get_notification_config"

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

doc_events = {
	"Lead Meetings": {
		"on_submit": "finbyz.api.leadmeeting_on_submit"
	},
	
	"Customer Meetings": {
		"on_submit": "finbyz.api.custmeeting_on_submit"
	},
	
	"Sales Invoice": {
		"on_submit": "finbyz.api.si_on_submit",
		"on_cancel": "finbyz.api.si_on_cancel"
	},
	
	"Timesheet": {
		"on_submit": "finbyz.api.ts_on_submit",
		"on_cancel": "finbyz.api.ts_on_cancel"
	},
}
scheduler_events = {
	"daily": [
		"finbyz.api.sales_order_payment_remainder"
	],
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"finbyz.tasks.all"
# 	],
# 	"daily": [
# 		"finbyz.tasks.daily"
# 	],
# 	"hourly": [
# 		"finbyz.tasks.hourly"
# 	],
# 	"weekly": [
# 		"finbyz.tasks.weekly"
# 	]
# 	"monthly": [
# 		"finbyz.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "finbyz.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "finbyz.event.get_events"
# }

