from load_planner.setup.custom_doctypes import create_load_planner_doctypes
from load_planner.setup.custom_fields import create_load_planner_custom_fields
from load_planner.setup.default_records import create_default_records
from load_planner.setup.workspace import create_or_update_workspace


def after_install():
    create_load_planner_doctypes()
    create_load_planner_custom_fields()
    create_default_records()
    create_or_update_workspace()


def after_migrate():
    create_load_planner_doctypes()
    create_load_planner_custom_fields()
    create_default_records()
    create_or_update_workspace()
