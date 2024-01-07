import frappe
from frappe import _
from frappe.desk.doctype.dashboard_chart.dashboard_chart import get_result
from frappe.utils import getdate
from frappe.utils.dashboard import cache_source
from frappe.utils.dateutils import get_period
from norden.norden.report.stock_ageing_report.stock_ageing_report import FIFOSlots, get_average_age
from operator import itemgetter
from erpnext.stock.doctype.warehouse.warehouse import apply_warehouse_filter
from typing import Any, Dict, List, Optional, TypedDict
from frappe.query_builder.functions import CombineDatetime
from frappe.utils import cint, date_diff, flt, getdate
from erpnext.stock.doctype.inventory_dimension.inventory_dimension import get_inventory_dimensions
from frappe.utils.nestedset import get_descendants_of


@frappe.whitelist()
@cache_source
def get_data(chart_name=None, chart=None, no_cache=None, filters=None,
			 from_date=None, to_date=None, timespan=None, time_interval=None,
			 heatmap_year=None) -> dict[str, list]:

	if filters:
		filters = frappe.parse_json(filters)
		from_date = filters.get("from_date")
		to_date = filters.get("to_date")
		company = filters.get("company")
		items = get_items(filters)
		sle = get_stock_ledger_entries(filters, items)
		iwb_map = get_item_warehouse_map(filters, sle)
		item_map = get_item_details(items, sle, filters)
		item_reorder_detail_map = get_item_reorder_details(item_map.keys())
		data = []
		dat = []
		for group_by_key in iwb_map:
			item = group_by_key[1]
			warehouse = group_by_key[2]
			company = group_by_key[0]
			if item_map.get(item):
				qty_dict = iwb_map[group_by_key]
				item_reorder_level = 0
				item_reorder_qty = 0
				if item + warehouse in item_reorder_detail_map:
					item_reorder_level = item_reorder_detail_map[item + warehouse]["warehouse_reorder_level"]
					item_reorder_qty = item_reorder_detail_map[item + warehouse]["warehouse_reorder_qty"]
				report_data = {
					"company": company,
				}
				report_data.update(qty_dict)
				dat.append(report_data)
		aggregated_data = {}
		for entry in dat:
			company_name = entry['company']
			if company_name == company:
				bal_qty = entry['bal_qty']
				bal_val = entry['bal_val']
				if company_name in aggregated_data:
					aggregated_data[company_name]['bal_qty'] += bal_qty
					aggregated_data[company_name]['bal_val'] += bal_val
				else:
					aggregated_data[company_name] = {'bal_qty': bal_qty, 'bal_val': bal_val}
	aggregated_data_list = [{'bal_qty': values['bal_qty']} for key, values in aggregated_data.items()]
	data.extend(aggregated_data_list)
	first_bal_qty_value = data[0]['bal_qty'] if data else 0
	frappe.errprint(first_bal_qty_value)
	return {
		"datasets": [
			{
				"name": _("Stock Quantity"),
				"values": first_bal_qty_value,
			},
		],
	}

def apply_conditions(query, filters):
	sle = frappe.qb.DocType("Stock Ledger Entry")
	warehouse_table = frappe.qb.DocType("Warehouse")
	if not filters.get("from_date"):
		frappe.throw(_("'From Date' is required"))
	if to_date := filters.get("to_date"):
		query = query.where(sle.posting_date <= to_date)
	else:
		frappe.throw(_("'To Date' is required"))
	if filters.get("warehouse"):
		query = apply_warehouse_filter(query, sle, filters)
	elif warehouse_type := filters.get("warehouse_type"):
		query = (
			query.join(warehouse_table)
			.on(warehouse_table.name == sle.warehouse)
			.where(warehouse_table.warehouse_type == warehouse_type)
		)
	return query

def get_stock_ledger_entries(filters, items: List[str]) -> List:
	sle = frappe.qb.DocType("Stock Ledger Entry")
	query = (
		frappe.qb.from_(sle)
		.select(
			sle.item_code,
			sle.warehouse,
			sle.posting_date,
			sle.actual_qty,
			sle.valuation_rate,
			sle.company,
			sle.voucher_type,
			sle.qty_after_transaction,
			sle.stock_value_difference,
			sle.item_code.as_("name"),
			sle.voucher_no,
			sle.stock_value,
			sle.batch_no,
		)
		.where((sle.docstatus < 2) & (sle.is_cancelled == 0))
		.orderby(CombineDatetime(sle.posting_date, sle.posting_time))
		.orderby(sle.creation)
		.orderby(sle.actual_qty)
	)
	inventory_dimension_fields = get_inventory_dimension_fields()
	if inventory_dimension_fields:
		for fieldname in inventory_dimension_fields:
			query = query.select(fieldname)
			if fieldname in filters and filters.get(fieldname):
				query = query.where(sle[fieldname].isin(filters.get(fieldname)))
	if items:
		query = query.where(sle.item_code.isin(items))
	query = apply_conditions(query, filters)
	return query.run(as_dict=True)


def get_inventory_dimension_fields():
	return [dimension.fieldname for dimension in get_inventory_dimensions()]


