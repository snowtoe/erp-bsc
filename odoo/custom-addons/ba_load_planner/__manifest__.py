{
    "name": "BA Load Planner",
    "version": "19.0.2.0.0",
    "summary": "Gebindefindung und Lademittel für logistische Auslieferungen",
    "description": """
Prototypisches Odoo-Modul für die Bachelorarbeit:
Gebindefindung und Lademittel.
""",
    "author": "Lux",
    "license": "LGPL-3",
    "category": "Inventory/Inventory",
    "depends": ["base", "contacts", "product", "stock", "sale"],
    "data": [
        "security/ir.model.access.csv",
        "views/load_unit_type_views.xml",
        "views/commission_group_views.xml",
        "views/commission_model_views.xml",
        "views/res_partner_views.xml",
        "views/product_template_views.xml",
        "views/load_plan_views.xml",
        "views/stock_picking_views.xml",
        "views/menu.xml",
    ],
    "application": True,
    "installable": True,
}
