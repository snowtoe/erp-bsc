from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    ba_height = fields.Float(string="Artikelhöhe")
