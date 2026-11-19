from collections import defaultdict

from odoo import api, models


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    @api.model
    def run(self, procurements, raise_user_error=True):
        by_channel = defaultdict(list)
        for procurement in procurements:
            by_channel[procurement.values.get('recipe_sales_channel_id', False)].append(procurement)
        result = True
        for channel_id, channel_procurements in by_channel.items():
            group = self.with_context(recipe_sales_channel_id=channel_id)
            # MRP performs the actual kit explosion, UoM conversion, and procurement.
            channel_result = super(ProcurementGroup, group).run(
                channel_procurements, raise_user_error=raise_user_error,
            )
            result = channel_result and result
        return result
