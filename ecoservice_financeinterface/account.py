# -*- encoding: utf-8 -*-
""" The account module extends the original OpenERP account objects with different attributes and methods
"""
##############################################################################
#    ecoservice_financeinterface
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
from openerp.tools.float_utils import float_round
import openerp.addons.decimal_precision as dp


class account_move(osv.osv):
    """ Inherits the account.move class and adds methods and attributes
    """
    _inherit = "account.move"
    _columns = {
                'vorlauf_id': fields.many2one('ecofi', 'Export', readonly=True, ondelete='set null', select=2),
                'ecofi_buchungstext': fields.char('Export Voucher Text', size=30),
                'ecofi_manual': fields.boolean('Set Counteraccounts manual'),
                'ecofi_autotax': fields.boolean('Automatic Tax Lines'),
    }

    def unlink(self, cr, uid, ids, context=None):
        """Method that prevents that account_moves which have been exported are being deleted

        :param cr: the current row, from the database cursor
        :param uid: the current user’s ID for security checks
        :param ids: List of account_move IDs
        :param context: context arguments, like lang, time zone
        """
        if context is None:
            context = {}
        for thismove in self.browse(cr, uid, ids, context):
            if 'delete_none' in context:
                if context['delete_none'] is True:
                    continue
            if thismove.vorlauf_id:
                raise osv.except_osv(_('Warning!'), _('Account moves which are already in an export can not be deleted!'))
        return super(account_move, self).unlink(cr, uid, ids, context)

    def financeinterface_test_move(self, cr, uid, move, context=None):
        """ Test if the move account counterparts are set correct """
        if context is None:
            context = {}
        res = ''
        checkdict = {}
        for line in self.pool.get('account.move').browse(cr, uid, move, context=context)['line_id']:
            if line.account_id and line.ecofi_account_counterpart:
                if line.account_id.id != line.ecofi_account_counterpart.id:
                    if line.ecofi_account_counterpart.id not in checkdict:
                        checkdict[line.ecofi_account_counterpart.id] = {}
                        checkdict[line.ecofi_account_counterpart.id]['check'] = 0
                        checkdict[line.ecofi_account_counterpart.id]['real'] = 0
                    checkdict[line.ecofi_account_counterpart.id]['check'] += line.debit - line.credit
                else:
                    if line.ecofi_account_counterpart.id not in checkdict:
                        checkdict[line.ecofi_account_counterpart.id] = {}
                        checkdict[line.ecofi_account_counterpart.id]['check'] = 0
                        checkdict[line.ecofi_account_counterpart.id]['real'] = 0
                    checkdict[line.ecofi_account_counterpart.id]['real'] += line.debit - line.credit
            else:
                res += _('Not all move lines have an account and an account counterpart defined.')
                return res
        for key in checkdict:
            if abs(checkdict[key]['check'] + checkdict[key]['real']) > 10 ** -4:
                res += _('The sum of the account lines debit/credit and the account_counterpart lines debit/credit is no Zero!')
                return res
        return False

    def finance_interface_checks(self, cr, uid, ids, context=None):
        """Hook Method for different checks wich is called if the moves post method is called """
        if context is None:
            context = {}
        for move in self.browse(cr, uid, ids, context=context):
            thiserror = ''
            if move.ecofi_manual is False:
                error = self.pool.get('ecofi').set_main_account(cr, uid, move, context=context)
                if error:
                    thiserror += error
                if thiserror != '':
                    raise osv.except_osv('Error', thiserror)
            error = self.financeinterface_test_move(cr, uid, move.id, context=context)
            if error:
                raise osv.except_osv('Error', error)
        return True

    def button_cancel(self, cr, uid, ids, context=None):
        """Check if the move has already been exported"""
        res = super(account_move, self).button_cancel(cr, uid, ids, context=context)
        for move in self.browse(cr, uid, ids, context=context):
            if move.vorlauf_id:
                raise osv.except_osv(_('Error!'), _('You cannot modify an already exported move.'))
            if move.ecofi_autotax:
                for line in move.line_id:
                    if line.ecofi_move_line_autotax:
                        self.pool.get('account.move.line').delete_autotaxline(cr, uid, [line.id], context=context)
        return res

    def post(self, cr, uid, ids, context=None):
        """ If a move is posted to a journal the Datev corresponding checks are being performed.

        :param ids: List of Move Ids
        """
        for move in self.browse(cr, uid, ids, context=context):
            if move.ecofi_autotax:
                for line in move.line_id:
                    if self.pool.get('ecofi').is_taxline(cr, line.account_id.id) and not line.ecofi_move_line_autotax:
                        raise osv.except_osv(_('Error!'), _('You can not create tax lines in an auto tax move.'))
                    self.pool.get('account.move.line').create_update_taxline(cr, uid, [line.id], context=context)
        if context is None:
            context = {}
        # HACK: 15.09.2014 14:16:42: olivier: do first the finance_interface_checks and then the post of the account_move -> otherwise we got an error when booking the opening entries
        self.finance_interface_checks(cr, uid, ids, context)
        res = super(account_move, self).post(cr, uid, ids, context=context)
        return res
