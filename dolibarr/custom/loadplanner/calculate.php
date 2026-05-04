<?php

$res = 0;
if (!$res && file_exists("../main.inc.php")) {
    $res = @include "../main.inc.php";
}
if (!$res && file_exists("../../main.inc.php")) {
    $res = @include "../../main.inc.php";
}

require_once DOL_DOCUMENT_ROOT . '/product/class/product.class.php';

$langs->loadLangs(array("loadplanner@loadplanner"));

if (empty($user->rights->loadplanner->read)) {
    accessforbidden();
}

function lp_length_to_mm($value, $unit)
{
    if ($value === null || $value === '') return 0;
    return ((float) $value) * pow(10, ((int) $unit) + 3);
}

function lp_weight_to_kg($value, $unit)
{
    if ($value === null || $value === '') return 0;
    return ((float) $value) * pow(10, (int) $unit);
}

function lp_get_object($db, $element, $id)
{
    if ($element === 'propal') {
        require_once DOL_DOCUMENT_ROOT . '/comm/propal/class/propal.class.php';
        $object = new Propal($db);
    } elseif ($element === 'commande') {
        require_once DOL_DOCUMENT_ROOT . '/commande/class/commande.class.php';
        $object = new Commande($db);
    } elseif ($element === 'facture') {
        require_once DOL_DOCUMENT_ROOT . '/compta/facture/class/facture.class.php';
        $object = new Facture($db);
    } else {
        return null;
    }

    if ($object->fetch($id) <= 0) {
        return null;
    }

    if (method_exists($object, 'fetch_thirdparty')) {
        $object->fetch_thirdparty();
    }

    return $object;
}

function lp_document_label($element)
{
    if ($element === 'propal') return 'Angebot';
    if ($element === 'commande') return 'Auftrag';
    if ($element === 'facture') return 'Rechnung';
    return $element;
}

function lp_document_url($element, $id)
{
    if ($element === 'propal') return DOL_URL_ROOT . '/comm/propal/card.php?id=' . ((int) $id);
    if ($element === 'commande') return DOL_URL_ROOT . '/commande/card.php?id=' . ((int) $id);
    if ($element === 'facture') return DOL_URL_ROOT . '/compta/facture/card.php?facid=' . ((int) $id);
    return '#';
}

function lp_get_customer_settings($db, $socid)
{
    global $conf;

    $settings = array(
        'has_forklift' => 0,
        'preferred_unit' => 'roll',
        'exists' => false
    );

    if ($socid <= 0) {
        return $settings;
    }

    $sql = "SELECT has_forklift, preferred_unit
            FROM " . MAIN_DB_PREFIX . "loadplanner_customer_setting
            WHERE entity = " . ((int) $conf->entity) . "
            AND fk_soc = " . ((int) $socid) . "
            LIMIT 1";

    $resql = $db->query($sql);

    if ($resql && ($obj = $db->fetch_object($resql))) {
        $settings['has_forklift'] = (int) $obj->has_forklift;
        $settings['preferred_unit'] = $obj->preferred_unit;
        $settings['exists'] = true;
    }

    return $settings;
}

function lp_save_customer_settings($db, $socid, $hasForklift, $preferredUnit)
{
    global $conf, $user;

    if ($preferredUnit !== 'palette' && $preferredUnit !== 'roll') {
        $preferredUnit = 'roll';
    }

    $sql = "INSERT INTO " . MAIN_DB_PREFIX . "loadplanner_customer_setting (
                entity,
                fk_soc,
                has_forklift,
                preferred_unit,
                datec,
                fk_user_modif
            ) VALUES (
                " . ((int) $conf->entity) . ",
                " . ((int) $socid) . ",
                " . ((int) $hasForklift) . ",
                '" . $db->escape($preferredUnit) . "',
                '" . $db->idate(dol_now()) . "',
                " . ((int) $user->id) . "
            )
            ON DUPLICATE KEY UPDATE
                has_forklift = " . ((int) $hasForklift) . ",
                preferred_unit = '" . $db->escape($preferredUnit) . "',
                fk_user_modif = " . ((int) $user->id);

    return $db->query($sql);
}

