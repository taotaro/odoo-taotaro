# -*- coding: utf-8 -*-

from odoo import models, fields, api

ALL_SELECTION = [
  ('deposit', 'Deposit'),
  ('withdraw', 'Withdraw'),
  ('interest', 'Interest'),
  ('credit_interest', 'Credit Interest')
]

PRINCIPAL_SELECTION = [
  ('deposit', 'Deposit'),
  ('withdraw', 'Withdraw')
]

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
  ledger = fields.Selection([
    ('principal', 'Principal'), 
    ('interest', 'Interest')
  ], string='Ledger')
  # entry_type_all = fields.Selection(ALL_SELECTION, string='Entry Type All')
  # entry_type_principal = fields.Selection(PRINCIPAL_SELECTION, string='Entry Type Principal')
  # entry_type = fields.Selection(
  #   selection='_compute_entry_type',
  #   string="Entry Type",
  #   store=True,
  # )
  account_id = fields.Many2one('saving_account', string='Account')
  amount = fields.Float(string='Amount')
  amount_signed = fields.Float(compute='_compute_amount_signed', string='Amount')
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
    accounts = self.env['saving_account'].search([('close_date','=',False)])
    rate = self.env['interest.rate'].search([('start_date','<=',fields.Date.today())])[-1]
    if accounts:
      for account in accounts:
        account_type = account.account_type
        rate = self.env['interest.rate'].search([
          ('start_date','<=',fields.Date.today()),
          ('account_type','=',account_type)], 
          order='start_date'
        )[-1]
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

  # @api.onchange('ledger')
  # def _compute_entry_type(self):
  #   print("selff", self)
  #   for rec in self:
  #     print("recc", rec.ledger)
  #     print("entryy", rec.entry_type)
  #     print("entry1", rec._fields['entry_type_all'].selection)
  #     if rec.ledger == 'principal':
  #       return rec._fields['entry_type_principal'].selection
  #     else:
  #       return rec._fields['entry_type_all'].selection       