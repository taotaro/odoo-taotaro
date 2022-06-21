# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SavingAccountEntry(models.Model):
  _name = "saving_account.entry"
  _description = "Entry of saving account"

  entry_no = fields.Integer(string='Entry No')
  entry_date = fields.Date(string='Entry Date', default=fields.Date.today())
  entry_type = fields.Selection([
    ('deposit', 'Deposit'),
    ('withdraw', 'Withdraw'),
    ('interest', 'Interest'),
    ('credit_interest', 'Credit Interest')
  ], string='Entry Type')
  account_id = fields.Many2one('saving_account', string='Account')
  amount = fields.Integer(string='Amount')
  ledger = fields.Selection([
    ('principal', 'Principal'), 
    ('interest', 'Interest')
  ], string='Ledger')
  description = fields.Text(string='Description')
  ref_no = fields.Char(string='Reference No')

  @api.model
  def create(self, vals):
    vals['entry_no'] = self.env['ir.sequence'].next_by_code('saving_account.entry')
    return super(SavingAccountEntry, self).create(vals)

  @api.model
  def calculate_daily_interest(self):
    print("Calculating daily interest")
    for rec in self:
      account_list = rec.env('saving_account').search([('account_id','=',rec.account_id)])
      if account_list:
        for account in account_list:
          interest_amount = account.total_principal * 1.5
      
      list = {
        'entry_type': 'interest',
        'account_id': rec.account_id,
        'amount': interest_amount,
        'ledger': 'interest',
      }
      self.env['saving_account.entry'].create(list)

    