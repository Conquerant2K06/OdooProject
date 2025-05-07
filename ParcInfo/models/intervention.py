from odoo import models, fields

class Intervention(models.Model):
    _name = 'parc.intervention'
    _description = 'Intervention pour la gestion de parc'

    date = fields.Datetime(string='Date de l’intervention', required=True)
    asset_id = fields.Many2one('parc.asset', string='Actif', required=True)
    technicien_id = fields.Many2one('res.users', string='Technicien', required=True)
    resultat = fields.Text(string='Résultat de l’intervention')
    description = fields.Text(string='Description de l’intervention')
    type_intervention = fields.Selection([
        ('maintenance', 'Maintenance préventive'),
        ('reparation', 'Réparation'),
        ('installation', 'Installation'),
        ('deplacement', 'Déplacement'),
    ], string='Type d\'intervention', required=True)
