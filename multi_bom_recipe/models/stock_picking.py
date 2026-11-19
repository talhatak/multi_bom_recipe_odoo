from odoo import api, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def _create_picking_from_pos_order_lines(self, location_dest_id, lines, picking_type, partner=False):
        pickings = self.env['stock.picking']
        # Session closing can contain several orders with different floors. Keep their
        # pickings separate so the correct channel is available before moves explode.
        for order in lines.order_id:
            order_lines = lines.filtered(lambda line: line.order_id == order)
            picking_model = self.with_context(recipe_pos_order_id=order.id)
            pickings |= super(StockPicking, picking_model)._create_picking_from_pos_order_lines(
                location_dest_id, order_lines, picking_type, partner=partner,
            )
        return pickings

    def _prepare_picking_vals(self, partner, picking_type, location_id, location_dest_id):
        vals = super()._prepare_picking_vals(partner, picking_type, location_id, location_dest_id)
        order = self.env['pos.order'].browse(self.env.context.get('recipe_pos_order_id')).exists()
        if order:
            vals.update({
                'pos_order_id': order.id,
                'pos_session_id': order.session_id.id,
                'origin': order.name,
            })
        return vals
