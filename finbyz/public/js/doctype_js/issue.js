
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
        frappe.model.open_mapped_doc({
            method:"finbyz.api.create_time_sheet",
            frm:cur_frm
        })
    },__("Create"));
    }
})

