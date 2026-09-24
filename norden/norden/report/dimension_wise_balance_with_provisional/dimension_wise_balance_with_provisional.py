# Copyright (c) 2025, Teampro and contributors
# For license information, please see license.txt

import frappe

@frappe.whitelist()
def execute(filters=None):
    filters = frappe._dict(filters or {})

    # Load snapshot if passed
    snapshot_data = []
    if filters.get("snapshot_name"):
        snapshot = frappe.get_doc("Saved Account Balance Snapshot", filters["snapshot_name"])
        snapshot_data = json.loads(snapshot.report_data or "[]")

    # Get actual GL data from system
    actual_data = get_actual_data(filters)

    # Merge provisional values
    data = []
    for row in actual_data:
        matching = next((x for x in snapshot_data if x['account'] == row['account'] and x.get('dimension') == row.get('dimension')), {})
        row['provisional'] = matching.get('provisional', 0)
        row['total'] = row['actual'] + row['provisional']
        data.append(row)

    return get_columns(), data

