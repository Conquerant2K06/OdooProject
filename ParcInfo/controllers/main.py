from odoo import http
from odoo.http import request

class LoginController(http.Controller):

    @http.route('/odoo/action-799', type='http', auth='public')
    def module_index(self, **kw):
        return request.redirect('/ParcInfo/login')
    
    @http.route('/ParcInfo/login', type='http', auth='public', website=True)
    def login_page(self, **kw):
        return request.render('ParcInfo.login_template', {})

    @http.route('/ParcInfo/authenticate', type='http', auth='public', website=True, methods=['POST'])
    def authenticate(self, **post):
        email = post.get('email')
        password = post.get('password')

        # Identifiants admin codés en dur
        ADMIN_EMAIL = 'angeemmanuel2k06@gmail.com'
        ADMIN_PASSWORD = 'ANGE2K06'

        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            request.session['user_role'] = 'admin_custom'
            request.session['admin_email'] = email
            return request.redirect('/web#action=799')

        # Tentative d'authentification via utilisateurs Odoo
        try:
            uid = request.session.authenticate(request.session.db, email, password)
        except Exception:
            uid = False

        if uid:
            user = request.env['res.users'].sudo().browse(uid)
            if user.has_group('base.group_user'):
                request.session['user_role'] = 'admin'
                return request.redirect('/web#action=799')

        # Tentative d'authentification client
        Client = request.env['parc.client'].sudo()
        client = Client.search([('email', '=', email)], limit=1)

        if client:
            if hasattr(client, 'password') and client.password == password:
                request.session['user_id'] = client.id
                request.session['user_role'] = 'client'
                return request.redirect('/my/equipments')
            else:
                return request.render('ParcInfo.login_template', {
                    'error': 'Mot de passe incorrect',
                    'email': email
                })
        else:
            return request.render('ParcInfo.login_template', {
                'error': 'Email non trouvé dans notre système'
            })

    @http.route('/my/equipments', type='http', auth='public', website=True)
    def equipment_page(self, **kw):
        if not request.session.get('user_role') == 'client' or not request.session.get('user_id'):
            return request.redirect('/ParcInfo/login')
        
        client = request.env['parc.client'].sudo().browse(request.session.get('user_id'))
        if not client.exists():
            request.session.pop('user_id', None)
            request.session.pop('user_role', None)
            return request.redirect('/ParcInfo/login')
        
        Equipment = request.env['parc.equipment'].sudo()
        equipments = Equipment.search([('client_id', '=', client.id)])

        return request.render('ParcInfo.portal_my_equipments', {
            'client': client,
            'equipments': equipments,
        })

    @http.route('/admin/login', type='http', auth='public', website=True)
    def admin_login_page(self, **kw):
        return request.render('ParcInfo.admin_login_template', {})

    @http.route('/ParcInfo/admin', type='http', auth='user', website=True)
    def admin_redirect(self, **kw):
        return request.redirect('/web#action=799')

    @http.route('/ParcInfo/logout', type='http', auth='public', website=True)
    def logout(self, **kw):
        if request.session.get('user_role') in ['admin', 'admin_custom']:
            request.session.logout()
        
        for key in ['user_id', 'user_role', 'admin_email']:
            if key in request.session:
                del request.session[key]

        return request.redirect('/ParcInfo/login')

    @http.route('/ParcInfo', type='http', auth='public', website=True)
    def index(self, **kw):
        if request.session.uid and request.env.user.has_group('base.group_user'):
            return request.redirect('/web#action=799')

        if request.session.get('user_role') == 'client' and request.session.get('user_id'):
            return request.redirect('/my/equipments')

        return request.redirect('/ParcInfo/login')

    @http.route('/', type='http', auth='public', website=True)
    def root(self, **kw):
        if request.session.uid and request.env.user.has_group('base.group_user'):
            return request.redirect('/web#action=799')

        if request.session.get('user_role') == 'client' and request.session.get('user_id'):
            return request.redirect('/my/equipments')

        return request.redirect('/ParcInfo/login')
