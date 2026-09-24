import frappe

def create_material_transfer_entry():
    """
    Create a Material Transfer Stock Entry:
      Item: 1311-124110GY
      From: Main Stores - NCME  (Rack: IND18-03-MEZ2)
      To:   Damage stock location - NCME  (Rack: IND18-DAMAGE)
    """

    item_code = "1311-124110GY"
    from_warehouse = "Main Stores - NCME"
    to_warehouse = "Damage stock location - NCME"
    from_rack = "IND18-03-MEZ2"
    to_rack = "IND18-DAMAGE"

    # Determine company from the source warehouse
    company = frappe.db.get_value("Warehouse", from_warehouse, "company")
    if not company:
        frappe.throw("Could not determine company from warehouse: {0}".format(from_warehouse))

    # Get item defaults
    item = frappe.db.get_value("Item", item_code, ["stock_uom", "valuation_rate"], as_dict=True)
    if not item:
        frappe.throw("Item {0} not found".format(item_code))

    # Check available stock in source rack
    rack_qty = frappe.db.sql("""
        SELECT SUM(actual_qty)
        FROM `tabStock Ledger Entry`
        WHERE item_code = %s
        AND warehouse = %s
        AND rack = %s
        AND is_cancelled = 0
    """, (item_code, from_warehouse, from_rack))[0][0] or 0

    if rack_qty <= 0:
        frappe.throw(
            "No stock available for item {0} in rack {1} at warehouse {2}".format(
                item_code, from_rack, from_warehouse
            )
        )

    # Create the Stock Entry
    se = frappe.new_doc("Stock Entry")
    se.stock_entry_type = "Material Transfer"
    se.company = company
    se.from_warehouse = from_warehouse
    se.to_warehouse = to_warehouse
    se.set_posting_time = 1
    se.posting_date = frappe.utils.nowdate()
    se.posting_time = frappe.utils.nowtime()

    se.append("items", {
        "item_code": item_code,
        "s_warehouse": from_warehouse,
        "t_warehouse": to_warehouse,
        "qty": rack_qty,
        "uom": item.stock_uom,
        "stock_uom": item.stock_uom,
        "conversion_factor": 1,
        "basic_rate": item.valuation_rate or 0,
        "rack": from_rack,
        "to_rack": to_rack,
    })

    se.insert(ignore_permissions=True)

    print("Stock Entry created: {0}".format(se.name))
    print("  Item: {0}".format(item_code))
    print("  From: {0} (Rack: {1})".format(from_warehouse, from_rack))
    print("  To:   {0} (Rack: {1})".format(to_warehouse, to_rack))
    print("  Qty:  {0}".format(rack_qty))

    return se.name


def debug_purpose():
    """Debug: investigate why UI shows 'Missing Finished Good' error for Material Transfer."""

    # 1. Check ALL Stock Entry Type records
    print("=== All Stock Entry Type records ===")
    all_types = frappe.db.get_all("Stock Entry Type", fields=["name", "purpose"])
    for t in all_types:
        print("  {0} -> purpose: {1}".format(t.name, t.purpose))

    # 2. Check Property Setters on Stock Entry purpose field
    print("\n=== Property Setters on Stock Entry 'purpose' field ===")
    ps = frappe.db.get_all("Property Setter",
        filters={"doc_type": "Stock Entry", "field_name": "purpose"},
        fields=["name", "property", "value"])
    for p in ps:
        print("  {0}: {1} = {2}".format(p.name, p.property, p.value))

    # 3. Check Property Setters on Stock Entry stock_entry_type field
    print("\n=== Property Setters on Stock Entry 'stock_entry_type' field ===")
    ps2 = frappe.db.get_all("Property Setter",
        filters={"doc_type": "Stock Entry", "field_name": "stock_entry_type"},
        fields=["name", "property", "value"])
    for p in ps2:
        print("  {0}: {1} = {2}".format(p.name, p.property, p.value))

    # 4. Check Custom Fields on Stock Entry
    print("\n=== Custom Fields on Stock Entry ===")
    cfs = frappe.db.get_all("Custom Field",
        filters={"dt": "Stock Entry"},
        fields=["fieldname", "label", "fieldtype", "options", "default"])
    for c in cfs:
        print("  {0} ({1}) default={2}".format(c.fieldname, c.fieldtype, c.default))

    # 5. Simulate UI creation: create SE with only stock_entry_type set (no purpose)
    print("\n=== Simulating UI creation (stock_entry_type only, no explicit purpose) ===")
    se = frappe.new_doc("Stock Entry")
    se.stock_entry_type = "Material Transfer"
    print("  Before validate: stock_entry_type={0}, purpose={1}".format(se.stock_entry_type, se.purpose))

    # Manually call set_purpose_for_stock_entry to see what it does
    se.set_purpose_for_stock_entry()
    print("  After set_purpose_for_stock_entry: purpose={0}".format(se.purpose))

    # 6. Check if purpose field has a default via Customize Form
    print("\n=== Meta field info for 'purpose' ===")
    meta = frappe.get_meta("Stock Entry")
    purpose_field = meta.get_field("purpose")
    if purpose_field:
        print("  default: {0}".format(purpose_field.default))
        print("  hidden: {0}".format(purpose_field.hidden))
        print("  read_only: {0}".format(purpose_field.read_only))
        print("  fetch_from: {0}".format(purpose_field.fetch_from))
        print("  options: {0}".format(purpose_field.options))

    # 7. Check recent Stock Entries created via UI to see their purpose values
    print("\n=== Recent Stock Entries (last 10) ===")
    recent = frappe.db.get_all("Stock Entry",
        fields=["name", "stock_entry_type", "purpose", "docstatus", "creation"],
        order_by="creation desc",
        limit=10)
    for r in recent:
        print("  {0} | type={1} | purpose={2} | docstatus={3} | {4}".format(
            r.name, r.stock_entry_type, r.purpose, r.docstatus, r.creation))


