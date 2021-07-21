# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import frappe
import datetime

from frappe import sendmail, msgprint, db, _
from frappe.utils import (
	get_fullname, get_datetime, nowdate, now_datetime, get_url_to_form, date_diff, add_days, add_months, getdate, cint, cstr)
from frappe.core.doctype.communication.email import make
from frappe.contacts.doctype.address.address import get_address_display, get_default_address
from frappe.contacts.doctype.contact.contact import get_contact_details, get_default_contact
from frappe.utils.jinja import validate_template
from frappe.utils import strip_html_tags
from frappe.model.mapper import get_mapped_doc
from email.utils import formataddr
from erpnext.accounts.utils import get_fiscal_year
from frappe.core.doctype.communication.email import make
from frappe.email.smtp import get_outgoing_email_account
from erpnext.setup.utils import get_exchange_rate

@frappe.whitelist()	
def si_on_submit(self, method):
	tradetx(self, method)

@frappe.whitelist()	
def si_on_cancel(self, method):
	can_tradetx(self, method)
	
@frappe.whitelist()	
def send_minutes(doc_name):
	
	doc = frappe.get_doc("Lead Meetings", doc_name)
	context = {"doc": doc}	
	
	minutes_message = """<p>Greeting from FinByz Tech Pvt. Ltd.!!</p>
				<p>Thank you for sparing your valuable time. 
				We have given you brief demo of ERP Sysem where we covered below points:</p><br>"""
				
	minutes_message += frappe.render_template(doc.discussion, context)
	
	if doc.actionables:
		actionable_heading = """<br><p>
							<strong>Actionables</strong>
						</p>
						<table border="1" cellspacing="0" cellpadding="0">
							<tbody>
								<tr>
									<td width="45%" valign="top">
										<p>
											<strong>Actionable</strong>
										</p>
									</td>
									<td width="30%" valign="top">
										<p>
											<strong>Responsibility</strong>
										</p>
									</td>
									<td width="25%" valign="top">
										<p>
											<strong>Exp. Completion Date</strong>
										</p>
									</td>
								</tr>"""
								
		actionable_row = """<tr>
								<td width="45%" valign="top"> {0}
								</td>
								<td width="30%" valign="top"> {1}
								</td>
								<td width="25%" valign="top"> {2}
								</td>
							</tr>"""
		
		actionable_rows = ""
		for row in doc.actionables:
			actionable_rows += actionable_row.format(row.actionable, row.responsible, row.get_formatted('expected_completion_date'))
			
		actionable_heading += actionable_rows
		actionable_heading += "</tbody></table>"
		minutes_message += actionable_heading
	
	subject = "Minutes of the Meeting on Date - {0}".format(get_datetime(doc.meeting_from).strftime("%A %d-%b-%Y"))
	
	representatives = [row.emp_user_id for row in doc.meeting_company_representative]
	representatives += [row.email_id for row in doc.meeting_party_representative]
	
	recipients = ",".join(representatives)
	
	# Send mail to representatives
	
	r = make(recipients=recipients, 
		cc="mukesh@finbyz.tech",
		subject=subject, 
		content=minutes_message,
		sender=frappe.session.user,
		sender_full_name=frappe.db.get_value("Employee",{"user_id":frappe.session.user},"employee_name"),
		doctype=doc.doctype,
		name=doc.name,
		send_email=True)

	frappe.msgprint(_("Minutes of the Meeting sent to All Participants"))


	
@frappe.whitelist()
def get_supplier_contacts(doctype, txt, searchfield, start, page_len, filters):

	return frappe.db.sql("""select `tabContact`.name from `tabContact`, `tabDynamic Link`
		where `tabDynamic Link`.link_doctype = 'Sales Partner' and (`tabDynamic Link`.link_name=%(name)s
		and `tabDynamic Link`.link_name like %(txt)s) and `tabContact`.name = `tabDynamic Link`.parent
		limit %(start)s, %(page_len)s""", {"start": start, "page_len":page_len, "txt": "%%%s%%" % txt, "name": filters.get('sales_partner')})


