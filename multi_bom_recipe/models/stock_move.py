from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def action_explode(self):
        by_channel = {}
        for move in self:
            channel_id = False
            if not move.bom_line_id:
                pos_order = move.picking_id.pos_order_id or move.group_id.pos_order_id
                if pos_order:
                    channel_id = pos_order.table_id.floor_id.id
                elif move.sale_line_id:
                    channel_id = move.sale_line_id.order_id.sales_channel_id.id
            by_channel.setdefault(channel_id, self.env['stock.move'])
            by_channel[channel_id] |= move

        result = self.env['stock.move']
        for channel_id, moves in by_channel.items():
            # Delegate explosion, returns, and component move quantities to standard MRP.
            moves = moves.with_context(recipe_sales_channel_id=channel_id)
            result |= super(StockMove, moves).action_explode()
        return result
