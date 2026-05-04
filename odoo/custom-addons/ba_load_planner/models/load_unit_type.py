from odoo import fields, models


class BaLoadUnitType(models.Model):
    _name = "ba.load.unit.type"
    _description = "Gebindeart"
    _order = "name"

    name = fields.Char(string="Bezeichnung", required=True)
    code = fields.Char(string="Code", required=True)
    kind = fields.Selection(
        [
            ("standard", "Standard"),
            ("compartment", "Fachgebinde"),
        ],
        string="Typ",
        required=True,
        default="standard",
    )

    length_cm = fields.Float(string="Länge (cm)")
    width_cm = fields.Float(string="Breite (cm)")
    max_height = fields.Float(string="Max. Höhe (cm)")
    max_volume = fields.Float(string="Max. Volumen (m³)")
    tare_weight = fields.Float(string="Eigengewicht (kg)")
    max_weight = fields.Float(string="Max. Nutzlast (kg)")
    max_compartments = fields.Integer(string="Max. Fächer")
    active = fields.Boolean(string="Aktiv", default=True)
    note = fields.Text(string="Beschreibung")

    _sql_constraints = [
        ("ba_load_unit_type_code_uniq", "unique(code)", "Der Code muss eindeutig sein."),
    ]
