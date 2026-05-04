import frappe


def upsert_named_doc(doctype, name_field, values):
    doc_name = values[name_field]

    if frappe.db.exists(doctype, doc_name):
        doc = frappe.get_doc(doctype, doc_name)
    else:
        doc = frappe.new_doc(doctype)

    for key, value in values.items():
        setattr(doc, key, value)

    doc.save(ignore_permissions=True)


def create_default_records():
    package_types = [
        {
            "package_type_name": "Palette",
            "code": "PAL",
            "package_kind": "Standard",
            "length_mm": 1200,
            "width_mm": 800,
            "max_height_mm": 1900,
            "max_weight_kg": 1200,
            "compartment_count": 1,
            "is_active": 1,
        },
        {
            "package_type_name": "Rollcontainer",
            "code": "ROL",
            "package_kind": "Standard",
            "length_mm": 800,
            "width_mm": 660,
            "max_height_mm": 1450,
            "max_weight_kg": 500,
            "compartment_count": 1,
            "is_active": 1,
        },
        {
            "package_type_name": "Fachcontainer",
            "code": "FAC",
            "package_kind": "Fachgebinde",
            "length_mm": 800,
            "width_mm": 660,
            "max_height_mm": 1450,
            "max_weight_kg": 500,
            "compartment_count": 4,
            "is_active": 1,
        },
    ]

    picking_groups = [
        {"group_name": "Trocken", "is_active": 1},
        {"group_name": "Kühl", "is_active": 1},
    ]

    picking_models = [
        {
            "model_name": "Standard Trocken",
            "picking_group": "Trocken",
            "primary_package_type": "Palette",
            "secondary_package_type": "Fachcontainer",
            "use_fachlogic": 1,
            "is_active": 1,
        },
        {
            "model_name": "Standard Kühl",
            "picking_group": "Kühl",
            "primary_package_type": "Rollcontainer",
            "secondary_package_type": "Fachcontainer",
            "use_fachlogic": 1,
            "is_active": 1,
        },
    ]

    for row in package_types:
        upsert_named_doc("LP Package Type", "package_type_name", row)

    for row in picking_groups:
        upsert_named_doc("LP Picking Group", "group_name", row)

    for row in picking_models:
        upsert_named_doc("LP Picking Model", "model_name", row)

    frappe.db.commit()
