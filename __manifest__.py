# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (C) Brayhan Jaramillo.
#               brayhanjaramillo@hotmail.com


{
    'name': 'Mrp Generate Request',
    'version': '10,0',
    'category': 'Create Request',
    'description': '',
    'author': 'Brayhan Andres Jaramillo Castaño',
    'depends': [
        'mrp',
        'base',
        'purchase_request',
        'alfa_amb_mrp_purchase_request'
    ],

    'data': [
        'views/mrp_production_inherit_view.xml',
    ],
    'installable': True,
}
