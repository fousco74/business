import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


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

# Custom fields required by Business print formats
CUSTOM_FIELDS = {
	"Company": [
		{
			"fieldname": "business_info_section",
			"fieldtype": "Section Break",
			"label": "Informations Business",
			"insert_after": "tax_id",
		},
		{
			"fieldname": "custom_rccm",
			"fieldtype": "Data",
			"label": "RCCM",
			"insert_after": "business_info_section",
		},
		{
			"fieldname": "custom_address_line",
			"fieldtype": "Data",
			"label": "Ligne d'adresse",
			"insert_after": "custom_rccm",
		},
		{
			"fieldname": "custom_capital_social",
			"fieldtype": "Data",
			"label": "Capital Social",
			"insert_after": "custom_address_line",
		},
		{
			"fieldname": "custom_bank_account_display",
			"fieldtype": "Small Text",
			"label": "Informations Bancaires",
			"insert_after": "custom_capital_social",
		},
	],
	"Supplier": [
		{
			"fieldname": "custom_rccm",
			"fieldtype": "Data",
			"label": "RCCM",
			"insert_after": "tax_id",
		},
	],
	"Delivery Note": [
		{
			"fieldname": "custom_observation",
			"fieldtype": "Small Text",
			"label": "Observations",
			"insert_after": "terms",
		},
	],
	"Material Request": [
		{
			"fieldname": "custom_priorite",
			"fieldtype": "Select",
			"label": "Priorité",
			"options": "\nNormale\nHaute\nUrgente",
			"insert_after": "schedule_date",
		},
		{
			"fieldname": "custom_observation",
			"fieldtype": "Small Text",
			"label": "Observations",
			"insert_after": "terms",
		},
	],
	"Purchase Order": [
		{
			"fieldname": "custom_observation",
			"fieldtype": "Small Text",
			"label": "Observations",
			"insert_after": "terms",
		},
	],
	"Sales Invoice": [
		{
			"fieldname": "custom_observation",
			"fieldtype": "Small Text",
			"label": "Observations",
			"insert_after": "terms",
		},
	],
	"Stock Reconciliation": [
		{
			"fieldname": "custom_observation",
			"fieldtype": "Small Text",
			"label": "Observations",
			"insert_after": "remarks",
		},
	],
}


def after_install():
	create_business_custom_fields()
	set_default_print_formats()


def create_business_custom_fields():
	create_custom_fields(CUSTOM_FIELDS, update=True)
	frappe.db.commit()


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
