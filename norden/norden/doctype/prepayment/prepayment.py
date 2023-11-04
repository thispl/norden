# # Copyright (c) 2023, Teampro and contributors
# # For license information, please see license.txt

# # import frappe
# import frappe
# import math
# from dateutil.relativedelta import relativedelta
# from frappe.model.document import Document
# from frappe.utils import (
#     add_days,
#     add_months,
#     cint,
#     ceil,
#     date_diff,
#     flt,
#     get_first_day,
#     get_last_day,
#     get_link_to_form,
#     getdate,
#     rounded,
#     today,
    
# )
# class Prepayment(Document):
#     def validate(self):
#         self.get_po()
#         self.payment_amt()
#         self.child_pay()
        
    
           
#     def get_po(self):
#         po_date = self.payment_posting_date
#         last_day = get_last_day(po_date)
#         self.posting_date = last_day

#     def payment_amt(self):
#         amt = ( self.total_amount_to_be_paid / self.total_number_of_prepayment )
#         self.payment_amount = ceil(amt)
        
#     def child_pay(self):
#         total_number_of_prepayment = int(self.total_number_of_prepayment)
#         if total_number_of_prepayment:
#             posting_date = frappe.utils.getdate(self.posting_date)
#             accumulated_amount = 0
#             for i in range(total_number_of_prepayment):
#                 if i == 0:
#                     end_of_month = posting_date
#                 else:
#                     end_of_month = end_of_month + relativedelta(months=1)
                    
#                 end_of_month = end_of_month.replace(day=1) + relativedelta(day=31)
#                 self.prepayment_amount = self.payment_amount
#                 accumulated_amount += self.prepayment_amount
#                 self.accumulated_amount = accumulated_amount
    
    

#     @frappe.whitelist()
#     def child_payment(self):
#         amt = ( self.total_amount_to_be_paid / self.total_number_of_prepayment )
#         payment_amount = ceil(amt)
#         dict_list = []
#         total_number_of_prepayment = int(self.total_number_of_prepayment)
#         if total_number_of_prepayment:
#             posting_date = frappe.utils.getdate(self.posting_date)
#             accumulated_amount = 0
#             for i in range(total_number_of_prepayment):
#                 if i == 0:
#                     end_of_month = posting_date
#                 else:
#                     end_of_month = end_of_month + relativedelta(months=1)
                    
#                 end_of_month = end_of_month.replace(day=1) + relativedelta(day=31)
#                 prepayment_amount = payment_amount
#                 accumulated_amount += prepayment_amount
#                 accumulated_amount = accumulated_amount
#                 dict_list.append(frappe._dict({"date": end_of_month,"prepayment_amount": payment_amount,"accumulated_amount": accumulated_amount}))    
#         return payment_amount,dict_list
    
# Copyright (c) 2023, Teampro and contributors
# For license information, please see license.txt

# import frappe
# from frappe.model.document import Document
import frappe
import math
from dateutil.relativedelta import relativedelta
from frappe.model.document import Document
from datetime import datetime, timedelta
from frappe.utils import add_years
from frappe.utils import (
    add_days,
    add_months,
    cint,
    nowdate,
    ceil,
    format_date,
    format_datetime,
    now_datetime,
    get_datetime,
    get_datetime_str,
    date_diff,
    get_time,
    cstr,
    flt,
    get_first_day,
    get_last_day,
    get_link_to_form,
    getdate,
    rounded,
    today,
    
)

