# -*- coding: utf-8 -*-
{
    "name": "Website Custom Snippet",
    "summary": "Module tạo custom snippet cho Odoo Website Builder.",
    "version": "18.0.1.0.1",  # Incremented version number
    "category": "Website",
    "author": "Your Name",
    "website": "https://yourcompany.com",
    "depends": ["website", "p2p_bridge"],
    "data": [
        "views/snippets/options.xml",
        "views/snippets/s_custom_snippet.xml",
        "views/snippets/loan_list_template.xml",
        "views/snippets/loan_list_table_partial.xml"
    ],
    "assets": {
        "web.assets_frontend": [
            "website_custom_snippet/static/src/snippets/s_custom_snippet/000.js",
            "website_custom_snippet/static/src/snippets/s_custom_snippet/000.scss",
            "website_custom_snippet/static/src/snippets/s_custom_snippet/000.xml"
        ],
        "website.assets_editor": [
            "website_custom_snippet/static/src/snippets/s_custom_snippet/options.js"
        ]
    },
    "installable": True,
    "application": False,
    "auto_install": False
}
