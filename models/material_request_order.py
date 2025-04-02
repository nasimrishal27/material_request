# -*- coding: utf-8 -*-
from email.policy import default

from odoo import _, api, fields, models


class MaterialRequestOrder(models.Model):
    """ model for storing Material Request Order details """
    _name = "material.request.order"
    _description = "Material Request Management"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name desc"

    name = fields.Char(string="Sequence", copy=False, default=lambda self: _('New'),
                       readonly=True)
    partner_id = fields.Many2one(comodel_name="res.users", string="Partner", default=lambda self: self.env.uid)
    company_id = fields.Many2one(comodel_name="res.company", string="Company", required=True,
                                 default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    order_line_ids = fields.One2many(comodel_name='material.request.order.line',
                                     inverse_name='order_id', ondelete='cascade')
    date = fields.Date('Date', default=fields.Date.today())
    state = fields.Selection([("draft", "Draft"), ("to-approve", "To Approve"),
                              ("to-confirm", "To Confirm"), ("confirm", "Confirmed"), ("reject", "Rejected")],
                             default="draft", tracking=True)

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
            print(purchasable_lines)
            # if purchasable_lines:
            #     for line in purchasable_lines:
            #
        elif self.env.user.has_group('material_request.material_request_group_manager'):
            self.write({'state': "to-confirm"})
        else:
            self.write({'state': "to-approve"})

    def action_reject(self):
        """ draft button """
        self.write({'state': "draft"})
