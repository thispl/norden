// Copyright (c) 2022, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on('Report Dashboard', {
	// refresh: function(frm) {

	// }
download: function (frm) {
	if (frm.doc.report == 'Bank Format') {
		var path = "norden.norden.doctype.report_dashboard.bank_format.download"
		var args = 'from_date=%(from_date)s&to_date=%(to_date)s&company=%(company)s&department=%(department)s&employee_grade=%(employee_grade)s'
	}
	

	if (path) {
		window.location.href = repl(frappe.request.url +
			'?cmd=%(cmd)s&%(args)s', {
			cmd: path,
			args: args,
			date: frm.doc.date,
			from_date : frm.doc.from_date,
			to_date : frm.doc.to_date,	
			company : frm.doc.company,
			department : frm.doc.department,
			employee_grade : frm.doc.employee_grade
		});
	}
},

});
