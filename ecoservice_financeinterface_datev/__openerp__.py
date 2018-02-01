# -*- encoding: utf-8 -*- # pylint: disable-msg=C0111
##############################################################################
#    ecoservice_financeinterface_datev
#    Copyright (c) 2013 ecoservice GbR (<http://www.ecoservice.de>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    This program based on OpenERP.
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
##############################################################################
{# pylint: disable-msg=W0104
    "name" : "Ecoservice Financial Interface Datev",
    "version" : "1.0",
    "depends" : ["base", "ecoservice_financeinterface"],
    "author" : "ecoservice",
    "website" : "www.ecoservice.de",
    "description": """The module ecoservice_financeinterface_datev provides methods to convert account moves to the Datevformat (Datev Dok.-Nr.: 1036228).

Details of the module:
* Configuration of automatic accounts
* Test of datev accounting rules
 
Further information under 
* Launchpad https://launchpad.net/ecoservice-openerp-addons
* Ecoservice Website http://www.ecoservice.de
""",
    "category" : "Accounting",
    "init_xml" : [],
    "update_xml" : [
                    'account_view.xml',
                    'res_company_view.xml',
                    'ecoservice_financeinterface_datev_installer_view.xml'
                    ],
    "demo_xml" : [],
    'test': [],
    "active": False,
    "installable": True
}
