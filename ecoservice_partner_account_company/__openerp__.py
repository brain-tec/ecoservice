# -*- encoding: utf-8 -*-
##############################################################################
#    ecoservice_partner_account_company
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
    "name" : "Ecoservice Partner Account Company",
    "version" : "1.0",
    "author" : "ecoservice",
    "category" : "Accounting",
    "website" : "http://www.ecoservice.de",
    "depends" : ["base",
                 "account"
                 ],
    "description": """If a partner is created a new debit and credit account will be created following a 
    sequence that can be created individually per company.""",
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
                    'ecoservice_partner_auto_account_company_data.xml',
                    'ecoservice_partner_auto_account_company_views.xml'
                    ],
    "active": False,
    "installable": True
}