account_move()


class account_move_line(osv.osv):
    """Inherits the account.move.line class and adds attributes
    """

    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if 'counterpart_name' in context and context['counterpart_name']:
            if not ids:
                return []
            result = []
            for line in self.browse(cr, uid, ids, context=context):
                if line.ref:
                    result.append((line.id, (line.name or '') + ' (' + line.ref + ')'))
                else:
                    result.append((line.id, line.name))
            return result
        else:
            return super(account_move_line, self).name_get(cr, uid, ids, context=context)

    _inherit = "account.move.line"
    _columns = {
                'ecofi_taxid': fields.many2one('account.tax', 'Move Tax'),
                'ecofi_brutto_credit': fields.float('Amount Credit Brutto', digits_compute=dp.get_precision('Account')),
                'ecofi_brutto_debit': fields.float('Amount Debit Brutto', digits_compute=dp.get_precision('Account')),
                'ecofi_account_counterpart': fields.many2one('account.account', 'Account Counterpart', ondelete='restrict', select=2),
                'ecofi_move_line_autotax': fields.many2one('account.move.line', 'Move Counterpart', ondelete='cascade', select=2),
                'ecofi_manual': fields.related('move_id', 'ecofi_manual', type='boolean', string="Manual", store=True),
    }

    def delete_autotaxline(self, cr, uid, move_lineids, context=None):
        """ Method that deletes the corresponding auto generated tax moves"""
        if context is None:
            context = {}
        for move_line in self.browse(cr, uid, move_lineids, context=context):
            move_line_main = self.browse(cr, uid, move_line.ecofi_move_line_autotax.id, context=context)
            update = {
                        'debit': move_line_main.ecofi_brutto_debit,
                        'credit': move_line_main.ecofi_brutto_credit,
                        'tax_code_id': False,
                        'tax_amount': 0.00,
                      }
            self.pool.get('account.move.line').unlink(cr, uid, [move_line.id], context=context)
            self.write(cr, uid, [move_line_main.id], update, context=context)
        return True

    def create_update_taxline(self, cr, uid, ids, context=None):
        "Method to create Tax Lines in manual Mode"
        if context is None:
            context = {}
        tax_obj = self.pool.get('account.tax')
        for move_line in self.pool.get('account.move.line').browse(cr, uid, ids, context=context):
            if move_line.ecofi_move_line_autotax:
                self.delete_autotaxline(cr, uid, [move_line.id], context=context)
            if move_line.ecofi_taxid:
                journal = self.pool.get('account.journal').browse(cr, uid, move_line.move_id.journal_id.id, context=context)
                tax_id = tax_obj.browse(cr, uid, move_line.ecofi_taxid.id)
                total = move_line.debit - move_line.credit
                if journal.type in ('purchase_refund', 'sale_refund'):
                    base_code = 'ref_base_code_id'
                    tax_code = 'ref_tax_code_id'
                    account_id = 'account_paid_id'
                    base_sign = 'ref_base_sign'
                    tax_sign = 'ref_tax_sign'
                else:
                    base_code = 'base_code_id'
                    tax_code = 'tax_code_id'
                    account_id = 'account_collected_id'
                    base_sign = 'base_sign'
                    tax_sign = 'tax_sign'
                all_taxes = {
                        'debit': 0,
                        'credit': 0,
                }
                tmp_cnt = 0
                real_tax_code_id = False
                real_tax_amount = 0
                for tax in tax_obj.compute_all_inv(cr, uid, [tax_id], total, 1.00, force_excluded=True).get('taxes'):
                    data = {
                        'move_id': move_line.move_id.id,
                        'name': ustr(move_line.name or '') + ' ' + ustr(tax['name'] or ''),
                        'date': move_line.date,
                        'partner_id': move_line.partner_id and move_line.partner_id.id or False,
                        'ref': move_line.ref and move_line.ref or False,
                        'account_tax_id': False,
                        'tax_code_id': tax[tax_code],
                        'tax_amount': tax[tax_sign] * abs(tax['amount']),
                        'account_id': tax[account_id] or move_line.account_id.id,
                        'credit': tax['amount'] < 0 and -tax['amount'] or 0.0,
                        'debit': tax['amount'] > 0 and tax['amount'] or 0.0,
                        'ecofi_move_line_autotax': move_line.id,
                    }
                    if data['tax_code_id']:
                        self.create(cr, uid, data, context)
                    if tmp_cnt == 0:
                        if tax[base_code]:
                            tmp_cnt += 1
                            real_tax_code_id = tax[base_code]
                            real_tax_amount = tax[base_sign] * abs(total)
                    all_taxes['debit'] += data['debit']
                    all_taxes['credit'] += data['credit']
                if all_taxes['debit'] >= all_taxes['credit']:
                    all_taxes['debit'] = all_taxes['debit'] - all_taxes['credit']
                    all_taxes['credit'] = 0
                else:
                    all_taxes['credit'] = all_taxes['credit'] - all_taxes['debit']
                    all_taxes['debit'] = 0
                actual_move = self.browse(cr, uid, move_line.id, context=context)
                self.write(cr, uid, [move_line.id], {
                    'ecofi_brutto_credit': actual_move.credit,
                    'ecofi_brutto_debit': actual_move.debit,
                    'debit': actual_move.debit - all_taxes['debit'],
                    'credit': actual_move.credit - all_taxes['credit'],
                    'tax_code_id': real_tax_code_id,
                    'tax_amount': real_tax_amount
                }, context=context)
