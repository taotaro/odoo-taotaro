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
  ref_no = fields.Selection([
    ('bf', 'BF'),
    ('dp', 'DP'),
    ('wd', 'WD'),
    ('ci', 'CI')
  ], string='Reference No')

  @api.model
  def create(self, vals):
    vals['entry_no'] = self.env['ir.sequence'].next_by_code('saving_account.entry')
    if vals['entry_type'] == 'deposit':
      vals['ref_no'] = 'dp'
      vals['ledger'] = 'principal'
    if vals['entry_type'] == 'withdraw':
      vals['ref_no'] = 'wd'
      vals['ledger'] = 'principal'
    if vals['entry_type'] == 'credit_interest':
      vals['ref_no'] = 'ci'
      vals['ledger'] = 'principal'
    return super(SavingAccountEntry, self).create(vals)

  @api.model
  def _cron_daily_interest(self):
    print("Calculating daily interest")
    account = self.env['saving_account'].search([('close_date','=',False)])
    rate = self.env['interest.rate'].search([('start_date','<=',fields.Date.today())])[-1]
    if account:
      account_type = account.account_type
      rate = self.env['interest.rate'].search([('start_date','<=',fields.Date.today()),('account_type','=',account_type)], order='start_date')[-1]
      if not rate:
        rate.annual_rate = 0
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
    