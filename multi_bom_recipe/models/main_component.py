from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


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
        digits='Product Unit',
        required=True,
    )
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        domain="[('id', 'in', allowed_uom_ids)]",
        required=True,
    )

    allowed_uom_ids = fields.Many2many('uom.uom', compute='_compute_allowed_uom_ids')

    _positive_quantity = models.Constraint(
        'CHECK(product_qty >= 0)', 'Component quantities cannot be negative.',
    )

    @api.depends('product_id', 'product_id.uom_id')
    def _compute_allowed_uom_ids(self):
        for line in self:
            unit = line.product_id.uom_id
            if unit:
                reference_id = int(unit.parent_path.split('/')[0])
                line.allowed_uom_ids = self.env['uom.uom'].search([('id', 'child_of', reference_id)])
            else:
                line.allowed_uom_ids = self.env['uom.uom']

    @api.constrains('product_id', 'product_uom_id')
    def _check_component_uom(self):
        for line in self:
            if line.product_id and line.product_uom_id and not line.product_uom_id._has_common_reference(line.product_id.uom_id):
                raise ValidationError(_('The component unit must share a reference unit with the product unit.'))

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
        return records.with_env(self.env)

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
