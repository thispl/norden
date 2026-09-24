frappe.pages['sales-person-wise-summary'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Sales Person Wise Summary',
		single_column: true
	});



	let $content = $(wrapper).find('.layout-main-section');
    $content.empty();

    let filter_html = `
        <div class="row mb-3">
            <div class="col-sm-3"><input type="date" id="from_date" class="form-control"></div>
            <div class="col-sm-3"><input type="date" id="to_date" class="form-control"></div>
            <div class="col-sm-2"><button id="filter_btn" class="btn btn-primary">Filter</button></div>
        </div>
    `;
    $content.append(filter_html);


	// let dashboard_tables = `<div style="display:flex; justify-content:space-around; align-items:center; padding-top:10px; ">

	// <div id="so_tab"></div> <div id="si_tab"></div> 
	
	// </div>`


	let dashboard_tables = `
    <div class="row mt-3">
        <div class="col-md-6" id="so_tab"></div>
        <div class="col-md-6" id="si_tab"></div>
    </div>
`;


	



	$content.append(dashboard_tables);


	 function load_dashboard(from_date, to_date) {
        $("#so_tab").empty();
        $("#si_tab").empty();

        frappe.call({
            method: "norden.norden.page.sales_person_wise_summary.sales_person_wise_summary.so_details",
            args: { from_date, to_date },
            callback: function(r) { render_so_tab("SO (Sales Person Wise)", $("#so_tab"), r.message, from_date, to_date); }
        });

        frappe.call({
            method: "norden.norden.page.sales_person_wise_summary.sales_person_wise_summary.si_details",
            args: { from_date, to_date },
            callback: function(r) { render_si_tab("SI (Sales Person Wise)", $("#si_tab"), r.message, from_date, to_date); }
        });
    }




	 $(document).on("click", "#filter_btn", function() {
        let from_date = $("#from_date").val();
        let to_date = $("#to_date").val();
        if (!from_date || !to_date) { frappe.msgprint("Please select both From Date and To Date"); return; }
        load_dashboard(from_date, to_date);
    });

    let today = frappe.datetime.get_today();
    $("#from_date").val(today);
    $("#to_date").val(today);
    load_dashboard(today, today);

	function format_dd_mm_yyyy(date_str) {
    let d = frappe.datetime.str_to_obj(date_str);
    let day = ("0" + d.getDate()).slice(-2);
    let month = ("0" + (d.getMonth() + 1)).slice(-2);
    let year = d.getFullYear();
    return `${day}.${month}.${year}`;
}



	function render_so_tab(title, $content, data, from_date, to_date){



		let html = `
			<div class="dashboard-table p-3 shadow-sm rounded bg-white" style="max-height:400px; overflow:auto;background-color:#d0dbe2;">
				<h4 class="text-center mb-3">${title}</h4>
				<table class="table table-bordered table-striped" style="background-color:#d0dbe2; border:1px solid black;">
					<thead style="border:1px solid black;">
						<tr style="background-color:#e8b7ba; text-align:center; font-weight:bold; border:1px solid black; ">
							<th colspan="2" style="border:1px solid black;">SO'S ${format_dd_mm_yyyy(from_date)}-${format_dd_mm_yyyy(to_date)}</th>
						</tr>
						<tr style="background-color:#b1a1c9; text-align:center; font-weight:bold; border:1px solid black;">
							<th style="border:1px solid black;">Sales Person</th><th style="border:1px solid black;">Total SO Value in AED</th>
						</tr>
					</thead>
					<tbody>
		`;
		let tot=0;
		if (data.length > 0) {
			data.forEach(row => {
				html += `<tr style="border:1px solid black;">
							<td style="text-align:left; background-color:white; border:1px solid black;">${row.sales_person_user}</td>
							<td style="text-align:right; background-color:white; border:1px solid black;">${parseFloat(row.value || 0).toFixed(2)}</td>

						</tr>`;
				tot +=row.value	

			});
			html += `<tr style="background-color:#b1a1c9; font-weight:bold; border:1px solid black;">
						<td  style="text-align:center; border:1px solid black;">Grand Total</td>
						<td  style=" text-align:right; border:1px solid black; ">${parseFloat(tot || 0).toFixed(2)}</td>
					</tr>`;
		} else {
			html += `<tr><td colspan="2" style="text-align:center;">No data</td></tr>`;
		}
		html += `</tbody></table></div>`;
		
		$content.append(html)
}



	
	function render_si_tab(title, $content, data, from_date, to_date){

			let html = `
			<div class="dashboard-table p-3 shadow-sm rounded bg-white" style="max-height:400px; overflow:auto;background-color:#d0dbe2; ">
				<h4 class="text-center mb-3" >${title}</h4>
				<table class="table table-bordered table-striped" style="background-color:#d0dbe2; border:1px solid black;">
					<thead style="border:1px solid black;">
						<tr style="background-color:#e8b7ba; text-align:center; font-weight:bold; border:1px solid black; ">
							<th colspan="2" style="border:1px solid black;">SI'S ${format_dd_mm_yyyy(from_date)}-${format_dd_mm_yyyy(to_date)}</th>
						</tr>
						<tr style="background-color:#b1a1c9; text-align:center; font-weight:bold; border:1px solid black;">
							<th style="border:1px solid black;">Sales Person</th><th style="border:1px solid black;">Total SI Value in AED</th>
						</tr>
					</thead>
					<tbody>
		`;

		let tot=0;
		if (data.length > 0) {
			data.forEach(row => {
				html += `<tr>
							<td style="text-align:left; background-color:white; border:1px solid black; ">${row.sales_person_user}</td>
							<td style="text-align:right; background-color:white; border:1px solid black; ">${parseFloat(row.value || 0).toFixed(2)}</td>
						</tr>`;
				tot +=row.value			
			});
			html += `<tr style="background-color:#b1a1c9; font-weight:bold; border:1px solid black;">
						<td  style="text-align:center; border:1px solid black;">Grand Total</td>
						<td  style="border:1px solid black; text-align:right;">${parseFloat(tot || 0).toFixed(2)}</td>
					</tr>`;
		} else {
			html += `<tr><td colspan="2" style="text-align:center;">No data</td></tr>`;
		}
		html += `</tbody></table></div>`;
		
		$content.append(html)
	}





}