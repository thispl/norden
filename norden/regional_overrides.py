def make_regional_gl_entries(gl_entries, doc):
	"""Hooked to make_regional_gl_entries in Purchase Invoice.It appends the region specific general ledger entries to the list of GL Entries."""
	country = frappe.get_cached_value("Company", doc.company, "country")

	if country != "United Arab Emirates":
		return gl_entries

	if doc.reverse_charge == "Y":
		tax_accounts = get_tax_accounts(doc.company)
		for tax in doc.get("taxes"):
			if tax.category not in ("Total", "Valuation and Total"):
				continue
			gl_entries = make_gl_entry(tax, gl_entries, doc, tax_accounts)
	return gl_entries


def make_gl_entry(tax, gl_entries, doc, tax_accounts):
	dr_or_cr = "credit" if tax.add_deduct_tax == "Add" else "debit"
	if flt(tax.base_tax_amount_after_discount_amount) and tax.account_head in tax_accounts:
		account_currency = get_account_currency(tax.account_head)

		gl_entries.append(
			doc.get_gl_dict(
				{
					"account": tax.account_head,
					"cost_center": tax.cost_center,
					"posting_date": doc.posting_date,
					"against": doc.supplier,
					dr_or_cr: tax.base_tax_amount_after_discount_amount,
					dr_or_cr + "_in_account_currency": tax.base_tax_amount_after_discount_amount
					if account_currency == doc.company_currency
					else tax.tax_amount_after_discount_amount,
				},
				account_currency,
				item=tax,
			)
		)
	return gl_entries

