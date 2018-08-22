frappe.views.calendar["Lead Meetings"] = {
	field_map: {
		"start": "meeting_from",
		"end": "meeting_to",
		"id": "name",
		"title": "organization"
	},
	gantt: true,
	get_events_method: "finbyz.finbyz.doctype.lead_meetings.lead_meetings.get_events"
};