function lp_calc_capacity($lengthMm, $widthMm, $heightMm, $weightKg, $unitType)
{
    if ($lengthMm <= 0 || $widthMm <= 0 || $heightMm <= 0 || $weightKg <= 0) {
        return 0;
    }

    if ($unitType === 'palette') {
        $baseLength = 1200;
        $baseWidth = 800;
        $maxHeight = 1900;
        $maxWeight = 1200;
    } else {
        $baseLength = 1450;
        $baseWidth = 660;
        $maxHeight = 800;
        $maxWeight = 500;
    }

    $itemsPerLayerNormal = floor($baseLength / $lengthMm) * floor($baseWidth / $widthMm);
    $itemsPerLayerRotated = floor($baseLength / $widthMm) * floor($baseWidth / $lengthMm);
    $itemsPerLayer = max($itemsPerLayerNormal, $itemsPerLayerRotated);

    $layers = floor($maxHeight / $heightMm);

    $byVolume = $itemsPerLayer * $layers;
    $byWeight = floor($maxWeight / $weightKg);

    return (int) max(0, min($byVolume, $byWeight));
}

function lp_create_calculation($db, $user, $object, $element, $hasForklift, $preferredUnit)
{
    global $conf;

    $ref = 'LP-' . dol_print_date(dol_now(), '%Y%m%d%H%M%S');

    $fkSoc = !empty($object->socid) ? (int) $object->socid : 0;
    $entity = !empty($object->entity) ? (int) $object->entity : (int) $conf->entity;

    $sql = "INSERT INTO " . MAIN_DB_PREFIX . "loadplanner_calc (
        entity,
        ref,
        element_type,
        fk_element,
        fk_soc,
        datec,
        fk_user_creat,
        has_forklift,
        preferred_unit,
        total_weight,
        note
    ) VALUES (
        " . $entity . ",
        '" . $db->escape($ref) . "',
        '" . $db->escape($element) . "',
        " . ((int) $object->id) . ",
        " . $fkSoc . ",
        '" . $db->idate(dol_now()) . "',
        " . ((int) $user->id) . ",
        " . ((int) $hasForklift) . ",
        '" . $db->escape($preferredUnit) . "',
        0,
        ''
    )";

    if (!$db->query($sql)) {
        return -1;
    }

    return $db->last_insert_id(MAIN_DB_PREFIX . "loadplanner_calc");
}

function lp_insert_line($db, $fkCalc, $unitType, $unitNo, $compartmentNo, $product, $qty, $itemsPerUnit, $totalWeight, $reason)
{
    $compartmentSql = ($compartmentNo === null) ? "NULL" : ((int) $compartmentNo);

    $sql = "INSERT INTO " . MAIN_DB_PREFIX . "loadplanner_calc_line (
        fk_calc,
        unit_type,
        unit_no,
        compartment_no,
        fk_product,
        product_ref,
        product_label,
        qty,
        items_per_unit,
        total_weight,
        reason
    ) VALUES (
        " . ((int) $fkCalc) . ",
        '" . $db->escape($unitType) . "',
        " . ((int) $unitNo) . ",
        " . $compartmentSql . ",
        " . ((int) $product->id) . ",
        '" . $db->escape($product->ref) . "',
        '" . $db->escape($product->label) . "',
        " . ((float) $qty) . ",
        " . ((int) $itemsPerUnit) . ",
        " . ((float) $totalWeight) . ",
        '" . $db->escape($reason) . "'
    )";

    return $db->query($sql);
}

