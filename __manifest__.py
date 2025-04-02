# -*- coding: utf-8 -*-
{
    'name': "Material Request Management",
    'version': '1.0',
    'depends': ['base', 'mail', 'product'],
    'sequence': 1,
    'author': "Suni",
    'category': 'All',
    'description': """
    Property Management
    """,
    # data files always loaded at installation
    'data': [
        'security/material_request_groups.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/material_request_order_view.xml',
        'views/material_request_menu_view.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}