'''@frappe.whitelist()
def get_contact_details(party, party_type):
	contact_person = get_default_contact(party_type, party)
	
	contact = frappe.get_doc("Contact", contact_person)
	
	return contact
'''

@frappe.whitelist()
def request_for_quote(doc_name):

	doc = frappe.get_doc("Trade Transactions", doc_name)
	
	if not doc.banks:
		frappe.msgprint(_("No contacts to send"))
		return
	
	if doc.mail_preview:
		validate_template(doc.mail_preview)
	
	context = {"doc": doc}	
	subject = "{0} Quote - {1} #{2}".format(doc.transaction_type ,doc.customer, doc.get_formatted('amount') or '')
	sales_partner = []
	count = 0
	
	for row in doc.banks:
		if not row.is_email_sent and row.contact_email:
			r = make(recipients=row.contact_email, 
				subject=subject, 
				content=frappe.render_template(doc.mail_preview, context),
				sender="trade@finbyz.tech",
				sender_full_name="Trade Finance - Finbyz",
				doctype=doc.doctype, 
				name=doc.name,
				send_email=True)
			row.is_email_sent = 1
			row.save()
			count += 1			
			sales_partner.append(row.sales_partner)
		doc.save()
		frappe.db.commit()
	if not count:
		frappe.msgprint(_("No Contacts to send"))
		return

	sales_partner = ",".join(sales_partner)
	frappe.msgprint(_("Email sent to {0}".format(sales_partner)))
		
#Update  Comments on Submit
def tradetx(self, method):
	for row in self.items:
		if row.get('trade_transaction'):
			target_doc = frappe.get_doc("Trade Transactions", row.trade_transaction)
			target_doc.invoice_no = self.name
			target_doc.deal_status = "Invoiced"
			target_doc.save()
			frappe.db.commit()

def can_tradetx(self, method):
	for row in self.items:
		if row.trade_transaction:	
			target_doc = frappe.get_doc("Trade Transactions", row.trade_transaction)
			target_doc.invoice_no = ""
			target_doc.deal_status = "Confirmed"
			target_doc.save()
			frappe.db.commit()
			
# subscription_doctype_query
def subscription_doctype_query(doctype, txt, searchfield, start, page_len, filters):
	list1= frappe.db.sql("""select parent from `tabDocField`
		where fieldname = 'subscription'
			and parent like %(txt)s
		order by
			if(locate(%(_txt)s, parent), locate(%(_txt)s, parent), 99999),
			parent
		limit %(start)s, %(page_len)s""".format(**{
			'key': searchfield,
		}), {
			'txt': "%%%s%%" % txt,
			'_txt': txt.replace("%", ""),
			'start': start,
			'page_len': page_len
		})
	list2= frappe.db.sql("""select dt from `tabCustom Field`
		where fieldname = 'subscription'
			and dt like %(txt)s
		order by
			if(locate(%(_txt)s, dt), locate(%(_txt)s, dt), 99999),
			dt
		limit %(start)s, %(page_len)s""".format(**{
			'key': searchfield,
		}), {
			'txt': "%%%s%%" % txt,
			'_txt': txt.replace("%", ""),
			'start': start,
			'page_len': page_len
		})
	return list1+list2

@frappe.whitelist()
def make_meetings(source_name, doctype, ref_doctype, target_doc=None):
	def set_missing_values(source, target):
		target.party_type = doctype
		now = now_datetime()
		if ref_doctype == "Meeting Schedule":
			target.scheduled_from = target.scheduled_to = now
		else:
			target.meeting_from = target.meeting_to = now
			if doctype == "Lead":
				target.organization = source.company_name
			else:
				target.organization = source.name

	def update_contact(source, target, source_parent):
		if doctype == 'Lead':
			if not source.organization_lead:
				target.contact_person = source.lead_name

	doclist = get_mapped_doc(doctype, source_name, {
			doctype: {
				"doctype": ref_doctype,
				"field_map":  {
					'company_name': 'organisation',
					'name': 'party'
				},
				"field_no_map": [
					"naming_series"
				],
				"postprocess": update_contact
			}
		}, target_doc, set_missing_values)

	return doclist
	
