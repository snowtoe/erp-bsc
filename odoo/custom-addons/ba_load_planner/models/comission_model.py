from odoo import api, fields, models
from odoo.exceptions import ValidationError


class BaCommissionModel(models.Model):
    _name = "ba.commission.model"
    _description = "Kommissioniermodell"
    _order = "name"

    name = fields.Char(string="Bezeichnung", required=True)
    commission_group_id = fields.Many2one(
        "ba.commission.group",
        string="Kommissioniergruppe",
        required=True,
        ondelete="restrict",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Kunde",
        help="Optional. Wenn leer, gilt das Modell als Standardmodell für die Kommissioniergruppe.",
    )
    primary_load_unit_type_id = fields.Many2one(
        "ba.load.unit.type",
        string="Gebindeart 1",
        required=True,
        ondelete="restrict",
    )
    secondary_load_unit_type_id = fields.Many2one(
        "ba.load.unit.type",
        string="Gebindeart 2",
        ondelete="restrict",
    )
    use_compartment_logic = fields.Boolean(
        string="Fachlogik verwenden",
        default=False,
    )
    small_quantity_threshold = fields.Float(
        string="Kleinmengen-Schwelle (m³)",
        help="Positionsvolumen bis zu dieser Schwelle wird als Kleinmenge behandelt.",
    )
    compartment_volume_limit = fields.Float(
        string="Max. Volumen pro Fach (m³)",
        help="Maximales belegbares Volumen eines einzelnen Fachs.",
    )
    max_compartments = fields.Integer(
        string="Max. Fächer",
        default=4,
    )
    min_main_fill_ratio = fields.Float(
        string="Mindestfüllgrad Hauptgebinde",
        default=0.35,
        help="Wenn die verbleibende Restmenge diesen Füllgrad eines Hauptgebindes nicht erreicht, geht sie in den Fachcontainer.",
    )
    loss_volume_per_level = fields.Float(
        string="Verlustvolumen je Etage (m³)",
        help="Zusätzlich belegtes Volumen je verwendeter Etage/Zwischenboden.",
    )
    active = fields.Boolean(string="Aktiv", default=True)
    note = fields.Text(string="Beschreibung")

    @api.constrains("primary_load_unit_type_id", "secondary_load_unit_type_id")
    def _check_distinct_load_unit_types(self):
        for rec in self:
            if (
                rec.primary_load_unit_type_id
                and rec.secondary_load_unit_type_id
                and rec.primary_load_unit_type_id == rec.secondary_load_unit_type_id
            ):
                raise ValidationError("Gebindeart 1 und Gebindeart 2 müssen unterschiedlich sein.")
