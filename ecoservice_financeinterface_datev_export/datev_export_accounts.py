# -*- encoding: utf-8 -*- # pylint: disable-msg=C0302
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
from osv import osv, fields
from tools import ustr
from tools.translate import _
from openerp import addons
from mako.template import Template as MakoTemplate


class ecofi_datev_formate(osv.osv):
    _inherit = 'ecofi.datev.formate'

    def _get_export_type(self, cr, uid, context={}):
        """Method that can be used by other Modules to add their interface to the selection of possible export formats"""
        res = super(ecofi_datev_formate, self)._get_export_type(cr, uid, context=context)
        res.append(('pktr', _('Accounts')))
        return res

    _columns = {
        'datev_type': fields.selection(_get_export_type, 'Exporttype'),
    }

    def get_partner(self, cr, uid, account_id, context={}):
        """ GET Partner Objects for the corresponding account_id"""
        thissql = """SELECT id from res_partner where id in
                        (SELECT split_part(res_id, ',', 2)::integer from ir_property
                        WHERE res_id like 'res.partner%' and value_reference = 'account.account,""" + str(account_id) + """')
                        and parent_id is Null """
        cr.execute(thissql)
        partner_ids = map(lambda x: int(x[0]), cr.fetchall())
        if len(partner_ids) == 1:
            partner_ids += self.pool.get('res.partner').search(cr, uid, [('parent_id', '=', partner_ids[0])])
            partners = self.pool.get('res.partner').read(cr, uid, partner_ids, ['type'], context=context)
            return_partner = False
            for partner in partners:
                if partner['type'] == 'invoice':
                    return_partner = partner['id']
                    break
                elif partner['type'] == 'default':
                    return_partner = partner['id']
                else:
                    if return_partner is False:
                        return_partner = partner['id']
            if return_partner:
                return self.pool.get('res.partner').browse(cr, uid, return_partner, context=context)
        else:
            return False

    def getfields_defaults(self, cr, thisimport, context=None):
        """Return the Defaults MakeHelp and CSV Template File"""
        if context is None:
            context = {}
        res = super(ecofi_datev_formate, self).getfields_defaults(cr, thisimport, context=context)
        if thisimport.datev_type == 'pktr':
            res['module'] = 'ecoservice_financeinterface_datev_export'
            res['csv_template'] = 'csv_templates/datev_deb_kred.csv'
            res['mako_help'] = _("""Possible Mako Object account and partner

            If you want to export the Code of the account and the Name of the Partner use:
            ${account.code} and ${partner.name} as Makotext.
            """)
        return res

    def generate_export_csv(self, cr, uid, export, ecofi_csv, context=None):
        """Funktion that fills the CSV Export"""
        if context is None:
            context = {}
        res = super(ecofi_datev_formate, self).generate_export_csv(cr, uid, export, ecofi_csv, context=context)
        if export.datev_type == 'pktr':
            try:
                domain = eval(export.datev_domain)
            except:
                domain = []
            account_ids = self.pool.get('account.account').search(cr, uid, domain, order='code asc', context=context)
            thisline = []
            for spalte in export.csv_spalten:
                if spalte.mako or 'export_all' in context:
                    thisline.append(ustr(spalte.feldname).encode('encoding' in context and context['encoding'] or 'iso-8859-1'))
            ecofi_csv.writerow(thisline)
            log = ''
            for account in self.pool.get('account.account').browse(cr, uid, account_ids, context=context):
                thisline = []
                writeline = True
                for spalte in export.csv_spalten:
                    if spalte.mako or 'export_all' in context:
                        try:
                            partner = self.get_partner(cr, uid, account.id, context=context)
                            reply = MakoTemplate(spalte.mako).render_unicode(account=account, partner=partner)
                            if reply == 'False':
                                reply = ''
                            convertet_value = self.pool.get('ecofi.datev.formate').convert_value(spalte.typ, reply, context=context)
                            if convertet_value['value'] is not False:
                                thisline.append(convertet_value['value'])
                            else:
                                log += _("Account: %s could not be exported!\n" % (account.code))
                                log += "\t %s\n" % (convertet_value['log'])
                                writeline = False
                                break
                        except:
                            thisline.append('')
                if writeline:
                    ecofi_csv.writerow(thisline)
            res['log'] += log
        return res
ecofi_datev_formate()
