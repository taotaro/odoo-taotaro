# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SavingAccount(models.Model):
    _name = 'saving_account'
    _description = 'Saving Account'

    account_no = fields.Char(string='Account ID')
    account_type = fields.Selection([
      ('normal', 'Normal'), 
      ('vip', 'VIP')
    ], string="Account Type")
    name = fields.Char(string='Account Name')
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone Number')
    open_date = fields.Date(string='Open Date', default=fields.Date.today())
    close_date = fields.Date(string='Close Date')
    principal_amount = fields.Char(string='Principal')
    interest_amount = fields.Char(string='Interest')
    custom1 = fields.Text(string='Custom 1')
    custom2 = fields.Text(string='Custom 2')

    @api.model
    def create(self, vals):
      vals['account_no'] = self.env['ir.sequence'].next_by_code('saving_account')
      return super(SavingAccount, self).create(vals)