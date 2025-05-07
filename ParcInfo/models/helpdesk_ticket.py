from odoo import models, fields

class HelpdeskTicket(models.Model):
    _name = 'helpdesk.ticket'
    _description = 'Ticket d\'assistance'

    name = fields.Char(string="Sujet", required=True)
    description = fields.Text(string="Description")
    client_id = fields.Many2one('res.partner', string="Client")
    state = fields.Selection([
        ('nouveau', 'Nouveau'),
        ('en_cours', 'En cours'),
        ('resolu', 'Résolu'),
        ('ferme', 'Fermé')
    ], string="Statut", default='nouveau')
    date_creation = fields.Datetime(string="Date de création", default=fields.Datetime.now)
