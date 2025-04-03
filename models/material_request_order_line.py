# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class MaterialRequestOrderLine(models.Model):
    """ model for storing Material Request Order Line details """
    _name = "material.request.order.line"

    order_id = fields.Many2one(comodel_name='material.request.order', string="Order Reference", required=True,
                               ondelete='cascade', copy=False)
    order_user_id = fields.Many2one(related='order_id.user_id', string="Customer", store=True)
    company_id = fields.Many2one(related='order_id.company_id', store=True)
    currency_id = fields.Many2one(related='order_id.currency_id', store=True)
    product_id = fields.Many2one(comodel_name='product.product', string="Product", ondelete='cascade')
    quantity = fields.Float(string="Quantity", digits='Product Unit of Measure', store=True)
    product_type = fields.Selection([("po", "Purchase Order"), ("it", "Internal Transfer")], string="Type",
                                    required=True, default="po")
    vendor_ids = fields.Many2many('res.partner')
    location_id = fields.Many2one('stock.location', domain=[('usage', '=', 'internal')])

    @api.onchange('product_type')
    def _onchange_product_type(self):
        self.vendor_ids = [fields.Command.clear()]