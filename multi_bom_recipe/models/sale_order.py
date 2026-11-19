from odoo import _, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sales_channel_id = fields.Many2one(
        'restaurant.floor', string='Sales Channel', ondelete='restrict', tracking=True,
        help='Restaurant floor used to choose the master recipe BoM for this order. '
             'Leave empty to use an ordinary BoM.',
    )

    def write(self, vals):
        if 'sales_channel_id' in vals:
            for order in self:
                if order.state not in ('draft', 'sent', 'cancel') and order.sales_channel_id.id != vals['sales_channel_id']:
                    raise UserError(_('The sales channel cannot be changed on a confirmed order. Cancel and reset the order to draft first.'))
        return super().write(vals)
