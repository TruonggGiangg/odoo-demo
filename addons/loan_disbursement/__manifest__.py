{
    'name': 'Loan Disbursement Management',
    'version': '1.0',
    'category': 'Finance',
    'summary': 'Quản lý giải ngân khoản vay',
    'description': """
        Module quản lý quy trình giải ngân khoản vay:
        - Quản lý danh sách giải ngân
        - Workflow phê duyệt
        - Tích hợp blockchain
        - Báo cáo giải ngân
    """,
    'author': 'P2P Lending Team',
    'website': 'https://www.p2plending.com',
    'depends': ['base', 'mail', 'loan_config', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/disbursement_views.xml',
        'views/menu_views.xml',
        'data/disbursement_sequence.xml',
        'views/web_templates.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
