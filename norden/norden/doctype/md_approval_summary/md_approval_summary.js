// Copyright (c) 2023, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on('MD Approval Summary', {
	refresh: function (frm) {
		// frappe.show_progress('Loading..',1);
		frm.disable_save()


		$('*[data-fieldname="expense_claim_summary"]').find('.grid-remove-rows').hide();
		$('*[data-fieldname="expense_claim_summary"]').find('.grid-remove-all-rows').hide();
		$('*[data-fieldname="expense_claim_summary"]').find('.grid-add-row').remove()


		$('*[data-fieldname="leave_application_approval"]').find('.grid-remove-rows').hide();
		$('*[data-fieldname="leave_application_approval"]').find('.grid-remove-all-rows').hide();
		$('*[data-fieldname="leave_application_approval"]').find('.grid-add-row').remove()


		$('*[data-fieldname="attendance_request_approval"]').find('.grid-remove-rows').hide();
		$('*[data-fieldname="attendance_request_approval"]').find('.grid-remove-all-rows').hide();
		$('*[data-fieldname="attendance_request_approval"]').find('.grid-add-row').remove()


		if (frappe.session.user) {
			frm.fields_dict["expense_claim_summary"].grid.add_custom_button(__('Reject'),
				function () {
					if (frm.doc.expense_claim_summary) {
						$.each(frm.doc.expense_claim_summary, function (i, d) {
							if (d.__checked == 1) {
								frm.call('submit_doc', {
									doctype: "Expense Claim",
									name: d.application_no,
									workflow_state: 'Rejected'
								}).then(r => {
									frm.get_field("expense_claim_summary").grid.grid_rows[d.idx - 1].remove();
								})
							}
						})
					}

				}).addClass('btn-danger')

			frm.fields_dict["expense_claim_summary"].grid.add_custom_button(__('Approve'),
				function () {
					if (frm.doc.expense_claim_summary) {
						$.each(frm.doc.expense_claim_summary, function (i, d) {
							if (d.__checked == 1) {
								frm.call('submit_doc', {
									doctype: "Expense Claim",
									name: d.application_no,
									workflow_state: 'Pending for HRM'
								}).then(r => {
									frm.get_field("expense_claim_summary").grid.grid_rows[d.idx - 1].remove();
								})
							}
						})
					}
				}).css({ 'color': 'white', 'background-color': "#009E60", "margin-left": "10px", "margin-right": "10px" });


			frm.fields_dict["leave_application_approval"].grid.add_custom_button(__('Reject'),
				function () {
					if (frm.doc.leave_application_approval) {
						$.each(frm.doc.leave_application_approval, function (i, d) {
							if (d.__checked == 1) {
								frm.call('submit_doc', {
									doctype: "Leave Application",
									name: d.application_no,
									workflow_state: 'Rejected'
								}).then(r => {
									frm.get_field("leave_application_approval").grid.grid_rows[d.idx - 1].remove();
								})
							}
						})
					}

				}).addClass('btn-danger')


			frm.fields_dict["leave_application_approval"].grid.add_custom_button(__('Approve'),
				function () {
					if (frm.doc.leave_application_approval) {
						$.each(frm.doc.leave_application_approval, function (i, d) {
							if (d.__checked == 1) {
								frm.refresh_field('leave_application_approval')
								frm.call('submit_doc', {
									doctype: "Leave Application",
									name: d.application_no,
									workflow_state: 'Approved'
								})
								.then(r => {
									frm.get_field("leave_application_approval").grid.grid_rows[d.idx - 1].remove();
								})
							}
						})
					}
				}).css({ 'color': 'white', 'background-color': "#009E60", "margin-left": "10px", "margin-right": "10px" });
		}

	},

	onload(frm) {
		frappe.run_serially([
			() => frm.call('get_expence_claim').then(r => {
				if (frappe.session.user) {
					if (r.message) {
						$.each(r.message, function (i, d) {
							frm.add_child('expense_claim_summary', {
								"application_no": d.name,
								'from_employee': d.employee,
								'employee_name': d.employee_name,
								'expense_approver': d.expense_approver,
								'total_amount': d.total_claimed_amount

							})
							frm.refresh_field('expense_claim_summary')
						})
					}

				}
			}),

			() => frm.call('get_leave_app').then(r => {
				if (frappe.session.user) {
					if (r.message) {
						$.each(r.message, function (i, d) {
							frm.add_child('leave_application_approval', {
								"application_no": d.name,
								'for_employee': d.employee,
								'employee_name': d.employee_name,
								'leave_type': d.leave_type,
								'from_date': d.from_date,
								'to_date': d.to_date,
								'total_leave_days': d.total_leave_days

							})
							frm.refresh_field('leave_application_approval')
						})
					}

				}
			}),

		])






	}

});
