from collections import defaultdict

from odoo import api, models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.model
    def run(self, procurements, raise_user_error=True):
        by_channel = defaultdict(list)
        for procurement in procurements:
            by_channel[procurement.values.get('recipe_sales_channel_id', False)].append(procurement)
        result = True
        for channel_id, channel_procurements in by_channel.items():
            rule = self.with_context(recipe_sales_channel_id=channel_id)
            # MRP performs the actual kit explosion, UoM conversion, and procurement.
            channel_result = super(StockRule, rule).run(
                channel_procurements, raise_user_error=raise_user_error,
            )
            result = channel_result and result
        return result
