{
    'name': 'Gestion de Parc Informatique',
    'version': '1.0',
    'category': 'Services/IT',
    'summary': 'Module de gestion de parc informatique pour prestataire de services IT',
    'description': """
Gestion de Parc Informatique
============================

Ce module permet de gérer:
* Le parc informatique (matériel et logiciel) par client
* Les contrats de service
* Les incidents et interventions
* La facturation récurrente automatisée
* Le suivi des garanties et licences
    """,
    'author': 'ANGE EMMANUEL',
    'website': 'https://www.ParcInfo.com',
    'depends': [
        'base',
        'mail',
        'account',
        'hr',
        'website',
        'portal',
        'stock',
        
        
       

        
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/equipment_views.xml',
        'views/contract_views.xml',
        'views/incident_views.xml',
        'views/client_views.xml',
        'views/invoice_views.xml',
        'views/intervention.xml',
        'views/facture_views.xml',
        'views/alerte_views.xml',
        'views/templates.xml',
        'views/stock_views.xml',
        'views/menu.xml', 
        'views/login_template.xml',
        
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            

           
        ],
    },
}