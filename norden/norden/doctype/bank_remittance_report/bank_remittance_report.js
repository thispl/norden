// Copyright (c) 2024, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bank Remittance Report", {
    downlaod(frm) {
        var path = "norden.norden.doctype.bank_remittance_report.bank_remittance_report.download";
        var args = {
            cmd: path,
            vdate: frm.doc.value_date,
            company:frm.doc.company
        };
    
        var url = repl(frappe.request.url + '?cmd=%(cmd)s', { cmd: path });
        url += '&' + $.param(args); 
        window.location.href = url;
    }

});
