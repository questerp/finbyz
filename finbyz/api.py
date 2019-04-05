# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import frappe
import datetime
from frappe import sendmail, msgprint, db, _
from frappe.utils import get_fullname, get_datetime, now_datetime, get_url_to_form, date_diff, add_days,add_months, getdate
from frappe.core.doctype.communication.email import make
from frappe.contacts.doctype.address.address import get_address_display, get_default_address
from frappe.contacts.doctype.contact.contact import get_contact_details, get_default_contact
from frappe.utils.jinja import validate_template
from frappe.model.mapper import get_mapped_doc
from erpnext.accounts.utils import get_fiscal_year


@frappe.whitelist()
def leadmeeting_on_submit(self, method):
	new_comm(self, method)

@frappe.whitelist()	
def custmeeting_on_submit(self, method):
	new_communication(self, method)
	
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
	
	representatives = [row.emp_user_id for row in doc.finbyz_representatives]
	representatives += [row.email_id for row in doc.lead_representatives]
	
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
	
	
#Update Lead Comments on Submit
def new_comm(self, method):
	user_name = frappe.db.get_value("Employee",{"user_id":frappe.session.user},"employee_name")
	url = get_url_to_form("Lead Meetings", self.name)
	# url = "http://erp.finbyz.in/desk#Form/Lead%20Meetings/" + self.name
	discussed = "<strong><a href="+url+">"+self.name+"</a>: </strong>"+ user_name + " Met "+ self.contact_person + " On "+ self.meeting_from +"<br>" + self.discussion.replace('\n', "<br>")
	cm = frappe.new_doc("Communication")
	cm.subject = self.name
	cm.communication_type = "Comment"
	cm.comment_type = "Comment"
	cm.content = discussed
	cm.reference_doctype = self.party_type
	cm.reference_name = self.party
	cm.user = frappe.session.user
	cm.sender_full_name = user_name
	cm.save(ignore_permissions=True)
	if self.party_type == "Lead":
		target_lead = frappe.get_doc("Lead", self.party)
		target_lead.status = "Meeting Done"
		target_lead.turnover = self.turnover
		target_lead.industry = self.industry
		target_lead.business_specifics = self.business_specifics
		target_lead.contact_by = self.contact_by
		target_lead.contact_date = self.contact_date
		if not target_lead.email_id:
			target_lead.email_id = self.email_id
		if not target_lead.lead_name:
			target_lead.lead_name = self.contact_person
		if not target_lead.mobile_no:
			target_lead.mobile_no = self.mobile_no
		target_lead.save(ignore_permissions=True)
	frappe.db.commit()
	
#Update Customer Comments on Submit
def new_communication(self, method):
	url = "http://erp.finbyz.in/desk#Form/Customer%20Meetings/" + self.name
	msgprint(url)
	if self.actionables:
		discussed = "<strong><a href="+url+">"+self.name+"</a>: </strong>"+ "Met "+ self.contact_person + " On "+ self.meeting_from +"<br>" + self.discussion.replace('\n', "<br>")+ "<br><strong>Actionable:</strong>" +self.actionables
	else:
		discussed = "<strong><a href="+url+">"+self.name+"</a>: </strong>"+ "Met "+ self.contact_person + " On "+ self.meeting_from +"<br>" + self.discussion.replace('\n', "<br>")
	msgprint(discussed)
	cm = frappe.new_doc("Communication")
	cm.subject = self.name
	cm.communication_type = "Comment"
	cm.comment_type = "Comment"
	cm.content = self.discussed
	cm.reference_doctype = "Customer"
	cm.reference_name = self.customer
	cm.save(ignore_permissions=True)
	frappe.db.commit()
	
#Update  Comments on Submit
def tradetx(self, method):
	for row in self.items:
		if row.trade_transaction:
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
				
@frappe.whitelist()
def docs_before_naming(self, method):
	from erpnext.accounts.utils import get_fiscal_year

	date = self.get("transaction_date") or self.get("posting_date") or getdate()

	fy = get_fiscal_year(date)[0]
	fiscal = frappe.db.get_value("Fiscal Year", fy, 'fiscal')

	if fiscal:
		self.fiscal = fiscal
	else:
		fy_years = fy.split("-")
		fiscal = fy_years[0][2:] + '-' + fy_years[1][2:]
		self.fiscal = fiscal