@frappe.whitelist()
def get_party_details(party=None, party_type="Customer", ignore_permissions=False):

	if not party:
		return {}

	if not db.exists(party_type, party):
		frappe.throw(_("{0}: {1} does not exists").format(party_type, party))

	return _get_party_details(party, party_type, ignore_permissions)

def _get_party_details(party=None, party_type="Customer", ignore_permissions=False):

	out = frappe._dict({
		party_type.lower(): party
	})

	party = out[party_type.lower()]

	if not ignore_permissions and not frappe.has_permission(party_type, "read", party):
		frappe.throw(_("Not permitted for {0}").format(party), frappe.PermissionError)

	party = frappe.get_doc(party_type, party)
	
	set_address_details(out, party, party_type)
	set_contact_details(out, party, party_type)
	set_other_values(out, party, party_type)

	return out

def set_address_details(out, party, party_type):
	billing_address_field = "customer_address" if party_type == "Lead" \
		else party_type.lower() + "_address"
	out[billing_address_field] = get_default_address(party_type, party.name)
	
	out.address_display = get_address_display(out[billing_address_field])

def set_contact_details(out, party, party_type):
	out.contact_person = get_default_contact(party_type, party.name)

	if not out.contact_person:
		out.update({
			"contact_person": None,
			"contact_display": None,
			"contact_email": None,
			"contact_mobile": None,
			"contact_phone": None,
			"contact_designation": None,
			"contact_department": None
		})
	else:
		out.update(get_contact_details(out.contact_person))

def set_other_values(out, party, party_type):
	# copy
	if party_type=="Customer":
		to_copy = ["customer_name", "customer_group", "territory", "language"]
	else:
		to_copy = ["supplier_name", "supplier_type", "language"]
	for f in to_copy:
		out[f] = party.get(f)
		
@frappe.whitelist()
def create_time_sheet(source_name, target_doc=None,ignore_permissions=False):
	query = frappe.db.sql("""
		select name from `tabTimesheet`
		where owner = '{}' and CAST(creation as DATE) = '{}' and docstatus = 0
		order by creation desc
		limit 1
	""".format(frappe.session.user,nowdate()),as_dict=1)
	if query:
		issue_doc = frappe.get_doc("Issue",source_name)
		doc = frappe.get_doc("Timesheet",query[0].name)
		desc = strip_html_tags(issue_doc.subject + "\n" + issue_doc.description or '') if issue_doc.description else strip_html_tags(issue_doc.subject) or ''
		doc.append("time_logs",{
			"from_time":datetime.datetime.now(),
			"activity_type":"Issue",
			"project":issue_doc.project,
			"issue":issue_doc.name,
			"description":desc or ''
		})
		doc.save(ignore_permissions=True)
		return doc
	def set_missing_values(source, target):
		target.company=source.company
		return target
	def post_process(source,target):
		row = target.append('time_logs', {})
		row.from_time=datetime.datetime.now()
		row.activity_type="Issue"
		row.project=source.project
		row.issue=source.name
		row.description = strip_html_tags(source.subject + "\n" + source.description)

	doclist = get_mapped_doc("Issue", source_name,
		{"Issue": {
			"doctype": "Timesheet",
			"field_map": {
				'company':'company',
			},
			"field_no_map":{
				"customer",
			}
		}}, target_doc,post_process, set_missing_values)


	return doclist

	# doclist = get_mapped_doc("Timesheet",source_name,{
	# 'Timesheet':{
	# 	"doctype": "Issue",
	# 	"field_map": {
	# 		'company':'company',
	# 		'customer':'costomer',
	# 	},
	# 	"field_no_map":['status']
	# }
	# }, target_doc)


