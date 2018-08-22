frappe.views.calendar["Customer Meetings"] = {
	field_map: {
		"start": "meeting_from",
		"end": "meeting_to",
		"id": "name",
		"title": "organization"
	},
	gantt: true,
	get_events_method: "finbyz.finbyz.doctype.customer_meetings.customer_meetings.get_events"
};