// Copyright (c) 2023, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on('Allocation Details', {
	item_code: function(frm) {
		frm.call('get_data').then(r=>{
			if (r.message) {
				frm.fields_dict.html.$wrapper.empty().append(r.message)
			}
		})
		if(frm.doc.item_code){
			frm.call('get_item_summary').then(r=>{
				if (r.message) {
					const data = r.message;
					let html = `
						<table class="table table-bordered table-sm">
								<tr style=background-color:#6f6f6f;padding:1px;color:white;text-align:center>
									<td>Item Code</td>
									<td>Item Name</td>
									<td>Unit</td>
									<td>Total Qty</td>
									<td>Reserved Qty</td>
									<td>Free Qty</td>
									<td>Non-sale Qty</td>
									<td>Demo Qty</td>
									<td>PO Qty</td>
									<td>SO Pending Qty</td>
								</tr>
							<tbody>`;

					data.forEach(row => {
						html += `<tr>
							<td>${row.item}</td>
							<td>${row.item_name}</td>
							<td>${row.unit}</td>
							<td style=text-align:right>${row.total_qty}</td>
							<td style=text-align:right>${row.reserved_qty}</td>
							<td style=text-align:right>${row.free_qty}</td>
							<td style=text-align:right>${row.non_sale_qty}</td>
							<td style=text-align:right>${row.demo_qty}</td>
							<td style=text-align:right>${row.po_qty}</td>
							<td style=text-align:right>${row.so_qty}</td>
						</tr>`;
					});

					html += `</tbody></table>`;

					frm.fields_dict.item_html.$wrapper.empty().append(html)
				}
			})
	}
	},
	company(frm){
		frm.call('get_item_summary').then(r=>{
			if (r.message) {
				const data = r.message;
				let html = `
					<table class="table table-bordered table-sm">
							<tr style=background-color:#6f6f6f;padding:1px;color:white;text-align:center>
								<td>Item Code</td>
								<td>Item Name</td>
								<td>Unit</td>
								<td>Total Qty</td>
								<td>Reserved Qty</td>
								<td>Free Qty</td>
								<td>Non-sale Qty</td>
								<td>Demo Qty</td>
								<td>PO Qty</td>
								<td>SO Pending Qty</td>
							</tr>
						<tbody>`;

				data.forEach(row => {
					html += `<tr>
						<td>${row.item}</td>
						<td>${row.item_name}</td>
						<td>${row.unit}</td>
						<td style=text-align:right>${row.total_qty}</td>
						<td style=text-align:right>${row.reserved_qty}</td>
						<td style=text-align:right>${row.free_qty}</td>
						<td style=text-align:right>${row.non_sale_qty}</td>
						<td style=text-align:right>${row.demo_qty}</td>
						<td style=text-align:right>${row.po_qty}</td>
						<td style=text-align:right>${row.so_qty}</td>
					</tr>`;
				});

				html += `</tbody></table>`;

				frm.fields_dict.item_html.$wrapper.empty().append(html)
			}
		})
	},
	like(frm){
		if(frm.doc.like){
			let html=""
			frm.call('get_item_summary').then(r=>{
				if (r.message) {
					const data = r.message;
					html += `
						<table class="table table-bordered table-sm">
								<tr style=background-color:#6f6f6f;padding:1px;color:white;text-align:center>
									<td>Item Code</td>
									<td>Item Name</td>
									<td>Unit</td>
									<td>Total Qty</td>
									<td>Reserved Qty</td>
									<td>Free Qty</td>
									<td>Non-sale Qty</td>
									<td>Demo Qty</td>
									<td>PO Qty</td>
									<td>SO Pending Qty</td>
								</tr>
							<tbody>`;

					data.forEach(row => {
						html += `<tr>
							<td>${row.item}</td>
							<td>${row.item_name}</td>
							<td>${row.unit}</td>
							<td style=text-align:right>${row.total_qty}</td>
							<td style=text-align:right>${row.reserved_qty}</td>
							<td style=text-align:right>${row.free_qty}</td>
							<td style=text-align:right>${row.non_sale_qty}</td>
							<td style=text-align:right>${row.demo_qty}</td>
							<td style=text-align:right>${row.po_qty}</td>
							<td style=text-align:right>${row.so_qty}</td>
						</tr>`;
					});

					html += `</tbody></table>`;

					frm.fields_dict.item_html.$wrapper.empty().append(html)
				}
			})
	}
	},
	onload(frm){
		frappe.db.get_value('Employee', {"user_id":frappe.session.user}, 'company').then(r => {
			if (r.message) {
				frm.set_value('company', r.message.company);
			}
			else{
				frm.set_value('company', "");
			}
		});
	}
});
