from collections import defaultdict

from odoo import api, fields, models


class MasterRecipe(models.Model):
    _name = 'master.recipe'
    _description = 'Master Recipe'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name, id'

    name = fields.Char(required=True)
    product_id = fields.Many2one(
        'product.template',
        string='Product',
        required=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    sales_channel_ids = fields.One2many(
        'sales.config.channel',
        'master_recipe_id',
        string='Sales Channels',
    )
    main_component_lines = fields.One2many(
        'main.component',
        'master_recipe_id',
        string='Main Components',
    )
    bom_counts = fields.Integer(
        string='BOM Count',
        compute='_compute_bom_counts',
    )

    def action_view_boms(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bills of Materials',
            'res_model': 'mrp.bom',
            'view_mode': 'list,form',
            'domain': [('master_recipe_id', '=', self.id)],
            'context': {
                'default_master_recipe_id': self.id,
                'default_product_tmpl_id': self.product_id.id,
                'search_default_master_recipe_id': self.id,
            },
        }

    @api.depends('sales_channel_ids', 'sales_channel_ids.channel_id')
    def _compute_bom_counts(self):
        bom_data = self.env['mrp.bom'].read_group(
            [('master_recipe_id', 'in', self.ids)],
            ['master_recipe_id'],
            ['master_recipe_id'],
        )
        counts = {
            record['master_recipe_id'][0]: record['master_recipe_id_count']
            for record in bom_data if record.get('master_recipe_id')
        }
        for recipe in self:
            recipe.bom_counts = counts.get(recipe.id, 0)

    def _get_channel_component_map(self, channel):
        self.ensure_one()
        component_map = defaultdict(float)

        for line in self.main_component_lines.filtered(lambda l: l.product_id and l.product_uom_id):
            qty = line.product_uom_id._compute_quantity(line.product_qty, line.product_id.uom_id)
            component_map[line.product_id.id] += qty

        channel_lines = self.sales_channel_ids.filtered(
            lambda line: line.channel_id == channel and line.product_id
        )
        for line in channel_lines:
            component_map[line.product_id.id] += line.product_qty

        return component_map

    def _prepare_bom_line_commands(self, channel):
        self.ensure_one()
        line_commands = [(5, 0, 0)]
        component_map = self._get_channel_component_map(channel)

        for product_id, qty in component_map.items():
            product = self.env['product.product'].browse(product_id)
            line_commands.append((0, 0, {
                'product_id': product.id,
                'product_qty': qty,
                'product_uom_id': product.uom_id.id,
            }))
        return line_commands

    def _prepare_recipe_bom_vals(self, channel):
        self.ensure_one()
        return {
            'product_tmpl_id': self.product_id.id,
            'product_id': False,
            'product_qty': 1.0,
            'product_uom_id': self.product_id.uom_id.id,
            'type': 'phantom',
            'company_id': self.company_id.id,
            'master_recipe_id': self.id,
            'sales_channel_id': channel.id,
            'is_master_recipe_bom': True,
            'code': f'MR-{self.id}-{channel.id}',
            'bom_line_ids': self._prepare_bom_line_commands(channel),
        }

    def _sync_recipe_boms(self):
        bom_obj = self.env['mrp.bom']
        for recipe in self:
            existing_boms = bom_obj.sudo().search([
                ('master_recipe_id', '=', recipe.id),
            ])
            active_channels = recipe.sales_channel_ids.mapped('channel_id')
            kept_boms = bom_obj.browse()

            for channel in active_channels:
                bom = existing_boms.filtered(lambda b: b.sales_channel_id == channel)[:1]
                vals = recipe._prepare_recipe_bom_vals(channel)
                if bom:
                    bom.with_context(no_sync=True).sudo().write(vals)
                else:
                    bom = bom_obj.with_company(recipe.company_id).with_context(no_sync=True).sudo().create(vals)
                kept_boms |= bom

            (existing_boms - kept_boms).with_context(no_sync=True).sudo().unlink()

    @api.model_create_multi
    def create(self, vals_list):
        records = super(MasterRecipe, self.with_context(skip_master_recipe_sync=True)).create(vals_list)
        records._sync_recipe_boms()
        return records

    def write(self, vals):
        res = super(MasterRecipe, self.with_context(skip_master_recipe_sync=True)).write(vals)
        self._sync_recipe_boms()
        return res

    def unlink(self):
        self.env['mrp.bom'].sudo().search([
            ('master_recipe_id', 'in', self.ids),
        ]).with_context(no_sync=True).unlink()
        return super(MasterRecipe, self.with_context(skip_master_recipe_sync=True)).unlink()
