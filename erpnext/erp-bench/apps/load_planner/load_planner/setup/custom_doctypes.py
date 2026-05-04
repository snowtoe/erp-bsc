import frappe


SYSTEM_MANAGER_PERMS = [
    {
        "role": "System Manager",
        "read": 1,
        "write": 1,
        "create": 1,
        "delete": 1,
        "print": 1,
        "email": 1,
        "share": 1,
        "export": 1,
        "report": 1,
    }
]


def ensure_permissions(doctype_doc, permissions):
    existing_roles = {p.role for p in doctype_doc.permissions}
    for perm in permissions:
        if perm["role"] not in existing_roles:
            doctype_doc.append("permissions", perm)


def ensure_doctype(doctype_definition):
    name = doctype_definition["name"]

    if frappe.db.exists("DocType", name):
        dt = frappe.get_doc("DocType", name)

        for key in [
            "module",
            "custom",
            "istable",
            "editable_grid",
            "autoname",
            "title_field",
            "track_changes",
        ]:
            if key in doctype_definition:
                setattr(dt, key, doctype_definition[key])

        existing_fields = {f.fieldname for f in dt.fields}
        for field in doctype_definition.get("fields", []):
            if field["fieldname"] not in existing_fields:
                dt.append("fields", field)

        ensure_permissions(dt, doctype_definition.get("permissions", []))
        dt.save(ignore_permissions=True)
        frappe.db.commit()
        frappe.clear_cache(doctype=name)
        return

    dt = frappe.get_doc(doctype_definition)
    dt.insert(ignore_permissions=True)
    frappe.db.commit()
    frappe.clear_cache(doctype=name)


