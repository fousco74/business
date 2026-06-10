import frappe


def extend_bootinfo(bootinfo):
	"""
	Fix pour Frappe v16 — deux bugs corrigés dans l'app business :

	BUG 1 : WorkspaceSidebar.get_sidebar_items() filtre via user.allow_modules
	qui est vide quand les permissions viennent du cache Redis.

	BUG 2 : Desktop Icons — le parent (ERPNext App) n'a que System Manager
	dans ses rôles, ce qui filtre les icônes enfants (Stock, Buying, Selling)
	même si l'enfant a le bon rôle. On corrige en incluant les parents dont
	au moins un enfant est permis.
	"""
	if frappe.session.user in ("Administrator", "Guest"):
		return

	workspace_pages = bootinfo.get("workspaces", {}).get("pages", [])
	if not workspace_pages:
		return

	# Forcer build_permissions pour peupler user.allow_modules
	user = frappe.get_user()
	if not user.allow_modules:
		user.build_permissions()

	if not user.allow_modules:
		return

	# Reconstruire le sidebar avec les bonnes permissions
	from frappe.boot import get_sidebar_items
	allowed_pages = [p.get("name") for p in workspace_pages]
	bootinfo.workspace_sidebar_item = get_sidebar_items(allowed_pages)

	# Recalculer les desktop icons
	frappe.cache.hdel("desktop_icons", frappe.session.user)

	from frappe.query_builder import DocType
	DI = DocType("Desktop Icon")
	all_icons = (
		frappe.qb.from_(DI)
		.select("label", "bg_color", "link", "link_type", "app", "icon_type",
				"parent_icon", "icon", "link_to", "idx", "standard", "logo_url",
				"hidden", "name", "restrict_removal", "icon_image")
		.where(
			(DI.standard == 1)
			| ((DI.standard == 0) & (DI.owner.isin(["Administrator", frappe.session.user])))
		)
		.distinct()
	).run(as_dict=True)

	all_icons.sort(key=lambda a: a.idx)

	permitted = []
	permitted_parent_labels = set()
	child_parent_map = {}  # label → parent_icon

	for s in all_icons:
		icon = frappe.get_doc("Desktop Icon", s.name)
		if icon.is_permitted(bootinfo):
			permitted.append(s)
			if not s.parent_icon:
				permitted_parent_labels.add(s.label)
			else:
				child_parent_map[s.label] = s.parent_icon

	# Fix BUG 2 : ajouter les parents dont un enfant est permis
	# même si le parent lui-même n'est pas dans permitted_parent_labels
	for child_label, parent_label in child_parent_map.items():
		if parent_label not in permitted_parent_labels:
			# Chercher l'icône parente et l'ajouter
			parent_icon_data = next((s for s in all_icons if s.label == parent_label), None)
			if parent_icon_data:
				permitted.insert(0, parent_icon_data)  # avant les enfants
				permitted_parent_labels.add(parent_label)

	# Filtre final
	bootinfo.desktop_icons = [
		s for s in permitted if not s.parent_icon or s.parent_icon in permitted_parent_labels
	]

	frappe.cache.hset("desktop_icons", frappe.session.user, bootinfo.desktop_icons)
