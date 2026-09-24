frappe.pages['sales-dashboard'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Sales Dashboard',
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

    let dashboard_html = `<div id="so_dashboard"></div><hr><div id="invoice_dashboard"></div>`;
    $content.append(dashboard_html);

    function load_dashboard(from_date, to_date) {
        $("#so_dashboard").empty();
        $("#invoice_dashboard").empty();

        frappe.call({
            method: "norden.norden.page.sales_dashboard.sales_dashboard.get_so_dashboard_data",
            args: { from_date, to_date },
            callback: function(r) { render_dashboard_so($("#so_dashboard"), r.message); }
        });

        frappe.call({
            method: "norden.norden.page.sales_dashboard.sales_dashboard.get_sales_dashboard_data",
            args: { from_date, to_date },
            callback: function(r) { render_dashboard($("#invoice_dashboard"), r.message); }
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
};

let header_style = "background-color:#4ba7cf; color:white; text-align:center; font-weight:bold;";
let total_style = "background-color:#d4f0f7; font-weight:bold;";

function render_dashboard($content, data) {
    $content.append(`
        <div class="row mb-4">
            <div class="col-sm-6">${render_date_wise("Total Invoiced (Date wise)", data.invoices.by_date)}</div>
            <div class="col-sm-6">${render_date_sales_wise("Total Invoiced (Date & Sales Person wise)", data.invoices.sales_person)}</div>
        </div>
        <div class="row mb-4">
            <div class="col-sm-6">${render_date_wise("Total Cancelled Invoice (Date wise)", data.invoices.cancelled_by_date)}</div>
            <div class="col-sm-6">${render_date_sales_wise("Total Cancelled Invoice (Date & Sales Person wise)", data.invoices.cancelled_by_sp)}</div>
        </div>
    `);
}

function render_dashboard_so($content, data) {
    $content.append(`
        <div class="row mb-4">
            <div class="col-sm-6">${render_date_wise("Incoming SO (Date wise)", data.orders.by_date)}</div>
            <div class="col-sm-6">${render_date_sales_wise("Incoming SO (Date & Sales Person wise)", data.orders.sales_person)}</div>
        </div>
        <div class="row mb-4">
            <div class="col-sm-6">${render_date_wise("Total Cancelled SO (Date wise)", data.orders.cancelled_by_date)}</div>
            <div class="col-sm-6">${render_date_sales_wise("Total Cancelled SO (Date & Sales Person wise)", data.orders.cancelled_by_sp)}</div>
        </div>
    `);
}

function render_date_wise(title, rows) {
    let html = `
        <div class="dashboard-table p-3 shadow-sm rounded bg-white" style="max-height:400px; overflow:auto;background-color:#d0dbe2;">
            <h4 class="text-center mb-3">${title}</h4>
            <table class="table table-bordered table-striped" style="background-color:#d0dbe2;">
                <thead>
                    <tr style="${header_style}">
                        <th>Date</th><th>Company</th><th>No Of Records</th><th>Total Value</th>
                    </tr>
                </thead>
                <tbody>
    `;
    if (rows.length > 0) {
        rows.forEach(row => {
            html += `<tr>
                        <td class="text-center">${row.date}</td>
                        <td>${row.company}</td>
                        <td class="text-center">${row.count}</td>
                        <td class="text-right">${format_currency(row.value, row.currency)}</td>
                     </tr>`;
        });
        html += `<tr style="${total_style}">
                    <td colspan="2" class="text-right">Grand Total</td>
                    <td class="text-center">${rows.reduce((sum,row)=>sum+row.count,0)}</td>
                    <td class="text-right">${format_currency(rows.reduce((sum,row)=>sum+row.value,0), rows[0].currency)}</td>
                 </tr>`;
    } else {
        html += `<tr><td colspan="4" class="text-center">No data</td></tr>`;
    }
    html += `</tbody></table></div>`;
    return html;
}

function render_date_sales_wise(title, rows) {
    let html = `
        <div class="dashboard-table p-3 shadow-sm rounded bg-white" style="max-height:400px; overflow:auto;background-color:#d0dbe2;">
            <h4 class="text-center mb-3">${title}</h4>
            <table class="table table-bordered table-striped" style="background-color:#d0dbe2;">
                <thead>
                    <tr style="${header_style}">
                        <th>Date</th><th>Sales Person</th><th>Company</th><th>No Of Records</th><th>Total Value</th>
                    </tr>
                </thead>
                <tbody>
    `;
    if (rows.length > 0) {
        rows.forEach(row => {
            html += `<tr>
                        <td class="text-center">${row.date}</td>
                        <td>${row.sales_person}</td>
                        <td>${row.company}</td>
                        <td class="text-center">${row.count}</td>
                        <td class="text-right">${format_currency(row.value, row.currency)}</td>
                     </tr>`;
        });
        html += `<tr style="${total_style}">
                    <td colspan="3" class="text-right">Grand Total</td>
                    <td class="text-center">${rows.reduce((sum,row)=>sum+row.count,0)}</td>
                    <td class="text-right">${format_currency(rows.reduce((sum,row)=>sum+row.value,0), rows[0].currency)}</td>
                 </tr>`;
    } else {
        html += `<tr><td colspan="5" class="text-center">No data</td></tr>`;
    }
    html += `</tbody></table></div>`;
    return html;
}
