<?php
/* Copyright (C) 2026 Load Planner Prototype
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation.
 */

include_once DOL_DOCUMENT_ROOT . '/core/modules/DolibarrModules.class.php';

class modLoadPlanner extends DolibarrModules
{
    public function __construct($db)
    {
        global $langs, $conf;

        $this->db = $db;

        $this->numero = 500000;

        $this->rights_class = 'loadplanner';
        $this->family = "technic";
        $this->module_position = 500;
        $this->name = preg_replace('/^mod/i', '', get_class($this));

        $this->description = "Load Planner module for container and loading unit calculation";
        $this->descriptionlong = "Prototype module for calculating suitable packaging and loading units such as pallets, roll containers and compartment containers.";

        $this->version = '1.0';

        $this->const_name = 'MAIN_MODULE_' . strtoupper($this->name);
        $this->picto = 'generic';

        $this->module_parts = array(
            'triggers' => 0,
            'login' => 0,
            'substitutions' => 0,
            'menus' => 1,
            'tpl' => 0,
            'barcode' => 0,
            'models' => 0,
            'css' => array(),
            'js' => array(),
            'hooks' => array(
                'data' => array(
                    'all'
                ),
                'entity' => '0'
            )
        );

        $this->dirs = array();

        $this->config_page_url = array("setup.php@loadplanner");

        $this->depends = array();
        $this->requiredby = array();
        $this->conflictwith = array();

        $this->phpmin = array(7, 4);
        $this->need_dolibarr_version = array(15, 0);

        $this->langfiles = array("loadplanner@loadplanner");

        $this->const = array();
        $this->tabs = array();
        $this->dictionaries = array();
        $this->boxes = array();

        $this->rights = array();

        $r = 0;
        $this->rights[$r][0] = $this->numero + 1;
        $this->rights[$r][1] = 'Read Load Planner results';
        $this->rights[$r][4] = 'read';
        $this->rights[$r][5] = '';
        $r++;

        $this->menu = array();

        $r = 0;

        $this->menu[$r++] = array(
            'fk_menu' => '',
            'type' => 'top',
            'titre' => 'LoadPlanner',
            'mainmenu' => 'loadplanner',
            'leftmenu' => '',
            'url' => '/custom/loadplanner/loadplannerindex.php',
            'langs' => 'loadplanner@loadplanner',
            'position' => 1000,
            'enabled' => '$conf->loadplanner->enabled',
            'perms' => '$user->rights->loadplanner->read',
            'target' => '',
            'user' => 2
        );

        $this->menu[$r++] = array(
            'fk_menu' => 'fk_mainmenu=loadplanner',
            'type' => 'left',
            'titre' => 'LoadPlannerHome',
            'mainmenu' => 'loadplanner',
            'leftmenu' => 'loadplanner_home',
            'url' => '/custom/loadplanner/loadplannerindex.php',
            'langs' => 'loadplanner@loadplanner',
            'position' => 100,
            'enabled' => '$conf->loadplanner->enabled',
            'perms' => '$user->rights->loadplanner->read',
            'target' => '',
            'user' => 2
        );

        $this->menu[$r++] = array(
            'fk_menu' => 'fk_mainmenu=loadplanner',
            'type' => 'left',
            'titre' => 'Gebindeberechnungen',
            'mainmenu' => 'loadplanner',
            'leftmenu' => 'loadplanner_calculations',
            'url' => '/custom/loadplanner/list.php',
            'langs' => 'loadplanner@loadplanner',
            'position' => 110,
            'enabled' => '$conf->loadplanner->enabled',
            'perms' => '$user->rights->loadplanner->read',
            'target' => '',
            'user' => 2
        );
    }

    public function init($options = '')
    {
        $sql = array();

        $sql[] = "CREATE TABLE IF NOT EXISTS " . MAIN_DB_PREFIX . "loadplanner_calc (
            rowid integer AUTO_INCREMENT PRIMARY KEY,
            entity integer DEFAULT 1 NOT NULL,
            ref varchar(64) NOT NULL,
            element_type varchar(32) NOT NULL,
            fk_element integer NOT NULL,
            fk_soc integer DEFAULT NULL,
            datec datetime NOT NULL,
            tms timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            fk_user_creat integer DEFAULT NULL,
            has_forklift tinyint DEFAULT 0,
            preferred_unit varchar(32) DEFAULT NULL,
            total_weight double(24,8) DEFAULT 0,
            note text
        ) ENGINE=innodb";

        $sql[] = "CREATE TABLE IF NOT EXISTS " . MAIN_DB_PREFIX . "loadplanner_calc_line (
            rowid integer AUTO_INCREMENT PRIMARY KEY,
            fk_calc integer NOT NULL,
            unit_type varchar(32) NOT NULL,
            unit_no integer NOT NULL DEFAULT 1,
            compartment_no integer DEFAULT NULL,
            fk_product integer DEFAULT NULL,
            product_ref varchar(128) DEFAULT NULL,
            product_label varchar(255) DEFAULT NULL,
            qty double(24,8) DEFAULT 0,
            items_per_unit integer DEFAULT 0,
            total_weight double(24,8) DEFAULT 0,
            reason text
        ) ENGINE=innodb";

        $sql[] = "CREATE TABLE IF NOT EXISTS " . MAIN_DB_PREFIX . "loadplanner_customer_setting (
            rowid integer AUTO_INCREMENT PRIMARY KEY,
            entity integer DEFAULT 1 NOT NULL,
            fk_soc integer NOT NULL,
            has_forklift tinyint DEFAULT 0,
            preferred_unit varchar(32) DEFAULT 'roll',
            datec datetime NOT NULL,
            tms timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            fk_user_modif integer DEFAULT NULL,
            UNIQUE KEY uk_loadplanner_customer_setting_soc (entity, fk_soc)
        ) ENGINE=innodb";

        return $this->_init($sql, $options);
    }

    public function remove($options = '')
    {
        $sql = array();

        return $this->_remove($sql, $options);
    }
}
