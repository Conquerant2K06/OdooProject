from odoo import models, fields, api
from odoo.exceptions import ValidationError
class ParcFacture(models.Model):
    _inherit = 'account.move'

    parc_ref = fields.Char(string="Référence parc informatique")
    parc_ticket_id = fields.Many2one('parc.ticket', string="Ticket associé")

def action_generer_facture_odoo(self):
    self.ensure_one()
    if not self.facture_lines:
        raise ValidationError("Veuillez ajouter au moins une ligne à la facture.")

    facture_vals = {
        'move_type': 'out_invoice',
        'partner_id': self.client_id.id,
        'invoice_date': self.date_facture,
        'invoice_line_ids': [],
        'ref': self.name,
    }

    for line in self.facture_lines:
        account_id = line.produit_id.property_account_income_id.id or \
                     line.produit_id.categ_id.property_account_income_categ_id.id
        if not account_id:
            raise ValidationError(
                f"Le produit '{line.produit_id.name}' n'a pas de compte de revenu défini."
            )
        invoice_line = {
            'product_id': line.produit_id.id,
            'quantity': line.quantite,
            'price_unit': line.prix_unitaire,
            'name': line.produit_id.name,
            'account_id': account_id,
        }
        facture_vals['invoice_line_ids'].append((0, 0, invoice_line))

    facture_odoo = self.env['account.move'].create(facture_vals)
    facture_odoo.action_post()

    return {
        'type': 'ir.actions.act_window',
        'res_model': 'account.move',
        'view_mode': 'form',
        'res_id': facture_odoo.id,
        'target': 'current',
    }
