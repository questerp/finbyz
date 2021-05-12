
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
    })    
    }
})

