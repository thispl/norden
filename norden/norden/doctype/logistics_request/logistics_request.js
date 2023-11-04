// Copyright (c) 2021, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on('Logistics Request', {
	download(frm) {
		let selected_files = []
		let selected_docs = frm.fields_dict.support_documents.grid.get_selected_children();
			frm.call({
				method: "get_supporting_docs",
				args: { "selected_docs": selected_docs },
			}).then((r) => {
				open_url_post("/api/method/frappe.core.api.file.zip_files", {
					files: JSON.stringify(r.message),
				});
			});
	},
	refresh: function (frm) {
		
		frappe.breadcrumbs.add("Buying", "Logistics Request");
		if (frm.doc.workflow_state == "Create Purchase Receipt") {
			frm.add_custom_button(__('Purchase Receipt'), function () {
				frappe.call({
					method: 'norden.custom.create_pr',
					args: {
						'company': frm.doc.company,
						'supplier': frm.doc.supplier,
						'product_description': frm.doc.product_description,
						'logistic': frm.doc.name,
						'total': frm.doc.total
					},
					callback(r) {
						if (r.message) {
							// console.log(r.message)
							frappe.set_route("Form", "Purchase Receipt", r.message)
						}
					}
				})

				// var pr = frappe.model.make_new_doc_and_get_name('Purchase Receipt');
				// pr = locals['Purchase Receipt'][pr];
				// // pr.naming_series = 'MAT-PRE-.YYYY.-'
				// pr.supplier = frm.doc.supplier
				// pr.company = frm.doc.company
				// pr.posting_date = frappe.datetime.now_date();
				// pr.transaction_date = ''
				// $.each(frm.doc.product_description,function(i,d){
				// 	var row = frappe.model.add_child(cur_frm.doc, "Purchase Receipt Item", "items");
				// 		row.item_code = d.item_code
				// 		row.item_name = d.item_name
				// 		row.schedule_date = d.schedule_date
				// 		row.qty = d.qty
				// 		row.uom = d.uom
				// 		row.stock_uom = d.stock_uom
				// })
				// pr.items = frm.doc.product_description
				// pr.landed_taxes = frm.doc.taxes
				// pr.logistics = frm.doc.name

				// frappe.set_route("Form", "Purchase Receipt",pr.name)
			})
		}

		frm.set_query("purchase_order", function () {
			return {
				filters: {
					"supplier": frm.doc.ffw
				}
			}
		})
	},

	setup: function (frm) {
		// 	if(frm.doc.add_sub){
		frm.set_query("ffw_name", "ffw_quotation", function (doc, cdt, cdn) {
			let d = locals[cdt][cdn];
			return {
				filters: [
					['Supplier', 'ffw', '=', 1]
				]
			};
		});

		frm.set_query("warehouse", function () {
			return {
				filters: {
					"company": frm.doc.company
				}
			}
		})
	},



	po_so(frm) {
		frm.set_value('order_no', '')
	},
	logistic_type(frm) {
		if (frm.doc.logistic_type == 'Export') {
			frm.set_value('po_so', 'Sales Order')
		}
		else if (frm.doc.logistic_type == 'Import') {
			frm.set_value('po_so', 'Purchase Order')
		}
	},
	validate(frm) {
		frm.refresh()
		// if (frm.doc.grand_total) {
		// 	frm.set_value('custom_duty', frm.doc.grand_total * 0.45)
		// }
		frm.call('compare_po_items').then(r => {
			if (r.message) {
				frappe.msgprint(r.message)
				frappe.validated = false
			}
		})
	},
	price_list_currency(frm){
		frm.trigger("currency")
	},
	currency(frm){
		frappe.call({
			method:"norden.custom.return_conversion",
			args:{
				"currency":frm.doc.currency,
				"price_list_currency":frm.doc.price_list_currency
			},
			callback(r){
				if(r){
					frm.set_value('conv_rate',r.message)
				}
			}
		})
		$.each(frm.doc.ffw_quotation,function(i,j){
			j.percentage_on_purchase_value = (j.total / (frm.doc.grand_total * frm.doc.conv_rate)) * 100
			console.log(j.percentage_on_purchase_value)
		})
		frm.refresh_field("ffw_quotation")
	},
	onload: function (frm) {
		// var rows = frm.fields_dict.support_documents.grid.data
		// console.log(rows)
		// $.each(rows,function(i,d){
		// 	console.log(d.data)
		// })

		// if (!frm.doc.__islocal){
		// 	if(frm.doc.company == "Norden Communication UK Limited"){
		// 		frm.set_df_property('custom_duty', 'hidden', 1);
		// 	}
		// }
		// if(frm.doc.grand_total){
		// 	frm.call('currency_conversion').then(r=>{
		// 		if (r.message) {
		// 			frm.set_value("custom_duty",r.message)
		// 		}
		// 	})	
		// }

		// if(frm.doc.po_so == "Sales Order"){
		// 	frm.set_df_property('section_break_12', 'hidden', 1);
		// }


		// if(frm.doc.po_so == "Purchase Order"){
		// 	frm.set_df_property('section_break_19', 'hidden', 1);
		// }

		if (frm.doc.workflow_state == "Draft") {
			frm.set_df_property('section_break_28', 'hidden', 1);
			frm.set_df_property('documents_status_section', 'hidden', 1);
			frm.set_df_property('applicable_charges_section', 'hidden', 1);
			frm.set_df_property('section_break_49', 'hidden', 1);
			frm.set_df_property('section_break_62', 'hidden', 1);
			frm.set_df_property('support_doc', 'hidden', 1);

		}


		// if(frm.doc.workflow_state != "Delivery"){
		// 	frm.set_df_property('delivery_section', 'hidden', 1);
		// }

		// else{
		// 	frm.set_df_property('delivery_section', 'hidden', 0);
		// }

		if (frm.doc.workflow_state == "Draft" || frm.doc.workflow_state == "Logistics OPS" || frm.doc.workflow_state == "Pending for HOD" || frm.doc.workflow_state == "Pending for COO" || frm.doc.workflow_state == "Attach Supporting Document" || frm.doc.workflow_state == "Pending for Confirmation" || frm.doc.workflow_state == "Document Review" || frm.doc.workflow_state == "Payment & Customs Clearance" || frm.doc.workflow_state == "Delivery" || frm.doc.workflow_state == "Waiting for ID Submission") {
			frm.set_df_property('section_break_74', 'hidden', 1);
			// frm.set_df_property('section_break_59', 'hidden', 1);
			// frm.set_df_property('logistic_type', 'read_only', 1);
			// frm.set_df_property('section_break_14', 'read_only', 1);

		}

		if (frm.doc.workflow_state == "Draft" || frm.doc.workflow_state == "Logistics OPS" || frm.doc.workflow_state == "Pending for HOD" || frm.doc.workflow_state == "Pending for COO" || frm.doc.workflow_state == "Attach Supporting Document" || frm.doc.workflow_state == "Pending for Confirmation" || frm.doc.workflow_state == "Document Review") {
			frm.set_df_property('section_break_59', 'hidden', 1);


		}

		if (frm.doc.workflow_state == "Logistics OPS" || frm.doc.workflow_state == "Pending for HOD" || frm.doc.workflow_state == "Pending for COO" || frm.doc.workflow_state == "Attach Supporting Document" || frm.doc.workflow_state == "Pending for Confirmation" || frm.doc.workflow_state == "E-Way Bill" || frm.doc.workflow_state == "Create Purchase Receipt" || frm.doc.workflow_state == "Document Review" || frm.doc.workflow_state == "Payment & Customs Clearance" || frm.doc.workflow_state == "Delivery" || frm.doc.workflow_state == "Create Purchase Receipt") {
			frm.set_df_property('logistic_type', 'read_only', 1);
			frm.set_df_property('po_so', 'read_only', 1);
			frm.set_df_property('order_no', 'read_only', 1);
			frm.set_df_property('file_number', 'read_only', 1);
			frm.set_df_property('company', 'read_only', 1);
			frm.set_df_property('supplier', 'read_only', 1);
			frm.set_df_property('country', 'read_only', 1);
			frm.set_df_property('inventory_destination', 'read_only', 1);
			frm.set_df_property('grand_total', 'read_only', 1);
			frm.set_df_property('project', 'read_only', 1);
			frm.set_df_property('final_doc', 'read_only', 1);
			frm.set_df_property('requester_name', 'read_only', 1);
			frm.set_df_property('custom_duty', 'read_only', 1);
			frm.set_df_property('product_description', 'read_only', 1);

			var df = frappe.meta.get_docfield("Attach Documents", "title", frm.doc.name);
			df.read_only = 1;
			var ss = frappe.meta.get_docfield("Attach Documents", "description", frm.doc.name);
			ss.read_only = 1;
			frm.set_df_property('tentative_production_completion', 'read_only', 1);

		}

		if (frm.doc.workflow_state == "Pending for HOD" || frm.doc.workflow_state == "Pending for COO" || frm.doc.workflow_state == "Attach Supporting Document" || frm.doc.workflow_state == "Pending for Confirmation" || frm.doc.workflow_state == "E-Way Bill" || frm.doc.workflow_state == "Create Purchase Receipt" || frm.doc.workflow_state == "Document Review" || frm.doc.workflow_state == "Payment & Customs Clearance" || frm.doc.workflow_state == "Delivery" || frm.doc.workflow_state == "Create Purchase Receipt") {
			frm.set_df_property('cargo_type', 'read_only', 1);
		}
		if (frm.doc.workflow_state == "Pending for HOD" || frm.doc.workflow_state == "Pending for COO" || frm.doc.workflow_state == "Attach Supporting Document" || frm.doc.workflow_state == "Pending for Confirmation" || frm.doc.workflow_state == "E-Way Bill" || frm.doc.workflow_state == "Create Purchase Receipt" || frm.doc.workflow_state == "Document Review" || frm.doc.workflow_state == "Payment & Customs Clearance" || frm.doc.workflow_state == "Delivery" || frm.doc.workflow_state == "Create Purchase Receipt") {
			frm.set_df_property('courier__awb__bl_number__container', 'read_only', 1);
			frm.set_df_property('dimensions', 'read_only', 1);
			frm.set_df_property('gross_wt', 'read_only', 1);
			frm.set_df_property('net_wt', 'read_only', 1);
			frm.set_df_property('uom', 'read_only', 1);
			frm.set_df_property('box_pallet_count', 'read_only', 1);
		}

		if (frm.doc.workflow_state == "Pending for HOD" || frm.doc.workflow_state == "Pending for COO" || frm.doc.workflow_state == "Attach Supporting Document" || frm.doc.workflow_state == "E-Way Bill" || frm.doc.workflow_state == "Pending for Confirmation" || frm.doc.workflow_state == "Document Review" || frm.doc.workflow_state == "Payment & Customs Clearance" || frm.doc.workflow_state == "Delivery" || frm.doc.workflow_state == "Create Purchase Receipt") {

			frm.set_df_property('norden_inco_terms', 'read_only', 1);
			frm.set_df_property('supplier_inco_terms', 'read_only', 1);
			frm.set_df_property('pol_seaportairport', 'read_only', 1);
			frm.set_df_property('pol_city', 'read_only', 1);
			frm.set_df_property('pol_country', 'read_only', 1);
			frm.set_df_property('pod_seaportairport', 'read_only', 1);
			frm.set_df_property('pod_city', 'read_only', 1);
			frm.set_df_property('pod_country', 'read_only', 1);
			frm.set_df_property('carrier_name', 'read_only', 1);
			frm.set_df_property('eta', 'read_only', 1);
			frm.set_df_property('etd', 'read_only', 1);
			frm.set_df_property('transit_time', 'read_only', 1);
			frm.set_df_property('document_dispatch_list', 'read_only', 1);
			frm.set_df_property('received_by', 'read_only', 1);
			frm.set_df_property('date', 'read_only', 1);
			frm.set_df_property('taxes', 'read_only', 1);
			frm.set_df_property('ffw_quotation', 'read_only', 1);
			frm.set_df_property('recommended_ffw', 'read_only', 1);
			frm.set_df_property('comments', 'read_only', 1);
		}

		if (frm.doc.workflow_state == "Pending for Confirmation" || frm.doc.workflow_state == "Document Review" || frm.doc.workflow_state == "Payment & Customs Clearance" || frm.doc.workflow_state == "Delivery" || frm.doc.workflow_state == "E-Way Bill" || frm.doc.workflow_state == "Create Purchase Receipt" || frm.doc.workflow_state == "Document Review" || frm.doc.workflow_state == "Payment & Customs Clearance" || frm.doc.workflow_state == "Delivery" || frm.doc.workflow_state == "Create Purchase Receipt") {
			var df = frappe.meta.get_docfield("Supporting Document", "document_type", frm.doc.name);
			df.read_only = 1;
		}

		if (frm.doc.workflow_state == "Delivery" || frm.doc.workflow_state == "E-Way Bill" || frm.doc.workflow_state == "Create Purchase Receipt") {
			frm.set_df_property('customs_clearance_status', 'read_only', 1);
			frm.set_df_property('customs_clearance', 'read_only', 1);

		}

		if (frm.doc.workflow_state == "Create Purchase Receipt") {
			frm.set_df_property('e_way_bill', 'read_only', 1);
			frm.set_df_property('e_way_no', 'read_only', 1);

		}

		if (frm.doc.workflow_state != 'Attach Bills') {
			frm.set_df_property('purchase_receipts_section', 'hidden', 1);
			frm.set_df_property('attach_bills_section', 'hidden', 1);
		}

		if (frm.doc.workflow_state == "Draft" || frm.doc.workflow_state == "Logistics OPS" || frm.doc.workflow_state == "Pending for HOD" || frm.doc.workflow_state == "Pending for COO" || frm.doc.workflow_state == "Attach Supporting Document" || frm.doc.workflow_state == "Payment & Customs Clearance" || frm.doc.workflow_state == "Delivery" || frm.doc.workflow_state == "Pending for Confirmation" || frm.doc.workflow_state == "Document Review") {
			if (!frm.doc.vehicle_number) {
				// frm.set_df_property('product_description', 'hidden', 1);
			}
		}


		if (frm.doc.workflow_state == "Draft" || frm.doc.workflow_state == "Logistics OPS" || frm.doc.workflow_state == "Pending for HOD" || frm.doc.workflow_state == "Pending for COO" || frm.doc.workflow_state == "Attach Supporting Document" || frm.doc.workflow_state == "Delivery" || frm.doc.workflow_state == "Pending for Confirmation" || frm.doc.workflow_state == "Waiting for NRIC Submission") {
			if (!frm.doc.vehicle_number) {
				frm.set_df_property('document_for_payment_clearance_section', 'hidden', 1);
			}

		}

		if (frm.doc.workflow_state == "Draft" || frm.doc.workflow_state == "Logistics OPS" || frm.doc.workflow_state == "Pending for HOD" || frm.doc.workflow_state == "Pending for COO" || frm.doc.workflow_state == "Attach Supporting Document") {
			if (!frm.doc.vehicle_number) {
				frm.set_df_property('nric_section', 'hidden', 1);
			}

		}

		if (frm.doc.workflow_state == "Draft" || frm.doc.workflow_state == "Logistics OPS" || frm.doc.workflow_state == "Pending for HOD" || frm.doc.workflow_state == "Pending for COO") {
			frm.set_df_property('support_doc', 'hidden', 1);

		}
		// else{
		// 	frm.set_df_property('support_doc', 'hidden', 0);
		// }

		if (frm.doc.__islocal) {
			if (!frm.doc.document_attached) {
				var data = [{ 'title': 'Draft Invoice' },
				{ 'title': 'Packing List' },
				{ 'title': 'Payment TCC' },
				]
				$.each(data, function (i, v) {
					frm.add_child('document_attached', {
						title: v.title,
					})
					frm.refresh_field('document_attached')
				})

			}
		}

		// if (frm.doc.__islocal) {
		// var documents_list = ['Invoice', 'Packing List', 'COO', 'Airway or Courier Bill', 'Bill of Lading (BL)', 'Check List for Accounts', 'Bill of Entry']
		// $.each(documents_list, function (i, v) {
		// 	frm.add_child('support_documents', {
		// 		document_type: v
		// 	})
		// 	frm.refresh_fields('support_documents')
		// })
		// }
		frm.set_query("ffw", function () {
			return {
				filters: {
					"ffw": 1
				}
			}
		})
		frm.set_query("cha", function () {
			return {
				filters: {
					"cha": 1
				}
			}
		})
		// frm.set_query("pol_seaportairport", function () {
		// 	return {
		// 		filters: {
		// 			"cargo_type": frm.doc.cargo_type
		// 		}
		// 	}
		// })
		// frm.set_query("pod_seaportairport", function () {
		// 	return {
		// 		filters: {
		// 			"cargo_type": frm.doc.cargo_type,
		// 			// "pod'_seaportairport" : 
		// 		}
		// 	}
		// })

		if (frm.doc.__islocal) {
			if (frm.doc.order_no) {
				frappe.call({
					method: 'frappe.client.get',
					args: {
						'doctype': frm.doc.po_so,
						'name': frm.doc.order_no,
					},
					callback(r) {
						frm.set_value('product_description', r.message.items)
						frm.refresh_fields('product_description')
						frm.set_value('grand_total', r.message.grand_total)
						frm.set_value('custom_duty', r.message.grand_total * 0.45)
						frm.set_value('supplier', r.message.supplier)
						frm.set_value('company', r.message.company)
						frm.set_value('country', r.message.country)
						// frm.set_value('file_number', r.message.file_number)
						frm.set_value('ffw', r.message.supplier)
						frm.set_value('consignment_type', r.message.consignment_type)
						frm.set_value('project', r.message.project_name)
						frm.set_value('cargo_type', r.message.mode_of_dispatch)
						// frm.set_value('cargo_type', r.message.mode_of_dispatch)
						frm.set_value('requester_name', r.message.requester_name)
					}
				})
			}
		}
	},
	eta(frm) {
		frm.trigger('transit_time')
	},
	etd(frm) {
		frm.trigger('transit_time')
	},
	transit_time(frm) {
		if (frm.doc.eta && frm.doc.etd) {
			var transit_time = frappe.datetime.get_diff(frm.doc.eta, frm.doc.etd)
			frm.set_value('transit_time', transit_time)
		}
	},
	customs_clearance_status(frm) {
		if (frm.doc.customs_clearance_status == 'Customs Clearance Completed') {
			frm.set_value('customs_clearance', frappe.datetime.nowdate())
		}
	},
	after_workflow_action(frm) {
		if (frm.doc.workflow_state == 'Pending for Logistics') {
			frm.call('pending_for_logistics')
		}
		else if (frm.doc.workflow_state == 'Pending for Accounts') {
			frm.call('pending_for_accounts')
		}
	},
});
frappe.ui.form.on('Purchase Order Item', {
	qty(frm, cdt, cdn) {
		var child = locals[cdt][cdn]
		if (child.qty && child.rate) {
			child.amount = child.qty * child.rate
		}
		var total = 0
		$.each(frm.doc.product_description, function (i, v) {
			total = total + v.amount
		})
		frm.refresh_fields('product_description')
		frm.set_value('grand_total', total)
		frm.set_value('freight_rate', total)
		frm.set_value('custom_duty', total * 0.45)
	},
	product_description_remove(frm) {
		var total = 0
		$.each(frm.doc.product_description, function (i, v) {
			if (v.amount) {
				total = total + v.amount
			}
		})
		frm.set_value('grand_total', total)
		frm.set_value('freight_rate', total)
		frm.set_value('custom_duty', total * 0.45)
	},
	payment_challan(frm) {
		if (frm.doc.payment_challan) {
			frm.set_value('customs_clearance_status', 'Payment Done')
		}
	}
})

frappe.ui.form.on('Supporting Document', {
	attach(frm, cdt, cdn) {
		var child = locals[cdt][cdn]
		if (child.attach) {
			if (child.document_type == 'Bill of Entry') {
				if (frm.doc.customs_clearance_status == 'Pending') {
					// console.log(frm.doc.customs_clearance_status)
					frm.set_value('customs_clearance_status', 'Shipment Ready for Payment')
				}
			}
		}
	}
})

frappe.ui.form.on('FFW Quotation', {
	quoted_value(frm, cdt, cdn) {
		var child = locals[cdt][cdn]

		// console.log(frm.doc.grand_total)
		// value = child.quoted_value * 100
		child.percentage_on_purchase_value = (child.quoted_value / (frm.doc.grand_total * frm.doc.conv_rate)) * 100
		child.total = child.quoted_value

		frm.refresh_fields('ffw_quotation')
	},

	clearance_amount(frm, cdt, cdn) {
		var child = locals[cdt][cdn]
		child.total = child.quoted_value + child.clearance_amount
		child.percentage_on_purchase_value = (child.total / (frm.doc.grand_total * frm.doc.conv_rate)) * 100


		frm.refresh_fields('ffw_quotation')
	},



})