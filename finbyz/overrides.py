
from __future__ import unicode_literals
import frappe
from frappe.utils import flt
from frappe import _
from erpnext.accounts.utils import get_account_currency
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (get_accounting_dimensions,
	get_dimension_filters)

#Period closing voucher override for finance book.
def make_gl_entries(self):
	gl_entries = []

	#finbyz changes
	company_book_entries = []
	incometax_book_entries = []
	finance_book_map = {}
	#net_pl_balance = 0
	
	dimension_fields = ['t1.cost_center','t1.finance_book']
	#finbyz changes end
	
	accounting_dimensions = get_accounting_dimensions()
	for dimension in accounting_dimensions:
		dimension_fields.append('t1.{0}'.format(dimension))

	dimension_filters, default_dimensions = get_dimension_filters()

	pl_accounts = self.get_pl_balances(dimension_fields)

	for acc in pl_accounts:
		if flt(acc.balance_in_company_currency):
			gl_entries.append(self.get_gl_dict({
				"account": acc.account,
				"cost_center": acc.cost_center,
				"account_currency": acc.account_currency,
				"debit_in_account_currency": abs(flt(acc.balance_in_account_currency)) \
					if flt(acc.balance_in_account_currency) < 0 else 0,
				"debit": abs(flt(acc.balance_in_company_currency)) \
					if flt(acc.balance_in_company_currency) < 0 else 0,
				"credit_in_account_currency": abs(flt(acc.balance_in_account_currency)) \
					if flt(acc.balance_in_account_currency) > 0 else 0,
				"credit": abs(flt(acc.balance_in_company_currency)) \
					if flt(acc.balance_in_company_currency) > 0 else 0
			}, item=acc))

			#finbyz changes
			if acc.finance_book == "" or acc.finance_book == None:
				acc.finance_book = "None"
			if flt(acc.balance_in_company_currency):
				finance_book_map.setdefault(acc.finance_book, frappe._dict({
						"net_pl_balance": 0.0
					}))
				finance_book_map[acc.finance_book].net_pl_balance = finance_book_map[acc.finance_book].net_pl_balance + flt(acc.balance_in_company_currency)
			
	for finance_book in finance_book_map:
		# finbyz changes end
		net_pl_balance = finance_book_map[finance_book].net_pl_balance

		if net_pl_balance:
			cost_center = frappe.db.get_value("Company", self.company, "cost_center")
			gl_entry = self.get_gl_dict({
				"account": self.closing_account_head,
				"debit_in_account_currency": abs(net_pl_balance) if net_pl_balance > 0 else 0,
				"debit": abs(net_pl_balance) if net_pl_balance > 0 else 0,
				"credit_in_account_currency": abs(net_pl_balance) if net_pl_balance < 0 else 0,
				"credit": abs(net_pl_balance) if net_pl_balance < 0 else 0,
				"cost_center": cost_center,
				"finance_book": None if finance_book == "None" else finance_book #change
			})

			gl_entries.append(gl_entry)

	from erpnext.accounts.general_ledger import make_gl_entries
	make_gl_entries(gl_entries,merge_entries=False) #change