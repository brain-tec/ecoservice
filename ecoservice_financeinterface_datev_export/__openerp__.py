# -*- encoding: utf-8 -*-
##############################################################################
#    ecoservice_financeinterface_datev_export
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
{
    "name" : "Ecoservice Financial Interface Datev Exports",
    "version" : "1.0",
    "depends" : ["ecoservice_financeinterface"],
    "author" : "ecoservice",
    "website" : "www.ecoservice.de",
    "description": """The module ecoservice_financeinterface_datev_export lets you configure different ascii base data exports.

Details of the module:
* Export of Paymentterms
* Export of Debit and Credit Account

Further information under
* Launchpad https://launchpad.net/ecoservice-openerp-addons
* Ecoservice Website http://www.ecoservice.de
""",
    "category" : "Accounting",
    "init_xml" : [],
    "update_xml" : ['datev_export.xml',
                    'wizard/export_ecofi_datev_export.xml',
                    'security/ir.model.access.csv',
                    ],
    "demo_xml" : [],
    'test': [],
    "active": False,
    "installable": True
}