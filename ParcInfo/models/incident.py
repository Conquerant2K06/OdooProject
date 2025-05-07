from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ParcIncident(models.Model):
    _name = 'parc.incident'
    _description = 'Incident sur équipement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, id desc'
    
    name = fields.Char(string='Référence', required=True, copy=False, readonly=True, default=lambda self: _('Nouveau'))
    
    client_id = fields.Many2one('parc.client', string='Client', required=True, tracking=True)
    equipment_id = fields.Many2one('parc.equipment', string='Équipement', required=True, 
                                   domain="[('client_id', '=', client_id)]", tracking=True)
    
    reported_by = fields.Many2one('res.partner', string='Signalé par', tracking=True)
    assignee_id = fields.Many2one('res.users', string='Assigné à', tracking=True)
    
    description = fields.Text(string='Description', required=True)
    
    date_reported = fields.Datetime(string='Date de signalement', default=fields.Datetime.now, tracking=True)
    date_fixed = fields.Datetime(string='Date de résolution', tracking=True)
    
    priority = fields.Selection([
        ('0', 'Basse'),
        ('1', 'Normale'),
        ('2', 'Haute'),
        ('3', 'Critique'),
    ], string='Priorité', default='1', tracking=True)
    
    state = fields.Selection([
        ('new', 'Nouveau'),
        ('in_progress', 'En cours'),
        ('waiting', 'En attente'),
        ('resolved', 'Résolu'),
        ('closed', 'Fermé'),
    ], string='État', default='new', tracking=True)
    
    solution = fields.Text(string='Solution')
    intervention_time = fields.Float(string='Temps d\'intervention (heures)')
    
    ticket_id = fields.Many2one('helpdesk.ticket', string='Ticket d\'assistance')
    company_id = fields.Many2one('res.company', string='Société', default=lambda self: self.env.company)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Nouveau')) == _('Nouveau'):
                vals['name'] = self.env['ir.sequence'].next_by_code('parc.incident.sequence') or _('Nouveau')
        return super().create(vals_list)
    
    @api.onchange('client_id')
    def _onchange_client(self):
        self.equipment_id = False
        self.reported_by = False
        
    def action_set_in_progress(self):
        for incident in self:
            incident.state = 'in_progress'
            
    def action_set_waiting(self):
        for incident in self:
            incident.state = 'waiting'
            
    def action_resolve(self):
        for incident in self:
            if not incident.solution:
                raise ValidationError(_("Veuillez décrire la solution avant de résoudre l'incident."))
            incident.state = 'resolved'
            incident.date_fixed = fields.Datetime.now()
            
    def action_close(self):
        for incident in self:
            incident.state = 'closed'
            
    def create_helpdesk_ticket(self):
        """Créer un ticket d'assistance à partir de l'incident"""
        for incident in self:
            if incident.ticket_id:
                raise ValidationError(_("Un ticket d'assistance existe déjà pour cet incident."))
                
            ticket = self.env['helpdesk.ticket'].create({
                'name': f"Incident {incident.name} - {incident.equipment_id.name}",
                'description': incident.description,
                'partner_id': incident.client_id.partner_id.id,
                'priority': incident.priority,
                'user_id': incident.assignee_id.id,
            })
            
            incident.ticket_id = ticket.id
            
            return {
                'name': _('Ticket d\'assistance'),
                'view_mode': 'form',
                'res_model': 'helpdesk.ticket',
                'res_id': ticket.id,
                'type': 'ir.actions.act_window',
            }