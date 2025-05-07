from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from collections import OrderedDict
from operator import itemgetter


class ParcPortal(CustomerPortal):
    
    def _prepare_home_portal_values(self, counters):
        """Ajoute des compteurs dans la page d'accueil du portail"""
        values = super()._prepare_home_portal_values(counters)
        
        if 'equipment_count' in counters:
            partner = request.env.user.partner_id
            equipment_count = request.env['parc.equipment'].search_count([
                '|',
                ('partner_id', '=', partner.id),
                ('user_id', '=', partner.id)
            ])
            values['equipment_count'] = equipment_count
            
        return values
    
    

    @http.route(['/my/equipments', '/my/equipments/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_equipments(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        """Page listant tous les équipements du client"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        Equipment = request.env['parc.equipment']
        
        domain = ['|', ('partner_id', '=', partner.id), ('user_id', '=', partner.id)]
        
        # Options de tri
        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'create_date desc'},
            'name': {'label': _('Nom'), 'order': 'name'},
            'state': {'label': _('État'), 'order': 'state'},
            'reference': {'label': _('Référence'), 'order': 'reference'},
        }
        
        # Options de filtrage
        searchbar_filters = {
            'all': {'label': _('Tous'), 'domain': []},
            'in_use': {'label': _('En service'), 'domain': [('state', '=', 'in_use')]},
            'maintenance': {'label': _('En maintenance'), 'domain': [('state', '=', 'maintenance')]},
            'software': {'label': _('Logiciels'), 'domain': [('is_software', '=', True)]},
            'hardware': {'label': _('Matériel'), 'domain': [('is_software', '=', False)]},
        }
        
        # Tri par défaut
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']
        
        # Filtre par défaut
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        
        # Pagination
        equipment_count = Equipment.search_count(domain)
        page_details = pager(
            url="/my/equipments",
            url_args={'sortby': sortby, 'filterby': filterby},
            total=equipment_count,
            page=page,
            step=self._items_per_page
        )
        
        # Recherche avec pagination
        equipments = Equipment.search(
            domain,
            order=sort_order,
            limit=self._items_per_page,
            offset=page_details['offset']
        )
        
        values.update({
            'equipments': equipments,
            'page_name': 'equipments',
            'pager': page_details,
            'default_url': '/my/equipments',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': searchbar_filters,
            'filterby': filterby,
        })
        
        # Utiliser le nom du module correct (ParcInfo)
        return request.render("ParcInfo.portal_my_equipments", values)
    
    @http.route(['/my/equipment/<int:equipment_id>'], type='http', auth="user", website=True)
    def portal_equipment_page(self, equipment_id, **kw):
        """Page de détail d'un équipement"""
        try:
            equipment_sudo = self._document_check_access('parc.equipment', equipment_id)
        except (AccessError, MissingError):
            return request.redirect('/my')
        
        # Récupération des incidents liés à cet équipement
        incidents = request.env['parc.incident'].sudo().search([
            ('equipment_id', '=', equipment_id)
        ])
        
        values = {
            'equipment': equipment_sudo,
            'incidents': incidents,
            'page_name': 'equipment',
        }
        
        # Utiliser le nom du module correct (ParcInfo)
        return request.render("ParcInfo.portal_equipment_page", values)
        
    @http.route(['/my/equipment/<int:equipment_id>/incidents'], type='http', auth="user", website=True)
    def portal_equipment_incidents(self, equipment_id, **kw):
        """Page listant les incidents d'un équipement"""
        try:
            equipment_sudo = self._document_check_access('parc.equipment', equipment_id)
        except (AccessError, MissingError):
            return request.redirect('/my')
            
        incidents = request.env['parc.incident'].sudo().search([
            ('equipment_id', '=', equipment_id)
        ])
        
        values = {
            'equipment': equipment_sudo,
            'incidents': incidents,
            'page_name': 'equipment_incidents',
        }
        
        # Utiliser le nom du module correct (ParcInfo)
        return request.render("ParcInfo.portal_equipment_incidents", values)