account_move_line()


class account_invoice(osv.osv):
    """ Inherits the account.invoice class and adds methods and attributes
    """
    _inherit = 'account.invoice'
    _columns = {
                'ecofi_buchungstext': fields.char('Export Voucher Text', size=30),
    }

    def action_move_create(self, cr, uid, ids, *args):
        """Extends the original action_move_create so that if
         an invoice is confirmed the finance interface attributes are transfered to the account move
        :param cr: the current row, from the database cursor,
        :param uid: the current user’s ID for security checks,
        :param ids: List of account_move IDs
        """
        thisreturn = super(account_invoice, self).action_move_create(cr, uid, ids, *args)
        if thisreturn:
            invoice = self.browse(cr, uid, ids)[0]
            self.pool.get('account.move').write(cr, uid, [invoice.move_id.id], {
                               'ecofi_buchungstext': invoice.ecofi_buchungstext or False,
                                })
        return thisreturn

    def inv_line_characteristic_hashcode(self, invoice, invoice_line):
        """Transfers the line tax to the hash code
        :param invoice: Invoice Object
        :param invoice_line: Invoice Line Object
        """
        res = super(account_invoice, self).inv_line_characteristic_hashcode(invoice, invoice_line)
        res += "-%s" % (invoice_line.get('ecofi_taxid', "False"))
        return res

    def line_get_convert(self, cr, uid, x, part, date, context=None):
        """Extends the line_get_convert method that it transfers the tax to the account_move_line
        """
        res = super(account_invoice, self).line_get_convert(cr, uid, x, part, date, context=context)
        if x.get('taxes', False):
            for tax in x.get('taxes', False):
                res['ecofi_taxid'] = tax.id
        return res

