from odoo import fields, models


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    master_recipe_id = fields.Many2one(
        'master.recipe',
        string='Master Recipe',
        ondelete='cascade',
        copy=False,
    )
    sales_channel_id = fields.Many2one(
        'restaurant.floor',
        string='Sales Channel',
        copy=False,
    )
    is_master_recipe_bom = fields.Boolean(
        string='Generated From Master Recipe',
        default=False,
        copy=False,
    )

    def _get_master_recipe_channel_bom(self, product, company_id, channel_name):
        return self.search([
            ('product_tmpl_id', '=', product.product_tmpl_id.id),
            ('product_id', '=', False),
            ('company_id', '=', company_id),
            ('type', '=', 'phantom'),
            ('is_master_recipe_bom', '=', True),
            ('sales_channel_id.name', '=ilike', channel_name),
        ], order='sequence, id', limit=1)

    def _get_blink_delivery_bom(self, product, company_id, order_type):
        return self._get_master_recipe_channel_bom(product, company_id, order_type)

    def _get_pos_channel_bom(self, product, company_id, floor):
        if not floor:
            return self.env['mrp.bom']
        return self._get_master_recipe_channel_bom(product, company_id, floor.name)
