from odoo import fields, models


class BaLoadPlan(models.Model):
    _name = "ba.load.plan"
    _description = "Gebindeplan"
    _order = "id desc"

    name = fields.Char(string="Referenz", required=True, default="New", copy=False)
    picking_id = fields.Many2one("stock.picking", string="Lieferung", required=True, ondelete="cascade")
    partner_id = fields.Many2one("res.partner", string="Kunde", required=True)
    commission_group_id = fields.Many2one("ba.commission.group", string="Kommissioniergruppe")
    commission_model_id = fields.Many2one("ba.commission.model", string="Kommissioniermodell")
    tour_code = fields.Char(string="Tourcode")
    delivery_date = fields.Date(string="Liefertag")
    state = fields.Selection(
        [
            ("draft", "Entwurf"),
            ("calculated", "Berechnet"),
            ("confirmed", "Bestätigt"),
        ],
        string="Status",
        default="draft",
        required=True,
    )
    total_volume = fields.Float(string="Gesamtvolumen")
    total_weight = fields.Float(string="Gesamtgewicht")
    note = fields.Text(string="Beschreibung")
    load_unit_ids = fields.One2many("ba.load.unit", "plan_id", string="Gebinde")
    load_unit_count = fields.Integer(string="Gebindeanzahl", compute="_compute_load_unit_count")

    def _compute_load_unit_count(self):
        for rec in self:
            rec.load_unit_count = len(rec.load_unit_ids)


class BaLoadUnit(models.Model):
    _name = "ba.load.unit"
    _description = "Gebinde"
    _order = "plan_id, sequence, id"

    name = fields.Char(string="Gebinde", required=True)
    plan_id = fields.Many2one("ba.load.plan", string="Gebindeplan", required=True, ondelete="cascade")
    sequence = fields.Integer(string="Sequenz", default=10)
    load_unit_type_id = fields.Many2one("ba.load.unit.type", string="Gebindeart", required=True, ondelete="restrict")
    partner_id = fields.Many2one("res.partner", string="Kunde")
    state = fields.Selection(
        [
            ("draft", "Entwurf"),
            ("calculated", "Berechnet"),
            ("fixed", "Fixiert"),
        ],
        string="Status",
        default="draft",
        required=True,
    )
    volume = fields.Float(string="Volumen")
    weight = fields.Float(string="Gewicht")
    compartment_ids = fields.One2many("ba.load.compartment", "load_unit_id", string="Fächer")
    compartment_count = fields.Integer(string="Fachanzahl", compute="_compute_compartment_count")
    note = fields.Text(string="Beschreibung")

    def _compute_compartment_count(self):
        for rec in self:
            rec.compartment_count = len(rec.compartment_ids)


class BaLoadCompartment(models.Model):
    _name = "ba.load.compartment"
    _description = "Gebindefach"
    _order = "load_unit_id, sequence, id"

    name = fields.Char(string="Fach", required=True)
    load_unit_id = fields.Many2one("ba.load.unit", string="Gebinde", required=True, ondelete="cascade")
    sequence = fields.Integer(string="Sequenz", default=10)
    partner_id = fields.Many2one("res.partner", string="Kunde")
    used_volume = fields.Float(string="Belegtes Volumen")
    highest_article_height = fields.Float(string="Höchste Artikelhöhe")
    level_count = fields.Integer(string="Etagen")
    loss_volume = fields.Float(string="Verlustvolumen")
    item_ids = fields.One2many("ba.load.item", "compartment_id", string="Artikel")


class BaLoadItem(models.Model):
    _name = "ba.load.item"
    _description = "Artikel im Gebinde"
    _order = "compartment_id, id"

    compartment_id = fields.Many2one("ba.load.compartment", string="Fach", required=True, ondelete="cascade")
    product_id = fields.Many2one("product.product", string="Artikel", required=True, ondelete="restrict")
    quantity = fields.Float(string="Menge", required=True, default=1.0)
    uom_id = fields.Many2one("uom.uom", string="ME")
    volume = fields.Float(string="Volumen")
    weight = fields.Float(string="Gewicht")
    article_height = fields.Float(string="Artikelhöhe")
