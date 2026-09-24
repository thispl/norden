frappe.pages["warehouse-dashboard"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: "Total Inventory",
    single_column: true,
  });

  page.add_inner_button(__("Refresh"), refresh);

  // ── Container ──────────────────────────────────────────────────────────────
  const $body = $(wrapper).find(".page-content");
  $body.css({ padding: "16px 20px" });

  // ── Date subtitle ──────────────────────────────────────────────────────────
  if (!$body.find(".inv-date-subtitle").length) {
    const today = frappe.datetime.str_to_user(frappe.datetime.get_today());
    $('<div class="inv-date-subtitle"></div>')
      .text(today)
      .insertBefore($body.find(".page-content > *").first())
      .css({
        fontSize: "12px",
        color: "#888",
        marginBottom: "12px",
        marginTop: "-8px",
      });
  }

  const $container = $('<div id="inv-table-container"></div>').appendTo($body);
  const $kpi_container = $('<div id="wh-kpi-container"></div>').appendTo($body);
  const $om_container = $('<div id="wh-om-container"></div>').appendTo($body);

  // ── NEW section containers ─────────────────────────────────────────────────
  const $inbound_container = $('<div id="wh-inbound-container"></div>').appendTo($body);
  const $mrb_container = $('<div id="wh-mrb-container"></div>').appendTo($body);
  const $dead_container = $('<div id="wh-dead-container"></div>').appendTo($body);

  // ── Styles ─────────────────────────────────────────────────────────────────
  if (!document.getElementById("total-inv-styles")) {
    const style = document.createElement("style");
    style.id = "total-inv-styles";
    style.textContent = `
      #inv-table-container {
        font-family: var(--font-stack);
      }

      /* ── Date subtitle ── */
      .inv-date-subtitle {
        font-size: 12px;
        color: #888;
        margin-bottom: 14px;
        margin-top: 2px;
        text-align: center;
      }

      /* ── Section headings ── */
      .inv-section-heading {
        font-size: 15px;
        font-weight: 700;
        color: #c0392b;
        text-align: left;
        margin: 24px 0 12px 0;
        letter-spacing: 0.03em;
        text-transform: uppercase;
      }

      /* ── Summary cards ── */
      .inv-summary {
        display: flex;
        gap: 12px;
        margin-bottom: 16px;
        flex-wrap: wrap;
      }
      .inv-card {
        background: #fff;
        border: 1px solid #f5c6c6;
        border-top: 3px solid #c0392b;
        border-radius: 6px;
        padding: 12px 20px;
        min-width: 160px;
        box-shadow: 0 1px 4px rgba(192,57,43,0.07);
      }
      .inv-card .label {
        font-size: 10px;
        color: #b03a2e;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 4px;
        font-weight: 600;
      }
      .inv-card .value {
        font-size: 22px;
        font-weight: 700;
        color: #2d2d2d;
      }

      /* ── Table scroll wrapper ── */
      .inv-wrap {
        overflow-x: auto;
        overflow-y: auto;
        max-height: calc(100vh - 230px);
        border: 1px solid #f5c6c6;
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(192,57,43,0.08);
      }

      /* ── Table ── */
      table.inv-tbl {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        min-width: 620px;
      }

      /* Sticky header */
      table.inv-tbl thead tr th {
        position: sticky;
        top: 0;
        z-index: 3;
        background: #c0392b;
        color: #fff;
        font-weight: 600;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 10px 14px;
        border-right: 1px solid rgba(255,255,255,0.18);
        white-space: nowrap;
        text-align: center;
      }
      table.inv-tbl thead tr th:last-child {
        border-right: none;
      }

      /* Warehouse section cell — sticky left col */
      table.inv-tbl td.cell-wh {
        position: sticky;
        left: 0;
        z-index: 2;
        background: #fdecea;
        border-right: 2px solid #e8a09a;
        font-size: 11px;
        font-weight: 700;
        color: #922b21;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        vertical-align: middle;
        text-align: center;
        min-width: 160px;
        max-width: 200px;
        word-break: break-word;
        padding: 8px 12px;
      }

      /* Sticky top-left corner header */
      table.inv-tbl thead tr th:first-child {
        position: sticky;
        left: 0;
        z-index: 4;
        background: #a93226;
      }

      /* Item cell */
      table.inv-tbl td.cell-item {
        vertical-align: middle;
        padding: 7px 12px;
        border-right: 1px solid #f5c6c6;
        text-align: center;
      }
      table.inv-tbl td.cell-item a.item-link {
        font-size: 12px;
        font-weight: 600;
        color: #c0392b;
        text-decoration: none;
        word-break: break-word;
      }
      table.inv-tbl td.cell-item a.item-link:hover {
        text-decoration: underline;
        color: #a93226;
      }

      /* Generic data cells */
      table.inv-tbl td {
        padding: 7px 12px;
        border-bottom: 1px solid #f5c6c6;
        border-right: 1px solid #f5c6c6;
        color: #2d2d2d;
        text-align: center;
      }
      table.inv-tbl td:last-child { border-right: none; }
      table.inv-tbl td.num {
        text-align: right;
        font-variant-numeric: tabular-nums;
        white-space: nowrap;
        font-size: 13px;
      }

      /* Alternating row colours */
      table.inv-tbl tbody tr:nth-child(odd) td {
        background: #fff8f7;
      }
      table.inv-tbl tbody tr:nth-child(even) td {
        background: #fde8e6;
      }
      table.inv-tbl tbody tr td.cell-wh {
        background: #fdecea !important;
      }

      /* Hover */
      table.inv-tbl tbody tr:hover td {
        background: #fcd4d0 !important;
      }
      table.inv-tbl tbody tr:hover td.cell-wh {
        background: #f5b7b1 !important;
      }

      /* Grand total row */
      table.inv-tbl tr.total-row td {
        font-weight: 700;
        background: #c0392b !important;
        color: #fff !important;
        border-top: 2px solid #a93226;
        font-size: 13px;
        text-align: right;
      }

      /* Empty state */
      .inv-empty {
        text-align: center;
        padding: 60px 0;
        color: #999;
        font-size: 14px;
      }

      /* ── KPI section ── */
      #wh-kpi-container {
        font-family: var(--font-stack);
        margin-top: 28px;
      }
      .kpi-wrap {
        overflow-x: auto;
        border: 1px solid #f5c6c6;
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(192,57,43,0.08);
        max-width: 560px;
      }
      table.kpi-tbl {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        min-width: 320px;
      }
      table.kpi-tbl thead tr th {
        position: sticky;
        top: 0;
        z-index: 3;
        background: #c0392b;
        color: #fff;
        font-weight: 600;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 10px 18px;
        border-right: 1px solid rgba(255,255,255,0.18);
        white-space: nowrap;
        text-align: center;
      }
      table.kpi-tbl thead tr th:last-child {
        border-right: none;
      }
      table.kpi-tbl td {
        padding: 9px 18px;
        border-bottom: 1px solid #f5c6c6;
        border-right: 1px solid #f5c6c6;
        color: #2d2d2d;
        font-size: 13px;
      }
      table.kpi-tbl td:first-child {
        text-align: left;
      }
      table.kpi-tbl td:last-child {
        border-right: none;
        text-align: right;
        font-variant-numeric: tabular-nums;
        font-weight: 600;
        color: #2d2d2d;
        white-space: nowrap;
      }
      table.kpi-tbl tbody tr:nth-child(odd) td { background: #fff8f7; }
      table.kpi-tbl tbody tr:nth-child(even) td { background: #fde8e6; }
      table.kpi-tbl tbody tr:hover td { background: #fcd4d0 !important; }
      table.kpi-tbl tbody tr:last-child td { border-bottom: none; }

      /* ── Order Management section ── */
      #wh-om-container {
        font-family: var(--font-stack);
        margin-top: 28px;
      }
      .om-wrap {
        overflow-x: auto;
        border: 1px solid #f5c6c6;
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(192,57,43,0.08);
        max-width: 560px;
      }
      table.om-tbl {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        min-width: 320px;
      }
      table.om-tbl thead tr th {
        position: sticky;
        top: 0;
        z-index: 3;
        background: #c0392b;
        color: #fff;
        font-weight: 600;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 10px 18px;
        border-right: 1px solid rgba(255,255,255,0.18);
        white-space: nowrap;
        text-align: center;
      }
      table.om-tbl thead tr th:last-child { border-right: none; }
      table.om-tbl td {
        padding: 9px 18px;
        border-bottom: 1px solid #f5c6c6;
        border-right: 1px solid #f5c6c6;
        color: #2d2d2d;
        font-size: 13px;
      }
      table.om-tbl td:first-child { text-align: left; }
      table.om-tbl td:last-child {
        border-right: none;
        text-align: right;
        font-variant-numeric: tabular-nums;
        font-weight: 600;
        color: #2d2d2d;
        white-space: nowrap;
      }
      table.om-tbl tbody tr:nth-child(odd) td { background: #fff8f7; }
      table.om-tbl tbody tr:nth-child(even) td { background: #fde8e6; }
      table.om-tbl tbody tr:hover td { background: #fcd4d0 !important; }
      table.om-tbl tbody tr:last-child td { border-bottom: none; }

      /* ══════════════════════════════════════════
         ── INBOUND section ──
      ══════════════════════════════════════════ */
      #wh-inbound-container {
        font-family: var(--font-stack);
        margin-top: 28px;
      }
      .inbound-wrap {
        overflow-x: auto;
        border: 1px solid #f5c6c6;
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(192,57,43,0.08);
        max-width: 560px;
      }
      table.inbound-tbl {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        min-width: 320px;
      }
      table.inbound-tbl thead tr th {
        position: sticky;
        top: 0;
        z-index: 3;
        background: #c0392b;
        color: #fff;
        font-weight: 600;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 10px 18px;
        border-right: 1px solid rgba(255,255,255,0.18);
        white-space: nowrap;
        text-align: center;
      }
      table.inbound-tbl thead tr th:first-child { text-align: left; }
      table.inbound-tbl thead tr th:last-child { border-right: none; }
      table.inbound-tbl td {
        padding: 9px 18px;
        border-bottom: 1px solid #f5c6c6;
        border-right: 1px solid #f5c6c6;
        color: #2d2d2d;
        font-size: 13px;
      }
      table.inbound-tbl td:first-child { text-align: left; }
      table.inbound-tbl td:last-child {
        border-right: none;
        text-align: right;
        font-variant-numeric: tabular-nums;
        font-weight: 600;
        white-space: nowrap;
      }
      table.inbound-tbl tbody tr:nth-child(odd) td { background: #fff8f7; }
      table.inbound-tbl tbody tr:nth-child(even) td { background: #fde8e6; }
      table.inbound-tbl tbody tr:hover td { background: #fcd4d0 !important; }
      table.inbound-tbl tbody tr:last-child td { border-bottom: none; }

      /* ══════════════════════════════════════════
         ── MRB Stock section ──
      ══════════════════════════════════════════ */
      #wh-mrb-container {
        font-family: var(--font-stack);
        margin-top: 28px;
      }
      .mrb-wrap {
        overflow-x: auto;
        border: 1px solid #f5c6c6;
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(192,57,43,0.08);
        max-width: 560px;
      }
      table.mrb-tbl {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        min-width: 320px;
      }
      table.mrb-tbl thead tr th {
        position: sticky;
        top: 0;
        z-index: 3;
        background: #c0392b;
        color: #fff;
        font-weight: 600;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 10px 18px;
        border-right: 1px solid rgba(255,255,255,0.18);
        white-space: nowrap;
        text-align: center;
      }
      table.mrb-tbl thead tr th:first-child { text-align: left; }
      table.mrb-tbl thead tr th:last-child { border-right: none; }
      table.mrb-tbl td {
        padding: 9px 18px;
        border-bottom: 1px solid #f5c6c6;
        border-right: 1px solid #f5c6c6;
        color: #2d2d2d;
        font-size: 13px;
      }
      table.mrb-tbl td:first-child { text-align: left; }
      table.mrb-tbl td:last-child {
        border-right: none;
        text-align: right;
        font-variant-numeric: tabular-nums;
        font-weight: 600;
        white-space: nowrap;
      }
      table.mrb-tbl tbody tr:nth-child(odd) td { background: #fff8f7; }
      table.mrb-tbl tbody tr:nth-child(even) td { background: #fde8e6; }
      table.mrb-tbl tbody tr:hover td { background: #fcd4d0 !important; }
      table.mrb-tbl tbody tr:last-child td { border-bottom: none; }

      /* ══════════════════════════════════════════
         ── Dead Stock / Aging Inventory section ──
      ══════════════════════════════════════════ */
      #wh-dead-container {
        font-family: var(--font-stack);
        margin-top: 28px;
        margin-bottom: 28px;
      }
      .dead-wrap {
        overflow-x: auto;
        overflow-y: auto;
        max-height: 420px;
        border: 1px solid #f5c6c6;
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(192,57,43,0.08);
        max-width: 560px;
      }
      table.dead-tbl {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        min-width: 320px;
      }
      table.dead-tbl thead tr th {
        position: sticky;
        top: 0;
        z-index: 3;
        background: #c0392b;
        color: #fff;
        font-weight: 600;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 10px 18px;
        border-right: 1px solid rgba(255,255,255,0.18);
        white-space: nowrap;
        text-align: center;
      }
      table.dead-tbl thead tr th:first-child { text-align: left; }
      table.dead-tbl thead tr th:last-child { border-right: none; }
      table.dead-tbl td {
        padding: 9px 18px;
        border-bottom: 1px solid #f5c6c6;
        border-right: 1px solid #f5c6c6;
        color: #2d2d2d;
        font-size: 13px;
      }
      table.dead-tbl td:first-child { text-align: left; }
      table.dead-tbl td:last-child {
        border-right: none;
        text-align: right;
        font-variant-numeric: tabular-nums;
        font-weight: 600;
        white-space: nowrap;
      }
      table.dead-tbl tbody tr:nth-child(odd) td { background: #fff8f7; }
      table.dead-tbl tbody tr:nth-child(even) td { background: #fde8e6; }
      table.dead-tbl tbody tr:hover td { background: #fcd4d0 !important; }
      table.dead-tbl tbody tr:last-child td { border-bottom: none; }
    `;
    document.head.appendChild(style);
  }

  // ── Main refresh ───────────────────────────────────────────────────────────
  function refresh() {
    $container.html(
      `<div style="padding:48px;text-align:center;">
        <span class="loading-spinner"></span>
        <p style="margin-top:14px;color:#c0392b;font-size:13px;">Loading inventory…</p>
      </div>`
    );

    frappe.call({
      method: "norden.norden.page.warehouse_dashboard.warehouse_dashboard.get_inventory_data",
      args: {
        company: "",
        warehouse: ""
      },
      callback(r) {
        if (r.exc) {
          $container.html(
            `<div class="inv-empty"><i class="fa fa-exclamation-circle"></i> Error loading data.</div>`
          );
          return;
        }
        render(r.message || []);
      },
    });

    refresh_kpi();
    refresh_om();
    refresh_inbound();
    refresh_mrb();
    refresh_dead();
  }

  // ── Render main inventory ──────────────────────────────────────────────────
  function render(rows) {
    if (!rows.length) {
      $container.html(`<div class="inv-empty">No inventory data found.</div>`);
      return;
    }

    const warehouses = {};
    const wh_order = [];
    console.log(rows)
    rows.forEach((row) => {
      const wh = row.warehouse || "Unknown";
      if (!warehouses[wh]) {
        warehouses[wh] = [];
        wh_order.push(wh);
      }
      warehouses[wh].push(row);
    });

    const total_qty = rows.reduce((s, r) => s + (r.actual_qty || 0), 0);
    const total_value = rows.reduce(
      (s, r) => s + (r.actual_qty || 0) * (r.valuation_rate || 0),
      0
    );

    let html = `
      <div class="inv-summary">
        <div class="inv-card">
          <div class="label">Warehouses</div>
          <div class="value">${wh_order.length}</div>
        </div>
        <div class="inv-card">
          <div class="label">Total Qty</div>
          <div class="value">${fmt_num(total_qty, 0)}</div>
        </div>
        <div class="inv-card">
          <div class="label">Total Value</div>
          <div class="value">${frappe.format(total_value, { fieldtype: "Currency" })}</div>
        </div>
      </div>

      <div class="inv-wrap">
        <table class="inv-tbl">
          <thead>
            <tr>
              <th>Warehouse</th>
              <th>Item</th>
              <th>UOM</th>
              <th>Qty</th>
              <th>Valuation Rate</th>
              <th>Value</th>
            </tr>
          </thead>
          <tbody>
    `;

    let grand_total = 0;

    wh_order.forEach((wh) => {
      const items = warehouses[wh];
      const rowspan = items.length;

      items.forEach((row, idx) => {
        const value = (row.actual_qty || 0) * (row.valuation_rate || 0);
        grand_total += value;

        const item_url = frappe.utils.get_form_link("Item", row.item_code);

        const wh_cell =
          idx === 0
            ? `<td class="cell-wh" rowspan="${rowspan}">${frappe.utils.escape_html(wh)}</td>`
            : "";

        html += `
          <tr>
            ${wh_cell}
            <td class="cell-item">
              <a class="item-link" href="${item_url}" target="_blank">
                ${frappe.utils.escape_html(row.item_code || "")}
              </a>
            </td>
            <td>${frappe.utils.escape_html(row.stock_uom || "")}</td>
            <td class="num">${fmt_num(row.actual_qty, 2)}</td>
            <td class="num">${frappe.format(row.valuation_rate || 0, { fieldtype: "Currency" })}</td>
            <td class="num">${frappe.format(value, { fieldtype: "Currency" })}</td>
          </tr>
        `;
      });
    });

    html += `
            <tr class="total-row">
              <td colspan="5" style="text-align:right;letter-spacing:0.04em;">Grand Total</td>
              <td class="num">${frappe.format(grand_total, { fieldtype: "Currency" })}</td>
            </tr>
          </tbody>
        </table>
      </div>
    `;

    $container.html(html);
  }

  // ── KPI refresh ────────────────────────────────────────────────────────────
  function refresh_kpi() {
    $kpi_container.html(spinner_html("Loading performance data…"));

    frappe.call({
      method: "norden.norden.page.warehouse_dashboard.warehouse_dashboard.get_warehouse_performance",
      args: {
        custom_picking_start_time: "08:00:00",
        custom_picking_end_time: "09:30:00"
      },
      callback(r) {
        if (r.exc || !r.message) {
          $kpi_container.html(error_html("Error loading KPI data."));
          return;
        }
        render_kpi(r.message);
      },
    });
  }

  function render_kpi(d) {
    const avg_time_display = d.avg_picking_time ? d.avg_picking_time + " min" : "—";

    $kpi_container.html(`
      <div class="inv-section-heading">Warehouse Performance</div>
      <div class="kpi-wrap">
        <table class="kpi-tbl">
          <thead><tr><th>KPI</th><th>Value</th></tr></thead>
          <tbody>
            <tr><td>Picking Accuracy</td><td>${d.picking_accuracy}%</td></tr>
            <tr><td>Order Fulfillment Rate</td><td>${d.fulfillment_rate}%</td></tr>
            <tr><td>Avg Picking Time</td><td>${avg_time_display}</td></tr>
            <tr><td>Space Utilization</td><td>—</td></tr>
          </tbody>
        </table>
      </div>
    `);
  }

  // ── Order Management refresh ───────────────────────────────────────────────
  function refresh_om() {
    $om_container.html(spinner_html("Loading order data…"));

    frappe.call({
      method: "norden.norden.page.warehouse_dashboard.warehouse_dashboard.get_order_management",
      args: {},
      callback(r) {
        if (r.exc || !r.message) {
          $om_container.html(error_html("Error loading order data."));
          return;
        }
        render_om(r.message);
      },
    });
  }

  function render_om(d) {
    $om_container.html(`
      <div class="inv-section-heading">Order Management</div>
      <div class="om-wrap">
        <table class="om-tbl">
          <thead><tr><th>Metric</th><th>Value</th></tr></thead>
          <tbody>
            <tr><td>Orders Received Today</td><td>${fmt_num(d.orders_received, 0)}</td></tr>
            <tr><td>Orders Processed</td><td>${fmt_num(d.orders_processed, 0)}</td></tr>
            <tr><td>Pending for QC</td><td>${fmt_num(d.pending_qc, 0)}</td></tr>
            <tr><td>Orders Pending</td><td>${fmt_num(d.orders_pending, 0)}</td></tr>
          </tbody>
        </table>
      </div>
    `);
  }

  // ══════════════════════════════════════════════════════════════════════════
  // ── INBOUND refresh ───────────────────────────────────────────────────────
  // ══════════════════════════════════════════════════════════════════════════
  function refresh_inbound() {
    $inbound_container.html(spinner_html("Loading inbound data…"));

    frappe.call({
      method: "norden.norden.page.warehouse_dashboard.warehouse_dashboard.get_inbound_data",
      args: {},
      callback(r) {
        if (r.exc || !r.message) {
          $inbound_container.html(error_html("Error loading inbound data."));
          return;
        }
        render_inbound(r.message);
      },
    });
  }

  /**
   * Expected payload from get_inbound_data:
   * {
   *   total_shipments_received : <number>,
   *   grn_pending              : <number>,
   *   pending_for_qc           : <number>
   * }
   */
  function render_inbound(d) {
    $inbound_container.html(`
      <div class="inv-section-heading">Inbound</div>
      <div class="inbound-wrap">
        <table class="inbound-tbl">
          <thead>
            <tr>
              <th>Metric</th>
              <th>Qty</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Total Shipments Received</td>
              <td>${fmt_num(d.total_shipments_received, 0)}</td>
            </tr>
            <tr>
              <td>GRN Pending</td>
              <td>${fmt_num(d.grn_pending, 0)}</td>
            </tr>
            <tr>
              <td>Pending for QC</td>
              <td>${fmt_num(d.pending_for_qc, 0)}</td>
            </tr>
          </tbody>
        </table>
      </div>
    `);
  }

  // ══════════════════════════════════════════════════════════════════════════
  // ── MRB Stock refresh ─────────────────────────────────────────────────────
  // ══════════════════════════════════════════════════════════════════════════
  function refresh_mrb() {
    $mrb_container.html(spinner_html("Loading MRB stock data…"));

    frappe.call({
      method: "norden.norden.page.warehouse_dashboard.warehouse_dashboard.get_mrb_stock",
      args: {},
      callback(r) {
        if (r.exc || !r.message) {
          $mrb_container.html("Loading MRB stock data.");
          return;
        }
        render_mrb(r.message);
      },
    });
  }

  /**
   * Expected payload from get_mrb_stock:
   * {
   *   total_stock_sku_wise : <number>
   * }
   */
  function render_mrb(d) {
    $mrb_container.html(`
      <div class="inv-section-heading">MRB Stock</div>
      <div class="mrb-wrap">
        <table class="mrb-tbl">
          <thead>
            <tr>
              <th></th>
              <th>Qty</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Total Stock SKU wise</td>
              <td>${fmt_num(d.total_stock_sku_wise, 0)}</td>
            </tr>
          </tbody>
        </table>
      </div>
    `);
  }

  // ══════════════════════════════════════════════════════════════════════════
  // ── Dead Stock / Aging Inventory refresh ──────────────────────────────────
  // ══════════════════════════════════════════════════════════════════════════
  function refresh_dead() {
    $dead_container.html(spinner_html("Loading dead stock data…"));

    frappe.call({
      method: "norden.norden.page.warehouse_dashboard.warehouse_dashboard.get_dead_stock",
      args: {},
      callback(r) {
        if (r.exc || !r.message) {
          $dead_container.html(error_html("Error loading dead stock data."));
          return;
        }
        render_dead(r.message);
      },
    });
  }

  /**
   * Expected payload from get_dead_stock:
   * [
   *   { item_code: "ITEM-001", qty: 25 },
   *   { item_code: "ITEM-002", qty: 10 },
   *   ...
   * ]
   */
  function render_dead(rows) {
    if (!rows || !rows.length) {
      $dead_container.html(`
      <div class="inv-section-heading">Dead Stock / Aging Inventory</div>
      <div class="inv-empty">No dead stock found.</div>
    `);
      return;
    }

    // 1. Group by warehouse, preserve order
    const groups = {};
    const order = [];
    rows.forEach((row) => {
      const wh = row.warehouse || "Unknown";
      if (!groups[wh]) { groups[wh] = []; order.push(wh); }
      groups[wh].push(row);
    });

    // 2. Build rows — rowspan on first item of each warehouse group
    let rows_html = "";
    order.forEach((warehouse, gIdx) => {
      const items = groups[warehouse];
      const lastGrp = gIdx === order.length - 1;

      items.forEach((row, idx) => {
        const isFirst = idx === 0;
        const isLast = idx === items.length - 1;
        const item_url = frappe.utils.get_form_link("Item", row.item_code);

        // Add group-end class on the last row of each group (draws a thicker divider)
        const trClass = (isLast && !lastGrp) ? ' class="dead-group-end"' : "";

        const wh_cell = isFirst
          ? `<td class="dead-wh-cell" rowspan="${items.length}">
             ${frappe.utils.escape_html(warehouse)}
           </td>`
          : "";

        rows_html += `
        <tr${trClass}>
          ${wh_cell}
          <td class="dead-item-cell">
            <a href="${item_url}" target="_blank">
              ${frappe.utils.escape_html(row.item_code || "")}
            </a>
          </td>
          <td class="dead-qty-cell">${fmt_num(row.qty, 0)}</td>
        </tr>
      `;
      });
    });

    $dead_container.html(`
    <div class="inv-section-heading">Dead Stock / Aging Inventory</div>
    <div class="dead-wrap">
      <table class="dead-tbl">
        <thead>
          <tr>
            <th>Warehouse</th>
            <th>Item ID</th>
            <th>Qty</th>
          </tr>
        </thead>
        <tbody>${rows_html}</tbody>
      </table>
    </div>
  `);
  }

  // ── Shared helpers ─────────────────────────────────────────────────────────
  function spinner_html(msg) {
    return `
      <div style="padding:24px;text-align:center;">
        <span class="loading-spinner"></span>
        <p style="margin-top:10px;color:#c0392b;font-size:13px;">${msg}</p>
      </div>`;
  }

  function error_html(msg) {
    return `<div class="inv-empty"><i class="fa fa-exclamation-circle"></i> ${msg}</div>`;
  }

  function fmt_num(val, decimals) {
    if (val === null || val === undefined) return "0";
    return Number(val).toLocaleString("en-IN", {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  }

  // Auto-load
  refresh();
};