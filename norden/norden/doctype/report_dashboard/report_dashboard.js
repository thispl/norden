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
	if (frm.doc.report == 'Unregistered Salary Report') {
		var path = "norden.norden.doctype.report_dashboard.unregistered_salary_report.download"
		var args = 'from_date=%(from_date)s&to_date=%(to_date)s&company=%(company)s&department=%(department)s&employee_grade=%(employee_grade)s'
	}
	if (frm.doc.report == 'Payroll Summary Report') {
		var path = "norden.norden.doctype.report_dashboard.payroll_summary_report.download"
		var args = 'from_date=%(from_date)s&to_date=%(to_date)s&company=%(company)s&department=%(department)s&employee_grade=%(employee_grade)s'
	}
	if (frm.doc.report == 'Test report') {
		var path = "norden.norden.doctype.report_dashboard.test_report.download"
		var args = 'from_date=%(from_date)s&to_date=%(to_date)s&company=%(company)s&department=%(department)s&employee_grade=%(employee_grade)s'
	}
	if (frm.doc.report == 'Summary Test Report') {
		console.log('hi')
		var path = "norden.norden.doctype.report_dashboard.summary_test_report.download"
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
