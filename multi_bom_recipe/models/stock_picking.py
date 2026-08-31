from odoo import api, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def _create_picking_from_pos_order_lines(
        self,
        location_dest_id,
        lines,
        picking_type,
        partner=False,
        refund_type=False,
        business_date=False,
    ):
        pickings = self.env['stock.picking']
        stockable_lines = lines.filtered(
            lambda l: l.product_id.type == 'consu'
            and not float_is_zero(l.qty, precision_rounding=l.product_id.uom_id.rounding)
        )
        if not stockable_lines:
            return pickings

        pos_order = stockable_lines[:1].order_id
        positive_lines = stockable_lines.filtered(lambda l: l.qty > 0)
        negative_lines = stockable_lines - positive_lines

        if positive_lines:
            location_id = picking_type.default_location_src_id.id
            picking_vals = self._prepare_picking_vals(partner, picking_type, location_id, location_dest_id)
            if pos_order:
                picking_vals.update({
                    'pos_order_id': pos_order.id,
                    'pos_session_id': pos_order.session_id.id,
                    'origin': pos_order.name,
                    'date_done': pos_order.date_order,
                })
            positive_picking = self.env['stock.picking'].create(picking_vals)

            positive_picking._create_move_from_pos_order_lines(positive_lines)

            try:
                with self.env.cr.savepoint():
                    positive_picking.write({'scheduled_date': business_date, 'date_done': business_date})
                    positive_picking._action_done()

                    moves = positive_picking.move_ids_without_package
                    moves.write({'date': business_date})
                    moves.move_line_ids.write({'date': business_date})

                    layer_ids = moves.stock_valuation_layer_ids.ids
                    if layer_ids:
                        self.env.cr.execute(
                            "UPDATE stock_valuation_layer SET create_date = %s WHERE id = ANY(%s)",
                            (business_date, layer_ids),
                        )

                    account_move_ids = moves.stock_valuation_layer_ids.account_move_id.ids
                    if account_move_ids:
                        self.env.cr.execute(
                            "UPDATE account_move SET date = %s WHERE id = ANY(%s)",
                            (business_date, account_move_ids),
                        )
                        self.env.cr.execute(
                            "UPDATE account_move_line SET date = %s WHERE move_id = ANY(%s)",
                            (business_date, account_move_ids),
                        )
            except (UserError, ValidationError):
                pass

            pickings |= positive_picking

        if negative_lines:
            if picking_type.return_picking_type_id:
                return_picking_type = picking_type.return_picking_type_id
                return_location_id = return_picking_type.default_location_dest_id.id
            else:
                return_picking_type = picking_type
                return_location_id = picking_type.default_location_src_id.id

            picking_vals = self._prepare_picking_vals(
                partner,
                return_picking_type,
                location_dest_id,
                return_location_id,
                refund_type=refund_type,
            )
            if pos_order:
                picking_vals.update({
                    'pos_order_id': pos_order.id,
                    'pos_session_id': pos_order.session_id.id,
                    'origin': pos_order.name,
                    'date_done': pos_order.date_order,
                })
            negative_picking = self.env['stock.picking'].create(picking_vals)
            negative_picking._create_move_from_pos_order_lines(negative_lines)

            self.env.flush_all()
            try:
                with self.env.cr.savepoint():
                    negative_picking.write({'scheduled_date': business_date, 'date_done': business_date})
                    negative_picking._action_done()

                    moves = negative_picking.move_ids_without_package
                    moves.write({'date': business_date})
                    moves.move_line_ids.write({'date': business_date})

                    layer_ids = moves.stock_valuation_layer_ids.ids
                    if layer_ids:
                        self.env.cr.execute(
                            "UPDATE stock_valuation_layer SET create_date = %s WHERE id = ANY(%s)",
                            (business_date, layer_ids),
                        )

                    account_move_ids = moves.stock_valuation_layer_ids.account_move_id.ids
                    if account_move_ids:
                        self.env.cr.execute(
                            "UPDATE account_move SET date = %s WHERE id = ANY(%s)",
                            (business_date, account_move_ids),
                        )
                        self.env.cr.execute(
                            "UPDATE account_move_line SET date = %s WHERE move_id = ANY(%s)",
                            (business_date, account_move_ids),
                        )
            except (UserError, ValidationError):
                pass

            pickings |= negative_picking

        return pickings
