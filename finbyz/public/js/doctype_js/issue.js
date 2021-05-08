
frappe.ui.form.on('Issue', {
	refresh : function(frm) {
        
		frm.add_custom_button(__("Go To Project Password"), function() {
            if (frm.doc.project){
            return frappe.set_route("Form","Project Password",frm.doc.project); 
        }
        else{
            frappe.msgprint("Enter Project");
        }
    })    
    }
})

