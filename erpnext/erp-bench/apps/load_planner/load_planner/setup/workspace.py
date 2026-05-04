import json
import frappe


def create_or_update_workspace():
    workspace_name = "Load Planner"

    content = [
        {
            "id": "lp_header_1",
            "type": "header",
            "data": {
                "text": "Konfiguration",
                "col": 12
            }
        },
        {
            "id": "lp_shortcut_1",
            "type": "shortcut",
            "data": {
                "shortcut_name": "Gebindearten",
                "col": 3,
                "link_to": "LP Package Type",
                "type": "DocType"
            }
        },
        {
            "id": "lp_shortcut_2",
            "type": "shortcut",
            "data": {
                "shortcut_name": "Kommissioniergruppen",
                "col": 3,
                "link_to": "LP Picking Group",
                "type": "DocType"
            }
        },
        {
            "id": "lp_shortcut_3",
            "type": "shortcut",
            "data": {
                "shortcut_name": "Kommissioniermodelle",
                "col": 3,
                "link_to": "LP Picking Model",
                "type": "DocType"
            }
        },
        {
            "id": "lp_shortcut_4",
            "type": "shortcut",
            "data": {
                "shortcut_name": "Gebindepläne",
                "col": 3,
                "link_to": "LP Package Plan",
                "type": "DocType"
            }
        },
        {
            "id": "lp_header_2",
            "type": "header",
            "data": {
                "text": "Operativ",
                "col": 12
            }
        },
        {
            "id": "lp_shortcut_5",
            "type": "shortcut",
            "data": {
                "shortcut_name": "Gebinde",
                "col": 3,
                "link_to": "LP Package",
                "type": "DocType"
            }
        },
        {
            "id": "lp_shortcut_6",
            "type": "shortcut",
            "data": {
                "shortcut_name": "Kunden",
                "col": 3,
                "link_to": "Customer",
                "type": "DocType"
            }
        },
        {
            "id": "lp_shortcut_7",
            "type": "shortcut",
            "data": {
                "shortcut_name": "Artikel",
                "col": 3,
                "link_to": "Item",
                "type": "DocType"
            }
        },
        {
            "id": "lp_shortcut_8",
            "type": "shortcut",
            "data": {
                "shortcut_name": "Rechnungen",
                "col": 3,
                "link_to": "Sales Invoice",
                "type": "DocType"
            }
        }
    ]

    if frappe.db.exists("Workspace", workspace_name):
        ws = frappe.get_doc("Workspace", workspace_name)
    else:
        ws = frappe.new_doc("Workspace")
        ws.title = workspace_name
        ws.label = workspace_name

    ws.module = "Load Planner"
    ws.public = 1
    ws.is_hidden = 0
    ws.icon = "package"
    ws.content = json.dumps(content)

    ws.save(ignore_permissions=True)
    frappe.db.commit()
