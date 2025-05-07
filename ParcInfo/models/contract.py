from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta

class ParcContract(models.Model):
    _name = 'parc.contract'
    _description = 'Contrat de service'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Référence du contrat', required=True, copy=False, tracking=True)
    client_id = fields.Many2one('parc.client', string='Client', required=True, tracking=True)
    start_date = fields.Date(string='Date de début', required=True, tracking=True)
    end_date = fields.Date(string='Date de fin', tracking=True)
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('active', 'Actif'),
        ('to_renew', 'À renouveler'),
        ('expired', 'Expiré'),
        ('cancelled', 'Annulé'),
    ], string='État', default='draft', tracking=True)
    
    subscription_id = fields.Many2one('sale.subscription', string='Abonnement associé', tracking=True)
    
    # Facturation
    invoice_frequency = fields.Selection([
        ('monthly', 'Mensuelle'),
        ('quarterly', 'Trimestrielle'),
        ('semi_annual', 'Semestrielle'),
        ('annual', 'Annuelle'),
    ], string='Fréquence de facturation', default='monthly', required=True, tracking=True)
    
    next_invoice_date = fields.Date(string='Prochaine date de facturation', compute='_compute_next_invoice_date', store=True)
    
    amount = fields.Float(string='Montant du contrat', required=True, tracking=True)
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.company.currency_id)
    
    company_id = fields.Many2one('res.company', string='Société', default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    asset_ids = fields.Many2many('parc.equipment', string='Équipements associés')
    notes = fields.Text(string='Notes')
    recurring_interval = fields.Integer(string='Intervalle de récurrence', default=1, help="Intervalle de temps entre les factures")
    
    # Relations
    equipment_ids = fields.One2many('parc.equipment', 'contract_id', string='Équipements couverts')
    equipment_count = fields.Integer(compute='_compute_equipment_count', string='Nombre d\'équipements')
    
    @api.depends('equipment_ids')
    def _compute_equipment_count(self):
        for contract in self:
            contract.equipment_count = len(contract.equipment_ids)
    
    @api.depends('start_date', 'invoice_frequency')
    def _compute_next_invoice_date(self):
        today = fields.Date.today()
        for contract in self:
            if not contract.start_date or contract.state != 'active':
                contract.next_invoice_date = False
                continue
                
            start_date = contract.start_date
            if start_date > today:
                contract.next_invoice_date = start_date
                continue
                
            # Calculer la prochaine date basée sur la fréquence
            if contract.invoice_frequency == 'monthly':
                delta = 30  # approximatif, à améliorer
            elif contract.invoice_frequency == 'quarterly':
                delta = 90
            elif contract.invoice_frequency == 'semi_annual':
                delta = 180
            else:  # annuel
                delta = 365
                
            # Trouver la prochaine date de facturation
            next_date = start_date
            while next_date <= today:
                next_date = next_date + timedelta(days=delta)
                
            contract.next_invoice_date = next_date
            
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for contract in self:
            if contract.end_date and contract.start_date > contract.end_date:
                raise ValidationError(_("La date de fin ne peut pas être antérieure à la date de début."))
    
    def action_activate(self):
        """Activer le contrat"""
        for contract in self:
            # Créer l'abonnement correspondant s'il n'existe pas déjà
            if not contract.subscription_id:
                subscription_vals = {
                    'name': contract.name,
                    'partner_id': contract.client_id.partner_id.id,
                    'recurring_invoice_line_ids': [(0, 0, {
                        'name': f'Services pour {contract.client_id.name}',
                        'price_unit': contract.amount,
                        'quantity': 1,
                    })],
                    'recurring_next_date': contract.next_invoice_date or fields.Date.today(),
                    'company_id': contract.company_id.id,
                }
                
                # Définir la règle de récurrence selon la fréquence choisie
                if contract.invoice_frequency == 'monthly':
                    subscription_vals['recurring_rule_type'] = 'month'
                    subscription_vals['recurring_interval'] = 1
                elif contract.invoice_frequency == 'quarterly':
                    subscription_vals['recurring_rule_type'] = 'month'
                    subscription_vals['recurring_interval'] = 3
                elif contract.invoice_frequency == 'semi_annual':
                    subscription_vals['recurring_rule_type'] = 'month'
                    subscription_vals['recurring_interval'] = 6
                else:  # annuel
                    subscription_vals['recurring_rule_type'] = 'year'
                    subscription_vals['recurring_interval'] = 1
                
                # Créer l'abonnement
                subscription = self.env['sale.subscription'].create(subscription_vals)
                contract.subscription_id = subscription.id
            
            contract.state = 'active'
            
    def action_set_to_renew(self):
        """Marquer le contrat comme à renouveler"""
        for contract in self:
            contract.state = 'to_renew'
            
    def action_cancel(self):
        """Annuler le contrat"""
        for contract in self:
            if contract.subscription_id:
                contract.subscription_id.write({'active': False})
            contract.state = 'cancelled'
            
    def action_renew(self):
        """Renouveler le contrat"""
        for contract in self:
            if not contract.end_date:
                raise UserError(_("Définissez une date de fin avant de renouveler le contrat."))
                
            # Créer un nouveau contrat basé sur l'actuel
            new_contract = contract.copy({
                'name': f'{contract.name}-R',
                'start_date': contract.end_date + timedelta(days=1),
                'end_date': False,
                'state': 'draft',
                'subscription_id': False,
            })
            
            # Rediriger vers le nouveau contrat
            return {
                'name': _('Contrat renouvelé'),
                'view_mode': 'form',
                'res_model': 'parc.contract',
                'res_id': new_contract.id,
                'type': 'ir.actions.act_window',
            }
    
    def check_expiry(self):
        """Vérifier les contrats expirant bientôt"""
        today = fields.Date.today()
        expiry_date = today + timedelta(days=30)
        contracts = self.search([
            ('end_date', '>=', today),
            ('end_date', '<=', expiry_date),
            ('state', '=', 'active')
        ])
        
        for contract in contracts:
            if contract.state != 'to_renew':
                contract.state = 'to_renew'
                contract.activity_schedule(
                    'mail.mail_activity_data_todo',
                    user_id=self.env.user.id,
                    note=f"Le contrat {contract.name} expire le {contract.end_date}",
                    summary="Contrat expirant",
                    date_deadline=contract.end_date
                )
        
        return True
def cron_activate_due_contracts(self):
    """Activer automatiquement les contrats dont la date de facturation est arrivée."""
    today = fields.Date.today()
    contracts = self.search([
        ('state', '=', 'draft'),
        ('start_date', '<=', today),
    ])
    
    for contract in contracts:
        contract.action_activate()
