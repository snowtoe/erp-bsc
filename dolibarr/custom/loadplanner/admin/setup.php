<?php

$res = 0;

if (!$res && file_exists("../../main.inc.php")) {
    $res = @include "../../main.inc.php";
}
if (!$res && file_exists("../../../main.inc.php")) {
    $res = @include "../../../main.inc.php";
}

require_once DOL_DOCUMENT_ROOT . '/core/lib/admin.lib.php';

$langs->loadLangs(array("admin", "loadplanner@loadplanner"));

if (!$user->admin) {
    accessforbidden();
}

$action = GETPOST('action', 'aZ09');

llxHeader('', $langs->trans("LoadPlannerSetup"));

$linkback = '<a href="' . DOL_URL_ROOT . '/admin/modules.php?restore_lastsearch_values=1">' . $langs->trans("BackToModuleList") . '</a>';

print load_fiche_titre($langs->trans("LoadPlannerSetup"), $linkback, 'title_setup');

print '<span class="opacitymedium">';
print $langs->trans("LoadPlannerSetupPage");
print '</span><br><br>';

print '<div class="info">';
print 'Das Modul ist aktiv. In den nächsten Schritten werden hier Einstellungen für Palette, Rollcontainer und Fachcontainer ergänzt.';
print '</div>';

llxFooter();
$db->close();
