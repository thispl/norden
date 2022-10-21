// Copyright (c) 2022, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on('Item Currency Conversion', {
	refresh: function(frm) {
		frm.disable_save()
		

	},
	
	item:function(frm){
		frm.call('get_data').then(r=>{
			if (r.message) {
				frm.fields_dict.html_7.$wrapper.empty().append(r.message)
			}
		})		
	},
	"filters": [
		{
			"fieldname": "price_list",
			"label": __("Price List"),
			"fieldtype": "Link",
			"reqd": 1
		},
		{
			"fieldname": "from_currency",
			"label": __("From Currency"),
			"fieldtype": "Data",
			"reqd": 1
		},
		{
			"fieldname": "convert_to",
			"label": __("Convert To"),
			"fieldtype": "Link",
			"reqd": 1
		},
	],
	download: function (frm) {
		window.location.href = repl(frappe.request.url +
			'?cmd=%(cmd)s&price_list=%(price_list)s&from_currency=%(from_currency)s&convert_to=%(convert_to)s', {
			cmd: "norden.norden.doctype.item_currency_conversion.item_currency_conversion.download",
			price_list: frm.doc.price_list,
			from_currency: frm.doc.from_currency,
			convert_to: frm.doc.convert_to
		
		});
	},
//  price_list(frm){
// 	 if ( frm.doc.price_list ){
		 
// 		 frm.trigger("item")
	 
// 	}
//  },
 convert_to(frm){
	if ( frm.doc.convert_to ){
		
		frm.trigger("item")
	
   }
}

});
