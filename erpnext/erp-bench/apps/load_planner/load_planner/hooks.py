app_name = "load_planner"
app_title = "Load Planner"
app_publisher = "lux@test.local"
app_description = "Load planning and packaging calculation"
app_email = "lux@test.local"
app_license = "mit"

doctype_js = {
    "Sales Invoice": "public/js/sales_invoice.js",
}

after_install = "load_planner.setup.install.after_install"
after_migrate = "load_planner.setup.install.after_migrate"

add_to_apps_screen = [
    {
        "name": "load_planner",
        "logo": "/assets/load_planner/load_planner_logo.svg",
        "title": "Load Planner",
        "route": "/desk",
        "has_permission": "load_planner.api.permission.has_app_permission",
    }
]
