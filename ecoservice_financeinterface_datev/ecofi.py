# -*- encoding: utf-8 -*-
""" The ecofi module extends the original OpenERP ecofi objects with different attributes and methods
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
from openerp.osv import osv
from decimal import Decimal
from openerp.tools.translate import _
from openerp.tools import ustr
from openerp import workflow
import logging
_logger = logging.getLogger(__name__)


class ecofi(osv.osv):
    """Inherits the ecofi class and adds methods and attributes
    """
    _inherit = 'ecofi'

    def migrate_datev(self, cr, uid, context=None):
        """ Function to migrate old moves to the new interface
        :param cr: the current row, from the database cursor
        :param uid: the current user’s ID for security checks
        :param context: context arguments, like lang, time zone
        """
        if context is None:
            context = {}
        _logger.info("Starting Move Migration")
        invoice_ids = self.pool.get('account.invoice').search(cr, uid, [])
        counter = 0
        for invoice in self.pool.get('account.invoice').browse(cr, uid, invoice_ids, context=context):
            counter += 1
            _logger.info(_("Migrate Move %s / %s") % (counter, len(invoice_ids)))
            if invoice.move_id:
                self.pool.get('account.move').write(cr, uid, [invoice.move_id.id], {
                                   'ecofi_buchungstext': invoice.ecofi_buchungstext or False,
                                })
                move = self.pool.get('account.move').browse(cr, uid, invoice.move_id.id)
                for invoice_line in invoice.invoice_line:
                    if invoice_line.invoice_line_tax_id:
                        for move_line in move.line_ids:
                            if move_line.account_id.id == invoice_line.account_id.id:
                                if move_line.debit + move_line.credit == abs(invoice_line.price_subtotal):
                                    self.pool.get('account.move.line').write(cr, uid, [move_line.id],
                                                            {'ecofi_taxid': invoice_line.invoice_line_tax_id[0].id})
        _logger.info(_("Move Migration Finished"))
        return True

    def field_config(self, cr, uid, move, line, errorcount, partnererror, thislog, thismovename, faelligkeit, datevdict):
        """ Method that generates gets the values for the different Datev columns.
        :param cr: the current row, from the database cursor
        :param uid: the current user’s ID for security checks
        :param move: account_move
        :param line: account_move_line
        :param errorcount: Errorcount
        :param partnererror: Partnererror
        :param thislog: Log
        :param thismovename: Movename
        :param faelligkeit: Fälligkeit
        """
        thisdate = move.date
        datevdict['Datum'] = '%s%s' % (thisdate[8:10], thisdate[5:7])
        if move.name:
            datevdict['Beleg1'] = ustr(move.name)
        if move.journal_id.type == 'purchase' and move.ref:
            datevdict['Beleg1'] = ustr(move.ref)
        datevdict['Beleg1'] = datevdict['Beleg1'][-12:]
        if faelligkeit:
            datevdict['Beleg2'] = faelligkeit
        datevdict['Waehrung'], datevdict['Kurs'] = self.format_waehrung(cr, uid, line, context={'lang': 'de_DE', 'date': thisdate})
        if line.move_id.ecofi_buchungstext:
            datevdict['Buchungstext'] = ustr(line.move_id.ecofi_buchungstext)
        if line.account_id.ustuebergabe:
            if move.partner_id:
                if move.partner_id.vat:
                    datevdict['EulandUSTID'] = ustr(move.partner_id.vat)
            if datevdict['EulandUSTID'] == '':
                errorcount += 1
                partnererror.append(move.partner_id.id)
                thislog = thislog + thismovename + _("Error: No sales tax identification number stored in the partner!\n")
        return (errorcount, partnererror, thislog, thismovename, datevdict)

    def format_umsatz(self, cr, uid, lineumsatz, context={}):
        """ Returns the formatted amount
        :param cr: the current row, from the database cursor
        :param uid: the current user’s ID for security checks
        :param lineumsatz: amountC
        :param context: context arguments, like lang, time zone
        :param lineumsatz:
        :param context:
        """
        Umsatz = ''
        Sollhaben = ''
        if lineumsatz < 0:
            Umsatz = str(lineumsatz * -1).replace('.', ',')
            Sollhaben = 's'
        if lineumsatz > 0:
            Umsatz = str(lineumsatz).replace('.', ',')
            Sollhaben = 'h'
        if lineumsatz == 0:
            Umsatz = str(lineumsatz).replace('.', ',')
            Sollhaben = 's'
        return Umsatz, Sollhaben

    def format_waehrung(self, cr, uid, line, context={}):
        """ Formats the currency for the export
        :param cr: the current row, from the database cursor
        :param uid: the current user’s ID for security checks
        :param line: account_move_line
        :param context: context arguments, like lang, time zone
        """
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        Waehrung = False
        if user.company_id:
            Waehrung = user.company_id.currency_id.id
        else:
            thiscompany = self.pool.get('res.company').search(cr, uid, [('parent_id', '=', False)])[0]
            thiscompany = self.pool.get('res.company').browse(cr, uid, [thiscompany], context=context)[0]
            Waehrung = thiscompany.currency_id.id
        if line.currency_id:
            Waehrung = line.currency_id.id
        if Waehrung:
            thisw = self.pool.get('res.currency').browse(cr, uid, Waehrung, context=context)
            Waehrung = thisw.name
            if Waehrung != 'EUR':
                Faktor = ustr(thisw.rate).replace('.', ',')
            else:
                Faktor = ''
        return Waehrung, Faktor

    def generate_csv(self, cr, uid, ecofi_csv, bookingdict, log, context={}):
        """ Implements the generate_csv method for the datev interface
        """
        if context.has_key('export_interface'):
            if context['export_interface'] == 'datev':
                ecofi_csv.writerow(bookingdict['buchungsheader'])
                for buchungsatz in bookingdict['buchungen']:
                    ecofi_csv.writerow(buchungsatz)
        (ecofi_csv, log) = super(ecofi, self).generate_csv(cr, uid, ecofi_csv, bookingdict, log, context=context)
        return ecofi_csv, log    
        
    def generate_csv_move_lines(self, cr, uid, move, buchungserror, errorcount, thislog, thismovename, exportmethod,
                          partnererror, buchungszeilencount, bookingdict, context={}):
        """ Implements the generate_csv_move_lines method for the datev interface     
        """
        if context.has_key('export_interface'):
            if context['export_interface'] == 'datev':
                if bookingdict.has_key('buchungen') is False:
                    bookingdict['buchungen'] = []
                if bookingdict.has_key('buchungsheader') is False:
                    bookingdict['buchungsheader'] = self.buchungenHeaderDatev()    
                faelligkeit = False
                for line in move.line_ids:
                    if line.debit == 0 and line.credit==0:
                        continue
                    datevkonto = line.ecofi_account_counterpart.code
                    datevgegenkonto = ustr(line.account_id.code)
                    if datevgegenkonto == datevkonto:
                        if line.date_maturity:
                            faelligkeit = '%s%s%s' % (line.date[8:10], line.date[5:7], line.date[2:4])
                        continue
                    lineumsatz = Decimal(str(0))
                    lineumsatz += Decimal(str(line.debit))
                    lineumsatz -= Decimal(str(line.credit))
                    context['waehrung'] = False
                    if line.amount_currency != 0.0:
                        lineumsatz = Decimal(str(line.amount_currency))
                        context['waehrung'] = True
                    buschluessel = ''  
                    if exportmethod == 'brutto':
                        if self.pool.get('ecofi').is_taxline(cr, line.account_id.id) and not line.ecofi_bu == 'SD':
                            continue
                        if line.ecofi_bu and line.ecofi_bu == '40':
                            buschluessel = '40'
                        else:
                            taxamount = self.pool.get('ecofi').calculate_tax(cr, uid, line, context)
                            lineumsatz = lineumsatz + Decimal(str(taxamount))
                            linetax = self.get_line_tax(cr, uid, line)
                            if line.account_id.automatic is False and linetax:
                                buschluessel = str(linetax.buchungsschluessel) # pylint: disable-msg=E1103
                    umsatz, sollhaben = self.format_umsatz(cr, uid, lineumsatz, context=context)           
                    datevdict = {'Sollhaben': sollhaben, 
                                 'Umsatz': umsatz, 
                                 'Gegenkonto': datevgegenkonto, 
                                 'Datum':'',
                                 'Konto': datevkonto or '', 
                                 'Beleg1':'', 
                                 'Beleg2':'',
                                 'Waehrung':'', 
                                 'Buschluessel': buschluessel,
                                 'Kost1':'',
                                 'Kost2':'', 
                                 'Kostmenge':'', 
                                 'Skonto':'', 
                                 'Buchungstext':'',
                                 'EulandUSTID':'', 
                                 'EUSteuer':'', 
                                 'Basiswaehrungsbetrag':'',
                                 'Basiswaehrungskennung':'', 
                                 'Kurs':'', 
                                 'Movename': ustr(move.name)
                                 }
                    (errorcount, partnererror, thislog, thismovename, datevdict) = self.field_config(cr,
                                                                    uid, move, line, errorcount, partnererror, thislog, 
                                                                    thismovename, faelligkeit, datevdict)
                    bookingdict['buchungen'].append(self.buchungenCreateDatev(datevdict))
                    buchungszeilencount += 1
        buchungserror, errorcount, thislog, partnererror, buchungszeilencount, bookingdict = super(ecofi, self).generate_csv_move_lines(cr,
            uid, move, buchungserror, errorcount, thislog, thismovename, exportmethod, partnererror, buchungszeilencount, bookingdict, 
            context=context)
        return buchungserror, errorcount, thislog, partnererror, buchungszeilencount, bookingdict
   
    def buchungenHeaderDatev(self):
        """ Method that creates the Datev CSV Headerlione
        """
        buchung = []
        buchung.append(ustr("Währungskennung").encode("iso-8859-1"))
        buchung.append(ustr("Soll-/Haben-Kennzeichen").encode("iso-8859-1"))
        buchung.append(ustr("Umsatz (ohne Soll-/Haben-Kennzeichen)").encode("iso-8859-1"))
        buchung.append(ustr("BU-Schlüssel ").encode("iso-8859-1"))
        buchung.append(ustr("Gegenkonto (ohne BU-Schlüssel)").encode("iso-8859-1"))
        buchung.append(ustr("Belegfeld 1").encode("iso-8859-1"))
        buchung.append(ustr("Belegfeld 2").encode("iso-8859-1"))
        buchung.append(ustr("Datum").encode("iso-8859-1"))
        buchung.append(ustr("Konto").encode("iso-8859-1"))
        buchung.append(ustr("Kostfeld 1").encode("iso-8859-1"))
        buchung.append(ustr("Kostfeld 2").encode("iso-8859-1"))
        buchung.append(ustr("Kostmenge").encode("iso-8859-1"))
        buchung.append(ustr("Skonto").encode("iso-8859-1"))
        buchung.append(ustr("Buchungstext").encode("iso-8859-1"))
        buchung.append(ustr("EU-Land und UStID").encode("iso-8859-1"))
        buchung.append(ustr("EU-Steuersatz").encode("iso-8859-1"))
        buchung.append(ustr("Basiswährungsbetrag").encode("iso-8859-1"))
        buchung.append(ustr("Basiswährungskennung").encode("iso-8859-1"))
        buchung.append(ustr("Kurs").encode("iso-8859-1"))
        return buchung
            
    def buchungenCreateDatev(self, datevdict):
        """Method that creates the datev csv moveline
        """
        buchung = []                     
        buchung.append(datevdict['Waehrung'].encode("iso-8859-1"))
        buchung.append(datevdict['Sollhaben'].encode("iso-8859-1"))
        buchung.append(datevdict['Umsatz'].encode("iso-8859-1"))
        if datevdict['Buschluessel'] == '0':
            datevdict['Buschluessel'] = ''            
        buchung.append(datevdict['Buschluessel'].encode("iso-8859-1"))
        buchung.append(datevdict['Gegenkonto'].encode("iso-8859-1"))
        buchung.append(datevdict['Beleg1'].encode("iso-8859-1"))          
        buchung.append(datevdict['Beleg2'].encode("iso-8859-1"))
        buchung.append(datevdict['Datum'].encode("iso-8859-1"))
        buchung.append(datevdict['Konto'].encode("iso-8859-1"))
        buchung.append(datevdict['Kost1'].encode("iso-8859-1"))
        buchung.append(datevdict['Kost2'].encode("iso-8859-1"))
        buchung.append(datevdict['Kostmenge'].encode("iso-8859-1"))
        buchung.append(datevdict['Skonto'].encode("iso-8859-1"))
        datevdict['Buchungstext'] = datevdict['Buchungstext'][0:30]
        buchung.append(datevdict['Buchungstext'].encode("iso-8859-1", 'ignore'))
        buchung.append(datevdict['EulandUSTID'].encode("iso-8859-1"))
        buchung.append(datevdict['EUSteuer'].encode("iso-8859-1"))
        buchung.append(datevdict['Basiswaehrungsbetrag'].encode("iso-8859-1"))
        buchung.append(datevdict['Basiswaehrungskennung'].encode("iso-8859-1"))
        buchung.append(datevdict['Kurs'].encode("iso-8859-1"))
        return buchung
    
ecofi()
