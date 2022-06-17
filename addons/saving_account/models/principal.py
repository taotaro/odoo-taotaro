# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PrincipalBase(models.Model):
  _name = "principal.base"
  _description = "Principal Base"

  entry_no = fields.Char(string='Entry No')
  entry_date = fields.Date(string='Entry Date', default=fields.Date.today())
  entry_type = fields.Selection([
    ('deposit', 'Deposit'),
    ('withdraw', 'Withdraw'),
    ('interest', 'Interest'),
    ('credit_interest', 'Credit Interest')
  ], string='Entry Type')
  account_id = fields.Many2one('saving_account', string='Account')
  account_type = fields.Many2one('saving_account', string='Account Type')
  principal_amount = fields.Integer(string='Amount')
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

  @api.model
  def calculate_daily_interest(self):
    print("Calculating daily interest")

    