class Prepayment(Document):
    def validate(self):
        self.child_payment()

    @frappe.whitelist()
    def child_payment(self):
        po_date = self.payment_posting_date
        last_day = get_last_day(po_date)

        self.posting_date = last_day
        number_of_days = date_diff(self.posting_date, self.payment_posting_date) + 1
        amt = ( self.total_amount_to_be_paid / self.total_number_of_prepayment )
        payment = ceil(amt)
        month_day = last_day
        datetime_str = format_datetime(month_day, format_string="yyyy-MM-dd HH:mm:ss")
        last_digit = datetime_str[8:10]
        str_int = int(last_digit)

        frappe.errprint(str_int)
        frappe.errprint(type(str_int))
        day_amt = payment / str_int
        first_month_amt = ceil(day_amt * number_of_days)
        dict_list = []
        end_of_month = ''
        add_do = ''
        total_number_of_prepayment = int(self.total_number_of_prepayment)
        if total_number_of_prepayment:
            posting_date = frappe.utils.getdate(self.posting_date)
            acc_amt = 0
            for i in range(0,(total_number_of_prepayment + 1)):
                if i == 0:
                    end_of_month = posting_date
                    new_amt = first_month_amt
                    acc_amt += new_amt
                elif i < (total_number_of_prepayment):
                    do = datetime.strptime(po_date, '%Y-%m-%d')
                    add_do = get_last_day(do + relativedelta(months = i))
                    add_do_str = add_do.strftime("%Y-%m-%d")
                    end_of_month =  add_do_str
                    new_amt = payment 
                    acc_amt += new_amt
                
                elif i == (total_number_of_prepayment):
                    do = datetime.strptime(po_date, '%Y-%m-%d')
                    add_do = do + relativedelta(months = total_number_of_prepayment)
                    add_do_str = add_do.strftime("%Y-%m-%d")
                    end_of_month =  add_do_str
                    new_amt = payment - first_month_amt
                    acc_amt += new_amt
                dict_list.append(frappe._dict({"date": end_of_month,"prepayment_amount": new_amt,"accumulated_amount": acc_amt}))    
        return payment,dict_list,first_month_amt
    
    def on_submit(self):
        if self.party_type == "Supplier":
            if self.journal_entry_created == 0:
                journal = frappe.new_doc("Journal Entry")
                journal.company = self.company
                journal.posting_date = self.posting_date
                journal.voucher_type = "Journal Entry"
                journal.pay_to_recd_from = self.party
                dict_list = []
                dict_list.append(frappe._dict({"account": self.prepayment_account,"cost_center":"Main - NCME","debit": self.total_amount_to_be_paid,"credit": 0}))
                dict_list.append(frappe._dict({"account": self.party_account,"party_type":self.party_type,"party":self.party,"cost_center":"Main - NCME","debit": 0,"credit": self.total_amount_to_be_paid}))
                for i in dict_list:
                
                    journal.append('accounts', {
                        'account': i.account,
                        'party_type':i.party_type,
                        'party':i.party,
                        'cost_center':i.cost_center,
                        'debit_in_account_currency':i.debit,
                        'credit_in_account_currency':i.credit
                    })
                journal.save(ignore_permissions=True)
                self.journal_entry_created = 1

                journal.submit()
                return journal.name
            
        if self.party_type == "Employee":
            if self.journal_entry_created == 0:
                journal = frappe.new_doc("Journal Entry")
                journal.company = self.company
                journal.posting_date = self.posting_date
                journal.voucher_type = "Journal Entry"
                journal.pay_to_recd_from = self.party
                dict_list = []
                dict_list.append(frappe._dict({"account": self.prepayment_account,"cost_center":"Main - NCME","debit": self.total_amount_to_be_paid,"credit": 0}))
                dict_list.append(frappe._dict({"account": self.party_account,"party_type":self.party_type,"party":self.party,"cost_center":"Main - NCME","debit": 0,"credit": self.total_amount_to_be_paid}))
                for i in dict_list:
                
                    journal.append('accounts', {
                        'account': i.account,
                        'party_type':i.party_type,
                        'party':i.party,
                        'cost_center':i.cost_center,
                        'debit_in_account_currency':i.debit,
                        'credit_in_account_currency':i.credit
                    })
                journal.save(ignore_permissions=True)
                self.journal_entry_created = 1
                journal.submit()
                return journal.name
