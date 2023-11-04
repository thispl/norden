frappe.pages['user-manual-document'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'User Manual Document',
		single_column: true
	});
	page.main.html(frappe.render_template('user_manual_document'))
}