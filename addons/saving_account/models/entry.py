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
  amount_signed = fields.Float(compute='_compute_amount_signed', string='Amount')
  ledger = fields.Selection([
    ('principal', 'Principal'), 
    ('interest', 'Interest')
  ], string='Ledger')
  description = fields.Text(string='Description')
  ref_no = fields.Selection([
    ('BF', 'BF'),
    ('DP', 'DP'),
    ('WD', 'WD'),
    ('CI', 'CI')
  ], string='Reference No')

  @api.model
  def create(self, vals):
    vals['entry_no'] = self.env['ir.sequence'].next_by_code('saving_account.entry')
    if vals['entry_type'] == 'deposit':
      vals['ref_no'] = 'DP'
      vals['ledger'] = 'principal'
    if vals['entry_type'] == 'withdraw':
      vals['ref_no'] = 'WD'
      vals['ledger'] = 'principal'
    if vals['entry_type'] == 'credit_interest':
      vals['ref_no'] = 'CI'
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

  @api.model
  def _cron_credit_interest(self):
    account = self.env['saving_account'].search([('close_date','=',False)])
    if account:
      deduct = {
        'entry_type': 'credit_interest',
        'account_id': account.id,
        'amount': account.total_interest,
        'ledger': 'interest'
      }
      add = {
        'entry_type': 'credit_interest',
        'account_id': account.id,
        'amount': account.total_interest,
        'ledger': 'principal'
      }
      self.create([deduct, add])
    return
  
  @api.depends('amount')
  def _compute_amount_signed(self):
    for rec in self:
      if rec.entry_type == 'withdraw':
        rec.amount_signed = - rec.amount
      elif rec.entry_type == 'credit_interest' and rec.ledger == 'interest':
        rec.amount_signed = - rec.amount
      else:
        rec.amount_signed = rec.amount
    