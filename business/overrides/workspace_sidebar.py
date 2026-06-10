import frappe
from frappe.desk.doctype.workspace_sidebar.workspace_sidebar import WorkspaceSidebar


class WorkspaceSidebarFixed(WorkspaceSidebar):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		allowed_modules = getattr(self, "allowed_modules", None)
		can_read = getattr(self, "can_read", None)
		user = getattr(self, "user", None)
		if user:
			if allowed_modules and not user.allow_modules:
				user.allow_modules = allowed_modules
			if can_read and not user.can_read:
				user.can_read = can_read

	def get_can_read_items(self):
		if not self.user.can_read:
			self.user.build_permissions()
		return self.user.can_read
