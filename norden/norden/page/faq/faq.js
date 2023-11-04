frappe.pages['faq'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'FAQ',
		single_column: true
	});
	page.main.html(frappe.render_template('faq'))
}