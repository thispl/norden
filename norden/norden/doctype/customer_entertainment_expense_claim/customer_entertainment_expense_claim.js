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
         
    }
 
 
});
