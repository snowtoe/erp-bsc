<?php

$res = 0;

if (!$res && file_exists("../main.inc.php")) {
    $res = @include "../main.inc.php";
}
if (!$res && file_exists("../../main.inc.php")) {
    $res = @include "../../main.inc.php";
}

$langs->loadLangs(array("loadplanner@loadplanner"));

if (empty($user->rights->loadplanner->read)) {
    accessforbidden();
}

/**
 * Convert Dolibarr length to millimeters.
 * Dolibarr usually stores length_units as power of ten relative to meters.
 * Example:
 *  0  = meter
 * -2  = centimeter
 * -3  = millimeter
 */
function lp_length_to_mm($value, $unit)
{
    if ($value === null || $value === '') {
        return 0;
    }

    $value = (float) $value;
    $unit = (int) $unit;

    return $value * pow(10, $unit + 3);
}

/**
 * Convert Dolibarr weight to kilograms.
 * Dolibarr usually stores weight_units as power of ten relative to kilograms.
 * Example:
 *  0  = kilogram
 * -3  = gram
 *  3  = ton
 */
function lp_weight_to_kg($value, $unit)
{
    if ($value === null || $value === '') {
        return 0;
    }

    $value = (float) $value;
    $unit = (int) $unit;

    return $value * pow(10, $unit);
}


function lp_calculate_load_units($quantity, $lengthMm, $widthMm, $heightMm, $weightKg, $hasForklift, $preferredUnit)
{
    $quantity = max(0, (int) $quantity);

    // Loading unit reference values
    $palletMaxWeightKg = 1200;
    $palletBaseLengthMm = 1200;
    $palletBaseWidthMm = 800;
    $palletMaxHeightMm = 1900;

    $rollMaxWeightKg = 500;
    $rollLengthMm = 1450;
    $rollWidthMm = 660;
    $rollHeightMm = 800;

    // Fachcontainer as roll container with four compartments
    $compartmentCount = 4;
    $compartmentMaxWeightKg = $rollMaxWeightKg / $compartmentCount;

    $totalWeightKg = $quantity * $weightKg;

    $result = array(
        'recommended_unit' => '',
        'full_units' => 0,
        'remaining_quantity' => 0,
        'items_per_unit' => 0,
        'total_weight_kg' => $totalWeightKg,
        'reason' => '',
        'warnings' => array()
    );

    if ($quantity <= 0) {
        $result['recommended_unit'] = 'Keine Berechnung';
        $result['reason'] = 'Die Menge muss größer als 0 sein.';
        return $result;
    }

    if ($lengthMm <= 0 || $widthMm <= 0 || $heightMm <= 0 || $weightKg <= 0) {
        $result['recommended_unit'] = 'Keine Berechnung';
        $result['reason'] = 'Für das Produkt müssen Länge, Breite, Höhe und Gewicht gepflegt sein.';
        return $result;
    }

    // Product orientation is simplified: length x width are placed on the loading base.
    $itemsPerPalletLayer = floor($palletBaseLengthMm / $lengthMm) * floor($palletBaseWidthMm / $widthMm);
    $palletLayers = floor($palletMaxHeightMm / $heightMm);
    $itemsPerPalletByVolume = $itemsPerPalletLayer * $palletLayers;
    $itemsPerPalletByWeight = floor($palletMaxWeightKg / $weightKg);
    $itemsPerPallet = (int) max(0, min($itemsPerPalletByVolume, $itemsPerPalletByWeight));

    $itemsPerRollLayer = floor($rollLengthMm / $lengthMm) * floor($rollWidthMm / $widthMm);
    $rollLayers = floor($rollHeightMm / $heightMm);
    $itemsPerRollByVolume = $itemsPerRollLayer * $rollLayers;
    $itemsPerRollByWeight = floor($rollMaxWeightKg / $weightKg);
    $itemsPerRoll = (int) max(0, min($itemsPerRollByVolume, $itemsPerRollByWeight));

    $itemsPerCompartment = (int) max(1, floor($itemsPerRoll / $compartmentCount));
    $itemsPerCompartmentByWeight = (int) max(1, floor($compartmentMaxWeightKg / $weightKg));
    $itemsPerCompartment = min($itemsPerCompartment, $itemsPerCompartmentByWeight);

    if ($itemsPerPallet <= 0) {
        $result['warnings'][] = 'Das Produkt passt rechnerisch nicht auf eine Palette.';
    }

    if ($itemsPerRoll <= 0) {
        $result['warnings'][] = 'Das Produkt passt rechnerisch nicht in einen Rollcontainer.';
    }

    // Decision logic
    if (!$hasForklift) {
        // Customer has no forklift -> roll container preferred.
        if ($itemsPerRoll > 0 && $quantity >= $itemsPerRoll) {
            $result['recommended_unit'] = 'Rollcontainer';
            $result['items_per_unit'] = $itemsPerRoll;
            $result['full_units'] = intdiv($quantity, $itemsPerRoll);
            $result['remaining_quantity'] = $quantity % $itemsPerRoll;
            $result['reason'] = 'Der Kunde verfügt über keinen Gabelstapler. Daher wird ein Rollcontainer bevorzugt.';
        } else {
            $result['recommended_unit'] = 'Fachcontainer';
            $result['items_per_unit'] = $itemsPerCompartment;
            $result['full_units'] = 1;
            $result['remaining_quantity'] = 0;
            $result['reason'] = 'Der Kunde verfügt über keinen Gabelstapler und die Menge ist für einen vollständigen Rollcontainer zu gering.';
        }
    } else {
        // Customer has forklift -> preferred unit can be used.
        if ($preferredUnit === 'pallet' && $itemsPerPallet > 0 && $quantity >= $itemsPerPallet) {
            $result['recommended_unit'] = 'Palette';
            $result['items_per_unit'] = $itemsPerPallet;
            $result['full_units'] = intdiv($quantity, $itemsPerPallet);
            $result['remaining_quantity'] = $quantity % $itemsPerPallet;
            $result['reason'] = 'Der Kunde verfügt über einen Gabelstapler und Palette wurde als bevorzugtes Lademittel gewählt.';
        } elseif ($preferredUnit === 'roll' && $itemsPerRoll > 0 && $quantity >= $itemsPerRoll) {
            $result['recommended_unit'] = 'Rollcontainer';
            $result['items_per_unit'] = $itemsPerRoll;
            $result['full_units'] = intdiv($quantity, $itemsPerRoll);
            $result['remaining_quantity'] = $quantity % $itemsPerRoll;
            $result['reason'] = 'Der Kunde verfügt über einen Gabelstapler, es wurde jedoch Rollcontainer als bevorzugtes Lademittel gewählt.';
        } else {
            $result['recommended_unit'] = 'Fachcontainer';
            $result['items_per_unit'] = $itemsPerCompartment;
            $result['full_units'] = 1;
            $result['remaining_quantity'] = 0;
            $result['reason'] = 'Die Menge ist für ein vollständiges Hauptlademittel zu gering. Daher wird ein Fachcontainer verwendet.';
        }
    }

    return $result;
}

