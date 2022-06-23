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
    account = self.env['saving_account'].search([('close_date','=',False)])
    rate = self.env['interest.rate'].search([('start_date','<=',fields.Date.today())])[-1]
    if account:
      account_type = account.account_type
      rate = self.env['interest.rate'].search([('start_date','<=',fields.Date.today()),('account_type','=',account_type)])[-1]
      if rate:
        interest_amount = (account.total_principal * (rate.annual_rate / 100)) / 365
        list = {
          'entry_type': 'interest',
          'account_id': account.id,
          'amount': interest_amount,
          'ledger': 'interest',
        }
        self.create(list)
    return
    