function lp_run_calculation($db, $user, $object, $element, $hasForklift, $preferredUnit)
{
    $fkCalc = lp_create_calculation($db, $user, $object, $element, $hasForklift, $preferredUnit);
    if ($fkCalc <= 0) {
        return -1;
    }

    $totalWeightAll = 0;
    $unitCounter = 1;

    foreach ($object->lines as $line) {
        if (empty($line->fk_product) || $line->qty <= 0) {
            continue;
        }

        $product = new Product($db);
        if ($product->fetch($line->fk_product) <= 0) {
            continue;
        }

        $qty = (int) ceil($line->qty);

        $lengthMm = lp_length_to_mm($product->length, $product->length_units);
        $widthMm = lp_length_to_mm($product->width, $product->width_units);
        $heightMm = lp_length_to_mm($product->height, $product->height_units);
        $weightKg = lp_weight_to_kg($product->weight, $product->weight_units);

        $lineWeight = $qty * $weightKg;
        $totalWeightAll += $lineWeight;

        $palletCapacity = lp_calc_capacity($lengthMm, $widthMm, $heightMm, $weightKg, 'palette');
        $rollCapacity = lp_calc_capacity($lengthMm, $widthMm, $heightMm, $weightKg, 'roll');

        $mainUnit = 'Fachcontainer';
        $mainCapacity = 0;
        $reason = '';

        if (!$hasForklift) {
            $mainUnit = 'Rollcontainer';
            $mainCapacity = $rollCapacity;
            $reason = 'Kunde verfügt über keinen Gabelstapler; daher wird Rollcontainer bevorzugt.';
        } else {
            if ($preferredUnit === 'palette') {
                $mainUnit = 'Palette';
                $mainCapacity = $palletCapacity;
                $reason = 'Kunde verfügt über einen Gabelstapler; Palette wurde als bevorzugtes Lademittel gewählt.';
            } else {
                $mainUnit = 'Rollcontainer';
                $mainCapacity = $rollCapacity;
                $reason = 'Kunde verfügt über einen Gabelstapler; Rollcontainer wurde als bevorzugtes Lademittel gewählt.';
            }
        }

        if ($mainCapacity <= 0 || $qty < $mainCapacity) {
            $perCompartment = (int) ceil($qty / 4);
            $remaining = $qty;

            for ($fach = 1; $fach <= 4; $fach++) {
                $compQty = min($perCompartment, $remaining);
                if ($compQty < 0) $compQty = 0;

                lp_insert_line(
                    $db,
                    $fkCalc,
                    'Fachcontainer',
                    $unitCounter,
                    $fach,
                    $product,
                    $compQty,
                    $perCompartment,
                    $compQty * $weightKg,
                    'Kleinmenge oder Restmenge; Verteilung auf Fachcontainer mit vier Fächern.'
                );

                $remaining -= $compQty;
                if ($remaining <= 0) {
                    $remaining = 0;
                }
            }

            $unitCounter++;
            continue;
        }

        $fullUnits = intdiv($qty, $mainCapacity);
        $restQty = $qty % $mainCapacity;

        for ($i = 1; $i <= $fullUnits; $i++) {
            lp_insert_line(
                $db,
                $fkCalc,
                $mainUnit,
                $unitCounter,
                null,
                $product,
                $mainCapacity,
                $mainCapacity,
                $mainCapacity * $weightKg,
                $reason
            );

            $unitCounter++;
        }

        if ($restQty > 0) {
            $perCompartment = (int) ceil($restQty / 4);
            $remaining = $restQty;

            for ($fach = 1; $fach <= 4; $fach++) {
                $compQty = min($perCompartment, $remaining);
                if ($compQty < 0) $compQty = 0;

                lp_insert_line(
                    $db,
                    $fkCalc,
                    'Fachcontainer',
                    $unitCounter,
                    $fach,
                    $product,
                    $compQty,
                    $perCompartment,
                    $compQty * $weightKg,
                    'Restmenge nach vollständigen Hauptlademitteln; Verteilung auf Fachcontainer mit vier Fächern.'
                );

                $remaining -= $compQty;
                if ($remaining <= 0) {
                    $remaining = 0;
                }
            }

            $unitCounter++;
        }
    }

    $sql = "UPDATE " . MAIN_DB_PREFIX . "loadplanner_calc
            SET total_weight = " . ((float) $totalWeightAll) . "
            WHERE rowid = " . ((int) $fkCalc);
    $db->query($sql);

    return $fkCalc;
}

$element = GETPOST('element', 'alpha');
$id = GETPOST('id', 'int');
$action = GETPOST('action', 'alpha');

$object = lp_get_object($db, $element, $id);

if (!$object) {
    accessforbidden('Beleg konnte nicht geladen werden.');
}

$socid = !empty($object->socid) ? (int) $object->socid : 0;
$customerSettings = lp_get_customer_settings($db, $socid);

$hasForklift = isset($_REQUEST['has_forklift']) ? GETPOST('has_forklift', 'int') : (int) $customerSettings['has_forklift'];
$preferredUnit = isset($_REQUEST['preferred_unit']) ? GETPOST('preferred_unit', 'alpha') : $customerSettings['preferred_unit'];

if ($preferredUnit !== 'palette' && $preferredUnit !== 'roll') {
    $preferredUnit = 'roll';
}

if ($action === 'confirmcalculate') {
    $saveCustomerSettings = GETPOST('save_customer_settings', 'int');

    if ($saveCustomerSettings && $socid > 0) {
        lp_save_customer_settings($db, $socid, $hasForklift, $preferredUnit);
    }

    $fkCalc = lp_run_calculation($db, $user, $object, $element, $hasForklift, $preferredUnit);

    if ($fkCalc > 0) {
        header('Location: ' . DOL_URL_ROOT . '/custom/loadplanner/card/view.php?id=' . ((int) $fkCalc));
        exit;
    } else {
        setEventMessages('Fehler bei der Gebindeberechnung.', null, 'errors');
    }
}

