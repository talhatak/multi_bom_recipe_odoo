from collections import defaultdict

from odoo import api, models
from odoo.tools import OrderedSet


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    def _get_procurement_kit_bom(self, procurement, kits_by_company):
        sale_line_id = procurement.values.get('sale_line_id')
        if sale_line_id:
            sale_line = self.env['sale.order.line'].browse(sale_line_id)
            sale_order = sale_line.order_id
            if sale_order and sale_order.is_blink_order and sale_order.order_type:
                bom = self.env['mrp.bom'].sudo()._get_blink_delivery_bom(
                    procurement.product_id,
                    procurement.company_id.id,
                    sale_order.order_type
                )
                if bom:
                    return bom
        return kits_by_company[procurement.company_id].get(procurement.product_id)

    @api.model
    def run(self, procurements, raise_user_error=True):
        procurements_without_kit = []
        product_by_company = defaultdict(OrderedSet)
        for procurement in procurements:
            product_by_company[procurement.company_id].add(procurement.product_id.id)

        kits_by_company = {
            company: self.env['mrp.bom']._bom_find(
                self.env['product.product'].browse(product_ids),
                company_id=company.id,
                bom_type='phantom',
            )
            for company, product_ids in product_by_company.items()
        }

        for procurement in procurements:
            bom_kit = self._get_procurement_kit_bom(procurement, kits_by_company)
            if bom_kit:
                order_qty = procurement.product_uom._compute_quantity(
                    procurement.product_qty,
                    bom_kit.product_uom_id,
                    round=False,
                )
                qty_to_produce = order_qty / bom_kit.product_qty
                _dummy, bom_sub_lines = bom_kit.explode(
                    procurement.product_id,
                    qty_to_produce,
                    never_attribute_values=procurement.values.get("never_product_template_attribute_value_ids"),
                )
                for bom_line, bom_line_data in bom_sub_lines:
                    bom_line_uom = bom_line.product_uom_id
                    quant_uom = bom_line.product_id.uom_id
                    values = dict(procurement.values, bom_line_id=bom_line.id)
                    component_qty, procurement_uom = bom_line_uom._adjust_uom_quantities(
                        bom_line_data['qty'],
                        quant_uom,
                    )
                    procurements_without_kit.append(self.env['procurement.group'].Procurement(
                        bom_line.product_id,
                        component_qty,
                        procurement_uom,
                        procurement.location_id,
                        procurement.name,
                        procurement.origin,
                        procurement.company_id,
                        values,
                    ))
            else:
                procurements_without_kit.append(procurement)

        return super().run(procurements_without_kit, raise_user_error=raise_user_error)
