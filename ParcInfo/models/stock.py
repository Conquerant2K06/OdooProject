from odoo import models, fields, api

class ArticleDeStock(models.Model):
    _name = 'parc.stock'
    _description = 'Article de Stock'

    nom = fields.Char(string='Nom', required=True)
    client_id = fields.Many2one('parc.client', string='Client', required=True)
    quantite = fields.Integer(string='Quantité', default=0)
    seuil = fields.Integer(string='Seuil de rupture', default=0)

    @api.depends('quantite', 'seuil')
    def _compute_est_en_rupture(self):
        for article in self:
            article.est_en_rupture = article.quantite < article.seuil

    est_en_rupture = fields.Boolean(string='Est en rupture', compute='_compute_est_en_rupture', store=True)

    def reapprovisionner(self, quantite_ajoutee):
        for article in self:
            article.quantite += quantite_ajoutee
