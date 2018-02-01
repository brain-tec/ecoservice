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
from osv import fields, osv
from tools.translate import _


class ecoservice_partner_auto_account_company(osv.osv):
    _name = "ecoservice.partner.auto.account.company"
    _description = "Configuration rules for automatic account generation"


    def _constraint_sequence(self, cr, uid, ids):
        for config in self.browse(cr, uid, ids):
            receivable_company = config.receivable_sequence_id.company_id and config.receivable_sequence_id.company_id.id or 0
            payable_company = config.payable_sequence_id.company_id and config.payable_sequence_id.company_id.id or 0
            config_company = config.company_id and config.company_id.id or 0
            if (receivable_company != payable_company) or (receivable_company != config_company):
                return False
        return True

    _columns = {
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'receivable_sequence_id': fields.many2one('ir.sequence', 'Receivable Sequence', required=True, domain=[('code', '=', 'partner.auto.receivable')]),
        'payable_sequence_id': fields.many2one('ir.sequence', 'Payable Sequence', required=True, domain=[('code', '=', 'partner.auto.payable')]),
        'receivable_template_id': fields.many2one('account.account', 'Receivable account Template', required=True),
        'payable_template_id': fields.many2one('account.account', 'Payable account Template', required=True, domain=[('type', '=', 'payable')]),
    }
    _sql_constraints = [
        ('code_company_uniq', 'unique (company_id)', _('The configuration must be unique per company !')),
        ('code_payable_uniq', 'unique (payable_sequence_id)', _('The Payable Sequence account must be unique per configuration')),
        ('code_receivable_uniq', 'unique (receivable_sequence_id)', _('The Receivable Sequence account must be unique per configuration'))
    ]
    _constraints = [
        (_constraint_sequence, _('The companys in the Sequences are not the same as the configured Company'), []),
    ]

    def get_accounts(self, cr, uid, partner_id, context=None):
        if context is None:
            context = {}
        partner_name = self.pool.get('res.partner').read(cr, uid, partner_id, ['name'], context=context)['name']
        user_company = self.pool.get('res.users').read(cr, uid, uid, ['company_id'])['company_id'][0]
        config_ids = self.search(cr, uid, [('company_id', '=', user_company)])
        account_obj = self.pool.get('account.account')
        for config in self.browse(cr, uid, config_ids, context=context):
            if 'type' in context and context['type'] == 'receivable' or 'type' not in context:
                receivable_field_ids = self.pool.get('ir.model.fields').search(cr, uid, [('model', '=', 'res.partner'), ('name', '=', 'property_account_receivable')])
                if len(receivable_field_ids) == 1:
                    property_ids = self.pool.get('ir.property').search(cr, uid, [('company_id', '=', config.company_id.id),
                                                                                 ('res_id', '=', 'res.partner,%s' % (partner_id)),
                                                                                 ('name', '=', 'property_account_receivable'),
                                                                                 ('fields_id', '=', receivable_field_ids[0])])
                    receivable_code = self.pool.get('ir.sequence').get_id(cr, uid, config.receivable_sequence_id.id, context=context)
                    receivable_account_values = {
                        'name': partner_name,
                        'currency_id': config.receivable_template_id.currency_id and config.receivable_template_id.currency_id.id or False,
                        'code': receivable_code,
                        'type': config.receivable_template_id.type,
                        'user_type': config.receivable_template_id.user_type and config.receivable_template_id.user_type.id or False,
                        'reconcile': config.receivable_template_id.reconcile,
                        'shortcut': config.receivable_template_id.shortcut,
                        'note': config.receivable_template_id.note,
                        'tax_ids': [(6, 0, config.receivable_template_id.tax_ids)],
                        'company_id': config.company_id.id,
                    }
                    receivable_account_id = account_obj.create(cr, uid, receivable_account_values, context=context)
                    receivable_property_value = {
                                        'name': 'property_account_receivable',
                                        'value_reference': 'account.account,%s' % (receivable_account_id),
                                        'res_id': 'res.partner,%s' % (partner_id),
                                        'company_id': config.company_id.id,
                                        'fields_id': receivable_field_ids[0],
                                        'type': 'many2one',
                    }
                    if len(property_ids) == 0:
                        self.pool.get('ir.property').create(cr, uid, receivable_property_value, context=context)
                    else:
                        self.pool.get('ir.property').write(cr, uid, property_ids, receivable_property_value, context=context)
            if 'type' in context and context['type'] == 'payable' or 'type' not in context:
                payable_field_ids = self.pool.get('ir.model.fields').search(cr, uid, [('model', '=', 'res.partner'), ('name', '=', 'property_account_payable')])
                if len(payable_field_ids) == 1:
                    payable_code = self.pool.get('ir.sequence').get_id(cr, uid, config.payable_sequence_id.id, context=context)
                    payable_account_values = {
                        'name': partner_name,
                        'currency_id': config.payable_template_id.currency_id and config.payable_template_id.currency_id.id or False,
                        'code': payable_code,
                        'type': config.payable_template_id.type,
                        'user_type': config.payable_template_id.user_type and config.payable_template_id.user_type.id or False,
                        'reconcile': config.payable_template_id.reconcile,
                        'shortcut': config.payable_template_id.shortcut,
                        'note': config.payable_template_id.note,
                        'tax_ids': [(6, 0, config.payable_template_id.tax_ids)],
                        'company_id': config.company_id.id,
                    }
                    payable_account_id = account_obj.create(cr, uid, payable_account_values, context=context)
                    payable_property_value = {
                                        'name': 'property_account_payable',
                                        'value_reference': 'account.account,%s' % (payable_account_id),
                                        'res_id': 'res.partner,%s' % (partner_id),
                                        'company_id': config.company_id.id,
                                        'fields_id': payable_field_ids[0],
                                        'type': 'many2one',
                    }
                    property_ids = self.pool.get('ir.property').search(cr, uid, [('company_id', '=', config.company_id.id),
                                                                                 ('res_id', '=', 'res.partner,%s' % (partner_id)),
                                                                                 ('name', '=', 'property_account_payable'),
                                                                                 ('fields_id', '=', payable_field_ids[0])])
                    if len(property_ids) == 0:
                        self.pool.get('ir.property').create(cr, uid, payable_property_value, context=context)
                    else:
                        self.pool.get('ir.property').write(cr, uid, property_ids, payable_property_value, context=context)
        return True

ecoservice_partner_auto_account_company()


class eco_partner(osv.osv):
    _inherit = 'res.partner'

    def create_accounts(self, cr, uid, ids, context={}):
        for partner in ids:
            self.pool.get('ecoservice.partner.auto.account.company').get_accounts(cr, uid, partner, context=context)
        return True
eco_partner()