@frappe.whitelist()		
def recalculate_depreciation(doc_name):
	doc = frappe.get_doc("Asset", doc_name)
	# fiscal_year = get_fiscal_year(doc.purchase_date)[0]
	# frappe.errprint(fiscal_year)
	year_end = get_fiscal_year(doc.purchase_date)[2]
	# frappe.errprint(year_end)
	# year_end_date = frappe.db.get_value("Fiscal Year","2017-2018","year_end_date")
	# frappe.errprint(year_end_date)
	useful_life_year_1 = date_diff(year_end,doc.purchase_date)
	
	if doc.schedules[0].depreciation_amount:
		sl_dep_year_1 = round((doc.schedules[1].depreciation_amount * useful_life_year_1)/ 365,2)
		#frappe.errprint(sl_dep_year_1)
		sl_dep_year_last = round(doc.schedules[1].depreciation_amount - sl_dep_year_1,2)
		frappe.db.set_value("Asset", doc_name, "depreciation_method", "Manual")
		frappe.db.set_value("Depreciation Schedule", doc.schedules[0].name, "depreciation_amount", sl_dep_year_1)
		frappe.db.set_value("Depreciation Schedule", doc.schedules[0].name, "accumulated_depreciation_amount", sl_dep_year_1)
		total_depre = len(doc.get('schedules'))
		if (doc.total_number_of_depreciations >= len(doc.get('schedules'))):
			fields =dict(
				schedule_date = add_months(doc.next_depreciation_date, doc.total_number_of_depreciations*12),
				depreciation_amount = sl_dep_year_last,
				accumulated_depreciation_amount = doc.gross_purchase_amount - doc.expected_value_after_useful_life,
				parent = doc.name,
				parenttype = doc.doctype,
				parentfield = 'schedules',
				idx = len(doc.get('schedules'))+1	
			)
			schedule = frappe.new_doc("Depreciation Schedule")
			schedule.db_set(fields, commit=True)
			schedule.insert(ignore_permissions=True)
			schedule.save(ignore_permissions=True)
			frappe.db.commit
			doc.reload()
		else:
			frappe.db.set_value("Depreciation Schedule", doc.schedules[(len(doc.get('schedules')))-1].name, "depreciation_amount", sl_dep_year_last)
			frappe.db.commit
		return sl_dep_year_1


@frappe.whitelist()
def send_employee_birthday_mails(self,method):
	frappe.errprint("In Function")
	data = db.sql("""
		SELECT
			employee_name, company_email
		FROM
			`tabEmployee`
		WHERE
			status = 'Active' 
			and DATE_FORMAT(date_of_birth,'%m-%d') = DATE_FORMAT(CURDATE(),'%m-%d') """, as_dict=1)

	for row in data:
		frappe.errprint("In Raw Data")
		recipients = [row.company_email]
		message = """<p>
				Dear {0},
			</p>
			<img src="/files/Employee_Birthday.png" style="position: relative;">
			<p style="font-size: 30px;color: #FF6550;position: absolute;top:60%;left: 5%">
			Happy Birthday {{ doc.employee_name }}</p>""".format(row.employee_name)
		frappe.errprint("Before email Sent")
		sendmail(recipients = recipients,
				cc = ['info@finbyz.com'],
				subject = 'Happy Birthday ' + row.employee_name,
				message = message)
				
@frappe.whitelist()
def asset_on_update_after_submit(self, method):
	for d in self.get('finance_books'):
		for row in self.get('schedules'):
			if not row.finance_book:
				row.db_set('finance_book', d.finance_book)
				row.db_set('finance_book_id', d.idx)

def ts_before_validate(self,method):
	if self._action=="submit":
		for row in self.time_logs:
			if not row.task:
				doc = frappe.new_doc("Task")
				doc.subject = row.activity_type
				doc.project = row.project
				doc.issue = row.issue
				doc.description = row.description
				doc.save(ignore_permissions=True)
				row.task = doc.name