def get_item_warehouse_map(filters, sle: List):
	iwb_map = {}
	from_date = getdate(filters.get("from_date"))
	to_date = getdate(filters.get("to_date"))
	float_precision = cint(frappe.db.get_default("float_precision")) or 3
	inventory_dimensions = get_inventory_dimension_fields()
	for d in sle:
		group_by_key = get_group_by_key(d, filters, inventory_dimensions)
		if group_by_key not in iwb_map:
			iwb_map[group_by_key] = frappe._dict(
				{
					"opening_qty": 0.0,
					"opening_val": 0.0,
					"in_qty": 0.0,
					"in_val": 0.0,
					"out_qty": 0.0,
					"out_val": 0.0,
					"bal_qty": 0.0,
					"bal_val": 0.0,
					"val_rate": 0.0,
				}
			)
		qty_dict = iwb_map[group_by_key]
		for field in inventory_dimensions:
			qty_dict[field] = d.get(field)
		if d.voucher_type == "Stock Reconciliation" and not d.batch_no:
			qty_diff = flt(d.qty_after_transaction) - flt(qty_dict.bal_qty)
		else:
			qty_diff = flt(d.actual_qty)
		value_diff = flt(d.stock_value_difference)
		if d.posting_date < from_date or (
			d.posting_date == from_date
			and d.voucher_type == "Stock Reconciliation"
			and frappe.db.get_value("Stock Reconciliation", d.voucher_no, "purpose") == "Opening Stock"
		):
			qty_dict.opening_qty += qty_diff
			qty_dict.opening_val += value_diff
		elif d.posting_date >= from_date and d.posting_date <= to_date:
			if flt(qty_diff, float_precision) >= 0:
				qty_dict.in_qty += qty_diff
				qty_dict.in_val += value_diff
			else:
				qty_dict.out_qty += abs(qty_diff)
				qty_dict.out_val += abs(value_diff)
		qty_dict.val_rate = d.valuation_rate
		qty_dict.bal_qty += qty_diff
		qty_dict.bal_val += value_diff
	iwb_map = filter_items_with_no_transactions(iwb_map, float_precision, inventory_dimensions)
	return iwb_map

def get_group_by_key(row, filters, inventory_dimension_fields) -> tuple:
	group_by_key = [row.company, row.item_code, row.warehouse]
	for fieldname in inventory_dimension_fields:
		if filters.get(fieldname):
			group_by_key.append(row.get(fieldname))
	return tuple(group_by_key)

def filter_items_with_no_transactions(iwb_map, float_precision: float, inventory_dimensions: list):
	pop_keys = []
	for group_by_key in iwb_map:
		qty_dict = iwb_map[group_by_key]
		no_transactions = True
		for key, val in qty_dict.items():
			if key in inventory_dimensions:
				continue
			val = flt(val, float_precision)
			qty_dict[key] = val
			if key != "val_rate" and val:
				no_transactions = False
		if no_transactions:
			pop_keys.append(group_by_key)
	for key in pop_keys:
		iwb_map.pop(key)
	return iwb_map

def get_items(filters) -> List[str]:
	if item_code := filters.get("item_code"):
		return [item_code]
	else:
		item_filters = {}
		if item_group := filters.get("item_group"):
			children = get_descendants_of("Item Group", item_group, ignore_permissions=True)
			item_filters["item_group"] = ("in", children + [item_group])
		if brand := filters.get("brand"):
			item_filters["brand"] = brand
		return frappe.get_all("Item", filters=item_filters, pluck="name", order_by=None)
	
def get_item_details(items: List[str], sle: List, filters):
	item_details = {}
	if not items:
		items = list(set(d.item_code for d in sle))
	if not items:
		return item_details
	item_table = frappe.qb.DocType("Item")
	query = (
		frappe.qb.from_(item_table)
		.select(
			item_table.name,
			item_table.item_name,
			item_table.description,
			item_table.item_group,
			item_table.brand,
			item_table.stock_uom,
		)
		.where(item_table.name.isin(items))
	)
	if uom := filters.get("include_uom"):
		uom_conv_detail = frappe.qb.DocType("UOM Conversion Detail")
		query = (
			query.left_join(uom_conv_detail)
			.on((uom_conv_detail.parent == item_table.name) & (uom_conv_detail.uom == uom))
			.select(uom_conv_detail.conversion_factor)
		)

	result = query.run(as_dict=1)
	for item_table in result:
		item_details.setdefault(item_table.name, item_table)
	if filters.get("show_variant_attributes"):
		variant_values = get_variant_values_for(list(item_details))
		item_details = {k: v.update(variant_values.get(k, {})) for k, v in item_details.items()}
	return item_details

def get_item_reorder_details(items):
	item_reorder_details = frappe._dict()
	if items:
		item_reorder_details = frappe.get_all(
			"Item Reorder",
			["parent", "warehouse", "warehouse_reorder_qty", "warehouse_reorder_level"],
			filters={"parent": ("in", items)},
		)
	return dict((d.parent + d.warehouse, d) for d in item_reorder_details)

def get_variants_attributes() -> List[str]:
	return frappe.get_all("Item Attribute", pluck="name")

def get_variant_values_for(items):
	attribute_map = {}
	attribute_info = frappe.get_all(
		"Item Variant Attribute",
		["parent", "attribute", "attribute_value"],
		{
			"parent": ("in", items),
		},
	)
	for attr in attribute_info:
		attribute_map.setdefault(attr["parent"], {})
		attribute_map[attr["parent"]].update({attr["attribute"]: attr["attribute_value"]})

	return attribute_map

