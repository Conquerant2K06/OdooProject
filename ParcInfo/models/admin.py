from odoo import models, fields

class ParcAdmin(models.Model):
    _name = 'parc.admin'
    _description = 'Administrateur du parc informatique'

    name = fields.Char(string="Nom", required=True)
    email = fields.Char(string="Email", required=True)
    password = fields.Char(string="Mot de passe", required=True)
    role = fields.Selection([
        ('it', 'IT'),
        ('manager', 'Manager'),
    ], string="Rôle")
