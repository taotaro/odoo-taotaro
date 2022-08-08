# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime
from ..helper import truncate_number

class SavingAccount(models.Model):
  _name = 'saving_account'
  _description = 'Saving Account'

  account_id = fields.One2many('saving_account.entry', 'account_id', string='Account ID')
  account_no = fields.Char(string='Account No')
  account_no_signed = fields.Char(compute='_compute_account_no_signed', string='Account No')
  account_type = fields.Selection([
    ('normal', 'Normal'), 
    ('vip', 'VIP')
  ], default='normal', string="Account Type")
  name = fields.Char(string='Account Name')
  email = fields.Char(string='Email')
  phone = fields.Char(string='Phone Number')
  open_date = fields.Date(string='Open Date', default=fields.Date.today())
  close_date = fields.Date(string='Close Date')
  principal_list_ids = fields.One2many('saving_account.entry', 'amount', string="Principal Lists", domain=[('entry_type','in',['deposit', 'withdraw'])])
  interest_list_ids = fields.One2many('saving_account.entry', 'entry_no', string="Interest Lists", domain=[('entry_type','=','interest')])
  total_principal = fields.Float(compute='_compute_total_principal', compute_sudo=True, string='Principal')
  total_interest = fields.Float(compute='_compute_total_interest', compute_sudo=True, string='Interest', digits=(16, 4))
  last_interest_credit = fields.Float(compute='_compute_last_interest_credit', compute_sudo=True, string='Last Interest Credit')
  custom1 = fields.Text(string='Custom 1')
  custom2 = fields.Text(string='Custom 2')

  @api.model
  def create(self, vals):
    # create unique id for each account
    vals['account_no'] = self.env['ir.sequence'].next_by_code('saving_account')
    return super(SavingAccount, self).create(vals)
  
  # calculate total principal amount of each account
  @api.depends('principal_list_ids')
  def _compute_total_principal(self):
    for rec in self:
      current_total = 0
      # search principal entries of account
      principal_list = rec.env['saving_account.entry'].search([
        ('account_id','=',rec.id), 
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

      # update the amount
      rec.total_principal = rec.total_principal + current_total
      rec.total_principal = truncate_number(rec.total_principal, 2)

  # calculate total interest of each account
  @api.onchange('interest_list_ids')
  def _compute_total_interest(self):
    for rec in self:
      current_total = 0
      # search interest entries of account
      interest_list = rec.env['saving_account.entry'].search([
        ('account_id','=',rec.id), 
        ('ledger','=','interest'),
        ('entry_type','in',['interest', 'credit_interest'])
      ])
      # tally the accumulated total
      if interest_list:
        for interest in interest_list:
          if interest.entry_type == 'interest':
            current_total = current_total + interest.amount
          if interest.entry_type == 'credit_interest':
            current_total = current_total - interest.amount

      # update the amount
      rec.total_interest = rec.total_interest + current_total
      rec.total_interest = truncate_number(rec.total_interest, 2)
  
  # add a sign to unique account id according to account type
  @api.depends('account_no')
  def _compute_account_no_signed(self):
    for rec in self:
      if rec.account_type == 'normal':
        rec.account_no_signed = rec.account_no + 'N'
      if rec.account_type == 'vip':
        rec.account_no_signed = rec.account_no + 'V'

  @api.depends('last_interest_credit')
  def _compute_last_interest_credit(self):
    for rec in self:
      interest_credit = rec.env['saving_account.entry'].search([
        ('account_id','=',rec.id), 
        ('entry_type','=','credit_interest'), 
        ('ledger','=','principal')
      ])
      if interest_credit:
        rec.last_interest_credit = interest_credit[-1].amount
      else:
        rec.last_interest_credit = 0.0

  # button to open the deposit/withdraw form of an account
  def open_deposit_withdraw_form(self):
    account_entry = self.env['saving_account.entry'].search([('account_id','=',self.id)])

    # if account is closed, give default entry type as withdraw. cannot do deposit
    if self.close_date:
      return {
        'res_model': 'saving_account.entry',
        'type': 'ir.actions.act_window',
        'view_mode': 'form',
        'view_id': self.env.ref('saving_account.view_entry_form1').id,
        'target': 'new',
        'context': {
          'default_account_id': self.id,
          'default_ledger': 'principal',
          'default_entry_type_principal': 'withdraw'
        }
      }
    # if account is still open, open regular entry form
    else:
      return {
        'res_model': 'saving_account.entry',
        'type': 'ir.actions.act_window',
        'view_mode': 'form',
        'view_id': self.env.ref('saving_account.view_entry_form1').id,
        'target': 'new',
        'context': {
          'default_account_id': self.id,
          'default_ledger': 'principal',
        }
      }

  # button to close account, move interest accumulated to principal 
  # and open deposit/withdraw form
  def action_close_account(self):
    account = self.env['saving_account'].search([('id','=',self.id)])
    if account['close_date'] == False:
      account['close_date'] = datetime.date.today()
      if account['total_interest'] > 0:
        # value to deduct from interest
        deduct = {
          'entry_type': 'credit_interest',
          'account_id': account.id,
          'amount': account['total_interest'],
          'ledger': 'interest'
        }
        # value to add to principal
        add = {
          'entry_type': 'credit_interest',
          'account_id': account.id,
          'amount': truncate_number(account['total_interest'], 2),
          'ledger': 'principal'
        }
        self.env['saving_account.entry'].create([deduct, add])

      #open deposit/withdraw form
      return {
        'res_model': 'saving_account.entry',
        'type': 'ir.actions.act_window',
        'view_mode': 'form',
        'view_id': self.env.ref('saving_account.view_entry_form1').id,
        'target': 'new',
        'context': {
          'default_account_id': account.id,
          'default_ledger': 'principal',
          'default_entry_type_principal': 'withdraw',
          'default_amount': account.total_principal + account.total_interest
        }
      }
    