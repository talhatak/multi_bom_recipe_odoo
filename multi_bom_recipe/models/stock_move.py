from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools import OrderedSet, float_is_zero


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _is_pos_channel_parent_move(self):
        self.ensure_one()
        pos_order = self.picking_id.pos_order_id
        return bool(
            pos_order
            and pos_order.table_id
            and pos_order.table_id.floor_id
            and not self.bom_line_id
        )

    def _get_bom_for_pos_explode(self):
        self.ensure_one()
        if self._is_pos_channel_parent_move():
            bom = self.env['mrp.bom'].sudo()._get_pos_channel_bom(
                self.product_id,
                self.company_id.id,
                self.picking_id.pos_order_id.table_id.floor_id,
            )
            if bom:
                return bom
        return self.env['mrp.bom'].sudo()._bom_find(
            self.product_id,
            company_id=self.company_id.id,
            bom_type='phantom',
        )[self.product_id]

    def action_explode(self):
        moves_ids_to_return = OrderedSet()
        moves_ids_to_unlink = OrderedSet()
        phantom_moves_vals_list = []

        for move in self:
            if (
                (not move.picking_type_id and not (
                    self.env.context.get('is_scrap')
                    or self.env.context.get('skip_picking_assignation')
                ))
                or (move.production_id and move.production_id.product_id == move.product_id)
            ):
                moves_ids_to_return.add(move.id)
                continue

            bom = move._get_bom_for_pos_explode()
            if not bom:
                moves_ids_to_return.add(move.id)
                continue

            if float_is_zero(move.product_uom_qty, precision_rounding=move.product_uom.rounding):
                factor = move.product_uom._compute_quantity(move.quantity, bom.product_uom_id) / bom.product_qty
            else:
                factor = move.product_uom._compute_quantity(move.product_uom_qty, bom.product_uom_id) / bom.product_qty

            _dummy, lines = bom.sudo().explode(
                move.product_id,
                factor,
                picking_type=bom.picking_type_id,
                never_attribute_values=move.never_product_template_attribute_value_ids,
            )
            phantom_moves_vals_list += move._generate_all_phantom_moves(lines)
            moves_ids_to_unlink.add(move.id)

        if phantom_moves_vals_list:
            phantom_moves = self.env['stock.move'].create(phantom_moves_vals_list)
            phantom_moves._adjust_procure_method()
            moves_ids_to_return |= phantom_moves.action_explode().ids

        move_to_unlink = self.env['stock.move'].browse(moves_ids_to_unlink).sudo()
        move_to_unlink.quantity = 0
        move_to_unlink._action_cancel()
        move_to_unlink.unlink()
        return self.env['stock.move'].browse(moves_ids_to_return)

    def _add_mls_related_to_order(self, related_order_lines, are_qties_done=True):
        lines_data = self._prepare_lines_data_dict(related_order_lines)
        moves_to_assign = self.filtered(
            lambda m: m.product_id.id not in lines_data
            or m.product_id.tracking == 'none'
            or (not m.picking_type_id.use_existing_lots and not m.picking_type_id.use_create_lots)
        )

        uoms_with_issues = set()
        for move in moves_to_assign.filtered(lambda m: m.product_uom_qty and m.product_uom != m.product_id.uom_id):
            converted_qty = move.product_uom._compute_quantity(
                move.product_uom_qty,
                move.product_id.uom_id,
                rounding_method='HALF-UP',
            )
            if not converted_qty:
                uoms_with_issues.add((move.product_uom.name, move.product_id.uom_id.name))

        if uoms_with_issues:
            error_message_lines = [
                _("Conversion Error: The following unit of measure conversions result in a zero quantity due to rounding:")
            ]
            for uom_from, uom_to in uoms_with_issues:
                error_message_lines.append(_(
                    ' - From "%(uom_from)s" to "%(uom_to)s"',
                    uom_from=uom_from,
                    uom_to=uom_to,
                ))
            error_message_lines.append(_(
                "\nThis issue occurs because the quantity becomes zero after rounding during the conversion. "
                "To fix this, adjust the conversion factors or rounding method to ensure that even the smallest quantity in the original unit "
                "does not round down to zero in the target unit."
            ))
            raise UserError('\n'.join(error_message_lines))

        for move in moves_to_assign:
            move.quantity = move.product_uom_qty

        moves_remaining = self - moves_to_assign
        existing_lots = moves_remaining._create_production_lots_for_pos_order(related_order_lines)
        move_lines_to_create = []

        if are_qties_done:
            for move in moves_remaining:
                move.move_line_ids.unlink()
                for line in lines_data[move.product_id.id]['order_lines']:
                    for lot in line.pack_lot_ids.filtered(lambda l: l.lot_name):
                        qty = 1 if line.product_id.tracking == 'serial' else abs(line.qty)
                        if existing_lots:
                            existing_lot = existing_lots.filtered_domain([
                                ('product_id', '=', line.product_id.id),
                                ('name', '=', lot.lot_name),
                            ])
                            quants = self.env['stock.quant']
                            if existing_lot:
                                quants = self.env['stock.quant'].search(
                                    [
                                        ('lot_id', '=', existing_lot.id),
                                        ('quantity', '>', '0.0'),
                                        ('location_id', 'child_of', move.location_id.id),
                                    ],
                                    order='id desc',
                                )
                            qty_left_to_assign = qty
                            for quant in quants:
                                if qty_left_to_assign <= 0:
                                    break
                                qty_chg = min(qty_left_to_assign, quant.quantity)
                                ml_vals = dict(move._prepare_move_line_vals(qty_chg))
                                qty_left_to_assign -= qty_chg
                                ml_vals.update({'quant_id': quant.id})
                                move_lines_to_create.append(ml_vals)
                            if qty_left_to_assign > 0:
                                ml_vals = dict(move._prepare_move_line_vals(qty_left_to_assign))
                                ml_vals.update({
                                    'lot_name': existing_lot.name,
                                    'lot_id': existing_lot.id,
                                })
                                move_lines_to_create.append(ml_vals)
                        else:
                            ml_vals = dict(move._prepare_move_line_vals(qty))
                            ml_vals.update({'lot_name': lot.lot_name})
                            move_lines_to_create.append(ml_vals)
            self.env['stock.move.line'].create(move_lines_to_create)
        else:
            for move in moves_remaining:
                for line in lines_data[move.product_id.id]['order_lines']:
                    for lot in line.pack_lot_ids.filtered(lambda l: l.lot_name):
                        qty = 1 if line.product_id.tracking == 'serial' else abs(line.qty)
                        if existing_lots:
                            existing_lot = existing_lots.filtered_domain([
                                ('product_id', '=', line.product_id.id),
                                ('name', '=', lot.lot_name),
                            ])
                            if existing_lot:
                                move._update_reserved_quantity(qty, move.location_id, lot_id=existing_lot)
                                continue