llxHeader('', 'Gebinde berechnen');

$backToDocument = '<a href="' . lp_document_url($element, $id) . '">Zurück zum Beleg</a>';

print load_fiche_titre('Gebinde berechnen', $backToDocument, 'generic');

print '<table class="border centpercent">';
print '<tr class="liste_titre"><td colspan="2">Ausgangsbeleg</td></tr>';
print '<tr><td class="titlefield">Belegtyp</td><td>' . dol_escape_htmltag(lp_document_label($element)) . '</td></tr>';
print '<tr><td>Referenz</td><td>' . dol_escape_htmltag($object->ref) . '</td></tr>';
print '<tr><td>Kunde</td><td>' . dol_escape_htmltag($object->thirdparty->name) . '</td></tr>';
print '</table>';

print '<br>';

print '<form method="POST" action="' . $_SERVER["PHP_SELF"] . '?element=' . urlencode($element) . '&id=' . ((int) $id) . '">';
print '<input type="hidden" name="token" value="' . newToken() . '">';
print '<input type="hidden" name="action" value="confirmcalculate">';

print '<table class="border centpercent">';
print '<tr class="liste_titre"><td colspan="2">Berechnungsparameter</td></tr>';

if (!$customerSettings['exists']) {
    print '<tr><td colspan="2"><div class="warning">Für diesen Kunden wurden noch keine Load-Planner-Kundeneinstellungen gespeichert. Die folgenden Werte können für diese Berechnung verwendet und optional beim Kunden gespeichert werden.</div></td></tr>';
} else {
    print '<tr><td colspan="2"><div class="opacitymedium">Die Werte wurden aus den gespeicherten Load-Planner-Kundeneinstellungen des Kunden übernommen.</div></td></tr>';
}

print '<tr>';
print '<td class="titlefield">Kunde hat Gabelstapler</td>';
print '<td>';
print '<select name="has_forklift" class="flat">';
print '<option value="1"' . ((int) $hasForklift === 1 ? ' selected' : '') . '>Ja</option>';
print '<option value="0"' . ((int) $hasForklift === 0 ? ' selected' : '') . '>Nein</option>';
print '</select>';
print '</td>';
print '</tr>';

print '<tr>';
print '<td>Bevorzugtes Lademittel</td>';
print '<td>';
print '<select name="preferred_unit" class="flat">';
print '<option value="palette"' . ($preferredUnit === 'palette' ? ' selected' : '') . '>Palette</option>';
print '<option value="roll"' . ($preferredUnit === 'roll' ? ' selected' : '') . '>Rollcontainer</option>';
print '</select>';
print '</td>';
print '</tr>';

print '<tr>';
print '<td>Beim Kunden speichern</td>';
print '<td><input type="checkbox" name="save_customer_settings" value="1"' . (!$customerSettings['exists'] ? ' checked' : '') . '> Diese Werte als Load-Planner-Kundeneinstellungen speichern</td>';
print '</tr>';

print '</table>';

print '<br>';
print '<input type="submit" class="button button-save" value="Gebinde berechnen und speichern">';
print '</form>';

print '<br>';

print '<table class="border centpercent">';
print '<tr class="liste_titre"><td>Produkt</td><td>Menge</td><td>Gewicht</td><td>Maße</td></tr>';

foreach ($object->lines as $line) {
    if (empty($line->fk_product)) {
        continue;
    }

    $product = new Product($db);
    $product->fetch($line->fk_product);

    $lengthMm = lp_length_to_mm($product->length, $product->length_units);
    $widthMm = lp_length_to_mm($product->width, $product->width_units);
    $heightMm = lp_length_to_mm($product->height, $product->height_units);
    $weightKg = lp_weight_to_kg($product->weight, $product->weight_units);

    print '<tr class="oddeven">';
    print '<td>' . dol_escape_htmltag($product->ref . ' - ' . $product->label) . '</td>';
    print '<td>' . price($line->qty) . '</td>';
    print '<td>' . price($weightKg) . ' kg</td>';
    print '<td>' . price($lengthMm) . ' x ' . price($widthMm) . ' x ' . price($heightMm) . ' mm</td>';
    print '</tr>';
}

print '</table>';

llxFooter();
$db->close();
