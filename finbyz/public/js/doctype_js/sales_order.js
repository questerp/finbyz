
//Contact Filter
cur_frm.fields_dict.other_contacts.grid.get_field("contact").get_query = function(doc) {
	if(cur_frm.doc.customer) {
		return {
			query: "frappe.contacts.doctype.contact.contact.contact_query",
			filters: { link_doctype: "Customer", link_name: cur_frm.doc.customer} 
		};
	}
	else frappe.throw(__("Please set Customer"));
};

frappe.ui.form.on('Other Contact', {

})