account_invoice()


class account_invoice_line(osv.osv):
    """ Inherits the account.invoice.line class and adds methods and attributes
    """
    _inherit = 'account.invoice.line'

    def create(self, cr, uid, vals, context=None):
        """Prevent that a user places two different taxes in an invoice line
        """
        if vals.get('invoice_line_tax_id', False):
            if len(vals['invoice_line_tax_id'][0][2]) > 1:
                raise osv.except_osv(_("Error"), _("""There can only be one tax per invoice line"""))
        result = super(account_invoice_line, self).create(cr, uid, vals, context=context)
        return result

    def write(self, cr, uid, ids, vals, context=None):
        """Prevent that a user places two different taxes in an invoice line
        """
        if vals.get('invoice_line_tax_id', False):
            if len(vals['invoice_line_tax_id'][0][2]) > 1:
                raise osv.except_osv(_("Error"), _("""There can only be one tax per invoice line"""))
        return super(account_invoice_line, self).write(cr, uid, ids, vals, context=context)
account_invoice_line()


class account_tax(osv.osv):
    """Inherits the account.tax class and adds attributes
    """
    _inherit = 'account.tax'
    _columns = {
                'buchungsschluessel': fields.integer('Posting key', required=True),
    }
    _defaults = {
                 'buchungsschluessel': lambda * a: -1,
    }

    def compute_all_inv(self, cr, uid, taxes, price_unit, quantity, product=None, partner=None, force_excluded=False):
        """
        :param force_excluded: boolean used to say that we don't want to consider the value of field price_include of
            tax. It's used in encoding by line where you don't matter if you encoded a tax with that boolean to True or
            False
        RETURN: {
                'total': 0.0,                # Total without taxes
                'total_included: 0.0,        # Total with taxes
                'taxes': []                  # List of taxes, see compute for the format
            }
        """

        # By default, for each tax, tax amount will first be computed
        # and rounded at the 'Account' decimal precision for each
        # PO/SO/invoice line and then these rounded amounts will be
        # summed, leading to the total amount for that tax. But, if the
        # company has tax_calculation_rounding_method = round_globally,
        # we still follow the same method, but we use a much larger
        # precision when we round the tax amount for each line (we use
        # the 'Account' decimal precision + 5), and that way it's like
        # rounding after the sum of the tax amounts of each line
        precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        tax_compute_precision = precision
        if taxes and taxes[0].company_id.tax_calculation_rounding_method == 'round_globally':
            tax_compute_precision += 5
        totalin = totalex = float_round(price_unit * quantity, precision)
        tin = []
        tex = []
        for tax in taxes:
            tin.append(tax)
        print tex
        print tin
        tin = self.compute_inv(cr, uid, tin, price_unit, quantity, product=product, partner=partner, precision=tax_compute_precision)
        for r in tin:
            totalex -= r.get('amount', 0.0)
        totlex_qty = 0.0
        try:
            totlex_qty = totalex / quantity
        except:
            pass
        tex = self._compute(cr, uid, tex, totlex_qty, quantity, product=product, partner=partner, precision=tax_compute_precision)
        for r in tex:
            totalin += r.get('amount', 0.0)
        return {
            'total': totalex,
            'total_included': totalin,
            'taxes': tin + tex
        }
account_tax()
