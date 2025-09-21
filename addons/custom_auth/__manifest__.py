{
    'name': 'Custom Auth Pages',
    'version': '1.0',
    'summary': 'Tùy biến trang đăng nhập và đăng ký',
    'description': 'Module này giúp tùy biến giao diện trang đăng nhập, đăng ký và đặt lại mật khẩu cho Odoo, sử dụng Tailwind CSS hiện đại.',
    'category': 'Website',
    'author': 'Your Name',
    'website': 'https://yourwebsite.com',
    'license': 'LGPL-3',
    'depends': ['auth_signup', 'web'],
    'data': [
        'views/custom_login_template.xml',
        'views/custom_signup_template.xml',
        'views/custom_reset_password_template.xml',
        'views/otp_popup_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'custom_auth/static/src/css/otp_popup.css',
            'custom_auth/static/src/js/login/login.js',
            'custom_auth/static/src/js/signup/signup.js',
            'custom_auth/static/src/js/signup/signup_with_otp.js',
            'custom_auth/static/src/js/reset_password/reset_password.js',
        ],
    },
    'installable': True,
    'application': True,
} 