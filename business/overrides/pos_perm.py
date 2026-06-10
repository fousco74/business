import frappe


def has_permission(doc, ptype, user):
    """Accorde l'accès Sales Invoice / POS Invoice aux utilisateurs assignés à un Profil PDV.

    Hook Frappe (has_permission dans hooks.py) — corrige le bug ERPNext v16 où
    Sales User n'a aucune permission par défaut sur Sales Invoice, ce qui provoque
    un 403 sur run_doc_method lors de la création du formulaire interne du POS.
    """
    if ptype not in ("read", "write", "create", "submit", "cancel", "amend"):
        return None

    check_user = user or frappe.session.user

    if frappe.db.exists("POS Profile User", {"user": check_user}):
        return True

    return None
