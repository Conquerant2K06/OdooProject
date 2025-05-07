from odoo import api, fields, models, _

class ParcClient(models.Model):
    _name = 'parc.client'
    _description = 'Client du Parc Informatique'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nom du client', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Contact associé', required=True, tracking=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Société', default=lambda self: self.env.company)
    asset_ids = fields.Many2many('parc.equipment', string='Équipements associés')
    # Référent technique côté client
    technical_contact_id = fields.Many2one('res.partner', string='Contact technique')
    type_id = fields.Many2one('parc.client.type', string='Type de client', required=True, tracking=True)
    # Relations inverses
    contract_ids = fields.One2many('parc.contract', 'client_id', string='Contrats')
    equipment_ids = fields.One2many('parc.equipment', 'client_id', string='Équipements')
    incident_ids = fields.One2many('parc.incident', 'client_id', string='Incidents')
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('active', 'Actif'),
        ('inactive', 'Inactif'),
    ], string='État', default='draft', tracking=True)
    recurring_interval = fields.Integer(string='Intervalle de récurrence', default=1, help="Intervalle de temps entre les factures")
    # Statistiques
    contract_count = fields.Integer(compute='_compute_counts', string='Nombre de contrats')
    equipment_count = fields.Integer(compute='_compute_counts', string='Nombre d\'équipements')
    incident_count = fields.Integer(compute='_compute_counts', string='Nombre d\'incidents')
    start_date = fields.Date(string='Date de début', tracking=True)
    end_date = fields.Date(string='Date de fin', tracking=True)
    @api.depends('contract_ids', 'equipment_ids', 'incident_ids')
    def _compute_counts(self):
        for client in self:
            client.contract_count = len(client.contract_ids)
            client.equipment_count = len(client.equipment_ids)
            client.incident_count = len(client.incident_ids)