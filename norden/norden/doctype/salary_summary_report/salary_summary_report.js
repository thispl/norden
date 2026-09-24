// Copyright (c) 2024, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on("Salary Summary Report", {
	download(frm) {
        if (frm.doc.report == 'Salary Summary Report') {
            console.log('hi')
            var path = "norden.norden.doctype.salary_summary_report.salary_summary.export_payroll_to_excel"
            var args = 'from_date=%(from_date)s&to_date=%(to_date)s&company=%(company)s'
        }
        if (path) {
            window.location.href = repl(frappe.request.url +
                '?cmd=%(cmd)s&%(args)s', {
                cmd: path,
                args: args,
                from_date : frm.doc.from_date,
                to_date : frm.doc.to_date,	
                company : frm.doc.company
            });
        }
	},
});
