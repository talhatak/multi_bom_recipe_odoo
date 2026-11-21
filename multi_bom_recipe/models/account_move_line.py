from odoo import models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _get_pos_picking_moves_for_cogs(self):
        self.ensure_one()
        pickings = self.move_id.sudo().pos_order_ids.picking_ids.filtered(lambda picking: picking.state == 'done')
        if self.move_id.move_type == 'out_refund':
            return pickings.move_ids.filtered(lambda move: move.state == 'done' and move.location_id.usage == 'customer')
        return pickings.move_ids.filtered(lambda move: move.state == 'done' and move.location_dest_id.usage == 'customer')

    def _get_pos_recipe_cogs_value(self):
        """Return component cost per sold product's default unit, or None for standard costing."""
        self.ensure_one()
        if not self.move_id.sudo().pos_order_ids or not self.product_id or self.product_uom_id.is_zero(self.quantity):
            return None
        moves = self._get_pos_picking_moves_for_cogs()
        recipe_moves = moves.filtered(
            lambda move: move.bom_line_id.bom_id.is_master_recipe_bom
            and move.bom_line_id.bom_id.product_tmpl_id == self.product_id.product_tmpl_id
        )
        if not recipe_moves:
            return None
        relevant_moves = recipe_moves | moves.filtered(lambda move: move.product_id == self.product_id)
        # Odoo 19 stores valuation on stock.move.value instead of valuation layers.
        valuation_total = abs(sum(relevant_moves.mapped('value')))
        # Share the cost across repeated invoice lines instead of charging it on each line.
        lines = self.move_id.invoice_line_ids.filtered(
            lambda line: line.product_id == self.product_id and line.quantity * self.quantity > 0
        )
        quantity = sum(abs(line.product_uom_id._compute_quantity(
            line.quantity, self.product_id.uom_id, round=False,
        )) for line in lines)
        if self.product_id.uom_id.is_zero(quantity):
            return None
        return valuation_total / quantity

    def _get_cogs_value(self):
        value = self._get_pos_recipe_cogs_value()
        if value is not None:
            return value
        return super()._get_cogs_value()
