import frappe
@frappe.whitelist() 
def prepayment_journal_entry(name,date,party_type):
    if party_type == "Supplier":
        pay = frappe.get_doc("Prepayment",name)
        for d in pay.get("prepayment_details"):
            if not d.journal_entry_number:
                jour = frappe.new_doc("Journal Entry")
                jour.company = pay.company
                jour.posting_date = date
                jour.voucher_type = "Journal Entry"
                jour.pay_to_recd_from = pay.party
                dict_list = []
                dict_list.append(frappe._dict({"account": pay.expense_account_name,"cost_center":"Main - NCME","debit": d.prepayment_amount,"credit": 0}))
                dict_list.append(frappe._dict({"account": pay.prepayment_account,"party_type":pay.party_type,"party":pay.party,"cost_center":"Main - NCME","debit": 0,"credit": d.prepayment_amount}))
                for i in dict_list:
                    
                    jour.append('accounts', {
                        'account': i.account,
                        'party_type':i.party_type,
                        'party':i.party,
                        'cost_center':i.cost_center,

                        'debit_in_account_currency':i.debit,
                        'credit_in_account_currency':i.credit
                    })
                jour.save(ignore_permissions=True)
                jour.submit()
                d.db_set("journal_entry_number", jour.name)
                
                return jour.name
    
    elif party_type == "Employee":
        pay = frappe.get_doc("Prepayment",name)
        for d in pay.get("prepayment_details"):
            if not d.journal_entry_number:
                jour = frappe.new_doc("Journal Entry")
                jour.company = pay.company
                jour.posting_date = date
                jour.voucher_type = "Journal Entry"
                jour.pay_to_recd_from = pay.party
                dict_list = []
                dict_list.append(frappe._dict({"account":pay.expense_account_name,"cost_center":"Main - NCME","debit": d.prepayment_amount,"credit": 0}))
                dict_list.append(frappe._dict({"account": pay.prepayment_account,"party_type":pay.party_type,"party":pay.party,"cost_center":"Main - NCME","debit": 0,"credit": d.prepayment_amount}))
                for i in dict_list:
                    
                    jour.append('accounts', {
                        'account': i.account,
                        'party_type':i.party_type,
                        'party':i.party,
                        'cost_center':i.cost_center,

                        'debit_in_account_currency':i.debit,
                        'credit_in_account_currency':i.credit
                    })
                jour.save(ignore_permissions=True)
                jour.submit()

                d.db_set("journal_entry_number", jour.name)
                return jour.name
