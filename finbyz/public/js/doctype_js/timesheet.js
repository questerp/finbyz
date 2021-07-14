cur_frm.fields_dict.time_logs.grid.get_field("issue").get_query = function(doc,cdt,cdn) {
    let d = locals[cdt][cdn];
	return {
		filters: {
			"status":"Open" ,
			"project": d.project,
		}
	}
};