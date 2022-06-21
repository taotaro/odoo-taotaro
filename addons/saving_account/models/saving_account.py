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
    total_principal = fields.Integer(compute='_compute_total_principal', compute_sudo=True, string='Principal')
    total_interest = fields.Char(compute='_compute_total_interest', string='Interest')
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
        principal_list = rec.env['saving_account.entry'].search([('account_id','=',rec.id), ('entry_type','in',['deposit', 'withdraw'])])
        if principal_list:
          for principal in principal_list:
            if principal.entry_type == "deposit":
              current_total = current_total + principal.amount
            if principal.entry_type == "withdraw":
              current_total = current_total - principal.amount

        rec.total_principal = rec.total_principal + current_total
    
    @api.onchange('interest_list_ids')
    def _compute_total_interest(self):
      print('Calculating total interest')
      for rec in self:
        current_total = 0
        interest_list = rec.env['saving_account.entry'].search([('account_id','=',rec.id), ('entry_type','in','interest')])
        if interest_list:
          for interest in interest_list:
            current_total = current_total + interest.amount

        rec.total_interest = rec.total_interest + current_total
      
    