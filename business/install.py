import frappe


DEFAULT_PRINT_FORMATS = {
	"Delivery Note": "Business Delivery Note",
	"Material Request": "Business Material Request",
	"Payment Entry": "Business Payment Entry",
	"Purchase Invoice": "Business Purchase Invoice",
	"Purchase Order": "Business Purchase Order",
	"Purchase Receipt": "Business Purchase Receipt",
	"Quotation": "Business Quotation",
	"Request for Quotation": "Business Request For Quotation",
	"Sales Invoice": "Business Sales Invoice",
	"Sales Order": "Business Sales Order",
	"Stock Entry": "Business Stock Entry",
	"Stock Reconciliation": "Business Stock Reconciliation",
	"Supplier Quotation": "Business Supplier Quotation",
}


def after_install():
	set_default_print_formats()


def set_default_print_formats():
	for doctype, format_name in DEFAULT_PRINT_FORMATS.items():
		if not frappe.db.exists("Print Format", format_name):
			continue
		existing = frappe.db.get_value(
			"Property Setter",
			{"doc_type": doctype, "property": "default_print_format"},
			"name",
		)
		if existing:
			frappe.db.set_value("Property Setter", existing, "value", format_name)
		else:
			frappe.make_property_setter(
				{
					"doctype": doctype,
					"property": "default_print_format",
					"value": format_name,
					"property_type": "Data",
					"doctype_or_field": "DocType",
				}
			)
	frappe.db.commit()
