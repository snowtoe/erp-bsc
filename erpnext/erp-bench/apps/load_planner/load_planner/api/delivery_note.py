import frappe

SHOW_SUMMARY_POPUP = True


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


def get_settings():
    # Übergangslösung: später durch frappe.get_single("Load Planner Settings") ersetzen
    return frappe._dict({
        "palette_length_mm": 1200,
        "palette_width_mm": 800,
        "palette_max_height_mm": 1900,
        "palette_max_weight_kg": 1200,
        "rollcontainer_length_mm": 800,
        "rollcontainer_width_mm": 660,
        "rollcontainer_max_height_mm": 1450,
        "rollcontainer_max_weight_kg": 500,
        "fachcontainer_compartments": 4,
    })


def get_customer_preference(customer):
    if not customer:
        return "Palette"

    has_forklift = cint(customer.get("lp_has_forklift"))
    preferred = customer.get("lp_preferred_carrier") or "Palette"

    if not has_forklift:
        return "Rollcontainer"

    return preferred


def capacity_for(item_doc, carrier, settings):
    item_l = cflt(item_doc.get("lp_length_mm"))
    item_w = cflt(item_doc.get("lp_width_mm"))
    item_h = cflt(item_doc.get("lp_height_mm"))
    item_weight = cflt(item_doc.get("lp_weight_kg"))

    if not all([item_l, item_w, item_h, item_weight]):
        return 0

    if carrier == "Palette":
        carrier_l = cflt(settings.palette_length_mm)
        carrier_w = cflt(settings.palette_width_mm)
        carrier_h = cflt(settings.palette_max_height_mm)
        carrier_weight = cflt(settings.palette_max_weight_kg)
    else:
        carrier_l = cflt(settings.rollcontainer_length_mm)
        carrier_w = cflt(settings.rollcontainer_width_mm)
        carrier_h = cflt(settings.rollcontainer_max_height_mm)
        carrier_weight = cflt(settings.rollcontainer_max_weight_kg)

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


def apply_load_plan(doc, method=None):
    settings = get_settings()
    customer = frappe.get_cached_doc("Customer", doc.customer) if doc.customer else None
    preferred_carrier = get_customer_preference(customer)

    total_pallets = 0
    total_rollcontainers = 0
    total_fachcontainers = 0
    summary_lines = []

    for row in doc.items:
        if not row.item_code:
            continue

        item_doc = frappe.get_cached_doc("Item", row.item_code)
        qty = cint(row.qty)
        capacity = capacity_for(item_doc, preferred_carrier, settings)

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
        fachcontainers = 1 if remainder > 0 else 0

        safe_set(row, "lp_recommended_carrier", preferred_carrier)
        safe_set(row, "lp_capacity_main_carrier", capacity)
        safe_set(row, "lp_full_carriers", full_carriers)
        safe_set(row, "lp_fachcontainer_qty", fachcontainers)
        safe_set(row, "lp_remainder_qty", remainder)

        if remainder > 0:
            note = f"{full_carriers}x {preferred_carrier}, Rest {remainder} im Fachcontainer"
        else:
            note = f"{full_carriers}x {preferred_carrier}"

        safe_set(row, "lp_loadplanner_note", note)

        if preferred_carrier == "Palette":
            total_pallets += full_carriers
        else:
            total_rollcontainers += full_carriers

        total_fachcontainers += fachcontainers
        summary_lines.append(f"{row.item_code}: {note}")

    summary = " | ".join(summary_lines)

    safe_set(doc, "lp_total_pallets", total_pallets)
    safe_set(doc, "lp_total_rollcontainers", total_rollcontainers)
    safe_set(doc, "lp_total_fachcontainers", total_fachcontainers)
    safe_set(doc, "lp_loadplanner_summary", summary)

    if SHOW_SUMMARY_POPUP and summary:
        frappe.msgprint(f"Load Planner: {summary}")
