// Copyright (c) 2022, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer Entertainment Expense Claim', {
   
    company(frm){
        if(frm.doc.company){
            var emp_basic = frappe.db.get_value('Company', frm.doc.company, 'default_payable_account')
            .then(r => {
                console.log(r.message.default_payable_account)
                frm.set_value('payable_account',r.message.default_payable_account)
    })
        }
         
    },
    employee(frm){
        frm.set_value('admin_mail_id','aiswarya@nordencommunication.com')
        frm.set_value('hrm_mail_id','kareem@nordencommunication.com')
        frm.set_value('accounts_mail_id','topson@nordencommunication.com')
        frm.set_value('cfo_mail_id','vijay@nordencommunication.com')
        frm.set_value('finance_mail_id','sabidha@nordencommunication.com')
        
        if(frm.doc.company == 'Norden Communication Pvt Ltd'){
            frm.set_value('finance_verifier_mail_id','salini@nordencommunication.com')
        }
        else if(frm.doc.company == 'Norden Research and Innovation Centre (OPC) Pvt. Ltd'){
            frm.set_value('finance_verifier_mail_id','lakshmi.devi@norden.co.uk')
        }
        
    }
 
 
});
