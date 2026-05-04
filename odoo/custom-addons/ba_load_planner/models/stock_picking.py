from math import floor

from odoo import fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    ba_commission_group_id = fields.Many2one(
        "ba.commission.group",
        string="Kommissioniergruppe",
        ondelete="restrict",
    )
    ba_tour_code = fields.Char(string="Tourcode")
    ba_delivery_date = fields.Date(string="Liefertag")
    ba_load_plan_ids = fields.One2many("ba.load.plan", "picking_id", string="Gebindepläne")
    ba_load_plan_count = fields.Integer(string="Anzahl Gebindepläne", compute="_compute_ba_load_plan_count")

    def _compute_ba_load_plan_count(self):
        for rec in self:
            rec.ba_load_plan_count = len(rec.ba_load_plan_ids)

    def action_view_ba_load_plans(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Gebindepläne",
            "res_model": "ba.load.plan",
            "view_mode": "list,form",
            "domain": [("picking_id", "=", self.id)],
            "context": {"default_picking_id": self.id},
        }

    def _find_commission_model(self, commission_group, partner):
        self.ensure_one()
        model_obj = self.env["ba.commission.model"]

        model = model_obj.search(
            [
                ("active", "=", True),
                ("commission_group_id", "=", commission_group.id),
                ("partner_id", "=", partner.id),
            ],
            limit=1,
        )
        if model:
            return model

        return model_obj.search(
            [
                ("active", "=", True),
                ("commission_group_id", "=", commission_group.id),
                ("partner_id", "=", False),
            ],
            limit=1,
        )

    def _get_customer_main_load_unit_type(self, partner, commission_model):
        preferred = partner.ba_preferred_main_load_unit_type_id or commission_model.primary_load_unit_type_id
        if not preferred:
            raise UserError("Für den Kunden bzw. das Kommissioniermodell ist kein Hauptgebinde hinterlegt.")

        if preferred.kind != "standard":
            raise UserError("Das Hauptgebinde des Kunden darf kein Fachgebinde sein.")

        if not partner.ba_has_forklift:
            code = (preferred.code or "").upper()
            name = (preferred.name or "").lower()
            if code != "ROL" and "roll" not in name:
                raise UserError(
                    "Kunden ohne Gabelstapler müssen als Hauptgebinde einen Rollcontainer haben."
                )
        return preferred

    def _create_standard_unit(self, plan, partner, load_unit_type, sequence):
        load_unit = self.env["ba.load.unit"].create(
            {
                "name": f"{load_unit_type.code}-{sequence}",
                "plan_id": plan.id,
                "sequence": sequence * 10,
                "load_unit_type_id": load_unit_type.id,
                "partner_id": partner.id,
                "state": "draft",
            }
        )
        compartment = self.env["ba.load.compartment"].create(
            {
                "name": "Fach 1",
                "load_unit_id": load_unit.id,
                "sequence": 10,
                "partner_id": partner.id,
            }
        )
        return {
            "load_unit": load_unit,
            "compartment": compartment,
            "remaining_volume": load_unit_type.max_volume if load_unit_type.max_volume > 0 else None,
            "remaining_weight": load_unit_type.max_weight if load_unit_type.max_weight > 0 else None,
            "used_volume": 0.0,
            "used_weight": 0.0,
            "highest_height": 0.0,
        }

    def _create_compartment_container(self, plan, partner, load_unit_type, sequence):
        load_unit = self.env["ba.load.unit"].create(
            {
                "name": f"{load_unit_type.code}-{sequence}",
                "plan_id": plan.id,
                "sequence": sequence * 10,
                "load_unit_type_id": load_unit_type.id,
                "partner_id": partner.id,
                "state": "draft",
            }
        )
        return {
            "load_unit": load_unit,
            "compartments": [],
            "used_volume": 0.0,
            "used_weight": 0.0,
        }

    def _update_compartment_metrics(self, compartment, commission_model):
        items = compartment.item_ids
        used_volume = sum(items.mapped("volume"))
        highest_height = max(items.mapped("article_height")) if items else 0.0
        level_count = 1 if highest_height > 0 else 0
        loss_volume = commission_model.loss_volume_per_level * level_count if level_count else 0.0

        compartment.write(
            {
                "used_volume": used_volume,
                "highest_article_height": highest_height,
                "level_count": level_count,
                "loss_volume": loss_volume,
            }
        )
        return used_volume + loss_volume

    def _can_spec_fit_in_compartment(self, spec, compartment_type, commission_model):
        max_compartments = commission_model.max_compartments or compartment_type.max_compartments or 4
        compartment_limit = commission_model.compartment_volume_limit or (
            (compartment_type.max_volume / max_compartments)
            if compartment_type.max_volume and max_compartments
            else 0.0
        )

        line_volume = spec["line_volume"]
        line_weight = spec["line_weight"]

        if compartment_limit > 0 and line_volume > compartment_limit + 1e-9:
            return False

        if compartment_type.max_weight > 0 and line_weight > compartment_type.max_weight + 1e-9:
            return False

        return True

    def _allocate_specs_to_compartment_containers(
        self, plan, partner, compartment_type, commission_model, specs, start_sequence
    ):
        if not specs:
            return [], start_sequence

        containers = []
        sequence = start_sequence
        max_compartments = commission_model.max_compartments or compartment_type.max_compartments or 4
        compartment_limit = commission_model.compartment_volume_limit or (
            (compartment_type.max_volume / max_compartments)
            if compartment_type.max_volume and max_compartments
            else 0.0
        )

        def new_container():
            nonlocal sequence
            container = self._create_compartment_container(plan, partner, compartment_type, sequence)
            containers.append(container)
            sequence += 1
            return container

        for spec in specs:
            remaining_qty = spec["qty"]
            unit_volume = spec["unit_volume"]
            unit_weight = spec["unit_weight"]
            unit_height = spec["unit_height"]
            product = spec["product"]
            uom = spec["move"].product_uom

            while remaining_qty > 0:
                target_container = None
                target_compartment = None
                qty_to_assign = 0

                for container in containers:
                    container_free_volume = (
                        compartment_type.max_volume - container["used_volume"]
                        if compartment_type.max_volume > 0
                        else None
                    )
                    container_free_weight = (
                        compartment_type.max_weight - container["used_weight"]
                        if compartment_type.max_weight > 0
                        else None
                    )

                    for comp in container["compartments"]:
                        comp_free_volume = compartment_limit - comp["used_volume"] if compartment_limit > 0 else None

                        max_by_compartment = remaining_qty
                        max_by_container_volume = remaining_qty
                        max_by_container_weight = remaining_qty

                        if comp_free_volume is not None and unit_volume > 0:
                            max_by_compartment = floor((comp_free_volume + 1e-9) / unit_volume)
                        if container_free_volume is not None and unit_volume > 0:
                            max_by_container_volume = floor((container_free_volume + 1e-9) / unit_volume)
                        if container_free_weight is not None and unit_weight > 0:
                            max_by_container_weight = floor((container_free_weight + 1e-9) / unit_weight)

                        possible = min(
                            remaining_qty,
                            max_by_compartment,
                            max_by_container_volume,
                            max_by_container_weight,
                        )
                        if unit_volume == 0 and unit_weight == 0:
                            possible = remaining_qty

                        if possible > 0:
                            target_container = container
                            target_compartment = comp
                            qty_to_assign = possible
                            break

                    if target_compartment:
                        break

                    if len(container["compartments"]) < max_compartments:
                        container_free_volume = (
                            compartment_type.max_volume - container["used_volume"]
                            if compartment_type.max_volume > 0
                            else None
                        )
                        container_free_weight = (
                            compartment_type.max_weight - container["used_weight"]
                            if compartment_type.max_weight > 0
                            else None
                        )

                        max_by_compartment = remaining_qty
                        max_by_container_volume = remaining_qty
                        max_by_container_weight = remaining_qty

                        if compartment_limit > 0 and unit_volume > 0:
                            max_by_compartment = floor((compartment_limit + 1e-9) / unit_volume)
                        if container_free_volume is not None and unit_volume > 0:
                            max_by_container_volume = floor((container_free_volume + 1e-9) / unit_volume)
                        if container_free_weight is not None and unit_weight > 0:
                            max_by_container_weight = floor((container_free_weight + 1e-9) / unit_weight)

                        possible = min(
                            remaining_qty,
                            max_by_compartment,
                            max_by_container_volume,
                            max_by_container_weight,
                        )
                        if unit_volume == 0 and unit_weight == 0:
                            possible = remaining_qty

                        if possible > 0:
                            rec = self.env["ba.load.compartment"].create(
                                {
                                    "name": f"Fach {len(container['compartments']) + 1}",
                                    "load_unit_id": container["load_unit"].id,
                                    "sequence": (len(container["compartments"]) + 1) * 10,
                                    "partner_id": partner.id,
                                }
                            )
                            comp = {"record": rec, "used_volume": 0.0}
                            container["compartments"].append(comp)
                            target_container = container
                            target_compartment = comp
                            qty_to_assign = possible
                            break

                if not target_compartment:
                    container = new_container()
                    rec = self.env["ba.load.compartment"].create(
                        {
                            "name": "Fach 1",
                            "load_unit_id": container["load_unit"].id,
                            "sequence": 10,
                            "partner_id": partner.id,
                        }
                    )
                    comp = {"record": rec, "used_volume": 0.0}
                    container["compartments"].append(comp)
                    target_container = container
                    target_compartment = comp

                    max_by_compartment = remaining_qty
                    max_by_container_volume = remaining_qty
                    max_by_container_weight = remaining_qty

                    if compartment_limit > 0 and unit_volume > 0:
                        max_by_compartment = floor((compartment_limit + 1e-9) / unit_volume)
                    if compartment_type.max_volume > 0 and unit_volume > 0:
                        max_by_container_volume = floor((compartment_type.max_volume + 1e-9) / unit_volume)
                    if compartment_type.max_weight > 0 and unit_weight > 0:
                        max_by_container_weight = floor((compartment_type.max_weight + 1e-9) / unit_weight)

                    qty_to_assign = min(
                        remaining_qty,
                        max_by_compartment,
                        max_by_container_volume,
                        max_by_container_weight,
                    )
                    if unit_volume == 0 and unit_weight == 0:
                        qty_to_assign = remaining_qty

                    if qty_to_assign <= 0:
                        raise UserError(
                            f"Artikel {product.display_name} passt mit den aktuellen Fachcontainer-Grenzen in kein Fach."
                        )

                line_volume = qty_to_assign * unit_volume
                line_weight = qty_to_assign * unit_weight

                self.env["ba.load.item"].create(
                    {
                        "compartment_id": target_compartment["record"].id,
                        "product_id": product.id,
                        "quantity": qty_to_assign,
                        "uom_id": uom.id,
                        "volume": line_volume,
                        "weight": line_weight,
                        "article_height": unit_height,
                    }
                )

                target_compartment["used_volume"] += line_volume
                target_container["used_volume"] += line_volume
                target_container["used_weight"] += line_weight
                remaining_qty -= qty_to_assign

        for container in containers:
            total_container_volume = 0.0
            for comp in container["compartments"]:
                total_container_volume += self._update_compartment_metrics(comp["record"], commission_model)

            container["load_unit"].write(
                {
                    "volume": total_container_volume,
                    "weight": container["used_weight"],
                    "state": "calculated",
                }
            )

        return containers, sequence

    def action_compute_load_plan(self):
        self.ensure_one()

        if self.state == "cancel":
            raise UserError("Für stornierte Lieferungen kann kein Gebindeplan berechnet werden.")

        moves = self.move_ids.filtered(lambda m: m.product_uom_qty > 0)
        if not moves:
            raise UserError("Es wurden keine Lieferpositionen mit Menge gefunden.")

        partner = self.partner_id
        if not partner:
            raise UserError("Die Lieferung hat keinen Kunden.")

        commission_group = self.ba_commission_group_id or partner.ba_commission_group_id
        if not commission_group:
            raise UserError("Bitte eine Kommissioniergruppe auf der Lieferung oder beim Kunden hinterlegen.")

        commission_model = self._find_commission_model(commission_group, partner)
        if not commission_model:
            raise UserError("Es wurde kein passendes Kommissioniermodell gefunden.")

        main_type = self._get_customer_main_load_unit_type(partner, commission_model)
        compartment_type = commission_model.secondary_load_unit_type_id

        compartment_enabled = (
            commission_model.use_compartment_logic
            and compartment_type
            and compartment_type.kind == "compartment"
        )

        all_specs = []
        total_volume = 0.0
        total_weight = 0.0

        for move in moves:
            product = move.product_id
            qty = move.product_uom_qty
            unit_volume = product.volume or 0.0
            unit_weight = product.weight or 0.0
            unit_height = product.product_tmpl_id.ba_height or 0.0
            line_volume = qty * unit_volume
            line_weight = qty * unit_weight

            spec = {
                "move": move,
                "product": product,
                "qty": qty,
                "unit_volume": unit_volume,
                "unit_weight": unit_weight,
                "unit_height": unit_height,
                "line_volume": line_volume,
                "line_weight": line_weight,
            }
            all_specs.append(spec)
            total_volume += line_volume
            total_weight += line_weight

        small_specs = []
        standard_specs = []

        for spec in all_specs:
            is_small = (
                compartment_enabled
                and commission_model.small_quantity_threshold > 0
                and spec["line_volume"] <= commission_model.small_quantity_threshold
            )

            if is_small and self._can_spec_fit_in_compartment(spec, compartment_type, commission_model):
                small_specs.append(spec)
            else:
                standard_specs.append(spec)

        plan_name = f"LP-{self.name}-{fields.Datetime.now().strftime('%Y%m%d%H%M%S')}"
        plan = self.env["ba.load.plan"].create(
            {
                "name": plan_name,
                "picking_id": self.id,
                "partner_id": partner.id,
                "commission_group_id": commission_group.id,
                "commission_model_id": commission_model.id,
                "tour_code": self.ba_tour_code,
                "delivery_date": self.ba_delivery_date or self.scheduled_date.date() if self.scheduled_date else False,
                "state": "draft",
                "total_volume": total_volume,
                "total_weight": total_weight,
            }
        )

        standard_units = []
        next_sequence = 1
        residual_specs = []

        if standard_specs:
            if not main_type.max_volume and not main_type.max_weight:
                raise UserError("Das Hauptgebinde benötigt mindestens Maximalvolumen oder Maximalgewicht.")

            standard_total_volume = sum(x["line_volume"] for x in standard_specs)
            standard_total_weight = sum(x["line_weight"] for x in standard_specs)

            if compartment_enabled and main_type.max_volume > 0:
                fill_ratio = standard_total_volume / main_type.max_volume if main_type.max_volume else 0.0
                if fill_ratio < (commission_model.min_main_fill_ratio or 0.0):
                    compartment_eligible = []
                    still_standard = []

                    for spec in standard_specs:
                        if self._can_spec_fit_in_compartment(spec, compartment_type, commission_model):
                            compartment_eligible.append(spec)
                        else:
                            still_standard.append(spec)

                    residual_specs = compartment_eligible
                    standard_specs = still_standard
                    standard_total_volume = sum(x["line_volume"] for x in standard_specs)
                    standard_total_weight = sum(x["line_weight"] for x in standard_specs)

            if standard_specs:
                if compartment_enabled:
                    by_volume = floor(standard_total_volume / main_type.max_volume) if main_type.max_volume > 0 else 0
                    by_weight = floor(standard_total_weight / main_type.max_weight) if main_type.max_weight > 0 else 0

                    if main_type.max_volume > 0 and main_type.max_weight > 0:
                        full_standard_unit_count = min(by_volume, by_weight)
                    else:
                        full_standard_unit_count = max(by_volume, by_weight)

                    if full_standard_unit_count <= 0:
                        compartment_eligible = []
                        still_standard = []

                        for spec in standard_specs:
                            if self._can_spec_fit_in_compartment(spec, compartment_type, commission_model):
                                compartment_eligible.append(spec)
                            else:
                                still_standard.append(spec)

                        residual_specs.extend(compartment_eligible)
                        standard_specs = still_standard
                    else:
                        for _i in range(1, full_standard_unit_count + 1):
                            standard_units.append(self._create_standard_unit(plan, partner, main_type, next_sequence))
                            next_sequence += 1

                if not standard_units and standard_specs:
                    standard_units.append(self._create_standard_unit(plan, partner, main_type, next_sequence))
                    next_sequence += 1

        if standard_specs:
            for spec in standard_specs:
                remaining_qty = spec["qty"]
                product = spec["product"]
                unit_volume = spec["unit_volume"]
                unit_weight = spec["unit_weight"]
                unit_height = spec["unit_height"]
                uom = spec["move"].product_uom

                while remaining_qty > 0:
                    target = None
                    qty_to_assign = 0

                    for candidate in standard_units:
                        max_by_volume = remaining_qty
                        max_by_weight = remaining_qty

                        if candidate["remaining_volume"] is not None and unit_volume > 0:
                            max_by_volume = floor((candidate["remaining_volume"] + 1e-9) / unit_volume)
                        if candidate["remaining_weight"] is not None and unit_weight > 0:
                            max_by_weight = floor((candidate["remaining_weight"] + 1e-9) / unit_weight)

                        possible = min(remaining_qty, max_by_volume, max_by_weight)
                        if unit_volume == 0 and unit_weight == 0:
                            possible = remaining_qty

                        if possible > 0:
                            target = candidate
                            qty_to_assign = possible
                            break

                    if not target:
                        residual_spec = {
                            "move": spec["move"],
                            "product": product,
                            "qty": remaining_qty,
                            "unit_volume": unit_volume,
                            "unit_weight": unit_weight,
                            "unit_height": unit_height,
                            "line_volume": remaining_qty * unit_volume,
                            "line_weight": remaining_qty * unit_weight,
                        }

                        if (
                            compartment_enabled
                            and self._can_spec_fit_in_compartment(residual_spec, compartment_type, commission_model)
                        ):
                            residual_specs.append(residual_spec)
                            break

                        target = self._create_standard_unit(plan, partner, main_type, next_sequence)
                        standard_units.append(target)
                        next_sequence += 1

                        if unit_volume == 0 and unit_weight == 0:
                            qty_to_assign = remaining_qty
                        else:
                            max_by_volume = remaining_qty
                            max_by_weight = remaining_qty

                            if target["remaining_volume"] is not None and unit_volume > 0:
                                max_by_volume = floor((target["remaining_volume"] + 1e-9) / unit_volume)
                            if target["remaining_weight"] is not None and unit_weight > 0:
                                max_by_weight = floor((target["remaining_weight"] + 1e-9) / unit_weight)

                            qty_to_assign = min(remaining_qty, max_by_volume, max_by_weight)

                        if qty_to_assign <= 0:
                            raise UserError(
                                f"Artikel {product.display_name} passt mit den aktuellen Hauptgebinde-Grenzen in kein Gebinde."
                            )

                    if qty_to_assign <= 0:
                        break

                    line_volume = qty_to_assign * unit_volume
                    line_weight = qty_to_assign * unit_weight

                    self.env["ba.load.item"].create(
                        {
                            "compartment_id": target["compartment"].id,
                            "product_id": product.id,
                            "quantity": qty_to_assign,
                            "uom_id": uom.id,
                            "volume": line_volume,
                            "weight": line_weight,
                            "article_height": unit_height,
                        }
                    )

                    target["used_volume"] += line_volume
                    target["used_weight"] += line_weight
                    target["highest_height"] = max(target["highest_height"], unit_height)

                    if target["remaining_volume"] is not None:
                        target["remaining_volume"] -= line_volume
                    if target["remaining_weight"] is not None:
                        target["remaining_weight"] -= line_weight

                    remaining_qty -= qty_to_assign

        for candidate in standard_units:
            level_count = 1 if candidate["highest_height"] > 0 else 0
            loss_volume = commission_model.loss_volume_per_level * level_count if level_count else 0.0

            candidate["compartment"].write(
                {
                    "used_volume": candidate["used_volume"],
                    "highest_article_height": candidate["highest_height"],
                    "level_count": level_count,
                    "loss_volume": loss_volume,
                }
            )

            candidate["load_unit"].write(
                {
                    "volume": candidate["used_volume"] + loss_volume,
                    "weight": candidate["used_weight"],
                    "state": "calculated",
                }
            )

        compartment_specs = small_specs + residual_specs
        if compartment_specs:
            if not compartment_enabled:
                raise UserError(
                    "Es gibt Klein- oder Restmengen, aber das Kommissioniermodell erlaubt keinen Fachcontainer."
                )

            self._allocate_specs_to_compartment_containers(
                plan,
                partner,
                compartment_type,
                commission_model,
                compartment_specs,
                next_sequence,
            )

        plan.write({"state": "calculated"})

        return {
            "type": "ir.actions.act_window",
            "name": "Gebindeplan",
            "res_model": "ba.load.plan",
            "res_id": plan.id,
            "view_mode": "form",
            "target": "current",
        }
