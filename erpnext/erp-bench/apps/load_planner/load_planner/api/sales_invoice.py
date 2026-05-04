import frappe


FALLBACK_PACKAGE_TYPES = {
    "Palette": {
        "name": "Palette",
        "code": "PAL",
        "package_kind": "Standard",
        "length_mm": 1200,
        "width_mm": 800,
        "max_height_mm": 1900,
        "max_weight_kg": 1200,
        "compartment_count": 1,
    },
    "Rollcontainer": {
        "name": "Rollcontainer",
        "code": "ROL",
        "package_kind": "Standard",
        "length_mm": 800,
        "width_mm": 660,
        "max_height_mm": 1450,
        "max_weight_kg": 500,
        "compartment_count": 1,
    },
    "Fachcontainer": {
        "name": "Fachcontainer",
        "code": "FAC",
        "package_kind": "Fachgebinde",
        "length_mm": 800,
        "width_mm": 660,
        "max_height_mm": 1450,
        "max_weight_kg": 500,
        "compartment_count": 4,
    },
}


def cint(value):
    try:
        return int(float(value or 0))
    except Exception:
        return 0


def cflt(value):
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def safe_set(doc, fieldname, value):
    meta = frappe.get_meta(doc.doctype)
    if meta.get_field(fieldname):
        doc.set(fieldname, value)


