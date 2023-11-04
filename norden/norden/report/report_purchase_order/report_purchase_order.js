// Copyright (c) 2023, Teampro and contributors
// For license information, please see license.txt


frappe.query_reports["Report Purchase Order"] = {
	"filters": [
	
		{
			"fieldname": "from_date",
            "label": __(" Order From Date"),
            "fieldtype": "Date",
			"reqd": 1
		},
		{
	
			"fieldname": "to_date",
			"label": __("Order To Date"),
			"fieldtype": "Date",
			"reqd": 1
		},
		{
			"fieldname": "supplier",
			"fieldtype": "Link",
			"options": "Supplier",
			"label": __("Vendor"),
			"width": "50px"
        },
		{
			"fieldname": "project",
			"fieldtype": "Link",
			"options": "Project",
			"label": __("Project"),
			"width": "50px"
        },
		{
			"fieldname":"status",
			"label":__("Status"),
			"fieldtype":"Select",
			"options":["","Draft","On Hold","To Receive and Bill","To Bill",
			"To Receive",
			"Completed",
			"Cancelled",
			"Closed",
			"Delivered"],
			"default": "",
			"width": "100px"
		}
	]
};
