from odoo import api, fields, models
from odoo.osv import expression


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    master_recipe_id = fields.Many2one(
        'master.recipe', string='Master Recipe', ondelete='cascade',
        copy=False, check_company=True, index=True,
    )
    sales_channel_id = fields.Many2one(
        'restaurant.floor', string='Sales Channel', copy=False, ondelete='restrict', index=True,
    )
    is_master_recipe_bom = fields.Boolean(
        string='Generated From Master Recipe', default=False, copy=False,
    )

    @api.model
    def _bom_find_domain(self, products, picking_type=None, company_id=False, bom_type=False):
        domain = super()._bom_find_domain(
            products, picking_type=picking_type, company_id=company_id, bom_type=bom_type,
        )
        # Channel recipes are selected explicitly, never as a default for another channel.
        return expression.AND([domain, [
            ('is_master_recipe_bom', '=', False), ('sales_channel_id', '=', False),
        ]])

    @api.model
    def _bom_find(self, products, picking_type=None, company_id=False, bom_type=False):
        result = super()._bom_find(
            products, picking_type=picking_type, company_id=company_id, bom_type=bom_type,
        )
        channel_id = self.env.context.get('recipe_sales_channel_id')
        if not channel_id or bom_type not in (False, 'phantom'):
            return result

        products = products.filtered(lambda product: product.type != 'service')
        if not products:
            return result
        # Use the base domain to retain Odoo's product, operation type, and active filters.
        domain = super()._bom_find_domain(
            products, picking_type=picking_type, company_id=company_id, bom_type='phantom',
        )
        domain = expression.AND([domain, [
            ('is_master_recipe_bom', '=', True),
            ('sales_channel_id', '=', channel_id),
            ('company_id', '=', company_id or self.env.context.get('company_id') or self.env.company.id),
        ]])
        by_template = {}
        for bom in self.search(domain, order='sequence, id'):
            by_template.setdefault(bom.product_tmpl_id.id, bom)
        for product in products:
            if product.product_tmpl_id.id in by_template:
                result[product] = by_template[product.product_tmpl_id.id]
        return result
