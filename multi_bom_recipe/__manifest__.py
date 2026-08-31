{
    'name': 'Multi BOM Recipe',
    'version': '18.0.1.0.0',
    'summary': 'Manage master recipes with sales channel and main component lines',
    'author': 'OpenAI',
    'license': 'LGPL-3',
    'depends': ['mrp', 'sale_mrp', 'stock_account', 'point_of_sale', 'uom', 'optp_ext', 'blink_integration'],
    'data': [
        'security/ir.model.access.csv',
        'views/master_recipe_views.xml',
        'views/mrp_bom.xml',
    ],
    'installable': True,
    'application': True,
}
