{
    'name': 'Loan Configuration',
    'version': '1.0',
    'category': 'Finance',
    'summary': 'Cấu hình hệ thống khoản vay',
    'description': """
        Module cấu hình cho hệ thống P2P Lending:
        - Cấu hình loại khoản vay
        - Cấu hình lãi suất
        - Cấu hình blockchain
        - Cấu hình phí dịch vụ
    """,
    'author': 'P2P Lending Team',
    'website': 'https://www.p2plending.com',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/loan_config_views.xml',
        'views/menu_views.xml',
        'data/loan_type_data.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
