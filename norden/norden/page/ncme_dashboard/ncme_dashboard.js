frappe.pages['ncme-dashboard'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'NCME Dashboard',
		single_column: true
	});
	frappe.breadcrumbs.add("Setup");
	$(frappe.render_template('ncme_dashboard')).appendTo(page.main);
}
