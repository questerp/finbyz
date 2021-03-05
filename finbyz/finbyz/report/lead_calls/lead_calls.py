# Copyright (c) 2013, FinByz Tech Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import datetime
from frappe import _, msgprint
from frappe.utils import getdate, nowdate, date_diff, get_fullname

def execute(filters=None):
	filters.from_date = getdate(filters.from_date or nowdate())
	filters.to_date = getdate(filters.to_date or nowdate())
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(data, filters)
	return columns, data , None, chart

	
def get_columns():
	
	columns = [
		{"label": _("Lead"), "fieldname": "lead", "fieldtype": "Link", "options": "Lead", "width": 80},
		{"label": _("User"), "fieldname": "user", "fieldtype": "Link", "options": "User", "width": 100},
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 120},
		{"label": _("Caller"), "fieldname": "caller", "fieldtype": "Data", "width": 110},
		{"label": _("Organization"), "fieldname": "organization", "fieldtype": "Data", "width": 110},
		{"label": _("Person"), "fieldname": "person", "fieldtype": "Data", "width": 110},
		{"label": _("Comment"), "fieldname": "comment", "fieldtype": "Data", "width": 400},
		{"label": _("Schedule"), "fieldname": "schedule", "fieldtype": "Date", "width": 120},
		{"label": _("Person"), "fieldname": "person", "fieldtype": "Data", "width": 110},
		{"label": _("Source"), "fieldname": "source", "fieldtype": "Data", "width": 110},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 110},
		{"label": _("Mobile"), "fieldname": "mobile", "fieldtype": "Data", "width": 110},
		{"label": _("Phone"), "fieldname": "phone", "fieldtype": "Data", "width": 110}
	]
	return columns

def get_data(filters):

	where_clause = ''
	where_clause+=filters.user and " and co.owner = '%s' " % filters.user or ""	
	where_clause+=filters.lead and " and co.reference_name = '%s' " % filters.lead or ""
	
	where_clause += " and co.creation between '%s 00:00:00' and '%s 23:59:59' " % (filters.from_date, filters.to_date)
	
	data = frappe.db.sql("""
		select
			co.reference_name as "lead", co.owner as "user" , co.creation as "date", co.comment_by as "caller", ld.company_name as "organization", ld.lead_name as "person",  co.content as "comment", co.comment_email, ld.contact_date as "schedule", ld.source as "source" , ld.Status as "status" , ld.mobile_no as "mobile" ,	ld.phone as "phone"
		from
			`tabComment` as co left join `tabLead` as ld on (co.reference_name = ld.name)
		where
			co.reference_doctype = "Lead" and co.comment_type="Comment"
			%s
		order by
			co.creation desc"""%where_clause, as_dict=1)

	for row in data:
		if not row["caller"]:
			row["caller"] = get_fullname(row['comment_email'])

	return data

def get_chart_data(data, filters):
	count = []
	based_on, date_range = None, None
	period = {"Day": "%d", "Week": "%W", "Month": "%m"}
	from_date, to_date = getdate(filters.from_date), getdate(filters.to_date)
	labels = list()
	diff = date_diff(filters.to_date, filters.from_date)
	
	if diff <= 30:
		based_on = "Day"
		date_range = diff
	elif diff <= 90 and diff > 30:
		based_on = "Week"
		date_range = int(to_date.strftime(period[based_on])) - int(from_date.strftime(period[based_on]))
	elif diff > 90:
		based_on = "Month"
		date_range = int(to_date.strftime(period[based_on])) - int(from_date.strftime(period[based_on]))
		
	if based_on == "Day":
		for d in range(date_range+1):
			cnt = 0
			date = from_date + datetime.timedelta(days=d)
			for row in data:
				sql_date = getdate(row["date"])
				if date == sql_date:
					cnt += 1
			
			count.append(cnt)
			labels.append(date.strftime("%d-%b '%y"))
	
	else:
		period_date = dict()
		for x in range(date_diff(to_date, from_date)+1):
			tmp_date = from_date + datetime.timedelta(days=x)
			tmp_period = str(tmp_date.strftime(period[based_on]))
			if tmp_period not in period_date:
				period_date[tmp_period] = [tmp_date]
			else:
				period_date[tmp_period].append(tmp_date)
		
		for key, values in sorted(period_date.items()):
			cnt = 0
			for date in values:
				for row in data:
					sql_date = getdate(row["date"])
					if date == sql_date:
						cnt += 1
						
			count.append(cnt)
			labels.append(values[0].strftime("%d-%b") + " to " + values[-1].strftime("%d-%b"))
	
	datasets = []
	
	if count:
		datasets.append({
			'title': "Total",
			'values': count
		})
	
	chart = {
		"data": {
			'labels': labels,
			'datasets': datasets
		}
	}
	chart["type"] = "bar"
	return chart