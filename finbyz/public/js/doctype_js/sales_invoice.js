frappe.ui.form.on('Sales Invoice', {
	refresh: function(frm){
		if (cur_frm.doc.company){
			frappe.db.get_value("Company", cur_frm.doc.company, 'company_series',(r) => {
				frm.set_value('company_series', r.company_series);
			});
		}
		if (frm.doc.__islocal){
			frm.trigger('naming_series');
		}
	},
	naming_series: function(frm) {
		if (frm.doc.company && !frm.doc.amended_from){
			frappe.call({
				method: "finbyz.api.check_counter_series",
				args: {
					'name': frm.doc.naming_series,
				},
				callback: function(e) {
					frm.set_value("series_value", e.message);
				}
			});
		}
	},
	company: function(frm){
		if (frm.doc.__islocal){
			frm.trigger('naming_series');
		}
	},
});