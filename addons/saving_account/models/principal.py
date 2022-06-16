# -*- coding: utf-8 -*-

from email.policy import default
from odoo import models, fields, api

class PrincipalBase(models.Model):
  _name = "principal.base"
  _description = "Principal Base"

  entry_date = fields.Date(string='Entry Date', default=fields.Date.today())
  entry_type = fields.Selection([
    ('deposit', 'Deposit'),
    ('withdraw', 'Withdraw'),
    ('interest', 'Interest'),
    ('credit_interest', 'Credit Interest')
  ], string='Entry Type')
  entry_no = fields.Char(string='Entry No')
  account_id = fields.Many2one('saving_account', string='Account')
  principal_amount = fields.Integer(string='Base Amount')
  ledger = fields.Selection([
    ('principal', 'Principal'), 
    ('interest', 'Interest')
  ], string='Ledger')
  description = fields.Text(string='Description')
  ref_no = fields.Char(string='Reference No')

  @api.model
  def create(self, vals):
    vals['entry_no'] = self.env['ir.sequence'].next_by_code('principal.base')
    return super(PrincipalBase, self).create(vals)