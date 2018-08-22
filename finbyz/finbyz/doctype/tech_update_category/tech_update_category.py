# -*- coding: utf-8 -*-
# Copyright (c) 2018, Finbyz Tech Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.website.website_generator import WebsiteGenerator
from frappe.website.render import clear_cache

class TechUpdateCategory(WebsiteGenerator):
	def autoname(self):
		# to override autoname of WebsiteGenerator
		self.name = self.category_name

	def on_update(self):
		clear_cache()

	def validate(self):
		if not self.route:
			self.route = 'tech_update/' + self.scrub(self.name)
		super(TechUpdateCategory, self).validate()
