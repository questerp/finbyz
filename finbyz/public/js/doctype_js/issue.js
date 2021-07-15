
frappe.ui.form.on('Issue', {
	refresh : function(frm) {
		frm.add_custom_button(__("Go To Project Password"), function() {
            if (frm.doc.project){
                frappe.db.get_value("Project Password",{'project':frm.doc.project},'name',function(r){
                    if(r.name){
                        frappe.set_route("Form","Project Password",r.name)
                    }
                })      
        }
        else{
            frappe.msgprint("Enter Project");
        }
    }),
    frm.add_custom_button(__("Timesheet"), function() {
        // frappe.model.open_mapped_doc({
        //     method:"finbyz.api.create_time_sheet",
        //     frm:cur_frm
        // })
        return frappe.call({
            method : "finbyz.api.create_time_sheet",
            args: {
                "source_name": frm.doc.name
            },
            callback: function(r) {
                if(!r.exc) {
                    var doc = frappe.model.sync(r.message);
                    frappe.set_route("Form", r.message.doctype, r.message.name);
                }
            }
        })
    },__("Create"));
    }
})

