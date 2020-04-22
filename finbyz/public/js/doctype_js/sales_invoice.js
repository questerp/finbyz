frappe.ui.form.on('Sales Invoice', {
	refresh: function(frm){
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
					'date': frm.doc.posting_date
				},
				callback: function(e) {
					frm.set_value("series_value", e.message);
				}
			});
		}
	},
	posting_date: function(frm) {
		if (frm.doc.company && !frm.doc.amended_from){
			frappe.call({
				method: "finbyz.api.check_counter_series",
				args: {
					'name': frm.doc.naming_series,
					'date': frm.doc.posting_date
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