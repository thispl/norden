// Copyright (c) 2022, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on('Approval Summary', {
	refresh: function(frm) {
		frm.disable_save()
		frm.trigger("data_fetch")

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
	
	$('*[data-fieldname="travel_request_approval"]').find('.grid-remove-rows').hide();
	$('*[data-fieldname="travel_request_approval"]').find('.grid-remove-all-rows').hide();
	$('*[data-fieldname="travel_request_approval"]').find('.grid-add-row').remove()

	
	//Operation Director
	if (frappe.user.has_role(['Operation Director'])){
		frm.fields_dict["quotation_approval"].grid.add_custom_button(__('Reject'),
		function () {
			if(frm.doc.quotation_approval){
				$.each(frm.doc.quotation_approval, function (i, d) {
					if (d.__checked == 1) {
						frm.call('submit_quote', {
							doctype: "Quotation",
							name: d.quotation,
							work_flow: 'Draft'
						}).then(r => {
							frm.get_field("quotation_approval").grid.grid_rows[d.idx - 1].remove();
						})
					}
				})
			}			
		}).addClass('btn-danger')


		frm.fields_dict["quotation_approval"].grid.add_custom_button(__('Approve'),
		function () {
			if(frm.doc.quotation_approval){
				$.each(frm.doc.quotation_approval, function (i, d) {
					if (d.__checked == 1) {
						frm.call('quote_submission', {
							doctype: "Quotation",
							name: d.quotation,
						}).then(r => {
							frm.get_field("quotation_approval").grid.grid_rows[d.idx - 1].remove();
						})
					}
				})
			}
		}).css({'color':'white','background-color':"#009E60","margin-left": "10px", "margin-right": "10px"});

		// frm.fields_dict["sales_order_approval"].grid.add_custom_button(__('Reject'),
		// function () {
		// 	if (d.__checked == 1) {
		// 	$.each(frm.doc.sales_order_approval, function (i, d) {
		// 		frm.call('submit_all_doc_after_approval', {
		// 			doctype: "Sales Order",
		// 			name: d.sales_order,
		// 			workflow_state: 'Draft'
		// 		})
		// 		frm.get_field("sales_order_approval").grid.grid_rows[d.idx - 1].remove();
				
				
		// 	})
		// }
		// }).addClass('btn-danger')


		// frm.fields_dict["sales_order_approval"].grid.add_custom_button(__('Approve'),function () {
		// 	if(frm.doc.sales_order_approval){
		// 	$.each(frm.doc.sales_order_approval, function (i, d) {
		// 		if (d.__checked == 1) {
		// 			console.log(d)
		// 			frm.call('submit_all_doc_after_approval', {
		// 				doctype: "Sales Order",
		// 				name: d.sales_order,
		// 				workflow_state: 'Pending for CFO'
		// 			})
		// 			frm.get_field("sales_order_approval").grid.grid_rows[d.idx - 1].remove();
		// 		}
				
		// 	})
			
		// }
		// }).css({'color':'white','background-color':"#009E60","margin-left": "10px", "margin-right": "10px"});

		frm.fields_dict["purchase_order_approval"].grid.add_custom_button(__('Reject'),
		function () {
			if(frm.doc.purchase_order_approval){
				$.each(frm.doc.purchase_order_approval, function (i, d) {
					if (d.__checked == 1) {
						frm.call('submit_all_doc_after_approval', {
							doctype: "Purchase Order",
							name: d.purchase_order,
							workflow_state: 'Draft'
						}).then(r => {
							frm.get_field("purchase_order_approval").grid.grid_rows[d.idx - 1].remove();
						})
					}
				})
			}			
		}).addClass('btn-danger')


		frm.fields_dict["purchase_order_approval"].grid.add_custom_button(__('Approve'),
		function () {
			if(frm.doc.purchase_order_approval){
				$.each(frm.doc.purchase_order_approval, function (i, d) {
					if (d.__checked == 1) {
						console.log(d)
						frm.call('submit_doc', {
							doctype: "Purchase Order",
							name: d.purchase_order,
							workflow_state: 'Approved'
						}).then(r => {
							frm.get_field("purchase_order_approval").grid.grid_rows[d.idx - 1].remove();
						})
					}
				})
			}
		}).css({'color':'white','background-color':"#009E60","margin-left": "10px", "margin-right": "10px"});
	}

	//COO
	if (frappe.user.has_role(['COO'])){
		frm.fields_dict["travel_request_approval"].grid.add_custom_button(__('Reject'),
		function () {
			if(frm.doc.travel_request_approval){
				$.each(frm.doc.travel_request_approval, function (i, d) {
					if (d.__checked == 1) {
						frm.call('submit_all_doc_after_approval', {
							doctype: "Travel Request",
							name: d.application_no,
							workflow_state: 'Rejected'
						}).then(r => {
							frm.get_field("travel_request_approval").grid.grid_rows[d.idx - 1].remove();
						})
					}
				})
			}
			
		}).addClass('btn-danger')
		frm.fields_dict["travel_request_approval"].grid.add_custom_button(__('Approve'),function () {
			if(frm.doc.travel_request_approval){
			$.each(frm.doc.travel_request_approval, function (i, d) {
				if (d.__checked == 1) {
					frm.call('submit_doc', {
						doctype: "Travel Request",
						name: d.application_no,
						workflow_state: 'Approved'
					}).then(r => {
						frm.get_field("travel_request_approval").grid.grid_rows[d.idx - 1].remove();
					})
				}				
			})
		}
		}).css({'color':'white','background-color':"#009E60","margin-left": "10px", "margin-right": "10px"});
		

		frm.fields_dict["quotation_approval"].grid.add_custom_button(__('Reject'),
		function () {
			if(frm.doc.quotation_approval){
				$.each(frm.doc.quotation_approval, function (i, d) {
					if (d.__checked == 1) {
						frm.call('submit_quote', {
							doctype: "Quotation",
							name: d.quotation,
							work_flow: 'Rejected'
						}).then(r => {
							frm.get_field("quotation_approval").grid.grid_rows[d.idx - 1].remove();
						})
					}
				})
			}
			
		}).addClass('btn-danger')


		frm.fields_dict["quotation_approval"].grid.add_custom_button(__('Approve'),
		function () {
			$.each(frm.doc.quotation_approval, function (i, d) {
				if (d.__checked == 1) {
					frm.call('submit_quote', {
						doctype: "Quotation",
						name: d.quotation,
						work_flow: 'Pending for CFO'
					}).then(r => {
						frm.get_field("quotation_approval").grid.grid_rows[d.idx - 1].remove();
					})
				}
			})
		}).css({'color':'white','background-color':"#009E60","margin-left": "10px", "margin-right": "10px"});


		frm.fields_dict["sales_order_approval"].grid.add_custom_button(__('Reject'),
		function () {
			$.each(frm.doc.sales_order_approval, function (i, d) {
					if (d.__checked == 1) {
					frm.call('submit_all_doc_after_approval', {
						doctype: "Sales Order",
						name: d.sales_order,
						workflow_state: 'Draft'
					}).then(r => {
						frm.get_field("sales_order_approval").grid.grid_rows[d.idx - 1].remove();
					})
				}
			})
		}).addClass('btn-danger')


		frm.fields_dict["sales_order_approval"].grid.add_custom_button(__('Approve'),function () {
			if(frm.doc.sales_order_approval){
			$.each(frm.doc.sales_order_approval, function (i, d) {
				if (d.__checked == 1) {
					frm.call('submit_all_doc_after_approval', {
						doctype: "Sales Order",
						name: d.sales_order,
						workflow_state: 'Pending for CFO'
					}).then(r => {
						frm.get_field("sales_order_approval").grid.grid_rows[d.idx - 1].remove();
					})
				}
				
			})
			
		}
		}).css({'color':'white','background-color':"#009E60","margin-left": "10px", "margin-right": "10px"});

		frm.fields_dict["purchase_order_approval"].grid.add_custom_button(__('Reject'),
		function () {
			if(frm.doc.purchase_order_approval){
				$.each(frm.doc.quotation_approval, function (i, d) {
					if (d.__checked == 1) {
						frm.call('submit_all_doc_after_approval', {
							doctype: "Purchase Order",
							name: d.purchase_order,
							workflow_state: 'Draft'
						}).then(r => {
							frm.get_field("purchase_order_approval").grid.grid_rows[d.idx - 1].remove();
						})
					}				
				})
			}			
		}).addClass('btn-danger')


		frm.fields_dict["purchase_order_approval"].grid.add_custom_button(__('Approve'),
		function () {
			if(frm.doc.purchase_order_approval){
				$.each(frm.doc.purchase_order_approval, function (i, d) {
					if (d.__checked == 1) {
						frm.call('submit_all_doc_after_approval', {
							doctype: "Purchase Order",
							name: d.purchase_order,
							workflow_state: 'Pending for CFO'
						}).then(r => {
							frm.get_field("purchase_order_approval").grid.grid_rows[d.idx - 1].remove();
						})
					}
				})
			}		
		}).css({'color':'white','background-color':"#009E60","margin-left": "10px", "margin-right": "10px"});



	}
	// CFO
	if (frappe.user.has_role(['CFO'])){
		frm.fields_dict["purchase_order_approval"].grid.add_custom_button(__('Reject'),
		function () {
			if(frm.doc.purchase_order_approval){
				$.each(frm.doc.purchase_order_approval, function (i, d) {
					if (d.__checked == 1) {
						frm.call('submit_all_doc_after_approval', {
							doctype: "Purchase Order",
							name: d.purchase_order,
							workflow_state: 'Draft'
						}).then(r => {
							frm.get_field("purchase_order_approval").grid.grid_rows[d.idx - 1].remove();
						})
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
							name: d.purchase_order,
							workflow_state: 'Approved'
						}).then(r => {
							frm.get_field("purchase_order_approval").grid.grid_rows[d.idx - 1].remove();
						})
					}
				})
			}		
		}).css({'color':'white','background-color':"#009E60","margin-left": "10px", "margin-right": "10px"});

		frm.fields_dict["sales_order_approval"].grid.add_custom_button(__('Reject'),
		function () {
			$.each(frm.doc.sales_order_approval, function (i, d) {
				if (d.__checked == 1) {
					if(d.workflow_state == "Pending for CFO"){
						frm.call('submit_all_doc_after_approval', {
							doctype: "Sales Order",
							name: d.sales_order,
							workflow_state: 'Draft'
						}).then(r => {
							frm.get_field("sales_order_approval").grid.grid_rows[d.idx - 1].remove();
						})
					}
				}
			})
		}).addClass('btn-danger')


		frm.fields_dict["sales_order_approval"].grid.add_custom_button(__('Approve'),function () {
		if(frm.doc.sales_order_approval){
			$.each(frm.doc.sales_order_approval, function (i, d) {
				if (d.__checked == 1) {
					if(d.workflow_state == "Pending for CFO"){
						frm.call('submit_doc', {
							doctype: "Sales Order",
							name: d.sales_order,
							workflow_state: 'Approved'
						}).then(r => {
							frm.get_field("sales_order_approval").grid.grid_rows[d.idx - 1].remove();
						})
					}
				}				
			})			
		}
		}).css({'color':'white','background-color':"#009E60","margin-left": "10px", "margin-right": "10px"});


		frm.fields_dict["expense_claim_summary"].grid.add_custom_button(__('Reject'),
		function () {
			if(frm.doc.expense_claim_summary){
				$.each(frm.doc.expense_claim_summary, function (i, d) {
					if (d.__checked == 1) {
						frm.call('submit_all_doc_after_approval', {
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
			if(frm.doc.expense_claim_summary){
				$.each(frm.doc.expense_claim_summary, function (i, d) {
					if (d.__checked == 1) {
						frm.call('submit_all_doc_after_approval', {
							doctype: "Expense Claim",
							name: d.application_no,
							workflow_state: 'Pending for Finance Verification'
						}).then(r => {
							frm.get_field("expense_claim_summary").grid.grid_rows[d.idx - 1].remove();
						})
					}
				})
			}
		}).css({'color':'white','background-color':"#009E60","margin-left": "10px", "margin-right": "10px"});
	}
	//HOD
	if (frappe.user.has_role(['HOD'])){
		frm.fields_dict["sales_order_approval"].grid.add_custom_button(__('Reject'),
		function () {
			$.each(frm.doc.sales_order_approval, function (i, d) {
				if (d.__checked == 1) {
					if(d.workflow_state == "Pending for HOD"){
						frm.call('submit_all_doc_after_approval', {
							doctype: "Sales Order",
							name: d.sales_order,
							workflow_state: 'Draft'
						}).then(r => {
							frm.get_field("sales_order_approval").grid.grid_rows[d.idx - 1].remove();	
						})
					}		
				}				
			})
		}).addClass('btn-danger')


		frm.fields_dict["sales_order_approval"].grid.add_custom_button(__('Approve'),
		function () {
			if(frm.doc.sales_order_approval){
				$.each(frm.doc.sales_order_approval, function (i, d) {
					if (d.__checked == 1) {
						if(d.workflow_state == "Pending for HOD"){
							frm.call('submit_all_doc_after_approval', {
								doctype: "Sales Order",
								name: d.sales_order,
								workflow_state: 'Pending for Accounts'
							}).then(r => {
								frm.get_field("sales_order_approval").grid.grid_rows[d.idx - 1].remove();
							})
						}
					}
				})
			}
		}).css({'color':'white','background-color':"#009E60","margin-left": "10px", "margin-right": "10px"});


		frm.fields_dict["travel_request_approval"].grid.add_custom_button(__('Reject'),
		function () {
			if(frm.doc.travel_request_approval){
				$.each(frm.doc.travel_request_approval, function (i, d) {
					if (d.__checked == 1) {
						frm.call('submit_all_doc_after_approval', {
							doctype: "Travel Request",
							name: d.application_no,
							workflow_state: 'Rejected'
						}).then(r => {
							frm.get_field("travel_request_approval").grid.grid_rows[d.idx - 1].remove();
						})
					}
				})
			}			
		}).addClass('btn-danger')

		frm.fields_dict["travel_request_approval"].grid.add_custom_button(__('Approve'),function () {
			if(frm.doc.travel_request_approval){
			$.each(frm.doc.travel_request_approval, function (i, d) {
				if (d.__checked == 1) {
					if(d.travel_type == "International"){
						frm.call('submit_all_doc_after_approval', {
							doctype: "Travel Request",
							name: d.application_no,
							workflow_state: 'Pending for COO'
						}).then(r => {
							frm.get_field("travel_request_approval").grid.grid_rows[d.idx - 1].remove();
						})
					}
					else{
						frm.call('submit_doc', {
							doctype: "Travel Request",
							name: d.application_no,
							workflow_state: 'Approved'
						}).then(r => {
							frm.get_field("travel_request_approval").grid.grid_rows[d.idx - 1].remove();
						})
					}
					
				}
				
			})
			
			
		}
		}).css({'color':'white','background-color':"#009E60","margin-left": "10px", "margin-right": "10px"});
		


		frm.fields_dict["expense_claim_summary"].grid.add_custom_button(__('Reject'),
		function () {
			if(frm.doc.expense_claim_summary){
				$.each(frm.doc.expense_claim_summary, function (i, d) {
					if (d.__checked == 1) {
						frm.call('submit_all_doc_after_approval', {
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
			if(frm.doc.expense_claim_summary){
				$.each(frm.doc.expense_claim_summary, function (i, d) {
					if (d.__checked == 1) {
						frm.call('submit_all_doc_after_approval', {
							doctype: "Expense Claim",
							name: d.application_no,
							workflow_state: 'Pending for HRM'
						}).then(r => {
							frm.get_field("expense_claim_summary").grid.grid_rows[d.idx - 1].remove();
						})
					}
				})
			}
		}).css({'color':'white','background-color':"#009E60","margin-left": "10px", "margin-right": "10px"});

		
		frm.fields_dict["leave_application_approval"].grid.add_custom_button(__('Reject'),
		function () {
			if(frm.doc.leave_application_approval){
				$.each(frm.doc.leave_application_approval, function (i, d) {
					if (d.__checked == 1) {
						frm.call('submit_all_doc_after_approval', {
							doctype: "Leave Application",
							name:  d.application_no,
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
			if(frm.doc.leave_application_approval){
				$.each(frm.doc.leave_application_approval, function (i, d) {
					if (d.__checked == 1) {
						frm.call('submit_doc', {
							doctype: "Leave Application",
							name: d.application_no,
							workflow_state:'Pending HRD Mark Attendance'
						}).then(r => {
							frm.get_field("leave_application_approval").grid.grid_rows[d.idx - 1].remove();
						})
					}
				})
			}
		}).css({'color':'white','background-color':"#009E60","margin-left": "10px", "margin-right": "10px"});
	}

	
	
	},

	onload(frm){
		frappe.run_serially([
			() => frm.clear_table('quotation_approval'),
			() => frm.call('get_quote_Pending_Operation_Director').then(r=>{
				if (frappe.session.user){
					if (frappe.user.has_role(['Operation Director'])){
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
					}					
				}
			}),
			
			() => frm.call('get_quote').then(r=>{
				if (frappe.session.user){
					if (frappe.user.has_role(['COO'])){
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
					}			
				}
			}),

			() => frm.call('get_quote_hod').then(r=>{
				if (frappe.session.user){
					if (frappe.user.has_role(['HOD Approver'])){
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
					}					
				}
			}),

			() => frm.call('get_sales_order_hod').then(r=>{
				if (frappe.session.user){
					if (frappe.user.has_role(['HOD Approver'])){
						if (r.message) {
							$.each(r.message, function (i, d) {
								frm.add_child('sales_order_approval', {
									'sales_order':d.name,
									'customer':d.customer,
									'date':d.transaction_date,
									'workflow_state':d.workflow_state
								})
								frm.refresh_field('sales_order_approval')
							})
						}
					}
				}
			})	,

			() => frm.call('get_sales_order_pod').then(r=>{
				if (frappe.session.user){
					if (frappe.user.has_role(['Operation Director'])){
						if (r.message) {
							$.each(r.message, function (i, d) {
								frm.add_child('sales_order_approval', {
									'sales_order':d.name,
									'customer':d.customer,
									'date':d.transaction_date,
									'workflow_state':d.workflow_state
								})
								frm.refresh_field('sales_order_approval')
							})
						}
					}
				}
			})	,

			() => frm.call('get_sales_order_cfo').then(r=>{
				
				if (frappe.session.user){
					if (frappe.user.has_role(['CFO'])){
						if (r.message) {
							$.each(r.message, function (i, d) {
								frm.add_child('sales_order_approval', {
									'sales_order':d.name,
									'customer':d.customer,
									'date':d.transaction_date,
									'workflow_state':d.workflow_state
								})
								frm.refresh_field('sales_order_approval')
							})
						}
					}
				}		
			})	,

			() => frm.call('get_po').then(r=>{
				
				if (frappe.session.user){
					if (frappe.user.has_role(['COO'])){
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
					}
				}		
			})	,

			() => frm.call('get_sales_order').then(r=>{
				if (frappe.session.user){
					if (frappe.user.has_role(['COO'])){
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
					}
				}
			})	,


			() => frm.call('get_po_cfo').then(r=>{
				if (frappe.session.user){
					if (frappe.user.has_role(['CFO'])){
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
					}
				}
			}),

			() => frm.call('get_po_pod').then(r=>{
				if (frappe.session.user){
					if (frappe.user.has_role(['Operation Director'])){
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
					}
				}
			}),

			() => frm.call('get_expence_claim').then(r=>{
				if (frappe.session.user){
					if (frappe.user.has_role(['HOD'])){
						if (r.message) {
							$.each(r.message, function (i, d) {
								frm.add_child('expense_claim_summary', {
									"application_no":d.name,
									'from_employee':d.employee,
									'employee_name':d.employee_name,
									'expense_approver':d.expense_approver,
									'total_amount':d.total_claimed_amount
									
								})
								frm.refresh_field('expense_claim_summary')
							})
						}
					}
				}
			}),

			() => frm.call('get_expence_claim_1').then(r=>{
				if (frappe.session.user){
					if (frappe.user.has_role(['CFO'])){
						if (r.message) {
							$.each(r.message, function (i, d) {
								frm.add_child('expense_claim_summary', {
									"application_no":d.name,
									'from_employee':d.employee,
									'employee_name':d.employee_name,
									'expense_approver':d.expense_approver,
									'total_amount':d.total_claimed_amount
									
								})
								frm.refresh_field('expense_claim_summary')
							})
						}
					}
				}
			}),

			() => frm.call('get_leave_app').then(r=>{
				if (frappe.session.user){
					if (frappe.user.has_role(['HOD'])){
						if (r.message) {
							$.each(r.message, function (i, d) {
								frm.add_child('leave_application_approval', {
									"application_no":d.name,
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
					}
				}
			}),

			() => frm.call('get_travel_req').then(r=>{
				if (frappe.session.user){
					if (frappe.user.has_role(['HOD'])){
						if (r.message) {
							$.each(r.message, function (i, d) {
								frm.add_child('travel_request_approval', {
									"application_no":d.name,
									'for_employee':d.employee,
									'employee_name':d.employee_name,
									'travel_type':d.travel_type,
									'from_date':d.date							
								})
								frm.refresh_field('travel_request_approval')
							})
						}
					}
				}
			}),

			() => frm.call('get_travel_req_coo').then(r=>{
				if (frappe.session.user){
					if (frappe.user.has_role(['COO'])){
						if (r.message) {
							$.each(r.message, function (i, d) {
								frm.add_child('travel_request_approval', {
									"application_no":d.name,
									'for_employee':d.employee,
									'employee_name':d.employee_name,
									'travel_type':d.travel_type,
									'from_date':d.date							
								})
								frm.refresh_field('travel_request_approval')
							})
						}
					}
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

frappe.ui.form.on("Quotation Approval", {
    quotation_approval: function(frm, cdt, cdn) {
        var child = locals[cdt][cdn];
        frm.set_df_property("child_table_fieldname", "read_only", 1, cdn);
    }
});

