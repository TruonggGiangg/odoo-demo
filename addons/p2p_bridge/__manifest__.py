{
    "name": "P2P MongoDB Bridge",
    "version": "1.0.9",
    "depends": ["base", "mail"],
    "author": "Toàn",
    "data": [
        "security/ir.model.access.csv",
        "views/p2p_wallet_view.xml",
        "views/borrower_views.xml",
        "views/investor_views.xml",
        "views/custom_templates.xml",
        "views/menu_views.xml",
        "wizard/sync_wizard_view.xml",
        "data/ir_cron.xml"
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "category": "P2P Lending Bridge",
    "summary": "Bridge để đồng bộ dữ liệu từ MongoDB sang Odoo",
    "description": """
        Module này cung cấp:
        - Đồng bộ dữ liệu wallet từ MongoDB
        - Đồng bộ dữ liệu loans từ MongoDB  
        - Cron job tự động đồng bộ mỗi 5 phút
        - Giao diện xem dữ liệu trong Odoo
        - Tool test kết nối và đồng bộ thủ công
    """,
}