def create_load_planner_doctypes():
    ensure_doctype({
        "doctype": "DocType",
        "name": "LP Package Type",
        "module": "Load Planner",
        "custom": 1,
        "autoname": "field:package_type_name",
        "title_field": "package_type_name",
        "track_changes": 1,
        "fields": [
            {
                "fieldname": "package_type_name",
                "label": "Gebindeart",
                "fieldtype": "Data",
                "reqd": 1,
                "in_list_view": 1,
            },
            {
                "fieldname": "code",
                "label": "Code",
                "fieldtype": "Data",
                "in_list_view": 1,
            },
            {
                "fieldname": "package_kind",
                "label": "Typ",
                "fieldtype": "Select",
                "options": "Standard\nFachgebinde",
                "default": "Standard",
                "in_list_view": 1,
            },
            {
                "fieldname": "length_mm",
                "label": "Länge (mm)",
                "fieldtype": "Float",
            },
            {
                "fieldname": "width_mm",
                "label": "Breite (mm)",
                "fieldtype": "Float",
            },
            {
                "fieldname": "max_height_mm",
                "label": "Max. Höhe (mm)",
                "fieldtype": "Float",
            },
            {
                "fieldname": "max_weight_kg",
                "label": "Max. Nutzlast (kg)",
                "fieldtype": "Float",
            },
            {
                "fieldname": "compartment_count",
                "label": "Anzahl Fächer",
                "fieldtype": "Int",
                "default": 1,
            },
            {
                "fieldname": "is_active",
                "label": "Aktiv",
                "fieldtype": "Check",
                "default": 1,
                "in_list_view": 1,
            },
        ],
        "permissions": SYSTEM_MANAGER_PERMS,
    })

    ensure_doctype({
        "doctype": "DocType",
        "name": "LP Picking Group",
        "module": "Load Planner",
        "custom": 1,
        "autoname": "field:group_name",
        "title_field": "group_name",
        "track_changes": 1,
        "fields": [
            {
                "fieldname": "group_name",
                "label": "Kommissioniergruppe",
                "fieldtype": "Data",
                "reqd": 1,
                "in_list_view": 1,
            },
            {
                "fieldname": "is_active",
                "label": "Aktiv",
                "fieldtype": "Check",
                "default": 1,
                "in_list_view": 1,
            },
        ],
        "permissions": SYSTEM_MANAGER_PERMS,
    })

    ensure_doctype({
        "doctype": "DocType",
        "name": "LP Picking Model",
        "module": "Load Planner",
        "custom": 1,
        "autoname": "field:model_name",
        "title_field": "model_name",
        "track_changes": 1,
        "fields": [
            {
                "fieldname": "model_name",
                "label": "Kommissioniermodell",
                "fieldtype": "Data",
                "reqd": 1,
                "in_list_view": 1,
            },
            {
                "fieldname": "picking_group",
                "label": "Kommissioniergruppe",
                "fieldtype": "Link",
                "options": "LP Picking Group",
                "in_list_view": 1,
            },
            {
                "fieldname": "primary_package_type",
                "label": "Gebindeart 1",
                "fieldtype": "Link",
                "options": "LP Package Type",
                "in_list_view": 1,
            },
            {
                "fieldname": "secondary_package_type",
                "label": "Gebindeart 2",
                "fieldtype": "Link",
                "options": "LP Package Type",
                "in_list_view": 1,
            },
            {
                "fieldname": "use_fachlogic",
                "label": "Fachlogik verwenden",
                "fieldtype": "Check",
                "default": 1,
                "in_list_view": 1,
            },
            {
                "fieldname": "is_active",
                "label": "Aktiv",
                "fieldtype": "Check",
                "default": 1,
                "in_list_view": 1,
            },
        ],
        "permissions": SYSTEM_MANAGER_PERMS,
    })

    ensure_doctype({
        "doctype": "DocType",
        "name": "LP Package Compartment",
        "module": "Load Planner",
        "custom": 1,
        "istable": 1,
        "editable_grid": 1,
        "fields": [
            {
                "fieldname": "compartment_no",
                "label": "Fach",
                "fieldtype": "Data",
                "in_list_view": 1,
            },
            {
                "fieldname": "assigned_qty",
                "label": "Menge im Fach",
                "fieldtype": "Int",
                "in_list_view": 1,
            },
            {
                "fieldname": "note",
                "label": "Notiz",
                "fieldtype": "Small Text",
            },
        ],
    })

    ensure_doctype({
        "doctype": "DocType",
        "name": "LP Package",
        "module": "Load Planner",
        "custom": 1,
        "autoname": "hash",
        "title_field": "package_no",
        "track_changes": 1,
        "fields": [
            {
                "fieldname": "package_no",
                "label": "Gebinde",
                "fieldtype": "Data",
                "read_only": 1,
                "in_list_view": 1,
            },
            {
                "fieldname": "package_plan",
                "label": "Gebindeplan",
                "fieldtype": "Link",
                "options": "LP Package Plan",
                "read_only": 1,
                "in_list_view": 1,
            },
            {
                "fieldname": "sales_invoice",
                "label": "Sales Invoice",
                "fieldtype": "Link",
                "options": "Sales Invoice",
                "read_only": 1,
            },
            {
                "fieldname": "customer",
                "label": "Kunde",
                "fieldtype": "Link",
                "options": "Customer",
                "read_only": 1,
            },
            {
                "fieldname": "package_type",
                "label": "Gebindeart",
                "fieldtype": "Data",
                "read_only": 1,
                "in_list_view": 1,
            },
            {
                "fieldname": "item_code",
                "label": "Artikel",
                "fieldtype": "Link",
                "options": "Item",
                "read_only": 1,
            },
            {
                "fieldname": "item_name",
                "label": "Artikelname",
                "fieldtype": "Data",
                "read_only": 1,
            },
            {
                "fieldname": "assigned_qty",
                "label": "Menge im Gebinde",
                "fieldtype": "Int",
                "read_only": 1,
            },
            {
                "fieldname": "capacity_qty",
                "label": "Gebindekapazität",
                "fieldtype": "Int",
                "read_only": 1,
            },
            {
                "fieldname": "is_partial",
                "label": "Teilgebinde",
                "fieldtype": "Check",
                "read_only": 1,
            },
            {
                "fieldname": "note",
                "label": "Notiz",
                "fieldtype": "Small Text",
                "read_only": 1,
            },
            {
                "fieldname": "compartments_section",
                "label": "Fächer",
                "fieldtype": "Section Break",
            },
            {
                "fieldname": "compartments",
                "label": "Fächer",
                "fieldtype": "Table",
                "options": "LP Package Compartment",
            },
        ],
        "permissions": SYSTEM_MANAGER_PERMS,
    })

    ensure_doctype({
        "doctype": "DocType",
        "name": "LP Package Plan Row",
        "module": "Load Planner",
        "custom": 1,
        "istable": 1,
        "editable_grid": 1,
        "fields": [
            {
                "fieldname": "package_no",
                "label": "Gebinde",
                "fieldtype": "Data",
                "in_list_view": 1,
            },
            {
                "fieldname": "package_doc",
                "label": "Gebindedokument",
                "fieldtype": "Link",
                "options": "LP Package",
                "in_list_view": 1,
            },
            {
                "fieldname": "item_code",
                "label": "Artikel",
                "fieldtype": "Link",
                "options": "Item",
                "in_list_view": 1,
            },
            {
                "fieldname": "item_name",
                "label": "Artikelname",
                "fieldtype": "Data",
            },
            {
                "fieldname": "package_type",
                "label": "Gebindeart",
                "fieldtype": "Data",
                "in_list_view": 1,
            },
            {
                "fieldname": "assigned_qty",
                "label": "Menge im Gebinde",
                "fieldtype": "Int",
                "in_list_view": 1,
            },
            {
                "fieldname": "capacity_qty",
                "label": "Gebindekapazität",
                "fieldtype": "Int",
            },
            {
                "fieldname": "is_partial",
                "label": "Teilgebinde",
                "fieldtype": "Check",
            },
            {
                "fieldname": "note",
                "label": "Notiz",
                "fieldtype": "Small Text",
            },
        ],
    })

    ensure_doctype({
        "doctype": "DocType",
        "name": "LP Package Plan",
        "module": "Load Planner",
        "custom": 1,
        "autoname": "hash",
        "title_field": "plan_title",
        "track_changes": 1,
        "fields": [
            {
                "fieldname": "plan_title",
                "label": "Gebindeplan",
                "fieldtype": "Data",
                "read_only": 1,
                "in_list_view": 1,
            },
            {
                "fieldname": "sales_invoice",
                "label": "Sales Invoice",
                "fieldtype": "Link",
                "options": "Sales Invoice",
                "read_only": 1,
                "in_list_view": 1,
            },
            {
                "fieldname": "customer",
                "label": "Kunde",
                "fieldtype": "Link",
                "options": "Customer",
                "read_only": 1,
                "in_list_view": 1,
            },
            {
                "fieldname": "picking_group",
                "label": "Kommissioniergruppe",
                "fieldtype": "Data",
                "read_only": 1,
            },
            {
                "fieldname": "picking_model",
                "label": "Kommissioniermodell",
                "fieldtype": "Data",
                "read_only": 1,
            },
            {
                "fieldname": "status",
                "label": "Status",
                "fieldtype": "Select",
                "options": "Entwurf\nBerechnet",
                "default": "Entwurf",
                "in_list_view": 1,
            },
            {
                "fieldname": "summary_section",
                "label": "Zusammenfassung",
                "fieldtype": "Section Break",
            },
            {
                "fieldname": "total_pallets",
                "label": "Anzahl Paletten",
                "fieldtype": "Int",
                "read_only": 1,
            },
            {
                "fieldname": "total_rollcontainers",
                "label": "Anzahl Rollcontainer",
                "fieldtype": "Int",
                "read_only": 1,
            },
            {
                "fieldname": "total_fachcontainers",
                "label": "Anzahl Fachcontainer",
                "fieldtype": "Int",
                "read_only": 1,
            },
            {
                "fieldname": "summary",
                "label": "Gebindezusammenfassung",
                "fieldtype": "Small Text",
                "read_only": 1,
            },
            {
                "fieldname": "packages_section",
                "label": "Gebinde",
                "fieldtype": "Section Break",
            },
            {
                "fieldname": "packages",
                "label": "Gebindezeilen",
                "fieldtype": "Table",
                "options": "LP Package Plan Row",
            },
        ],
        "permissions": SYSTEM_MANAGER_PERMS,
    })
