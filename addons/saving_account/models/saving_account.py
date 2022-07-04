# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SavingAccount(models.Model):
    _name = 'saving_account'
    _description = 'Saving Account'

    account_id = fields.One2many('saving_account.entry', 'account_id', string='Account ID')
    account_no = fields.Char(string='Account No')
    account_type = fields.Selection([
      ('normal', 'Normal'), 
      ('vip', 'VIP')
    ], string="Account Type")
    name = fields.Char(string='Account Name')
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone Number')
    open_date = fields.Date(string='Open Date', default=fields.Date.today())
    close_date = fields.Date(string='Close Date')
    principal_list_ids = fields.One2many('saving_account.entry', 'amount', string="Principal Lists", domain=[('entry_type','in',['deposit', 'withdraw'])])
    interest_list_ids = fields.One2many('saving_account.entry', 'entry_no', string="Interest Lists", domain=[('entry_type','=','interest')])
    total_principal = fields.Float(compute='_compute_total_principal', compute_sudo=True, string='Principal')
    total_interest = fields.Float(compute='_compute_total_interest', compute_sudo=True, string='Interest', digits=(16, 4))
    # last_interest_credit = fields.Float(compute='_compute_last_interest_credit', compute_sudo=True, string='Last Interest Credit')
    custom1 = fields.Text(string='Custom 1')
    custom2 = fields.Text(string='Custom 2')

    @api.model
    def create(self, vals):
      vals['account_no'] = self.env['ir.sequence'].next_by_code('saving_account')
      return super(SavingAccount, self).create(vals)
    
    @api.depends('principal_list_ids')
    def _compute_total_principal(self):
      print('Calculating total principal')
      for rec in self:
        current_total = 0
        principal_list = rec.env['saving_account.entry'].search([
          ('account_id','=',rec.id), 
          ('ledger','=','principal'),
          ('entry_type','in',['deposit', 'withdraw', 'credit_interest'])
        ])
        if principal_list:
          for principal in principal_list:
            if principal.entry_type == "deposit":
              current_total = current_total + principal.amount
            if principal.entry_type == "withdraw":
              current_total = current_total - principal.amount
            if principal.entry_type == "credit_interest":
              current_total = current_total + principal.amount

        rec.total_principal = rec.total_principal + current_total
    
    @api.onchange('interest_list_ids')
    def _compute_total_interest(self):
      print('Calculating total interest')
      for rec in self:
        current_total = 0
        interest_list = rec.env['saving_account.entry'].search([
          ('account_id','=',rec.id), 
          ('ledger','=','interest'),
          ('entry_type','in',['interest', 'credit_interest'])
        ])
        if interest_list:
          for interest in interest_list:
            if interest.entry_type == 'interest':
              current_total = current_total + interest.amount
            # if interest.entry_type == 'credit_interest':
            #   current_total = current_total - interest.amount

        rec.total_interest = rec.total_interest + current_total

    
    # @api.depends('last_interest_credit')
    # def _compute_last_interest_credit(self):
    #   for rec in self:
    #     interest_credit = rec.env['saving_account.entry'].search([('account_id','=',rec.id), ('entry_type','=','interest')], limit=1)[-1]
    #     if interest_credit:
    #       rec.last_interest_credit = interest_credit.amount
    #     else:
    #       rec.last_interest_credit = 0.0
      
    def open_deposit_withdraw_form(self):
      print("Deposit/Withdraw", self.env['saving_account'].search([('id','=',self.id)]))
      return {
        'res_model': 'saving_account.entry',
        'type': 'ir.actions.act_window',
        'view_mode': 'form',
        'view_id': self.env.ref('saving_account.view_entry_form').id,
        'target': 'new',
        'context': {'account_id': self.env['saving_account'].search([('account_id','=',self.id)]).id}
      }