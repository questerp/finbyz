# -*- coding: utf-8 -*-
# Copyright (c) 2019, FinByz Tech Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cstr, cint
from frappe.utils.data import quoted
from frappe.model.document import Document

import requests
import json

integration = frappe.get_single("Market Wire Integration")

class ForexProjectPassword(Document):
	def validate(self):
		if self.is_new():
			self.create_company()
		else:
			self.update_users()
			self.update_company()

	def create_company(self):
		url = self.get_host()
		content = self.get_content()
		headers = self.get_headers()

		response = requests.post(url, json.dumps(content), headers=headers)

		if response.status_code != 201:
			frappe.throw(title="Error while saving data!", msg=cstr(response.text))

		else:
			response_json = response.json()
			self.company_id = cint(response_json['id'])

			for user in response_json['users']:
				for row in self.user:
					if user['username'] == row.web_user_name:
						row.user_id = cint(user['id'])
						break

	def update_company(self):
		url = self.get_host() + quoted(self.party_name)
		content = self.get_content()
		headers = self.get_headers()

		response = requests.put(url, json.dumps(content), headers=headers)

		if response.status_code != 200:
			frappe.throw(title="Error while updating data!", msg=cstr(response.text))

		else:
			response_json = response.json()

			for user in response_json['users']:
				for row in self.user:
					if user['username'] == row.web_user_name:
						row.user_id = cint(user['id'])
						break

	def update_users(self):
		if cint(self.service_stopped):
			for row in self.user:
				row.inactive = 1

	def get_content(self):
		email = "\n".join(cstr(self.contact_email).split(","))
		content = {
			"company_name": self.party_name,
			"person_name": self.contact_display,
			"mobile_number": self.contact_mobile,
			"email": email,
			"subscription_start_date": str(self.service_period_from),
			"subscription_end_date": str(self.service_period_to),
			"mode": self.service_type.lower(),
			"is_active": not cint(self.service_stopped),
			"users": []
		}

		for row in self.user:
			content['users'].append({
				'id': row.get('user_id', ''),
				'first_name': row.first_name,
				'last_name': row.last_name,
				'email': row.email,
				'username': row.web_user_name,
				'password': row.web_pwd,
				'inactive': cint(row.inactive),
			})

		return content

	def get_host(self):
		return integration.host

	def get_headers(self):
		headers = {}

		for row in integration.headers:
			headers.setdefault(row.header_name, row.parameter_value)

		return headers
