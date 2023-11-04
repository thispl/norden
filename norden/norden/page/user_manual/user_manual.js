frappe.pages['user_manual'].on_page_load = function(wrapper) {
	
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'User Manual',
		single_column: true,
		card_layout : true,
		
	});
	page.main.html(frappe.render_template('user_manual'))
}