$action = GETPOST('action', 'alpha');
$socid = GETPOST('socid', 'int');
$productid = GETPOST('productid', 'int');
$quantity = GETPOST('quantity', 'int');
$hasForklift = GETPOST('has_forklift', 'int');
$preferredUnit = GETPOST('preferred_unit', 'alpha');

if ($quantity <= 0) {
    $quantity = 1;
}

if (empty($preferredUnit)) {
    $preferredUnit = 'pallet';
}

$customers = array();
$sql = "SELECT rowid, nom FROM " . MAIN_DB_PREFIX . "societe WHERE client IN (1,2,3) ORDER BY nom ASC";
$resql = $db->query($sql);
if ($resql) {
    while ($obj = $db->fetch_object($resql)) {
        $customers[] = $obj;
    }
}

$products = array();
$sql = "SELECT rowid, ref, label, weight, weight_units, length, length_units, width, width_units, height, height_units
        FROM " . MAIN_DB_PREFIX . "product
        WHERE entity IN (" . getEntity('product') . ")
        ORDER BY ref ASC";
$resql = $db->query($sql);
if ($resql) {
    while ($obj = $db->fetch_object($resql)) {
        $products[] = $obj;
    }
}

$selectedProduct = null;
if ($productid > 0) {
    $sql = "SELECT rowid, ref, label, weight, weight_units, length, length_units, width, width_units, height, height_units
            FROM " . MAIN_DB_PREFIX . "product
            WHERE rowid = " . ((int) $productid);
    $resql = $db->query($sql);
    if ($resql) {
        $selectedProduct = $db->fetch_object($resql);
    }
}

$result = null;
if ($action === 'calculate' && $selectedProduct) {
    $lengthMm = lp_length_to_mm($selectedProduct->length, $selectedProduct->length_units);
    $widthMm = lp_length_to_mm($selectedProduct->width, $selectedProduct->width_units);
    $heightMm = lp_length_to_mm($selectedProduct->height, $selectedProduct->height_units);
    $weightKg = lp_weight_to_kg($selectedProduct->weight, $selectedProduct->weight_units);

    $result = lp_calculate_load_units(
        $quantity,
        $lengthMm,
        $widthMm,
        $heightMm,
        $weightKg,
        (bool) $hasForklift,
        $preferredUnit
    );
}

llxHeader('', $langs->trans("LoadPlanner"));

print load_fiche_titre($langs->trans("LoadPlanner"), '', 'generic');

print '<div class="fichecenter">';

print '<form method="POST" action="' . $_SERVER["PHP_SELF"] . '">';
print '<input type="hidden" name="token" value="' . newToken() . '">';
print '<input type="hidden" name="action" value="calculate">';

print '<table class="border centpercent">';
print '<tr class="liste_titre">';
print '<td colspan="2">Gebindeberechnung</td>';
print '</tr>';

