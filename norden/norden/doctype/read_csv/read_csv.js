// Copyright (c) 2025, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on("Read CSV", {
	refresh(frm) {

	},
    download: function(frm) {
        var path = "norden.norden.doctype.read_csv.read_csv.download";
        window.location.href = "/api/method/" + path;
    }
});
