# -*- coding: utf-8 -*-

from cgi import test
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
  amount = fields.Float(string='Amount')
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
  def _cron_daily_interest(self):
    print("Calculating daily interest")
    account = self.env['saving_account'].search([('close_date','!=',False)])
    if account:
      interest_amount = account.total_principal * 1.5
      print("account", account)
      print("Interest amount", interest_amount)
      list = {
        'entry_type': 'interest',
        'account_id': account.id,
        'amount': interest_amount,
        'ledger': 'interest',
      }
      self.create(list)
    return
    