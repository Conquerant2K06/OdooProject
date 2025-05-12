from odoo import api, fields, models, _
from datetime import timedelta
from odoo.exceptions import UserError

class EquipmentType(models.Model):
    _name = 'parc.equipment.type'
    _description = 'Type d\'équipement'
    
    name = fields.Char(string='Type d\'équipement', required=True)
    code = fields.Char(string='Code', required=True)
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Le code doit être unique!')
    ]

class Equipment(models.Model):
    _name = 'parc.equipment'
    _description = 'Équipement de parc informatique'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']  # Ajout de portal.mixin
    _order = 'create_date desc'
    
    name = fields.Char(string='Nom', required=True, tracking=True)
    reference = fields.Char(string='Référence', tracking=True, copy=False)
    serial_number = fields.Char(string='Numéro de série', tracking=True)
    
    type_id = fields.Many2one('parc.equipment.type', string='Type d\'équipement', required=True)
    model = fields.Char(string='Modèle', tracking=True)
    brand = fields.Char(string='Marque', tracking=True)
    
    client_id = fields.Many2one('parc.client', string='Client', required=True, tracking=True)
    user_id = fields.Many2one('res.partner', string='Utilisateur final', domain="[('parent_id', '=', client_id)]", tracking=True)
    
    installation_date = fields.Date(string='Date d\'installation', tracking=True)
    warranty_end_date = fields.Date(string='Fin de garantie', tracking=True)
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('allocated', 'Alloué'),
        ('in_use', 'En service'),
        ('maintenance', 'En maintenance'),
        ('end_of_life', 'Fin de vie'),
    ], string='État', default='draft', tracking=True)
    
    is_software = fields.Boolean(string='Est un logiciel', default=False)
    license_key = fields.Char(string='Clé de licence')
    license_expiry = fields.Date(string='Expiration de la licence')
    
    contract_id = fields.Many2one('parc.contract', string='Contrat', tracking=True)
    company_id = fields.Many2one('res.company', string='Société', default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    
    notes = fields.Text(string='Notes')
    incident_ids = fields.One2many('parc.incident', 'equipment_id', string='Incidents')
    incident_count = fields.Integer(compute='_compute_incident_count', string='Nombre d\'incidents')
    image = fields.Binary(string='Image', attachment=True, help="Image de l'équipement", required=True)
    # Champ pour lier l'équipement au partenaire (important pour le portail)
    partner_id = fields.Many2one('res.partner', string='Partenaire', 
                                 related='client_id.partner_id', store=True, 
                                 help="Partenaire associé à cet équipement pour l'accès au portail")
    
    @api.depends('incident_ids')
    def _compute_incident_count(self):
        for equipment in self:
            equipment.incident_count = len(equipment.incident_ids)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('reference'):
                vals['reference'] = self.env['ir.sequence'].next_by_code('parc.equipment.sequence')
        return super().create(vals_list)
    
    def _compute_access_url(self):
        """Surcharge pour définir l'URL d'accès dans le portail"""
        super()._compute_access_url()
        for equipment in self:
            equipment.access_url = f'/my/equipment/{equipment.id}'
    
    def check_warranty_expiry(self):
        """Vérifier les équipements dont la garantie expire bientôt"""
        today = fields.Date.today()
        expiry_date = today + timedelta(days=30)
        equipments = self.search([
            ('warranty_end_date', '>=', today),
            ('warranty_end_date', '<=', expiry_date),
            ('state', 'in', ['allocated', 'in_use'])
        ])
        
        for equipment in equipments:
            equipment.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=self.env.user.id,
                note=f"La garantie de l'équipement {equipment.name} expire le {equipment.warranty_end_date}",
                summary="Garantie expirante",
                date_deadline=equipment.warranty_end_date
            )
        
        return True
    
    def check_license_expiry(self):
        """Vérifier les licences logicielles expirant bientôt"""
        today = fields.Date.today()
        expiry_date = today + timedelta(days=30)
        equipments = self.search([
            ('is_software', '=', True),
            ('license_expiry', '>=', today),
            ('license_expiry', '<=', expiry_date),
            ('state', 'in', ['allocated', 'in_use'])
        ])
        
        for equipment in equipments:
            equipment.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=self.env.user.id,
                note=f"La licence logicielle {equipment.name} expire le {equipment.license_expiry}",
                summary="Licence expirante",
                date_deadline=equipment.license_expiry
            )
        
        return True
    
    def action_view_incidents(self):
        """Ouvre la vue des incidents liés à cet équipement"""
        self.ensure_one()
        return {
            'name': _('Incidents'),
            'type': 'ir.actions.act_window',
            'res_model': 'parc.incident',
            'view_mode': 'list,form',
            'domain': [('equipment_id', '=', self.id)],
            'context': {'default_equipment_id': self.id},
        }
        
    # Méthode optionnelle pour l'intégration portail
    def _get_portal_return_action(self):
        """Définit l'action de retour après une action dans le portail"""
        return {
            'type': 'ir.actions.act_url',
            'url': self.access_url,
            'target': 'self',
        }
        
    # Méthodes supplémentaires pour le portail
    def _get_report_base_filename(self):
        """Nom de base pour les rapports téléchargés depuis le portail"""
        return f"Equipment-{self.reference}"