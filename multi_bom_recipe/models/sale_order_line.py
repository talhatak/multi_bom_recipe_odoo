from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_procurement_values(self, group_id=False):
        values = super()._prepare_procurement_values(group_id=group_id)
        values['recipe_sales_channel_id'] = self.order_id.sales_channel_id.id
        return values

    def _get_qty_procurement(self, previous_product_uom_qty=False):
        # Quantity increases must compare against the same kit used at confirmation.
        self.ensure_one()
        line = self.with_context(recipe_sales_channel_id=self.order_id.sales_channel_id.id)
        return super(SaleOrderLine, line)._get_qty_procurement(
            previous_product_uom_qty=previous_product_uom_qty,
        )

    @api.depends('product_uom_qty', 'qty_delivered', 'product_id', 'state', 'order_id.sales_channel_id')
    def _compute_qty_to_deliver(self):
        for channel in self.mapped('order_id.sales_channel_id'):
            lines = self.filtered(lambda line: line.order_id.sales_channel_id == channel)
            super(SaleOrderLine, lines.with_context(recipe_sales_channel_id=channel.id))._compute_qty_to_deliver()
        ordinary_lines = self.filtered(lambda line: not line.order_id.sales_channel_id)
        if ordinary_lines:
            super(SaleOrderLine, ordinary_lines.with_context(recipe_sales_channel_id=False))._compute_qty_to_deliver()
