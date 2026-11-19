from odoo import api, fields, models


class MainComponent(models.Model):
    _name = 'main.component'
    _description = 'Main Component'
    _order = 'id'
    _check_company_auto = True

    master_recipe_id = fields.Many2one(
        'master.recipe',
        string='Master Recipe',
        required=True,
        ondelete='cascade',
        check_company=True,
    )
    company_id = fields.Many2one(related='master_recipe_id.company_id', store=True, index=True)
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        check_company=True,
        required=True,
    )
    product_qty = fields.Float(
        string='Quantity',
        default=1.0,
        required=True,
    )
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        domain="[('category_id', '=', product_uom_category_id)]",
        required=True,
    )

    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')

    _sql_constraints = [
        ('positive_quantity', 'CHECK(product_qty >= 0)', 'Component quantities cannot be negative.'),
    ]

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for record in self:
            record.product_uom_id = record.product_id.uom_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('product_id') and not vals.get('product_uom_id'):
                vals['product_uom_id'] = self.env['product.product'].browse(vals['product_id']).uom_id.id
        records = super(MainComponent, self.with_context(skip_master_recipe_sync=True)).create(vals_list)
        if not self.env.context.get('skip_master_recipe_sync'):
            records.mapped('master_recipe_id')._sync_recipe_boms()
        return records

    def write(self, vals):
        recipes = self.mapped('master_recipe_id')
        res = super(MainComponent, self.with_context(skip_master_recipe_sync=True)).write(vals)
        if not self.env.context.get('skip_master_recipe_sync'):
            (recipes | self.mapped('master_recipe_id'))._sync_recipe_boms()
        return res

    def unlink(self):
        recipes = self.mapped('master_recipe_id')
        res = super(MainComponent, self.with_context(skip_master_recipe_sync=True)).unlink()
        if not self.env.context.get('skip_master_recipe_sync'):
            recipes._sync_recipe_boms()
        return res
