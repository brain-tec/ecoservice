# -*- encoding: utf-8 -*-
""" The account module extends the original OpenERP account objects with different attributes and methods
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
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import ustr
from decimal import Decimal

class account_account(osv.osv):
    """Inherits the account.account class and adds attributes
    """
    _inherit = "account.account"
    _columns = {
                'ustuebergabe': fields.boolean('Datev UST-ID', help=_("""Is required when transferring 
                a sales tax identification number  from the account partner (e.g. EU-Invoice)""")),
                'automatic':fields.boolean('Datev Automatikkonto'),
                'datev_steuer': fields.many2one('account.tax','Datev Steuerkonto'),
                'datev_steuer_erforderlich':fields.boolean('Steuerbuchung erforderlich?'),
    }
    _defaults = {
                 'ustuebergabe': lambda * a: False,
    }
account_account()

class account_tax(osv.osv):
    """Inherits the account.tax class and adds attributes
    """
    _inherit = 'account.tax'
    _columns = {
                'datev_skonto': fields.many2one('account.account','Datev Skontokonto'),
    }
account_tax()


class account_payment_term(osv.osv):
    """Inherits the account.payment.term class and adds attributes
    """
    _inherit = "account.payment.term"
    _columns = {
                'zahlsl': fields.integer('Payment key'),
    }
account_payment_term()

class account_move(osv.osv):
    """ Inherits the account.move class to add checkmethods to the original post methode
    """
    _inherit = "account.move"

    def datev_checks(self, cr, uid, move, context={}):
        """Constraintcheck if export method is 'brutto'
        :param cr: the current row, from the database cursor
        :param uid: the current user’s ID for security checks
        :param move: account_move
        :param ecofikonto: main account of the move
        :param context: context arguments, like lang, time zone
        """
        error = ''
        UmsatzSteuer = Decimal(str(0))
        BerechneteSteuer = Decimal(str(0))
        linecount = 0
        calccount = 0
        taxaccounts = []
        linetax_ids = []
        for line in move.line_id:
            linecount += 1
            if line.account_id.id != line.ecofi_account_counterpart.id:
                if self.pool.get('ecofi').is_taxline(cr, line.account_id.id):
                    UmsatzSteuer += Decimal(str(line.debit))
                    UmsatzSteuer -= Decimal(str(line.credit))
                    for realtax in self.pool.get('ecofi').get_tax(cr, line.account_id.id):
                        taxaccounts.append(realtax)
                else:
                    linetax = False
                    if line.account_tax_id:
                        linetax = line.account_tax_id
                    if line.ecofi_taxid:
                        linetax = line.ecofi_taxid
                    if linetax:
                        calccount += 1
                        linetax_ids.append(linetax.id)  # pylint: disable-msg=E1103
                    taxamount = self.pool.get('ecofi').calculate_tax(cr, uid, line, context)
                    BerechneteSteuer += Decimal(str(taxamount))
                    if line.account_id.automatic is True and linetax is False:
                        error += _("""The Account is an Autoaccount, although the moveline %s has no tax!\n""") % (linecount)
                    if line.account_id.datev_steuer_erforderlich is True and linetax is False:
                        error += _("""The Account requires a tax, although the moveline %s has no tax!\n""") % (linecount)
                    if line.account_id.automatic is True and linetax:
                        if line.account_id.datev_steuer:
                            if linetax.id != line.account_id.datev_steuer.id:  # pylint: disable-msg=E1103
                                error += _("""The account is an Autoaccount, altough the taxaccount (%s) in the moveline %s is an other than the configured %s!\n""") % (linecount,  # pylint: disable-msg=C0301
                                                        linetax.name, line.account_id.datev_steuer.name)  # pylint: disable-msg=E1103
                        else:
                            if linetax != False:
                                error += _("""The account is an Autoaccount, altough the taxaccount (%s) in the moveline %s is an other than the configured %s!\n""") % (linecount,  # pylint: disable-msg=C0301
                                                        linetax.name, line.account_id.datev_steuer.name)  # pylint: disable-msg=E1103
                    if line.account_id.automatic is False and linetax and linetax.buchungsschluessel < 0:  # pylint: disable-msg=E1103
                        error += _(ustr("""The bookingkey for the tax %s is not configured!\n""")) % (linetax.name)  # pylint: disable-msg=E1103,C0301
            else:
                taxamount = self.pool.get('ecofi').calculate_tax(cr, uid, line, context)
                BerechneteSteuer += Decimal(str(taxamount))

        if error == '':
            return False
        return error

    def finance_interface_checks(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        res = super(account_move, self).finance_interface_checks(cr, uid, ids, context=context)
        for move in self.browse(cr, uid, ids, context=context):
            thiserror = ''
            error = self.datev_checks(cr, uid, move, context)
            if error:
                raise osv.except_osv('Error', error)
        return res

account_move()