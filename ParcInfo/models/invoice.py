from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ParcInvoice(models.Model):
    _name = 'parc.invoice'
    _description = 'Facture du parc informatique'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Référence', readonly=True, default=lambda self: _('Nouveau'))
    contract_id = fields.Many2one('parc.contract', string='Contrat', required=True)
    client_id = fields.Many2one('parc.client', string='Client', related='contract_id.client_id', store=True)
    
    invoice_date = fields.Date(string='Date de facturation', default=fields.Date.today)
    due_date = fields.Date(string='Date d\'échéance')
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('invoiced', 'Facturé'),
        ('paid', 'Payé'),
        ('cancelled', 'Annulé'),
    ], string='État', default='draft', tracking=True)
    
    amount = fields.Float(string='Montant', related='contract_id.amount', readonly=True)
    currency_id = fields.Many2one('res.currency', related='contract_id.currency_id', readonly=True)
    
    invoice_id = fields.Many2one('account.move', string='Facture associée')
    company_id = fields.Many2one('res.company', string='Société', default=lambda self: self.env.company)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Nouveau')) == _('Nouveau'):
                vals['name'] = self.env['ir.sequence'].next_by_code('parc.invoice.sequence') or _('Nouveau')
        return super().create(vals_list)
    
    def action_generate_invoice(self):
        """Générer une facture client"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_("Vous ne pouvez générer une facture que pour les enregistrements en état 'Brouillon'."))
                
            if not record.contract_id.client_id.partner_id:
                raise UserError(_("Le client doit avoir un partenaire associé pour créer une facture."))
                
            invoice_vals = {
                'partner_id': record.contract_id.client_id.partner_id.id,
                'invoice_date': record.invoice_date,
                'invoice_date_due': record.due_date,
                'move_type': 'out_invoice',
                'invoice_line_ids': [(0, 0, {
                    'name': f"Services pour {record.contract_id.name}",
                    'quantity': 1,
                    'price_unit': record.amount,
                })],
                'ref': record.name,
            }
            
            invoice = self.env['account.move'].create(invoice_vals)
            record.invoice_id = invoice.id
            record.state = 'invoiced'
            
            # Afficher la facture créée
            return {
                'name': _('Facture client'),
                'view_mode': 'form',
                'res_model': 'account.move',
                'res_id': invoice.id,
                'type': 'ir.actions.act_window',
            }
            
    def action_set_paid(self):
        """Marquer comme payé"""
        for record in self:
            record.state = 'paid'
            
    def action_cancel(self):
        """Annuler la facture"""
        for record in self:
            if record.invoice_id and record.invoice_id.state == 'posted':
                raise UserError(_("Vous ne pouvez pas annuler cette facture car elle est déjà validée."))
                
            if record.invoice_id:
                record.invoice_id.button_cancel()
                
            record.state = 'cancelled'
    
    @api.model
    def generate_recurrent_invoices(self):
        """Générer les factures récurrentes basées sur les contrats actifs"""
        today = fields.Date.today()
        
        # Rechercher les contrats actifs dont la prochaine date de facturation est aujourd'hui
        contracts = self.env['parc.contract'].search([
            ('state', '=', 'active'),
            ('next_invoice_date', '=', today)
        ])
        
        invoices_created = self.env['parc.invoice']
        
        for contract in contracts:
            # Créer l'enregistrement de facture
            due_date = today
            if contract.invoice_frequency == 'monthly':
                due_date = today + fields.timedelta(days=30)
            elif contract.invoice_frequency == 'quarterly':
                due_date = today + fields.timedelta(days=90)
            elif contract.invoice_frequency == 'semi_annual':
                due_date = today + fields.timedelta(days=180)
            else:  # annuel
                due_date = today + fields.timedelta(days=365)
                
            invoice = self.create({
                'contract_id': contract.id,
                'invoice_date': today,
                'due_date': due_date,
            })
            
            # Générer la facture dans account.move
            invoice.action_generate_invoice()
            invoices_created |= invoice
            
        return invoices_created