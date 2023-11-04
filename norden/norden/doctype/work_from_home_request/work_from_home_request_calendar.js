// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.views.calendar["Work From Home Request"] = {
	field_map: {
		"start": "work_from_date",
		"end": "work_to_date",
		"id": "name",
		"title": "employee_name",
		"docstatus": 1,
		"allDay": "employee_name"
	},
	options: {
		header: {
			left: 'prev,next today',
			center: 'title',
			right: 'month'
		}
	},
	get_events_method: "frappe.desk.calendar.get_events",
}
