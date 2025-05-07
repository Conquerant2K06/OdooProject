# models/alerte.py
from odoo import models, fields, api
from datetime import timedelta, date

class ParcAlerte(models.Model):
    _name = 'parc.alerte'
    _description = 'Alerte sur le matériel'

    name = fields.Char()
    asset_id = fields.Many2one('parc.equipment')
    type_alerte = fields.Selection([
        ('garantie', 'Fin de garantie'),
        ('maintenance', 'Maintenance préventive'),
        ('licence', 'Expiration licence')
    ])
    date_alerte = fields.Date()

    @api.model
    def check_alertes(self):
        assets = self.env['parc.equipment'].search([])
        for asset in assets:
            if asset.garantie_expiration and asset.garantie_expiration <= date.today() + timedelta(days=30):
                self.create({
                    'name': f"Garantie proche de l'expiration : {asset.name}",
                    'asset_id': asset.id,
                    'type_alerte': 'garantie',
                    'date_alerte': date.today()
                })
