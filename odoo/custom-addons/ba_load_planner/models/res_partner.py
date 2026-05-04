from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    ba_commission_group_id = fields.Many2one(
        "ba.commission.group",
        string="Kommissioniergruppe",
        ondelete="restrict",
    )

    ba_has_forklift = fields.Boolean(
        string="Hat Gabelstapler",
        default=False,
        help="Wenn deaktiviert, muss das Hauptgebinde Rollcontainer sein.",
    )

    ba_preferred_main_load_unit_type_id = fields.Many2one(
        "ba.load.unit.type",
        string="Bevorzugtes Hauptgebinde",
        domain=[("kind", "=", "standard")],
        ondelete="restrict",
        help="Palette oder Rollcontainer. Bei Kunden ohne Gabelstapler muss hier ein Rollcontainer gewählt werden.",
    )
