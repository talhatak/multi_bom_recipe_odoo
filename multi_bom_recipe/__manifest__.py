{
    'name': 'Multi BOM Recipe',
    'version': '18.0.2.0.0',
    'summary': 'Manage master recipes with sales channel and main component lines',
    'author': 'Talha Khan | Odoo Developer | Technical Consultant',
    'license': 'LGPL-3',
    'depends': ['mrp', 'sale_mrp', 'stock_account', 'point_of_sale', 'pos_restaurant', 'uom', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/recipe_security.xml',
        'views/master_recipe_views.xml',
        'views/mrp_bom.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': True,
}
