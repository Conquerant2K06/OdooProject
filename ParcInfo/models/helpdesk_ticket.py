from odoo import models, fields

class HelpdeskTicket(models.Model):
    _name = 'helpdesk.ticket'
    _description = 'Ticket d\'assistance'

    name = fields.Char(string="Sujet", required=True)
    description = fields.Text(string="Description")
    partner_id = fields.Many2one('res.partner', string="Partenaire")
    client_id = fields.Many2one('parc.client', string="Client")
    user_id = fields.Many2one('res.users', string="Utilisateur", default=lambda self: self.env.user)
    priority = fields.Selection([
        ('0', 'Basse'),
        ('1', 'Normale'),
        ('2', 'Haute'),
        ('3', 'Critique'),
    ], string='Priorité', default='1', tracking=True)
    state = fields.Selection([
        ('nouveau', 'Nouveau'),
        ('en_cours', 'En cours'),
        ('resolu', 'Résolu'),
        ('ferme', 'Fermé')
    ], string="Statut", default='nouveau')
    date_creation = fields.Datetime(string="Date de création", default=fields.Datetime.now)