def rotated_fit(carrier_l, carrier_w, item_l, item_w):
    if not all([carrier_l, carrier_w, item_l, item_w]):
        return 0

    normal = int(carrier_l // item_l) * int(carrier_w // item_w)
    rotated = int(carrier_l // item_w) * int(carrier_w // item_l)
    return max(normal, rotated)


def get_package_type_settings(package_type_name):
    if not package_type_name:
        return None

    if frappe.db.exists("LP Package Type", package_type_name):
        doc = frappe.get_cached_doc("LP Package Type", package_type_name)
        return frappe._dict({
            "name": doc.name,
            "code": doc.code,
            "package_kind": doc.package_kind,
            "length_mm": cflt(doc.length_mm),
            "width_mm": cflt(doc.width_mm),
            "max_height_mm": cflt(doc.max_height_mm),
            "max_weight_kg": cflt(doc.max_weight_kg),
            "compartment_count": cint(doc.compartment_count) or 1,
        })

    fallback = FALLBACK_PACKAGE_TYPES.get(package_type_name)
    if fallback:
        return frappe._dict(fallback)

    return None


def resolve_customer_rules(customer):
    picking_group = (customer.get("lp_picking_group") or "").strip()
    picking_model_name = (customer.get("lp_picking_model") or "").strip()
    primary_name = (customer.get("lp_primary_package_type") or "").strip()
    secondary_name = (customer.get("lp_secondary_package_type") or "").strip()

    if picking_model_name and frappe.db.exists("LP Picking Model", picking_model_name):
        model = frappe.get_cached_doc("LP Picking Model", picking_model_name)

        if not picking_group:
            picking_group = model.get("picking_group") or ""

        if not primary_name:
            primary_name = model.get("primary_package_type") or ""

        if not secondary_name and cint(model.get("use_fachlogic")):
            secondary_name = model.get("secondary_package_type") or "Fachcontainer"

    if not primary_name:
        primary_name = "Palette"

    if not secondary_name:
        secondary_name = "Fachcontainer"

    if not cint(customer.get("lp_has_forklift")):
        primary_name = "Rollcontainer"

    primary = get_package_type_settings(primary_name)
    secondary = None if secondary_name == "Keine" else get_package_type_settings(secondary_name)

    return frappe._dict({
        "picking_group": picking_group,
        "picking_model": picking_model_name,
        "primary": primary,
        "secondary": secondary,
    })


def capacity_for(item_doc, carrier):
    if not carrier:
        return 0

    item_l = cflt(item_doc.get("lp_length_mm"))
    item_w = cflt(item_doc.get("lp_width_mm"))
    item_h = cflt(item_doc.get("lp_height_mm"))
    item_weight = cflt(item_doc.get("lp_weight_kg"))

    if not all([item_l, item_w, item_h, item_weight]):
        return 0

    carrier_l = cflt(carrier.length_mm)
    carrier_w = cflt(carrier.width_mm)
    carrier_h = cflt(carrier.max_height_mm)
    carrier_weight = cflt(carrier.max_weight_kg)

    per_layer = rotated_fit(carrier_l, carrier_w, item_l, item_w)
    if per_layer <= 0:
        return 0

    layers = int(carrier_h // item_h)
    if layers <= 0:
        return 0

    by_dimension = per_layer * layers
    by_weight = int(carrier_weight // item_weight)

    if by_weight <= 0:
        return 0

    return min(by_dimension, by_weight)


def package_prefix(package_type):
    if not package_type:
        return "PKG"

    if package_type.get("code"):
        return package_type.code

    return {
        "Palette": "PAL",
        "Rollcontainer": "ROL",
        "Fachcontainer": "FAC",
    }.get(package_type.name, "PKG")


def split_into_compartments(qty, compartment_count=4):
    qty = cint(qty)
    compartment_count = max(1, cint(compartment_count))

    if qty <= 0:
        return []

    base = qty // compartment_count
    remainder = qty % compartment_count

    compartments = []
    for i in range(compartment_count):
        assigned_qty = base + (1 if i < remainder else 0)
        if assigned_qty <= 0:
            continue

        compartments.append({
            "compartment_no": f"Fach {i + 1}",
            "assigned_qty": assigned_qty,
            "note": f"{assigned_qty} Stück in Fach {i + 1}",
        })

    return compartments


def build_package_rows(invoice, rules):
    package_rows = []
    summary_lines = []

    total_pallets = 0
    total_rollcontainers = 0
    total_fachcontainers = 0
    sequence = 1

    primary = rules.primary
    secondary = rules.secondary

    preferred_carrier_name = primary.name if primary else "Palette"
    secondary_name = secondary.name if secondary else "Keine"
    fach_count = secondary.compartment_count if secondary else 4

    for row in invoice.items:
        if not row.item_code:
            continue

        item_doc = frappe.get_cached_doc("Item", row.item_code)
        qty = cint(row.qty)
        capacity = capacity_for(item_doc, primary)

        if capacity <= 0:
            safe_set(row, "lp_recommended_carrier", "")
            safe_set(row, "lp_capacity_main_carrier", 0)
            safe_set(row, "lp_full_carriers", 0)
            safe_set(row, "lp_fachcontainer_qty", 0)
            safe_set(row, "lp_remainder_qty", qty)
            safe_set(row, "lp_loadplanner_note", "Fehlende oder unplausible Artikelmaße/Gewichte")
            summary_lines.append(f"{row.item_code}: keine Berechnung möglich")
            continue

        full_carriers = qty // capacity
        remainder = qty % capacity
        fachcontainers = 1 if remainder > 0 and secondary_name == "Fachcontainer" else 0

        safe_set(row, "lp_recommended_carrier", preferred_carrier_name)
        safe_set(row, "lp_capacity_main_carrier", capacity)
        safe_set(row, "lp_full_carriers", full_carriers)
        safe_set(row, "lp_fachcontainer_qty", fachcontainers)
        safe_set(row, "lp_remainder_qty", remainder)

        if remainder > 0 and fachcontainers > 0:
            note = f"{full_carriers}x {preferred_carrier_name}, Rest {remainder} im Fachcontainer"
        elif remainder > 0:
            note = f"{full_carriers}x {preferred_carrier_name}, Rest {remainder} ohne Sekundärgebinde"
        else:
            note = f"{full_carriers}x {preferred_carrier_name}"

        safe_set(row, "lp_loadplanner_note", note)

        for _ in range(full_carriers):
            package_rows.append({
                "package_no": f"{package_prefix(primary)}-{sequence}",
                "item_code": row.item_code,
                "item_name": row.item_name,
                "package_type": preferred_carrier_name,
                "assigned_qty": capacity,
                "capacity_qty": capacity,
                "is_partial": 0,
                "note": f"Vollgebinde für {row.item_code}",
                "compartments": [],
            })
            sequence += 1

        if fachcontainers > 0:
            package_rows.append({
                "package_no": f"{package_prefix(secondary)}-{sequence}",
                "item_code": row.item_code,
                "item_name": row.item_name,
                "package_type": "Fachcontainer",
                "assigned_qty": remainder,
                "capacity_qty": remainder,
                "is_partial": 1,
                "note": f"Restmenge {remainder} für {row.item_code}",
                "compartments": split_into_compartments(remainder, fach_count),
            })
            sequence += 1

        if preferred_carrier_name == "Palette":
            total_pallets += full_carriers
        elif preferred_carrier_name == "Rollcontainer":
            total_rollcontainers += full_carriers

        total_fachcontainers += fachcontainers
        summary_lines.append(f"{row.item_code}: {note}")

    summary = " | ".join(summary_lines) if summary_lines else "Keine Positionen vorhanden"

    return {
        "package_rows": package_rows,
        "summary": summary,
        "picking_group": rules.picking_group,
        "picking_model": rules.picking_model,
        "totals": {
            "pallets": total_pallets,
            "rollcontainers": total_rollcontainers,
            "fachcontainers": total_fachcontainers,
        }
    }


def delete_existing_packages(plan_name):
    package_names = frappe.get_all(
        "LP Package",
        filters={"package_plan": plan_name},
        pluck="name"
    )

    for package_name in package_names:
        frappe.delete_doc("LP Package", package_name, ignore_permissions=True, force=1)


def create_or_update_package_plan(invoice, result):
    existing_plan_name = invoice.get("lp_package_plan")

    if existing_plan_name and frappe.db.exists("LP Package Plan", existing_plan_name):
        plan = frappe.get_doc("LP Package Plan", existing_plan_name)
    else:
        plan = frappe.new_doc("LP Package Plan")

    plan.plan_title = f"Gebindeplan zu {invoice.name}"
    plan.sales_invoice = invoice.name
    plan.customer = invoice.customer
    plan.picking_group = result.get("picking_group") or ""
    plan.picking_model = result.get("picking_model") or ""
    plan.status = "Berechnet"
    plan.total_pallets = result["totals"]["pallets"]
    plan.total_rollcontainers = result["totals"]["rollcontainers"]
    plan.total_fachcontainers = result["totals"]["fachcontainers"]
    plan.summary = result["summary"]
    plan.set("packages", [])
    plan.save(ignore_permissions=True)

    delete_existing_packages(plan.name)

    created_rows = []

    for package_row in result["package_rows"]:
        package_doc = frappe.new_doc("LP Package")
        package_doc.package_no = package_row["package_no"]
        package_doc.package_plan = plan.name
        package_doc.sales_invoice = invoice.name
        package_doc.customer = invoice.customer
        package_doc.package_type = package_row["package_type"]
        package_doc.item_code = package_row["item_code"]
        package_doc.item_name = package_row["item_name"]
        package_doc.assigned_qty = package_row["assigned_qty"]
        package_doc.capacity_qty = package_row["capacity_qty"]
        package_doc.is_partial = package_row["is_partial"]
        package_doc.note = package_row["note"]

        for compartment in package_row.get("compartments", []):
            package_doc.append("compartments", compartment)

        package_doc.save(ignore_permissions=True)

        created_rows.append({
            "package_no": package_row["package_no"],
            "package_doc": package_doc.name,
            "item_code": package_row["item_code"],
            "item_name": package_row["item_name"],
            "package_type": package_row["package_type"],
            "assigned_qty": package_row["assigned_qty"],
            "capacity_qty": package_row["capacity_qty"],
            "is_partial": package_row["is_partial"],
            "note": package_row["note"],
        })

    plan.set("packages", [])
    for created_row in created_rows:
        plan.append("packages", created_row)

    plan.save(ignore_permissions=True)
    return plan.name


@frappe.whitelist()
def calculate_packages(sales_invoice_name):
    if not sales_invoice_name:
        frappe.throw("Keine Sales Invoice übergeben.")

    invoice = frappe.get_doc("Sales Invoice", sales_invoice_name)

    if not invoice.customer:
        frappe.throw("Bitte zuerst einen Kunden auswählen.")

    customer = frappe.get_cached_doc("Customer", invoice.customer)
    rules = resolve_customer_rules(customer)

    result = build_package_rows(invoice, rules)
    plan_name = create_or_update_package_plan(invoice, result)

    safe_set(invoice, "lp_package_plan", plan_name)
    safe_set(invoice, "lp_picking_group_used", result.get("picking_group") or "")
    safe_set(invoice, "lp_picking_model_used", result.get("picking_model") or "")
    safe_set(invoice, "lp_plan_status", "Berechnet")
    safe_set(invoice, "lp_total_pallets", result["totals"]["pallets"])
    safe_set(invoice, "lp_total_rollcontainers", result["totals"]["rollcontainers"])
    safe_set(invoice, "lp_total_fachcontainers", result["totals"]["fachcontainers"])
    safe_set(invoice, "lp_plan_summary", result["summary"])

    invoice.save(ignore_permissions=True)

    return {
        "status": "success",
        "summary": result["summary"],
        "plan_name": plan_name,
        "totals": result["totals"],
        "picking_group": result.get("picking_group") or "",
        "picking_model": result.get("picking_model") or "",
    }
