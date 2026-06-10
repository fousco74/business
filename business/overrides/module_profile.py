import frappe


def before_delete(doc, method=None):
	if doc.name == "Pack Business":
		frappe.throw(frappe._("Le profil de module 'Pack Business' ne peut pas être supprimé."))