def ts_on_submit(self, method):
	for row in self.time_logs:
		if cint(row.completed):
			doc = frappe.get_doc('Task', row.task)
			doc.status = "Completed"
			doc.completed_on = get_datetime(row.to_time).date()
			doc.completed_by = frappe.session.user
			doc.save(ignore_permissions=True)

def ts_on_cancel(self, method):
	for row in self.time_logs:
		if row.task:
			doc = frappe.get_doc("Task",row.task)
			row.db_set('task',None)
			doc.delete(ignore_permissions=True)
		# if cint(row.completed):
		# 	doc = frappe.get_doc('Task', row.task)
		# 	doc.status = "Open"
		# 	doc.save()

@frappe.whitelist()
def send_lead_mail(recipients, person, email_template, doc_name):

	template = frappe.get_doc('Email Template',email_template)
	doc = frappe.get_doc('Lead',doc_name)
	context = doc.as_dict()
	message = frappe.render_template(template.response, context)
	subject = template.subject
	email_account = get_outgoing_email_account(True, append_to = "Lead")
	sender = email_account.default_sender

	make(
		recipients = recipients,
		subject = subject,
		content = message,
		sender = sender,
		doctype = "Lead",
		name = doc_name,
		send_email = True
	)
	return "Mail send successfully!"

def check_sub(string, sub_str): 
	if (string.find(sub_str) == -1): 
	   return False 
	else: 
		return True


from frappe.core.doctype.role.role import get_info_based_on_role
from frappe.utils import validate_email_address

def get_list_of_recipients(self, doc, context):
	recipients = []
	cc = []
	bcc = []
	for recipient in self.recipients:
		if recipient.condition:
			if not frappe.safe_eval(recipient.condition, None, context):
				continue
		if recipient.email_by_document_field:
			email_ids_value = doc.get(recipient.email_by_document_field)
			if validate_email_address(email_ids_value):
				email_ids = email_ids_value.replace(",", "\n")
				recipients = recipients + email_ids.split("\n")

			# else:
			# 	print "invalid email"
		if recipient.cc and "{" in recipient.cc:
			recipient.cc = frappe.render_template(recipient.cc, context)

		if recipient.cc:
			recipient.cc = recipient.cc.replace(",", "\n")
			cc = cc + recipient.cc.split("\n") 

		#finbyz changes
		if recipient.cc_field:
			email_ids_value = doc.get(recipient.cc_field)
			if validate_email_address(email_ids_value):
				email_ids = email_ids_value.replace(",", "\n")
				cc = cc + email_ids.split("\n")
		# end
		if recipient.bcc and "{" in recipient.bcc:
			recipient.bcc = frappe.render_template(recipient.bcc, context)

		if recipient.bcc:
			recipient.bcc = recipient.bcc.replace(",", "\n")
			bcc = bcc + recipient.bcc.split("\n")

		#For sending emails to specified role
		if recipient.email_by_role:
			# get_emails_from_role (used in version-12) in version-13 get_info_based_on_role()
			emails = get_info_based_on_role(recipient.email_by_role,'email')

			for email in emails:
				recipients = recipients + email.split("\n")

	if not recipients and not cc and not bcc:
		return None, None, None
	return list(set(recipients)), list(set(cc)), list(set(bcc))

@frappe.whitelist()
def sales_order_payment_remainder():
	# mail on every tuesday
	if getdate().weekday() == 2:
		frappe.enqueue(send_sales_order_mails, queue='long', timeout=5000, job_name='Payment Reminder Mails')
		return "Payment Reminder Mails Send"

