<?php

$res = 0;
if (!$res && file_exists("../main.inc.php")) {
    $res = @include "../main.inc.php";
}
if (!$res && file_exists("../../main.inc.php")) {
    $res = @include "../../main.inc.php";
}

if (empty($user->rights->loadplanner->read)) {
    accessforbidden();
}

llxHeader('', 'Gebindeberechnungen');

print load_fiche_titre('Gebindeberechnungen', '', 'generic');

$sql = "SELECT c.*, s.nom as customer_name
        FROM " . MAIN_DB_PREFIX . "loadplanner_calc c
        LEFT JOIN " . MAIN_DB_PREFIX . "societe s ON s.rowid = c.fk_soc
        ORDER BY c.rowid DESC";

$resql = $db->query($sql);

print '<table class="border centpercent">';
print '<tr class="liste_titre">';
print '<td>Referenz</td>';
print '<td>Belegtyp</td>';
print '<td>Kunde</td>';
print '<td>Datum</td>';
print '<td>Gabelstapler</td>';
print '<td>Lademittelwunsch</td>';
print '<td>Gesamtgewicht</td>';
print '</tr>';

while ($obj = $db->fetch_object($resql)) {
    $url = dol_buildpath('/loadplanner/card/view.php', 1) . '?id=' . ((int) $obj->rowid);

    print '<tr class="oddeven">';
    print '<td><a href="' . $url . '">' . dol_escape_htmltag($obj->ref) . '</a></td>';
    print '<td>' . dol_escape_htmltag($obj->element_type) . '</td>';
    print '<td>' . dol_escape_htmltag($obj->customer_name) . '</td>';
    print '<td>' . dol_print_date($db->jdate($obj->datec), 'dayhour') . '</td>';
    print '<td>' . ((int) $obj->has_forklift ? 'Ja' : 'Nein') . '</td>';
    print '<td>' . dol_escape_htmltag($obj->preferred_unit) . '</td>';
    print '<td>' . price($obj->total_weight) . ' kg</td>';
    print '</tr>';
}

print '</table>';

llxFooter();
$db->close();
