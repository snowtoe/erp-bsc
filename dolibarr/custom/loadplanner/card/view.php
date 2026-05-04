<?php

$res = 0;
if (!$res && file_exists("../../main.inc.php")) {
    $res = @include "../../main.inc.php";
}
if (!$res && file_exists("../../../main.inc.php")) {
    $res = @include "../../../main.inc.php";
}

if (empty($user->rights->loadplanner->read)) {
    accessforbidden();
}

function lp_document_label_view($element)
{
    if ($element === 'propal') return 'Angebot';
    if ($element === 'commande') return 'Auftrag';
    if ($element === 'facture') return 'Rechnung';
    return $element;
}

function lp_document_url_view($element, $id)
{
    if ($element === 'propal') return DOL_URL_ROOT . '/comm/propal/card.php?id=' . ((int) $id);
    if ($element === 'commande') return DOL_URL_ROOT . '/commande/card.php?id=' . ((int) $id);
    if ($element === 'facture') return DOL_URL_ROOT . '/compta/facture/card.php?facid=' . ((int) $id);
    return '#';
}

$id = GETPOST('id', 'int');

$sql = "SELECT c.*, s.nom as customer_name
        FROM " . MAIN_DB_PREFIX . "loadplanner_calc c
        LEFT JOIN " . MAIN_DB_PREFIX . "societe s ON s.rowid = c.fk_soc
        WHERE c.rowid = " . ((int) $id);

$resql = $db->query($sql);
$calc = $db->fetch_object($resql);

if (!$calc) {
    accessforbidden('Berechnung nicht gefunden.');
}

llxHeader('', 'Gebindeberechnung');

$linkback = '<a href="' . DOL_URL_ROOT . '/custom/loadplanner/list.php">Zurück zur Liste</a>';
$linkDocument = '<a href="' . lp_document_url_view($calc->element_type, $calc->fk_element) . '">Zum Ausgangsbeleg</a>';

print load_fiche_titre('Gebindeberechnung ' . dol_escape_htmltag($calc->ref), $linkback . ' &nbsp; | &nbsp; ' . $linkDocument, 'generic');

print '<table class="border centpercent">';
print '<tr class="liste_titre"><td colspan="2">Kopfdaten</td></tr>';
print '<tr><td class="titlefield">Referenz</td><td>' . dol_escape_htmltag($calc->ref) . '</td></tr>';
print '<tr><td>Belegtyp</td><td>' . dol_escape_htmltag(lp_document_label_view($calc->element_type)) . '</td></tr>';
print '<tr><td>Kunde</td><td>' . dol_escape_htmltag($calc->customer_name) . '</td></tr>';
print '<tr><td>Gabelstapler</td><td>' . ((int) $calc->has_forklift ? 'Ja' : 'Nein') . '</td></tr>';
print '<tr><td>Bevorzugtes Lademittel</td><td>' . ($calc->preferred_unit === 'palette' ? 'Palette' : 'Rollcontainer') . '</td></tr>';
print '<tr><td>Gesamtgewicht</td><td>' . price($calc->total_weight) . ' kg</td></tr>';
print '</table>';

print '<br>';

$sql = "SELECT *
        FROM " . MAIN_DB_PREFIX . "loadplanner_calc_line
        WHERE fk_calc = " . ((int) $id) . "
        ORDER BY unit_no ASC, compartment_no ASC, rowid ASC";

$resql = $db->query($sql);

print '<table class="border centpercent">';
print '<tr class="liste_titre">';
print '<td>Lademittel</td>';
print '<td>Nr.</td>';
print '<td>Fach</td>';
print '<td>Produkt</td>';
print '<td>Menge</td>';
print '<td>Gewicht</td>';
print '<td>Begründung</td>';
print '</tr>';

while ($line = $db->fetch_object($resql)) {
    print '<tr class="oddeven">';
    print '<td>' . dol_escape_htmltag($line->unit_type) . '</td>';
    print '<td>' . (int) $line->unit_no . '</td>';
    print '<td>' . ($line->compartment_no !== null ? (int) $line->compartment_no . ' / 4' : '-') . '</td>';
    print '<td>' . dol_escape_htmltag($line->product_ref . ' - ' . $line->product_label) . '</td>';
    print '<td>' . price($line->qty) . '</td>';
    print '<td>' . price($line->total_weight) . ' kg</td>';
    print '<td>' . dol_escape_htmltag($line->reason) . '</td>';
    print '</tr>';
}

print '</table>';

print '<br>';
print '<div class="tabsAction">';
print '<a class="butAction" href="' . lp_document_url_view($calc->element_type, $calc->fk_element) . '">Zum Ausgangsbeleg</a>';
print '<a class="butAction" href="' . DOL_URL_ROOT . '/custom/loadplanner/list.php">Zur Liste der Gebindeberechnungen</a>';
print '</div>';

llxFooter();
$db->close();
