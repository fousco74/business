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

	# Recalculer les desktop icons avec le sidebar corrigé ci-dessus.
	# NB : tout échec ici ne doit JAMAIS casser le boot — on retombe alors
	# sur les icônes déjà calculées par frappe.boot.get_desktop_icons().
	try:
		frappe.cache.hdel("desktop_icons", frappe.session.user)
		bootinfo.desktop_icons = _recompute_desktop_icons(bootinfo)
		frappe.cache.hset("desktop_icons", frappe.session.user, bootinfo.desktop_icons)
	except Exception:
		frappe.log_error("business.extend_bootinfo: recalcul des desktop icons échoué")


def _recompute_desktop_icons(bootinfo):
	"""Rejoue la logique de permission de frappe.desk...desktop_icon.get_desktop_icons
	sur le sidebar reconstruit, en incluant les parents dont au moins un enfant
	est permis (BUG 2)."""
	from frappe.desk.doctype.desktop_icon.desktop_icon import check_app_permission
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

	# rôles configurés par icône (child table Has Role)
	icon_roles_map = {}
	icon_names = [s.name for s in all_icons]
	if icon_names:
		for r in frappe.get_all(
			"Has Role",
			filters={"parenttype": "Desktop Icon", "parent": ["in", icon_names]},
			fields=["parent", "role"],
		):
			icon_roles_map.setdefault(r.parent, set()).add(r.role)

	user_roles = set(frappe.get_roles())

	def is_permitted(s):
		if s.icon_type == "Folder":
			permitted = True
		elif s.icon_type == "App":
			permitted = check_app_permission(s.label, s.app)
		else:
			# lien Workspace Sidebar : présent dans le boot ⇒ au moins un item visible
			sidebar = bootinfo.workspace_sidebar_item.get((s.label or "").lower())
			permitted = bool(sidebar and sidebar.get("items"))
		if permitted and icon_roles_map.get(s.name):
			permitted = bool(icon_roles_map[s.name] & user_roles)
		return permitted

	permitted = []
	permitted_parent_labels = set()
	child_parent_map = {}  # label → parent_icon

	for s in all_icons:
		if is_permitted(s):
			permitted.append(s)
			if not s.parent_icon:
				permitted_parent_labels.add(s.label)
			else:
				child_parent_map[s.label] = s.parent_icon

	# Fix BUG 2 : ajouter les parents dont un enfant est permis
	# même si le parent lui-même n'est pas dans permitted_parent_labels
	for child_label, parent_label in child_parent_map.items():
		if parent_label not in permitted_parent_labels:
			parent_icon_data = next((s for s in all_icons if s.label == parent_label), None)
			if parent_icon_data:
				permitted.insert(0, parent_icon_data)  # avant les enfants
				permitted_parent_labels.add(parent_label)

	# Filtre final
	return [
		s for s in permitted if not s.parent_icon or s.parent_icon in permitted_parent_labels
	]
