// Copyright (c) 2022, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on('Approval Summary', {
	refresh: function(frm) {
		// frappe.show_progress('Loading..',1);
		frm.disable_save()

	$('*[data-fieldname="quotation_approval"]').find('.grid-remove-rows').hide();
	$('*[data-fieldname="quotation_approval"]').find('.grid-remove-all-rows').hide();
	$('*[data-fieldname="quotation_approval"]').find('.grid-add-row').remove()

	$('*[data-fieldname="sales_order_approval"]').find('.grid-remove-rows').hide();
	$('*[data-fieldname="sales_order_approval"]').find('.grid-remove-all-rows').hide();
	$('*[data-fieldname="sales_order_approval"]').find('.grid-add-row').remove()

	$('*[data-fieldname="purchase_order_approval"]').find('.grid-remove-rows').hide();
	$('*[data-fieldname="purchase_order_approval"]').find('.grid-remove-all-rows').hide();
	$('*[data-fieldname="purchase_order_approval"]').find('.grid-add-row').remove()

	
	$('*[data-fieldname="expense_claim_summary"]').find('.grid-remove-rows').hide();
	$('*[data-fieldname="expense_claim_summary"]').find('.grid-remove-all-rows').hide();
	$('*[data-fieldname="expense_claim_summary"]').find('.grid-add-row').remove()


	$('*[data-fieldname="leave_application_approval"]').find('.grid-remove-rows').hide();
	$('*[data-fieldname="leave_application_approval"]').find('.grid-remove-all-rows').hide();
	$('*[data-fieldname="leave_application_approval"]').find('.grid-add-row').remove()


	$('*[data-fieldname="attendance_request_approval"]').find('.grid-remove-rows').hide();
	$('*[data-fieldname="attendance_request_approval"]').find('.grid-remove-all-rows').hide();
	$('*[data-fieldname="attendance_request_approval"]').find('.grid-add-row').remove()
	
	if (frappe.user.has_role(['COO'])){
		frm.fields_dict["quotation_approval"].grid.add_custom_button(__('Reject'),
				function () {
					if(frm.doc.quotation_approval){
						$.each(frm.doc.quotation_approval, function (i, d) {
						if (d.__checked == 1) {
							frm.call('submit_doc', {
								doctype: "Quotation",
								name: d.quotation,
								workflow_state: 'Rejected'
							})
							frm.get_field("quotation_approval").grid.grid_rows[d.idx - 1].remove();
						}
						})
					}
					
				}).addClass('btn-danger')


				frm.fields_dict["quotation_approval"].grid.add_custom_button(__('Approve'),
				function () {
					if(frm.doc.quotation_approval){
						$.each(frm.doc.quotation_approval, function (i, d) {
						if (d.__checked == 1) {
							frm.call('submit_quote', {
								doctype: "Quotation",
								name: d.quotation,
								work_flow: 'Pending for CFO'
							})
							frm.get_field("quotation_approval").grid.grid_rows[d.idx - 1].remove();
						}
						})
					}
				}).css({'color':'white','background-color':"#009E60","margin-left": "10px", "margin-right": "10px"});

				frm.fields_dict["sales_order_approval"].grid.add_custom_button(__('Reject'),
				function () {
					if (d.__checked == 1) {
					$.each(frm.doc.sales_order_approval, function (i, d) {
						frm.call('submit_doc', {
							doctype: "Sales Order",
							name: d.sales_order,
							workflow_state: 'Draft'
						})
						frm.get_field("sales_order_approval").grid.grid_rows[d.idx - 1].remove();
						
					})
				}
				}).addClass('btn-danger')


				frm.fields_dict["sales_order_approval"].grid.add_custom_button(__('Approve'),function () {
					if(frm.doc.sales_order_approval){
					$.each(frm.doc.sales_order_approval, function (i, d) {
						if (d.__checked == 1) {
							console.log(d)
							frm.call('submit_doc', {
								doctype: "Sales Order",
								name: d.sales_order,
								workflow_state: 'Pending for CFO'
							})
							frm.get_field("sales_order_approval").grid.grid_rows[d.idx - 1].remove();
						}
					})
					
				}
				}).css({'color':'white','background-color':"#009E60","margin-left": "10px", "margin-right": "10px"});

				frm.fields_dict["purchase_order_approval"].grid.add_custom_button(__('Reject'),
				function () {
					if(frm.doc.purchase_order_approval){
					$.each(frm.doc.quotation_approval, function (i, d) {
						if (d.__checked == 1) {
							frm.call('submit_doc', {
								doctype: "Purchase Order",
								name: d.purchase_order,
								workflow_state: 'Draft'
							})
							frm.get_field("purchase_order_approval").grid.grid_rows[d.idx - 1].remove();
						}
							})
					}
					
				}).addClass('btn-danger')


				frm.fields_dict["purchase_order_approval"].grid.add_custom_button(__('Approve'),
				function () {
					if(frm.doc.purchase_order_approval){
						$.each(frm.doc.purchase_order_approval, function (i, d) {
							if (d.__checked == 1) {
								frm.call('submit_doc', {
									doctype: "Purchase Order",
									name: d.on_duty_application,
									workflow_state: 'Pending for CFO'
								})
								frm.get_field("purchase_order_approval").grid.grid_rows[d.idx - 1].remove();
							}
								})
					}
				
				}).css({'color':'white','background-color':"#009E60","margin-left": "10px", "margin-right": "10px"});



	}

	if (frappe.user.has_role(['HOD'])){

		frm.fields_dict["sales_order_approval"].grid.add_custom_button(__('Reject'),
				function () {
					if (d.__checked == 1) {
					$.each(frm.doc.sales_order_approval, function (i, d) {
						frm.call('submit_doc', {
							doctype: "Sales Order",
							name: d.sales_order,
							workflow_state: 'Draft'
						})
						frm.get_field("sales_order_approval").grid.grid_rows[d.idx - 1].remove();
						
					})
				}
				}).addClass('btn-danger')


				frm.fields_dict["sales_order_approval"].grid.add_custom_button(__('Approve'),function () {
					if(frm.doc.sales_order_approval){
					$.each(frm.doc.sales_order_approval, function (i, d) {
						if (d.__checked == 1) {
							console.log(d)
							frm.call('submit_doc', {
								doctype: "Sales Order",
								name: d.sales_order,
								workflow_state: 'Pending for Accounts'
							})
							frm.get_field("sales_order_approval").grid.grid_rows[d.idx - 1].remove();
						}
					})
					
				}
				}).css({'color':'white','background-color':"#009E60","margin-left": "10px", "margin-right": "10px"});
		
		frm.fields_dict["expense_claim_summary"].grid.add_custom_button(__('Reject'),
				function () {
					if(frm.doc.quotation_approval){
						$.each(frm.doc.quotation_approval, function (i, d) {
						if (d.__checked == 1) {
							frm.call('submit_doc', {
								doctype: "Expense Claim",
								name: d.expense_claim,
								workflow_state: 'Rejected'
							})
							frm.get_field("expense_claim_summary").grid.grid_rows[d.idx - 1].remove();
						}
						})
					}
					
				}).addClass('btn-danger')


				frm.fields_dict["expense_claim_summary"].grid.add_custom_button(__('Approve'),
				function () {
					if(frm.doc.quotation_approval){
						$.each(frm.doc.quotation_approval, function (i, d) {
						if (d.__checked == 1) {
							frm.call('submit_quote', {
								doctype: "Expense Claim",
								name: d.expense_claim,
								work_flow: 'Pending for Admin Verification'
							})
							frm.get_field("expense_claim_summary").grid.grid_rows[d.idx - 1].remove();
						}
						})
					}
				}).css({'color':'white','background-color':"#009E60","margin-left": "10px", "margin-right": "10px"});

				
				frm.fields_dict["leave_application_approval"].grid.add_custom_button(__('Reject'),
				function () {
					if(frm.doc.quotation_approval){
						$.each(frm.doc.quotation_approval, function (i, d) {
						if (d.__checked == 1) {
							frm.call('submit_doc', {
								doctype: "Attendance Request",
								name: d.leave_application,
								workflow_state: 'Rejected'
							})
							frm.get_field("leave_application_approval").grid.grid_rows[d.idx - 1].remove();
						}
						})
					}
					
				}).addClass('btn-danger')


				frm.fields_dict["leave_application_approval"].grid.add_custom_button(__('Approve'),
				function () {
					if(frm.doc.quotation_approval){
						$.each(frm.doc.quotation_approval, function (i, d) {
						if (d.__checked == 1) {
							frm.call('submit_quote', {
								doctype: "Attendance Request",
								name: d.leave_application,
								work_flow: 'Approved'
							})
							frm.get_field("leave_application_approval").grid.grid_rows[d.idx - 1].remove();
						}
						})
					}
				}).css({'color':'white','background-color':"#009E60","margin-left": "10px", "margin-right": "10px"});
			}



			//# CFO
			if (frappe.user.has_role(['CFO'])){

				frm.fields_dict["purchase_order_approval"].grid.add_custom_button(__('Reject'),
				function () {
					if(frm.doc.purchase_order_approval){
					$.each(frm.doc.quotation_approval, function (i, d) {
						if (d.__checked == 1) {
							frm.call('submit_doc', {
								doctype: "Purchase Order",
								name: d.purchase_order,
								workflow_state: 'Draft'
							})
							frm.get_field("purchase_order_approval").grid.grid_rows[d.idx - 1].remove();
						}
							})
					}
					
				}).addClass('btn-danger')


				frm.fields_dict["purchase_order_approval"].grid.add_custom_button(__('Approve'),
				function () {
					if(frm.doc.purchase_order_approval){
						$.each(frm.doc.purchase_order_approval, function (i, d) {
							if (d.__checked == 1) {
								frm.call('submit_doc', {
									doctype: "Purchase Order",
									name: d.on_duty_application,
									workflow_state: 'Approved'
								})
								frm.get_field("purchase_order_approval").grid.grid_rows[d.idx - 1].remove();
							}
								})
					}
				
				}).css({'color':'white','background-color':"#009E60","margin-left": "10px", "margin-right": "10px"});
				frm.fields_dict["sales_order_approval"].grid.add_custom_button(__('Reject'),
				function () {
					if (d.__checked == 1) {
					$.each(frm.doc.sales_order_approval, function (i, d) {
						frm.call('submit_doc', {
							doctype: "Sales Order",
							name: d.sales_order,
							workflow_state: 'Draft'
						})
						frm.get_field("sales_order_approval").grid.grid_rows[d.idx - 1].remove();
						
					})
				}
				}).addClass('btn-danger')


				frm.fields_dict["sales_order_approval"].grid.add_custom_button(__('Approve'),function () {
					if(frm.doc.sales_order_approval){
					$.each(frm.doc.sales_order_approval, function (i, d) {
						if (d.__checked == 1) {
							console.log(d)
							frm.call('submit_doc', {
								doctype: "Sales Order",
								name: d.sales_order,
								workflow_state: 'Approved'
							})
							frm.get_field("sales_order_approval").grid.grid_rows[d.idx - 1].remove();
						}
					})
					
				}
				}).css({'color':'white','background-color':"#009E60","margin-left": "10px", "margin-right": "10px"});


				frm.fields_dict["expense_claim_summary"].grid.add_custom_button(__('Reject'),
						function () {
							if(frm.doc.quotation_approval){
								$.each(frm.doc.quotation_approval, function (i, d) {
								if (d.__checked == 1) {
									frm.call('submit_doc', {
										doctype: "Expense Claim",
										name: d.expense_claim,
										workflow_state: 'Rejected'
									})
									frm.get_field("expense_claim_summary").grid.grid_rows[d.idx - 1].remove();
								}
								})
							}
							
						}).addClass('btn-danger')
		
		
						frm.fields_dict["expense_claim_summary"].grid.add_custom_button(__('Approve'),
						function () {
							if(frm.doc.quotation_approval){
								$.each(frm.doc.quotation_approval, function (i, d) {
									console.log(d)
								if (d.__checked == 1) {
									frm.call('submit_quote', {
										doctype: "Expense Claim",
										name: d.expense_claim,
										work_flow: 'Pending for Finance Verification'
									})
									frm.get_field("expense_claim_summary").grid.grid_rows[d.idx - 1].remove();
								}
								})
							}
						}).css({'color':'white','background-color':"#009E60","margin-left": "10px", "margin-right": "10px"});
					}
	
	},

	onload(frm){
		// frappe.publish_progress(5, title='Loading', description='Loading')
		frappe.run_serially([
			() => frm.call('get_quote').then(r=>{
				if (r.message) {
					$.each(r.message, function (i, s) {
						frm.add_child('quotation_approval', {
							'quotation':s.name,
							'customer':s.party_name,
							'date':s.transaction_date,
							'sales_person':s.sales_person_name
						})
						frm.refresh_field('quotation_approval')
					})
				}
			}),

			() => frm.call('get_sales_order_hod').then(r=>{
				if (r.message) {
					$.each(r.message, function (i, d) {
						frm.add_child('sales_order_approval', {
							'sales_order':d.name,
							'customer':d.customer,
							'date':d.transaction_date,
						})
						frm.refresh_field('sales_order_approval')
					})
				}
			})	,

			() => frm.call('get_sales_order_cfo').then(r=>{
				if (r.message) {
					$.each(r.message, function (i, d) {
						frm.add_child('sales_order_approval', {
							'sales_order':d.name,
							'customer':d.customer,
							'date':d.transaction_date,
						})
						frm.refresh_field('sales_order_approval')
					})
				}
			})	,

			() => frm.call('get_sales_order').then(r=>{
				if (r.message) {
					$.each(r.message, function (i, d) {
						frm.add_child('sales_order_approval', {
							'sales_order':d.name,
							'customer':d.customer,
							'date':d.transaction_date,
						})
						frm.refresh_field('sales_order_approval')
					})
				}
			})	,


			() => frm.call('get_po_cfo').then(r=>{
				if (r.message) {
					$.each(r.message, function (i, d) {
						frm.add_child('purchase_order_approval', {
							'purchase_order':d.name,
							'supplier':d.supplier,
							'date':d.transaction_date,
						})
						frm.refresh_field('purchase_order_approval')
					})
				}
			})	,

			() => frm.call('get_expence_claim').then(r=>{
				if (r.message) {
					$.each(r.message, function (i, d) {
						frm.add_child('expense_claim_summary', {
							'from_employee':d.employee,
							'employee_name':d.employee_name,
							'expense_approver':d.expense_approver,
							'total_amount':d.total_claimed_amount
							
						})
						frm.refresh_field('expense_claim_summary')
					})
				}
			})	,

			() => frm.call('get_expence_claim_1').then(r=>{
				if (r.message) {
					$.each(r.message, function (i, d) {
						frm.add_child('expense_claim_summary', {
							'from_employee':d.employee,
							'employee_name':d.employee_name,
							'expense_approver':d.expense_approver,
							'total_amount':d.total_claimed_amount
							
						})
						frm.refresh_field('expense_claim_summary')
					})
				}
			})	,

			() => frm.call('get_leave_app').then(r=>{
				if (r.message) {
					$.each(r.message, function (i, d) {
						frm.add_child('leave_application_approval', {
							'for_employee':d.employee,
							'employee_name':d.employee_name,
							'leave_type':d.leave_type,
							'from_date':d.from_date,
							'to_date':d.to_date,
							'total_leave_days':d.total_leave_days
							
						})
						frm.refresh_field('leave_application_approval')
					})
				}
			}),
			// () => frm.call('get_att_req').then(r=>{
			// 	if (r.message) {
			// 		$.each(r.message, function (i, d) {
			// 			frm.add_child('leave_application_approval', {
			// 				'for_employee':d.employee,
			// 				'employee_name':d.employee_name,
			// 				'reason':d.reason,
			// 				'from_date':d.from_date,
			// 				'to_date':d.to_date,
							
			// 			})
			// 			frm.refresh_field('leave_application_approval')
			// 		})
			// 	}
			// })
				
	

		])
		
	
		
	
		
	
	}

	

	
});
