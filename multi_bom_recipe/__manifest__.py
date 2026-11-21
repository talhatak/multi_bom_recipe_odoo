# -*- coding: utf-8 -*-
#############################################################################
#
#    Copyright (C) 2026-TODAY Talha Khan
#    Author: Talha Khan
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License (LGPL v3).
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program. If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Multi BOM Recipe',
    'version': '17.0.2.1.1',
    'category': 'Manufacturing',
    'summary': """Master recipes, channel-specific bills of materials, shared
    ingredients, restaurant POS recipes, and Sales Order recipe selection
    for Odoo 17""",
    'description': """Multi BOM Recipe for Odoo 17
    Manage shared ingredients and channel-specific components from one master
    recipe. Automatically generate and maintain a kit bill of materials for
    each selected restaurant floor used as a sales channel.

    Define common ingredients once, add packaging or other extras for Delivery
    and Pickup, and open the generated bills of materials from the recipe.
    Restaurant POS selects the recipe using the order's table floor. Sales
    Orders use the Sales Channel selected on the quotation.

    Includes component quantity conversion, duplicate component merging,
    company-specific recipes, and access rules for recipe management.
    """,
    'author': 'Talha Khan | Odoo Developer | Technical Consultant',
    'company': 'Talha Khan',
    'maintainer': 'Talha Khan',
    'website': 'https://github.com/talhatak/multi_bom_recipe_odoo',
    'depends': [
        'mrp',
        'sale_mrp',
        'stock_account',
        'point_of_sale',
        'pos_restaurant',
        'uom',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/recipe_security.xml',
        'views/master_recipe_views.xml',
        'views/mrp_bom.xml',
        'views/sale_order_views.xml',
    ],
    'license': 'LGPL-3',
    'images': ['static/description/banner-17.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
