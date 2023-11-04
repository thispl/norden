frappe.pages['holiday-list-2023'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Holiday List-2023',
		single_column: true
	});
	page.main.html(frappe.render_template('holiday-list-2023'))
}
