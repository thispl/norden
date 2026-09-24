// Copyright (c) 2024, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on("Item Price List Upload Tool", {
    // 	refresh(frm) {
    
    // 	},
    get_template: function (frm) {
        console.log(frappe.request.url)
        window.location.href = repl(frappe.request.url +
            '?cmd=%(cmd)s&currency=%(currency)s', {
            cmd: "norden.norden.doctype.item_price_list_upload_tool.item_price_list_upload_tool.get_template",
            currency: frm.doc.currency,
            // valid_from: frm.doc.valid_from
        });
    },
    // upload(frm){
    //     window.location.href = repl(frappe.request.url +
    //         '?cmd=%(cmd)s&currency=%(currency)s&valid_from=%(valid_from)s', {
    //         cmd: "norden.norden.doctype.item_price_list_upload_tool.item_price_list_upload_tool.upload_data",
    //         currency: frm.doc.currency,
    //         valid_from: frm.doc.valid_from
    //     });
    // }
    });
    