@frappe.whitelist()
def send_sales_order_mails():
	from frappe.utils import fmt_money

	# def show_progress(status, customer, invoice):
	# 	frappe.publish_realtime(event="cities_progress", message={'status': status, 'customer': customer, 'invoice': invoice}, user=frappe.session.user)

	def header(customer):
		return """<strong>""" + customer + """</strong><br><br>Dear Sir,<br><br>
		
		We wish to invite your kind immediate attention to our following invoices which are unpaid till date and are overdue for payment.<br>
		<div align="center">
			<table border="1" cellspacing="0" cellpadding="0" width="100%">
				<thead>
					<tr>
						<th width="20%" valign="top">Proforma No</th>
						<th width="20%" valign="top">Proforma Date</th>
						<th width="20%" valign="top">Net Total</th>
						<th width="20%" valign="top">Total Amount</th>
						<th width="20%" valign="top">Outstanding Amount</th>
					</tr></thead><tbody>"""

	def table_content(name, transaction_date, net_total, rounded_total, outstanding_amount):
		transaction_date = transaction_date.strftime("%d-%m-%Y") if bool(transaction_date) else '-'
		
		rounded_total = fmt_money(rounded_total, 2, 'INR')
		net_total = fmt_money(net_total, 2, 'INR')
		outstanding_amount = fmt_money(outstanding_amount, 2, 'INR')

		return """<tr>
				<td width="20%" valign="top" align="center"> {0} </td>
				<td width="20%" valign="top" align="center"> {1} </td>
				<td width="20%" valign="top" align="right"> {2} </td>
				<td width="20%" valign="top" align="right"> {3} </td>
				<td width="20%" valign="top" align="right"> {4} </td>
			</tr>""".format(name, transaction_date, net_total, rounded_total, outstanding_amount)
	
	def footer(net_amount,actual_amount, outstanding_amount):
		net_amt = fmt_money(sum(net_amount), 2, 'INR')
		actual_amt = fmt_money(sum(actual_amount), 2, 'INR')
		outstanding_amt = fmt_money(sum(outstanding_amount), 2, 'INR')
		return """<tr>
					<td width="40%" colspan="2" valign="top" align="right">
						<strong>Net Receivable &nbsp; </strong>
					</td>
					<td align="right" width="20%" valign="top">
						<strong> {} </strong>
					</td>
					<td align="right" width="20%" valign="top">
						<strong> {} </strong>
					</td>
					<td align="right" width="20%" valign="top">
						<strong> {} </strong>
					</td>
				</tr></tbody></table></div><br>
				Request you to release the payment at earliest. <br><br>
				If you need any clarifications for any of above proforma invoice, please reach out to our Accounts Team by sending email to accounts@finbyz.tech or call Mr. Ravin Ramoliya (+91 8200899005).<br><br>
				We will appreciate your immediate response in this regard.<br><br>
				If payment already made from your end, kindly provide details of the payment/s made to enable us to reconcile and credit your account.<br><br>
				
				<div>
				<table cellpadding="4px" cellspacing="0" style="background: none; margin: 0; padding: 0px;">
					<tbody><tr>
						<td style="padding-bottom: 0px; border-right: 3px solid #a0ce4e;" valign="top"><img id="preview-image-url" src="https://drive.google.com/uc?id=0B3eTCgrrV-DDTVFIbTJsSmhYWTQ"></td>
						<td style="padding-top: 0; padding-bottom: 0; padding-left: 12px; padding-right: 0;">
							<table border="0" cellpadding="4px" cellspacing="0" style="background: none; border-width: 0px; border: 0px; margin: 0; padding: 1px;">
								<tbody><tr>
									<td colspan="2" style="padding-bottom: 2px; color: #a0ce4e; font-size: 18px; font-family: Arial, Helvetica, sans-serif;">Accounts Team</td>
								</tr>
								<tr>
									<td colspan="2" style="padding-bottom: 0px; color: #333333; font-size: 14px; font-family: Arial, Helvetica, sans-serif;"><strong>FinByz Tech Pvt. Ltd.</strong></td>
								</tr>
								<tr>
									<td style="padding-bottom: 0px; vertical-align: top; width: 20px; color: #a0ce4e; font-size: 14px; font-family: Arial, Helvetica, sans-serif;" valign="top" width="20">P:</td>
									<td style="padding-bottom: 0px; color: #333333; font-size: 14px; font-family: Arial, Helvetica, sans-serif;">+91-79-48912428</td>
								</tr>
								<tr>
									<td style="padding-bottom: 0px; vertical-align: top; width: 20px; color: #a0ce4e; font-size: 14px; font-family: Arial, Helvetica, sans-serif;" valign="top" width="20">A:</td>
									<td style="padding-bottom: 0px; vertical-align: top; color: #333333; font-size: 14px; font-family: Arial, Helvetica, sans-serif;" valign="top">504- Addor Ambition, Navrang Circle, Navrangpura, Ahmedabad -380014</td>
								</tr>
								<tr>
									<td style="padding-bottom: 0px; vertical-align: top; width: 20px; color: #a0ce4e; font-size: 14px; font-family: Arial, Helvetica, sans-serif;" valign="top" width="20">W:</td>
									<td style="padding-bottom: 0px; vertical-align: top; color: #333333; font-size: 14px; font-family: Arial, Helvetica, sans-serif;" valign="top">
										<a href="https://finbyz.tech" style="color: #1D9FDB; text-decoration: none; font-weight: normal; font-size: 14px;">Finbyz.tech</a>  <span style="color: #a0ce4e;">E: </span><a href="mailto:accounts@finbyz.tech" style="color: #1D9FDB; text-decoration: none; font-weight: normal; font-size: 14px;">accounts@finbyz.tech</a>
									</td>
								</tr>
							</tbody></table>
						</td>
					</tr>
				</tbody></table>
				<p></p>
				<div align="center" style="color: rgb(34, 34, 34); margin: 0cm 0cm 0.0001pt; font-size: 11pt; font-family: Calibri, sans-serif; text-align: center; line-height: 12.65pt;">
					<hr align="center" size="2" width="100%">
				</div>
				<p style="color: rgb(34, 34, 34); margin: 0cm 0cm 0.0001pt; font-size: 11pt; font-family: Calibri, sans-serif; line-height: 12.65pt;"><a href="https://www.facebook.com/finbyz" style="color: rgb(17, 85, 204);" target="_blank"><span style="color: blue;"><img alt="Facebook" border="0" height="32" src="https://docs.google.com/a/finbyz.com/uc?id=0B3eTCgrrV-DDVjJvcXRscHBtLUE&amp;export=download" width="32"></span></a>  <a href="https://www.google.co.in/+finbyz" style="color: rgb(17, 85, 204);" target="_blank"><span style="color: blue;"><img alt="Google+" border="0" height="32" src="https://docs.google.com/a/finbyz.com/uc?id=0B3eTCgrrV-DDVHExNXR3VUxKaGs&amp;export=download" width="32"></span></a>  <a href="https://www.linkedin.com/company/finbyz" style="color: rgb(17, 85, 204);" target="_blank"><span style="color: blue;"><img alt="Linkedin" border="0" height="32" src="https://docs.google.com/a/finbyz.com/uc?id=0B3eTCgrrV-DDRGdHUExsbjVRR2s&amp;export=download" width="32"></span></a>  <a href="https://twitter.com/Finbyz" style="color: rgb(17, 85, 204);" target="_blank"><span style="color: blue;"><img alt="Twitter" border="0" height="32" src="https://docs.google.com/a/finbyz.com/uc?id=0B3eTCgrrV-DDTS1KRndoZnBXc1U&amp;export=download" width="32"></span></a></p>
			</div>
				
				""".format(net_amt,actual_amt, outstanding_amt)

	non_customers = ()

	data = frappe.get_list("Sales Order", filters={
			'status': ['in', ('To Deliver and Bill')],
			'delivery_date': ("<", nowdate()),
			'currency': 'INR',
			'docstatus': 1,
			'dont_send_payment_reminder': 0,
			'customer': ['not in', non_customers]},
			order_by='transaction_date',
			fields=["name", "customer", "transaction_date","net_total", "rounded_total", "advance_paid", "contact_email", "naming_series","owner"])

	def get_customers():
		customers_list = list(set([d.customer for d in data if d.customer]))
		customers_list.sort()

		for customer in customers_list:
			yield customer

	def get_customer_si(customer):
		for d in data:
			if d.customer == customer:
				yield d

	cnt = 0
	customers = get_customers()

	sender = formataddr(("FinByz Tech Pvt. Ltd.", "info@finbyz.com"))
	for customer in customers:
		attachments, outstanding, actual_amount, net_amount,recipients, cc = [], [], [], [], [], 'accounts@finbyz.tech'
		table = ''

		# customer_si = [d for d in data if d.customer == customer]
		customer_si = get_customer_si(customer)

		for si in customer_si:
			# show_progress('In Progress', customer, si.name)
			name = "Previous Year Outstanding"
			if si.naming_series != "OSINV-":
				name = si.name
				try:
					attachments.append({
						"print_format_attachment": 1,
						"doctype": "Sales Order",
						"name": si.name,
						"print_format": 'Pro-Forma Invoice',
						"print_letterhead": 1,
						"lang": 'en'
					})
				except:
					pass

			table += table_content(name, si.transaction_date, si.net_total,
						si.rounded_total, (si.rounded_total-si.advance_paid))

			outstanding.append((si.rounded_total-si.advance_paid))
			actual_amount.append(si.rounded_total or 0.0)
			net_amount.append(si.net_total or 0.0)

			if bool(si.contact_email) and si.contact_email not in recipients:
				recipients.append(si.contact_email)
				cc = cc + ', ' + si.owner

			if si.other_contacts:
				other_contact_list = [d.email_id for d in si.other_contacts]
				recipients = recipients + other_contact_list
			
		message = header(customer) + '' + table + '' + footer(net_amount, actual_amount, outstanding)
		recipients = list(set(recipients))
		#recipients  = ['nirali.satapara@finbyz.tech']
		try:
			make(recipients=recipients,
				sender = sender,
				subject = 'Overdue Payment: ' + customer,
				content = message,
				attachments = attachments,
				cc = (cc),
				doctype= "Sales Order",
				name= si.name,
				send_email=True
			)
			
			# cnt += 1
			# show_progress('Mail Sent', customer, "All")
		except:
			frappe.log_error("Mail Sending Issue", frappe.get_traceback())
			continue

	#show_progress('Success', "All Mails Sent", str(cnt))
	#frappe.db.set_value("Cities", "CITY0001", "total", cnt)

