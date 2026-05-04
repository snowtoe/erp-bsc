from odoo import fields, models


class BaCommissionGroup(models.Model):
    _name = "ba.commission.group"
    _description = "Kommissioniergruppe"
    _order = "name"

    name = fields.Char(string="Bezeichnung", required=True)
    code = fields.Char(string="Code", required=True)
    active = fields.Boolean(string="Aktiv", default=True)
    note = fields.Text(string="Beschreibung")

    _sql_constraints = [
        ("ba_commission_group_code_uniq", "unique(code)", "Der Code muss eindeutig sein."),
    ]
