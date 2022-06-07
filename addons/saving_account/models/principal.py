# -*- coding: utf-8 -*-

from email.policy import default
from odoo import models, fields, api

class Principal(models.Model):
  _name = "principal"
  _description = "Principal"

  entry_date = fields.Date(string='Entry Date')
  entry_type = fields.Selection([
    ('deposit', 'Deposit'),
    ('withdraw', 'Withdraw'),
    ('interest2principal', 'Interest2Principal')
  ], string='Entry Type')
  entry_no = fields.Char(string='Entry No', default=1)
  account_id = fields.Many2one('saving_account', string='Account')
  base_amount = fields.Integer(string='Base Amount')
  add_amount = fields.Integer(string='Added Amount')
  ledger = fields.Selection([
    ('principal', 'Principal'), 
    ('interest', 'Interest')
  ], string='Ledger')
  ref_no = fields.Char(string='Reference No')

  # on create method
  @api.model
  def create(self, vals):
    obj = super(Principal, self).create(vals)
    if obj.entry_no == '/':
      number = self.env['ir.sequence'].get('PR') or '/'
      obj.write({'entry_no': number})
    return obj

