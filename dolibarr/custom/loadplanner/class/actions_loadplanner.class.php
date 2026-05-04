<?php

class ActionsLoadplanner
{
    public $resprints = '';
    public $results = array();

    private $documentButtonPrinted = false;
    private $customerButtonPrinted = false;

    private function getDocumentElement($object, $context)
    {
        if (!empty($object->element)) {
            if ($object->element === 'propal') return 'propal';
            if ($object->element === 'commande') return 'commande';
            if ($object->element === 'facture') return 'facture';
        }

        $className = is_object($object) ? strtolower(get_class($object)) : '';

        if (strpos($className, 'propal') !== false) return 'propal';
        if (strpos($className, 'commande') !== false) return 'commande';
        if (strpos($className, 'facture') !== false) return 'facture';

        if (strpos($context, 'propalcard') !== false) return 'propal';
        if (strpos($context, 'ordercard') !== false) return 'commande';
        if (strpos($context, 'invoicecard') !== false) return 'facture';

        return '';
    }

    private function isDocumentContext($object, $context)
    {
        if (strpos($context, 'propalcard') !== false) return true;
        if (strpos($context, 'ordercard') !== false) return true;
        if (strpos($context, 'invoicecard') !== false) return true;

        if (!empty($object->element)) {
            if ($object->element === 'propal') return true;
            if ($object->element === 'commande') return true;
            if ($object->element === 'facture') return true;
        }

        $className = is_object($object) ? strtolower(get_class($object)) : '';

        if (strpos($className, 'propal') !== false) return true;
        if (strpos($className, 'commande') !== false) return true;
        if (strpos($className, 'facture') !== false) return true;

        return false;
    }

    private function isThirdpartyContext($object, $context)
    {
        if (strpos($context, 'thirdpartycard') !== false) return true;
        if (strpos($context, 'companycard') !== false) return true;

        if (!empty($object->element) && $object->element === 'societe') return true;

        $className = is_object($object) ? strtolower(get_class($object)) : '';
        if (strpos($className, 'societe') !== false) return true;

        return false;
    }

    private function printDocumentButton($object, $context)
    {
        if ($this->documentButtonPrinted) {
            return 0;
        }

        if (empty($object) || empty($object->id)) {
            return 0;
        }

        if (!$this->isDocumentContext($object, $context)) {
            return 0;
        }

        $element = $this->getDocumentElement($object, $context);

        if (empty($element)) {
            return 0;
        }

        $url = DOL_URL_ROOT . '/custom/loadplanner/calculate.php?element=' . urlencode($element) . '&id=' . ((int) $object->id);

        print '<a class="butAction" href="' . $url . '">Gebinde berechnen</a>';

        $this->documentButtonPrinted = true;

        return 0;
    }

    private function printCustomerSettingsButton($object, $context)
    {
        if ($this->customerButtonPrinted) {
            return 0;
        }

        if (empty($object) || empty($object->id)) {
            return 0;
        }

        if (!$this->isThirdpartyContext($object, $context)) {
            return 0;
        }

        $url = DOL_URL_ROOT . '/custom/loadplanner/customer_settings.php?socid=' . ((int) $object->id);

        print '<a class="butAction" href="' . $url . '">Load-Planner Einstellungen</a>';

        $this->customerButtonPrinted = true;

        return 0;
    }

    public function addMoreActionsButtons($parameters, &$object, &$action, $hookmanager)
    {
        global $conf;

        if (empty($conf->loadplanner->enabled)) {
            return 0;
        }

        $context = !empty($parameters['context']) ? $parameters['context'] : '';

        $this->printDocumentButton($object, $context);
        $this->printCustomerSettingsButton($object, $context);

        return 0;
    }

    public function formObjectOptions($parameters, &$object, &$action, $hookmanager)
    {
        global $conf;

        if (empty($conf->loadplanner->enabled)) {
            return 0;
        }

        $context = !empty($parameters['context']) ? $parameters['context'] : '';

        $this->printDocumentButton($object, $context);
        $this->printCustomerSettingsButton($object, $context);

        return 0;
    }

    public function formConfirm($parameters, &$object, &$action, $hookmanager)
    {
        global $conf;

        if (empty($conf->loadplanner->enabled)) {
            return 0;
        }

        $context = !empty($parameters['context']) ? $parameters['context'] : '';

        $this->printDocumentButton($object, $context);
        $this->printCustomerSettingsButton($object, $context);

        return 0;
    }
}
