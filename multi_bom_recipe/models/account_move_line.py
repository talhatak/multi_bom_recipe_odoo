from odoo import models
from odoo.tools import float_is_zero


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _get_pos_picking_moves_for_cogs(self):
        self.ensure_one()
        if not self.move_id.pos_order_ids:
            return self.env['stock.move']

        pickings = self.move_id.pos_order_ids.sudo().mapped('picking_ids').filtered(
            lambda p: p.state == 'done'
        )
        if self.move_id.move_type == 'out_refund':
            return pickings.mapped('move_ids').filtered(
                lambda m: m.state == 'done' and m.location_id.usage == 'customer'
            )
        return pickings.mapped('move_ids').filtered(
            lambda m: m.state == 'done' and m.location_dest_id.usage == 'customer'
        )

    def _get_pos_cogs_price_unit(self):
        self.ensure_one()
        if not self.move_id.pos_order_ids or not self.product_id or float_is_zero(
            self.quantity, precision_rounding=self.product_uom_id.rounding
        ):
            return False

        moves = self._get_pos_picking_moves_for_cogs()
        if not moves:
            return False

        relevant_moves = moves.filtered(
            lambda m: m.product_id == self.product_id
            or (
                m.bom_line_id
                and m.bom_line_id.bom_id
                and m.bom_line_id.bom_id.product_tmpl_id == self.product_id.product_tmpl_id
            )
        )
        if not relevant_moves:
            return False

        valuation_total = abs(sum(relevant_moves.stock_valuation_layer_ids.mapped('value')))
        if not valuation_total:
            return False

        quantity = abs(self.quantity)
        if float_is_zero(quantity, precision_rounding=self.product_uom_id.rounding):
            return False

        return valuation_total / quantity

    def _stock_account_get_anglo_saxon_price_unit(self):
        self.ensure_one()
        pos_price_unit = self._get_pos_cogs_price_unit()
        if pos_price_unit:
            return pos_price_unit
        return super()._stock_account_get_anglo_saxon_price_unit()
