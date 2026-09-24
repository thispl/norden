import frappe
@frappe.whitelist()
def get_itinerary(travel_request):
    travel_request = frappe.get_doc("Travel Request",travel_request)
    return travel_request.itinerary