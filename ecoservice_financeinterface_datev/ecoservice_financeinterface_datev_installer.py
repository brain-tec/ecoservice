# -*- encoding: utf-8 -*-
"""Installer for the datev interface
"""
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

from osv import fields, osv

class ecoservice_financeinterface_datev_installer(osv.osv_memory):
    """ Installer for the Datev interface
    """
    _name = 'ecoservice.financeinterface.datev.installer'
    _inherit = 'res.config.installer'

    _columns = {
        'name': fields.char('Name', size=64),
        'migrate_datev': fields.boolean('Migrate', help="If you select this, all account moves from invoices will be migrated."),
    }

    def execute(self, cr, uid, ids, context=None):
        """
        This function is used to create contact and address from existing partner address
        """
        if context is None:
            context = {}
        record = self.browse(cr, uid, ids, context=context)[0]
        if record.migrate_datev:
            self.pool.get("ecofi").migrate_datev(cr, uid, context=context)

ecoservice_financeinterface_datev_installer()