def debug_rack_stock():
    """Debug: check stock for item 1311-124110GY in Main Stores - NCME across all racks."""
    item_code = "1311-124110GY"
    warehouse = "Main Stores - NCME"

    # 1. Stock per rack
    print("=== Stock for {0} in {1} (by rack) ===".format(item_code, warehouse))
    rack_stock = frappe.db.sql("""
        SELECT rack, SUM(actual_qty) as qty
        FROM `tabStock Ledger Entry`
        WHERE item_code = %s
        AND warehouse = %s
        AND is_cancelled = 0
        GROUP BY rack
        ORDER BY rack
    """, (item_code, warehouse), as_dict=True)
    for r in rack_stock:
        print("  Rack: '{0}' | Qty: {1}".format(r.rack, r.qty))

    # 2. Total stock in warehouse (regardless of rack)
    total = frappe.db.sql("""
        SELECT SUM(actual_qty)
        FROM `tabStock Ledger Entry`
        WHERE item_code = %s
        AND warehouse = %s
        AND is_cancelled = 0
    """, (item_code, warehouse))[0][0] or 0
    print("\n  Total stock (all racks): {0}".format(total))

    # 3. Check Bin table
    bin_qty = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty")
    print("  Bin actual_qty: {0}".format(bin_qty))

    # 4. Check if "Main" rack exists and has stock
    main_rack_qty = frappe.db.sql("""
        SELECT SUM(actual_qty)
        FROM `tabStock Ledger Entry`
        WHERE item_code = %s
        AND warehouse = %s
        AND rack = %s
        AND is_cancelled = 0
    """, (item_code, warehouse, "Main"))[0][0] or 0
    print("\n  Rack 'Main' qty: {0}".format(main_rack_qty))

    # 5. Check what racks exist for this item in this warehouse (including NULL rack)
    print("\n=== All SLE entries for this item/warehouse (last 20) ===")
    sles = frappe.db.get_all("Stock Ledger Entry",
        filters={"item_code": item_code, "warehouse": warehouse, "is_cancelled": 0},
        fields=["name", "rack", "actual_qty", "qty_after_transaction", "posting_date", "voucher_type", "voucher_no"],
        order_by="posting_date desc, creation desc",
        limit=20)
    for s in sles:
        print("  {0} | rack='{1}' | actual_qty={2} | after={3} | {4} | {5}".format(
            s.name, s.rack, s.actual_qty, s.qty_after_transaction, s.voucher_type, s.voucher_no))

    # 6. Check if "Damage stock location - NCME" warehouse exists
    damage_wh = frappe.db.get_value("Warehouse", "Damage stock location - NCME", "name")
    print("\n=== Target warehouse ===")
    print("  Damage stock location - NCME exists: {0}".format(bool(damage_wh)))

    # 7. Check company
    company = frappe.db.get_value("Warehouse", warehouse, "company")
    print("  Source warehouse company: {0}".format(company))
    if damage_wh:
        damage_company = frappe.db.get_value("Warehouse", "Damage stock location - NCME", "company")
        print("  Target warehouse company: {0}".format(damage_company))


def dump_client_script():
    """Dump the actual Client Script from database for Stock Entry."""
    cs = frappe.db.get_value("Client Script", {"dt": "Stock Entry"}, ["name", "script", "enabled"], as_dict=True)
    if not cs:
        print("No Client Script found for Stock Entry")
        return
    print("Name: {0}".format(cs.name))
    print("Enabled: {0}".format(cs.enabled))
    print("\n=== Script (length: {0}) ===".format(len(cs.script)))
    # Print in chunks to avoid truncation
    lines = cs.script.split('\n')
    for i, line in enumerate(lines):
        print("{0:04d}: {1}".format(i+1, line))