def opportunity_validate(self,method):
	if self.opportunity_amount and self.probability:
		self.opportunity_size = self.opportunity_amount * self.probability / 100

@frappe.whitelist()
def get_activity_cost(employee=None, activity_type=None, currency=None):
	base_currency = frappe.defaults.get_global_default('currency')
	rate = frappe.db.get_values("Activity Cost", {"employee": employee}, ["costing_rate", "billing_rate"], as_dict=True)
	if not rate:
		rate = frappe.db.get_values("Activity Type", {"activity_type": activity_type},
			["costing_rate", "billing_rate"], as_dict=True)
		if rate and currency and currency!=base_currency:
			exchange_rate = get_exchange_rate(base_currency, currency)
			rate[0]["costing_rate"] = rate[0]["costing_rate"] * exchange_rate
			rate[0]["billing_rate"] = rate[0]["billing_rate"] * exchange_rate

	return rate[0] if rate else {}

def validate_project_dates(project_end_date, task, task_start, task_end, actual_or_expected_date):
	pass
	# if task.get(task_start) and date_diff(project_end_date, getdate(task.get(task_start))) < 0:
	# 	frappe.throw(_("Task's {0} Start Date cannot be after Project's End Date.").format(actual_or_expected_date))

	# if task.get(task_end) and date_diff(project_end_date, getdate(task.get(task_end))) < 0:
	# 	frappe.throw(_("Task's {0} End Date cannot be after Project's End Date.").format(actual_or_expected_date))
