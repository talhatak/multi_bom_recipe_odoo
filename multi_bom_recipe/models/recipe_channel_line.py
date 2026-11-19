from odoo import api, fields, models


class MasterRecipeChannelLine(models.Model):
    _name = 'master.recipe.channel.line'
    _description = 'Master Recipe Channel Component'
    _order = 'id'
    _check_company_auto = True

    master_recipe_id = fields.Many2one(
        'master.recipe', required=True, ondelete='cascade', index=True,
        check_company=True,
    )
    company_id = fields.Many2one(related='master_recipe_id.company_id', store=True, index=True)
    channel_id = fields.Many2one('restaurant.floor', string='Sales Channel', required=True, ondelete='restrict')
    product_id = fields.Many2one('product.product', string='Component', required=True, check_company=True)
    product_qty = fields.Float(string='Quantity', default=1.0, required=True, digits='Product Unit of Measure')
    product_uom_id = fields.Many2one(related='product_id.uom_id', string='Unit of Measure', readonly=True)

    _sql_constraints = [
        ('positive_quantity', 'CHECK(product_qty >= 0)', 'Component quantities cannot be negative.'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        records = super(MasterRecipeChannelLine, self.with_context(skip_master_recipe_sync=True)).create(vals_list)
        if not self.env.context.get('skip_master_recipe_sync'):
            records.mapped('master_recipe_id')._sync_recipe_boms()
        return records

    def write(self, vals):
        recipes = self.mapped('master_recipe_id')
        result = super(MasterRecipeChannelLine, self.with_context(skip_master_recipe_sync=True)).write(vals)
        if not self.env.context.get('skip_master_recipe_sync'):
            (recipes | self.mapped('master_recipe_id'))._sync_recipe_boms()
        return result

    def unlink(self):
        recipes = self.mapped('master_recipe_id')
        result = super(MasterRecipeChannelLine, self.with_context(skip_master_recipe_sync=True)).unlink()
        if not self.env.context.get('skip_master_recipe_sync'):
            recipes._sync_recipe_boms()
        return result
