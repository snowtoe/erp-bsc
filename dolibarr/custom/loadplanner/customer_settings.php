<?php

$res = 0;
if (!$res && file_exists("../main.inc.php")) {
    $res = @include "../main.inc.php";
}
if (!$res && file_exists("../../main.inc.php")) {
    $res = @include "../../main.inc.php";
}

require_once DOL_DOCUMENT_ROOT . '/societe/class/societe.class.php';

if (empty($user->rights->loadplanner->read)) {
    accessforbidden();
}

function lp_get_customer_settings_page($db, $socid)
{
    global $conf;

    $settings = array(
        'has_forklift' => 0,
        'preferred_unit' => 'roll',
        'exists' => false
    );

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

function lp_save_customer_settings_page($db, $socid, $hasForklift, $preferredUnit)
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

$socid = GETPOST('socid', 'int');
$action = GETPOST('action', 'alpha');

$thirdparty = new Societe($db);

if ($socid <= 0 || $thirdparty->fetch($socid) <= 0) {
    accessforbidden('Kunde konnte nicht geladen werden.');
}

if ($action === 'save') {
    $hasForklift = GETPOST('has_forklift', 'int');
    $preferredUnit = GETPOST('preferred_unit', 'alpha');

    if (lp_save_customer_settings_page($db, $socid, $hasForklift, $preferredUnit)) {
        setEventMessages('Load-Planner-Kundeneinstellungen wurden gespeichert.', null, 'mesgs');
    } else {
        setEventMessages('Fehler beim Speichern der Load-Planner-Kundeneinstellungen.', null, 'errors');
    }
}

$settings = lp_get_customer_settings_page($db, $socid);

llxHeader('', 'Load-Planner Kundeneinstellungen');

$backToCustomer = '<a href="' . DOL_URL_ROOT . '/societe/card.php?socid=' . ((int) $socid) . '">Zurück zum Kunden</a>';

print load_fiche_titre('Load-Planner Kundeneinstellungen', $backToCustomer, 'generic');

print '<table class="border centpercent">';
print '<tr class="liste_titre"><td colspan="2">Kunde</td></tr>';
print '<tr><td class="titlefield">Name</td><td>' . dol_escape_htmltag($thirdparty->name) . '</td></tr>';
print '<tr><td>Kundennummer</td><td>' . dol_escape_htmltag($thirdparty->code_client) . '</td></tr>';
print '</table>';

print '<br>';

print '<form method="POST" action="' . $_SERVER["PHP_SELF"] . '?socid=' . ((int) $socid) . '">';
print '<input type="hidden" name="token" value="' . newToken() . '">';
print '<input type="hidden" name="action" value="save">';

print '<table class="border centpercent">';
print '<tr class="liste_titre"><td colspan="2">Logistische Parameter</td></tr>';

print '<tr>';
print '<td class="titlefield">Kunde hat Gabelstapler</td>';
print '<td>';
print '<select name="has_forklift" class="flat">';
print '<option value="1"' . ((int) $settings['has_forklift'] === 1 ? ' selected' : '') . '>Ja</option>';
print '<option value="0"' . ((int) $settings['has_forklift'] === 0 ? ' selected' : '') . '>Nein</option>';
print '</select>';
print '</td>';
print '</tr>';

print '<tr>';
print '<td>Bevorzugtes Lademittel</td>';
print '<td>';
print '<select name="preferred_unit" class="flat">';
print '<option value="palette"' . ($settings['preferred_unit'] === 'palette' ? ' selected' : '') . '>Palette</option>';
print '<option value="roll"' . ($settings['preferred_unit'] === 'roll' ? ' selected' : '') . '>Rollcontainer</option>';
print '</select>';
print '</td>';
print '</tr>';

print '</table>';

print '<br>';
print '<input type="submit" class="button button-save" value="Speichern">';
print '</form>';

print '<br>';
print '<div class="opacitymedium">';
print 'Diese Parameter werden bei der Gebindeberechnung aus Angeboten, Aufträgen und Rechnungen automatisch als Voreinstellung verwendet.';
print '</div>';

llxFooter();
$db->close();