print '<tr>';
print '<td class="titlefield">Kunde</td>';
print '<td>';
print '<select name="socid" class="flat minwidth300">';
print '<option value="0">-- Kunde auswählen --</option>';
foreach ($customers as $customer) {
    $selected = ($socid == $customer->rowid) ? ' selected' : '';
    print '<option value="' . (int) $customer->rowid . '"' . $selected . '>' . dol_escape_htmltag($customer->nom) . '</option>';
}
print '</select>';
print '</td>';
print '</tr>';

print '<tr>';
print '<td>Produkt</td>';
print '<td>';
print '<select name="productid" class="flat minwidth300">';
print '<option value="0">-- Produkt auswählen --</option>';
foreach ($products as $product) {
    $selected = ($productid == $product->rowid) ? ' selected' : '';
    $label = $product->ref . ' - ' . $product->label;
    print '<option value="' . (int) $product->rowid . '"' . $selected . '>' . dol_escape_htmltag($label) . '</option>';
}
print '</select>';
print '</td>';
print '</tr>';

print '<tr>';
print '<td>Menge</td>';
print '<td><input type="number" name="quantity" min="1" value="' . (int) $quantity . '" class="flat"></td>';
print '</tr>';

print '<tr>';
print '<td>Kunde hat Gabelstapler</td>';
print '<td>';
print '<select name="has_forklift" class="flat">';
print '<option value="1"' . ($hasForklift ? ' selected' : '') . '>Ja</option>';
print '<option value="0"' . (!$hasForklift ? ' selected' : '') . '>Nein</option>';
print '</select>';
print '</td>';
print '</tr>';

print '<tr>';
print '<td>Bevorzugtes Lademittel</td>';
print '<td>';
print '<select name="preferred_unit" class="flat">';
print '<option value="pallet"' . ($preferredUnit === 'pallet' ? ' selected' : '') . '>Palette</option>';
print '<option value="roll"' . ($preferredUnit === 'roll' ? ' selected' : '') . '>Rollcontainer</option>';
print '</select>';
print '</td>';
print '</tr>';

print '</table>';

print '<br>';
print '<input type="submit" class="button button-save" value="Berechnen">';

print '</form>';

if ($selectedProduct) {
    $lengthMm = lp_length_to_mm($selectedProduct->length, $selectedProduct->length_units);
    $widthMm = lp_length_to_mm($selectedProduct->width, $selectedProduct->width_units);
    $heightMm = lp_length_to_mm($selectedProduct->height, $selectedProduct->height_units);
    $weightKg = lp_weight_to_kg($selectedProduct->weight, $selectedProduct->weight_units);

    print '<br>';
    print '<table class="border centpercent">';
    print '<tr class="liste_titre"><td colspan="2">Produktdaten</td></tr>';
    print '<tr><td class="titlefield">Produkt</td><td>' . dol_escape_htmltag($selectedProduct->ref . ' - ' . $selectedProduct->label) . '</td></tr>';
    print '<tr><td>Länge</td><td>' . price($lengthMm) . ' mm</td></tr>';
    print '<tr><td>Breite</td><td>' . price($widthMm) . ' mm</td></tr>';
    print '<tr><td>Höhe</td><td>' . price($heightMm) . ' mm</td></tr>';
    print '<tr><td>Gewicht</td><td>' . price($weightKg) . ' kg</td></tr>';
    print '</table>';
}

if ($result) {
    print '<br>';
    print '<table class="border centpercent">';
    print '<tr class="liste_titre"><td colspan="2">Berechnungsergebnis</td></tr>';
    print '<tr><td class="titlefield">Empfohlenes Lademittel</td><td><strong>' . dol_escape_htmltag($result['recommended_unit']) . '</strong></td></tr>';
    print '<tr><td>Einheiten</td><td>' . (int) $result['full_units'] . '</td></tr>';
    print '<tr><td>Artikel pro Einheit</td><td>' . (int) $result['items_per_unit'] . '</td></tr>';
    print '<tr><td>Restmenge</td><td>' . (int) $result['remaining_quantity'] . '</td></tr>';
    print '<tr><td>Gesamtgewicht</td><td>' . price($result['total_weight_kg']) . ' kg</td></tr>';
    print '<tr><td>Begründung</td><td>' . dol_escape_htmltag($result['reason']) . '</td></tr>';

    if (!empty($result['warnings'])) {
        print '<tr><td>Hinweise</td><td>';
        foreach ($result['warnings'] as $warning) {
            print '<div class="warning">' . dol_escape_htmltag($warning) . '</div>';
        }
        print '</td></tr>';
    }

    print '</table>';
}

print '<br>';
print '<div class="opacitymedium">';
print 'Hinweis: Diese Berechnung ist ein prototypisches Entscheidungsmodell für die Bachelorarbeit. Sie vereinfacht die reale Packlogik, indem Produkte lagenweise anhand von Grundfläche, Höhe und Gewicht berechnet werden.';
print '</div>';

print '</div>';

llxFooter();
$db->close();
