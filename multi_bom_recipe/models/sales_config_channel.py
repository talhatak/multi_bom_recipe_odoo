from odoo import api, fields, models


class SalesConfigChannel(models.Model):
    _inherit = 'sales.config.channel'

    master_recipe_id = fields.Many2one(
        'master.recipe',
        string='Master Recipe',
        ondelete='cascade',
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super(SalesConfigChannel, self.with_context(skip_master_recipe_sync=True)).create(vals_list)
        if not self.env.context.get('skip_master_recipe_sync'):
            records.mapped('master_recipe_id')._sync_recipe_boms()
        return records

    def write(self, vals):
        recipes = self.mapped('master_recipe_id')
        res = super(SalesConfigChannel, self.with_context(skip_master_recipe_sync=True)).write(vals)
        if not self.env.context.get('skip_master_recipe_sync'):
            (recipes | self.mapped('master_recipe_id'))._sync_recipe_boms()
        return res

    def unlink(self):
        recipes = self.mapped('master_recipe_id')
        res = super(SalesConfigChannel, self.with_context(skip_master_recipe_sync=True)).unlink()
        if not self.env.context.get('skip_master_recipe_sync'):
            recipes._sync_recipe_boms()
        return res
