# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from ..helper import truncate_number


PRINCIPAL_SELECTION = [
    ('deposit', 'Deposit'),
    ('withdraw', 'Withdraw'),
  ]

ALL_SELECTION = [
    ('deposit', 'Deposit'),
    ('withdraw', 'Withdraw'),
    ('interest', 'Interest'),
    ('credit_interest', 'Credit Interest')
  ]

class SavingAccountEntry(models.Model):
  _name = "saving_account.entry"
  _description = "Entry of saving account"

  entry_no = fields.Integer(string='Entry No')
  entry_date = fields.Date(string='Entry Date', default=fields.Date.today())
  entry_type = fields.Selection(ALL_SELECTION, string='Entry Type')
  entry_type_principal = fields.Selection(PRINCIPAL_SELECTION, string='Entry Type')
  ledger = fields.Selection([
    ('principal', 'Principal'), 
    ('interest', 'Interest')
  ], string='Ledger')
  account_id = fields.Many2one('saving_account', string='Account')
  account_no = fields.Char(related='account_id.account_no', string='Account No')
  account_type = fields.Selection(related='account_id.account_type', string='Account Type')
   
  amount = fields.Float(string='Amount', digits=(16, 4))
  amount_signed = fields.Float(compute='_compute_amount_signed', string='Amount', digits=(16, 4))
  description = fields.Text(string='Description')
  reference = fields.Text(string='Reference')
  ref_no = fields.Selection([
    ('BF', 'BF'),
    ('DP', 'DP'),
    ('WD', 'WD'),
    ('CI', 'CI')
  ], string='Ref. No.')

  # calculate the current principal ammount
  def calculate_total_principal(self):
    current_total = 0
    # search principal entries of account
    principal_list = self.env['saving_account.entry'].search([
      ('account_id','=',self.account_id.id), 
      ('ledger','=','principal'),
    ])
    # tally the accumulated total
    if principal_list:
      for principal in principal_list:
        if principal.entry_type == "deposit":
          current_total = current_total + principal.amount
        elif principal.entry_type == "withdraw":
          current_total = current_total - principal.amount
        elif principal.entry_type == "credit_interest":
          current_total = current_total + principal.amount
    
    return current_total

  # check for validity and produce errors
  @api.constrains('entry_type_principal', 'entry_type', 'amount')
  def _check_amount(self):
    print("calling check amount")
    for rec in self:
      current_total = rec.account_id.total_principal + rec.amount
      # check if account is closed or not
      if rec.entry_type == 'deposit' and rec.account_id.close_date != False:
        raise ValidationError(_("Deposit is not allowed for closed account. 不能為已關閉的帳戶進行存款操作。"))
      #check if amount is greater than total money in account
      elif rec.entry_type == 'withdraw' and rec.amount > current_total:
        raise ValidationError(_("Withdraw Amount must not be larger than Principal Amount. 提款金額不能高於帳戶本金金額。"))
      elif rec.amount < 0:
        raise ValidationError(_("Value must not be negative. 數值不能為負值。"))

  @api.model
  def create(self, vals):
    print("calling create")
    # fill entry type field if there is any special conditions
    try:
      if vals['entry_type_principal']:
        self['entry_type'] = self['entry_type_principal']
        vals['entry_type'] = vals['entry_type_principal']
    except:
      print("no entry_type_principal")

    # fill reference number according to entry type
    if vals['entry_type']:
      if vals['entry_type'] == 'deposit':
        vals['ref_no'] = 'DP'
        vals['ledger'] = 'principal'
      if vals['entry_type'] == 'withdraw':
        vals['ref_no'] = 'WD'
        vals['ledger'] = 'principal'
      if vals['entry_type'] == 'credit_interest':
        vals['ref_no'] = 'CI'

    # create unique id for each entry
    vals['entry_no'] = self.env['ir.sequence'].next_by_code('saving_account.entry')

    return super(SavingAccountEntry, self).create(vals)

  # calculates daily interest with specified rate
  @api.model
  def _cron_daily_interest(self):
    print("Calculating daily interest")
    # search for accounts that are still open
    accounts = self.env['saving_account'].search([('close_date','=',False)])
    if accounts:
      for account in accounts:
        account_type = account.account_type
        # find rate to calculate daily interest
        rate = self.env['interest.rate'].search([
          ('start_date','<=',fields.Date.today()),
          ('account_type','=',account_type)], 
          order='start_date'
        )[-1]
        # if no rate, then no calculation
        if not rate:
          rate.annual_rate = 0
        # if rate is found, create the interest record
        if rate:
          interest_amount = (account.total_principal * (rate.annual_rate / 100)) / 365
          list = {
            'ledger': 'interest',
            'entry_type': 'interest',
            'account_id': account.id,
            'amount': truncate_number(interest_amount, 4),
            'description': 'Daily Interest - Base Amount: %.2f' % account.total_principal
          }
          self.create(list)
    return

  # moving credit interests from interest to principal by creating records
  @api.model
  def _cron_credit_interest(self):
    accounts = self.env['saving_account'].search([('close_date','=',False)])
    if accounts:
      for account in accounts:
        # value to deduct from interest
        deduct = {
          'ledger': 'interest',
          'entry_type': 'credit_interest',
          'account_id': account.id,
          'amount': account.total_interest,
        }
        # value to add to principal
        add = {
          'ledger': 'principal',
          'entry_type': 'credit_interest',
          'account_id': account.id,
          'amount': truncate_number(account.total_interest, 2)
        }
        self.create([deduct, add])
    return
  
  # displays negative values in the tree view
  @api.depends('amount')
  def _compute_amount_signed(self):
    for rec in self:
      if rec.entry_type == 'withdraw':
        rec.amount_signed = "-" + truncate_number(rec.amount, 2)
      elif rec.entry_type == 'credit_interest' and rec.ledger == 'interest':
        rec.amount_signed = "-" + truncate_number(rec.amount, 4)
      else:
        rec.amount_signed = truncate_number(rec.amount, 4)
      
      if rec.ledger == 'principal':
        rec.amount_signed = truncate_number(rec.amount_signed, 2)     
