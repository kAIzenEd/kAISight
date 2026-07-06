# -*- coding: utf-8 -*-
{
    "name": "kaiSight",
    "version": "19.0.1.0.4",
    "category": "Productivity/Reporting",
    "summary": "Interactive dashboards and saved reports for any Odoo model",
    "description": """
kaiSight provides lightweight, interactive dashboards and saved report definitions
that work with any installed addon model via the ORM (search_read / read_group).

Other addons can ship predefined dashboards and widgets through XML data or
create them programmatically on ``kai.view.dashboard``.
    """,
    "author": "Kaiddons",
    "license": "LGPL-3",
    "depends": ["base", "web"],
    "data": [
        "security/kai_view_security.xml",
        "security/ir.model.access.csv",
        "data/demo_dashboard.xml",
        "views/report_views.xml",
        "views/dashboard_views.xml",
        "views/menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            ("include", "web.chartjs_lib"),
            "kaiSight/static/src/fields/kai_domain_field.js",
            "kaiSight/static/src/widgets/count_widget.xml",
            "kaiSight/static/src/widgets/chart_widget.xml",
            "kaiSight/static/src/widgets/list_widget.xml",
            "kaiSight/static/src/dashboard_action/dashboard.xml",
            "kaiSight/static/src/dashboard_action/dashboard.scss",
            "kaiSight/static/src/widgets/count_widget.js",
            "kaiSight/static/src/widgets/chart_widget.js",
            "kaiSight/static/src/widgets/list_widget.js",
            "kaiSight/static/src/dashboard_action/dashboard.js",
        ],
    },
    "application": True,
    "installable": True,
    "icon": "static/description/icon.svg",
    #"post_init_hook": "migrate_report_fields.migrate",
}
