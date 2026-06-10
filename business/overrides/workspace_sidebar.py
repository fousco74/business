import frappe
from frappe.desk.doctype.workspace_sidebar.workspace_sidebar import WorkspaceSidebar


class WorkspaceSidebarFixed(WorkspaceSidebar):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		if self.allowed_modules and not self.user.allow_modules:
			self.user.allow_modules = self.allowed_modules
		if self.can_read and not self.user.can_read:
			self.user.can_read = self.can_read
		# Debug temporaire
		frappe.logger().info(
			f"[business] WorkspaceSidebarFixed: module={getattr(self,'module',None)} "
			f"allowed_modules={self.allowed_modules[:3] if self.allowed_modules else self.allowed_modules!r} "
			f"user.allow_modules={self.user.allow_modules[:3] if self.user.allow_modules else '[]'} "
			f"user={frappe.session.user}"
		)

	def get_can_read_items(self):
		if not self.user.can_read:
			self.user.build_permissions()
		return self.user.can_read
