from __future__ import unicode_literals
from frappe import _

def get_data(data):
    # data['internal_links'] = {
    #     'Timesheet': ['Time Sheets', 'issue_ref_no']
    #     }
    data['transactions'] += [
        {
            'label': _('Timesheet'),
            'items': ['Timesheet']
        },
	]
    return data