# -*- coding: utf-8 -*-
{
    "name": "P2P Lending Dashboard",
    "version": "18.0.1.0.4",
    "category": "Finance",
    "summary": "Bảng điều khiển và thống kê cho P2P Lending",
    "description": """
        Module cung cấp bảng điều khiển và các chức năng phân tích dữ liệu cho hệ thống P2P Lending.
        - Hiển thị thống kê về khoản vay
        - Hiển thị thống kê về khoản đầu tư
        - Biểu đồ phân tích xu hướng
        - Cung cấp báo cáo trực quan
    """,
    "author": "Your Company",
    "website": "https://www.yourcompany.com",
    "depends": ["base", "web", "p2p_bridge"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/dashboard_views.xml",
        "views/menu_views.xml",
        "data/demo_data.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
    "assets": {
        "web.assets_backend": [
            # Stylesheets - tải trước
            "p2p_dashboard/static/src/css/dashboard.css",
            "p2p_dashboard/static/src/css/dashboard_stats.css",
            # Chart.js (UMD) - cần trước khi load widget
            "p2p_dashboard/static/lib/chartjs/chart.umd.min.js",
            # JavaScript - tải các files theo đúng thứ tự
            "p2p_dashboard/static/src/js/dashboard_graph_renderer_utf8.js",
            "p2p_dashboard/static/src/js/dashboard_graph_widget_registry.js",
            "p2p_dashboard/static/src/js/chart_debug_helper.js",
        ],
        "web.assets_qweb": [
            "p2p_dashboard/static/src/xml/dashboard_graph_renderer.xml",
        ],
    }
}