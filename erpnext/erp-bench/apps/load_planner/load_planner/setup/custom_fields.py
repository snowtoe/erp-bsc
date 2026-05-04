from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def get_custom_fields():
    return {
        "Customer": [
            {
                "fieldname": "lp_load_planning_section",
                "label": "Load Planning",
                "fieldtype": "Section Break",
                "insert_after": "customer_name"
            },
            {
                "fieldname": "lp_picking_group",
                "label": "Kommissioniergruppe",
                "fieldtype": "Link",
                "options": "LP Picking Group",
                "insert_after": "lp_load_planning_section"
            },
            {
                "fieldname": "lp_picking_model",
                "label": "Kommissioniermodell",
                "fieldtype": "Link",
                "options": "LP Picking Model",
                "insert_after": "lp_picking_group"
            },
            {
                "fieldname": "lp_has_forklift",
                "label": "Hat Gabelstapler",
                "fieldtype": "Check",
                "insert_after": "lp_picking_model"
            },
            {
                "fieldname": "lp_primary_package_type",
                "label": "Bevorzugtes Hauptgebinde",
                "fieldtype": "Link",
                "options": "LP Package Type",
                "insert_after": "lp_has_forklift"
            },
            {
                "fieldname": "lp_secondary_package_type",
                "label": "Sekundärgebinde",
                "fieldtype": "Link",
                "options": "LP Package Type",
                "insert_after": "lp_primary_package_type"
            },
        ],
        "Item": [
            {
                "fieldname": "lp_load_planning_section",
                "label": "Load Planning",
                "fieldtype": "Section Break",
                "insert_after": "item_group"
            },
            {
                "fieldname": "lp_length_mm",
                "label": "Länge (mm)",
                "fieldtype": "Float",
                "insert_after": "lp_load_planning_section"
            },
            {
                "fieldname": "lp_width_mm",
                "label": "Breite (mm)",
                "fieldtype": "Float",
                "insert_after": "lp_length_mm"
            },
            {
                "fieldname": "lp_height_mm",
                "label": "Höhe (mm)",
                "fieldtype": "Float",
                "insert_after": "lp_width_mm"
            },
            {
                "fieldname": "lp_weight_kg",
                "label": "Gewicht (kg)",
                "fieldtype": "Float",
                "insert_after": "lp_height_mm"
            },
        ],
        "Sales Invoice": [
            {
                "fieldname": "lp_load_planning_section",
                "label": "Load Planning",
                "fieldtype": "Section Break",
                "insert_after": "customer"
            },
            {
                "fieldname": "lp_package_plan",
                "label": "Gebindeplan",
                "fieldtype": "Link",
                "options": "LP Package Plan",
                "read_only": 1,
                "insert_after": "lp_load_planning_section"
            },
            {
                "fieldname": "lp_picking_group_used",
                "label": "Verwendete Kommissioniergruppe",
                "fieldtype": "Data",
                "read_only": 1,
                "insert_after": "lp_package_plan"
            },
            {
                "fieldname": "lp_picking_model_used",
                "label": "Verwendetes Kommissioniermodell",
                "fieldtype": "Data",
                "read_only": 1,
                "insert_after": "lp_picking_group_used"
            },
            {
                "fieldname": "lp_plan_status",
                "label": "Load-Planning-Status",
                "fieldtype": "Data",
                "read_only": 1,
                "insert_after": "lp_picking_model_used"
            },
            {
                "fieldname": "lp_total_pallets",
                "label": "Anzahl Paletten",
                "fieldtype": "Int",
                "read_only": 1,
                "insert_after": "lp_plan_status"
            },
            {
                "fieldname": "lp_total_rollcontainers",
                "label": "Anzahl Rollcontainer",
                "fieldtype": "Int",
                "read_only": 1,
                "insert_after": "lp_total_pallets"
            },
            {
                "fieldname": "lp_total_fachcontainers",
                "label": "Anzahl Fachcontainer",
                "fieldtype": "Int",
                "read_only": 1,
                "insert_after": "lp_total_rollcontainers"
            },
            {
                "fieldname": "lp_plan_summary",
                "label": "Gebindezusammenfassung",
                "fieldtype": "Small Text",
                "read_only": 1,
                "insert_after": "lp_total_fachcontainers"
            },
        ],
        "Sales Invoice Item": [
            {
                "fieldname": "lp_recommended_carrier",
                "label": "Empfohlenes Gebinde",
                "fieldtype": "Data",
                "read_only": 1,
                "in_list_view": 1,
                "insert_after": "description"
            },
            {
                "fieldname": "lp_capacity_main_carrier",
                "label": "Kapazität Hauptgebinde",
                "fieldtype": "Int",
                "read_only": 1,
                "insert_after": "lp_recommended_carrier"
            },
            {
                "fieldname": "lp_full_carriers",
                "label": "Volle Gebinde",
                "fieldtype": "Int",
                "read_only": 1,
                "in_list_view": 1,
                "insert_after": "lp_capacity_main_carrier"
            },
            {
                "fieldname": "lp_fachcontainer_qty",
                "label": "Fachcontainer",
                "fieldtype": "Int",
                "read_only": 1,
                "insert_after": "lp_full_carriers"
            },
            {
                "fieldname": "lp_remainder_qty",
                "label": "Restmenge",
                "fieldtype": "Int",
                "read_only": 1,
                "insert_after": "lp_fachcontainer_qty"
            },
            {
                "fieldname": "lp_loadplanner_note",
                "label": "Load-Planning-Notiz",
                "fieldtype": "Small Text",
                "read_only": 1,
                "insert_after": "lp_remainder_qty"
            },
        ],
    }


def create_load_planner_custom_fields():
    create_custom_fields(get_custom_fields(), update=True)
