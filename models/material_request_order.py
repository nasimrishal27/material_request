# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class MaterialRequestOrder(models.Model):
    """ model for storing Material Request Order details """
    _name = "material.request.order"
    _description = "Material Request Management"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name desc"

    name = fields.Char(string="Sequence", copy=False, default=lambda self: _('New'),
                       readonly=True)
    user_id = fields.Many2one(comodel_name="res.users", string="User",
                              default=lambda self: self.env.uid)
    company_id = fields.Many2one(comodel_name="res.company", string="Company", required=True,
                                 default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    order_line_ids = fields.One2many(comodel_name='material.request.order.line',
                                     inverse_name='order_id', ondelete='cascade')
    date = fields.Date('Date', default=fields.Date.today())
    state = fields.Selection([("draft", "Draft"), ("to-approve", "To Approve"),
                              ("to-confirm", "To Confirm"), ("confirm", "Confirmed"),
                              ("reject", "Rejected")], default="draft", tracking=True)
    purchase_order_count = fields.Integer(compute='_compute_purchase_order_count')
    internal_transfer_count = fields.Integer(compute='_compute_internal_transfer_count')

    @api.depends('state')
    def _compute_purchase_order_count(self):
        """ Computing purchase order count """
        for rec in self:
            rec.purchase_order_count = self.env['purchase.order'].search_count(
                [('material_request_id', '=', self.id)])

    @api.depends('state')
    def _compute_internal_transfer_count(self):
        """ Computing purchase order count """
        for rec in self:
            rec.internal_transfer_count = self.env['stock.picking'].search_count(
                [('material_request_id', '=', self.id)])

    @api.model
    def create(self, vals):
        """ Create a sequence for the model """
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('material.request.order')
        return super().create(vals)

    def action_draft(self):
        """ draft button """
        self.write({'state': "draft"})

    def action_confirm(self):
        """ confirm button """
        if self.env.user.has_group('material_request.material_request_group_administrator'):
            self.write({'state': "confirm"})
            purchasable_lines = self.order_line_ids.filtered(lambda l: l.product_type == 'po')
            transferable_lines = self.order_line_ids.filtered(lambda l: l.product_type == 'it')
            if purchasable_lines:
                for line in purchasable_lines:
                    for rec in line.vendor_ids:
                        draft_po = self.env['purchase.order'].search(
                            [('partner_id', '=', rec.id), ('material_request_id', '=', self.id),
                             ('state', '=', 'draft')])
                        if draft_po:
                            existing_line = draft_po.order_line.filtered(
                                lambda l: l.product_id.id == line.product_id.id)
                            if existing_line:
                                existing_line.write({"product_qty": line.quantity})
                            else:
                                self.env['purchase.order.line'].create({
                                    "order_id": draft_po.id,
                                    "product_id": line.product_id.id,
                                    "product_qty": line.quantity})
                        else:
                            self.env['purchase.order'].create({
                                "partner_id": rec.id,
                                "material_request_id": self.id,
                                'order_line': [
                                    fields.Command.create({
                                        "order_id": draft_po.id,
                                        "product_id": line.product_id.id,
                                        "product_qty": line.quantity,
                                    }),
                                ]
                            })
            if transferable_lines:
                for line in transferable_lines:
                    draft_it = self.env['stock.picking'].search([('material_request_id', '=', self.id),
                             ('state', '=', 'draft'), ('location_dest_id', '=', line.location_id.id)])
                    if draft_it:
                        existing_line = draft_it.move_ids.filtered(
                            lambda l: l.product_id.id == line.product_id.id)
                        if existing_line:
                            existing_line.write({"product_uom_qty": line.quantity})
                        else:
                            self.env['stock.move'].create({
                                "picking_id": draft_it.id,
                                "name": line.product_id.name,
                                "location_id": self.env.ref("stock.stock_location_stock").id,
                                "location_dest_id": line.location_id.id,
                                "product_id": line.product_id.id,
                                "product_uom_qty": line.quantity})
                    else:
                        self.env['stock.picking'].create({
                            "owner_id": self.user_id.id,
                            "material_request_id": self.id,
                            "picking_type_id": self.env.ref("stock.picking_type_internal").id,
                            "location_id": self.env.ref("stock.stock_location_stock").id,
                            "location_dest_id": line.location_id.id,
                            'move_ids': [
                                fields.Command.create({
                                    "picking_id": draft_it.id,
                                    "name": line.product_id.name,
                                    "location_id": self.env.ref("stock.stock_location_stock").id,
                                    "location_dest_id": line.location_id.id,
                                    "product_id": line.product_id.id,
                                    "product_uom_qty": line.quantity,
                                }),
                            ]
                        })
        elif self.env.user.has_group('material_request.material_request_group_manager'):
            self.write({'state': "to-confirm"})
        else:
            self.write({'state': "to-approve"})

    def action_reject(self):
        """ reject button """
        self.write({'state': "draft"})

    def action_open_purchase_order(self):
        """ smart button fo purchase order"""
        return {
            "name": "Purchase Order",
            "type": "ir.actions.act_window",
            "res_model": "purchase.order",
            'view_mode': 'list, form',
            'views': [(False, 'list'), (False, 'form')],
            'domain': [("material_request_id", "=", self.id)],
            "target": "current",
        }

    def action_open_internal_transfer(self):
        """ smart button fo purchase order"""
        return {
            "name": "Internal Transfer",
            "type": "ir.actions.act_window",
            "res_model": "stock.picking",
            'view_mode': 'list, form',
            'views': [(False, 'list'), (False, 'form')],
            'domain': [("material_request_id", "=", self.id)],
            "target": "current",
        }