# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SavingAccount(models.Model):
    _name = 'saving_account'
    _description = 'Saving Account'

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
    principal_list_ids = fields.One2many('principal.base', 'entry_no', string="Principal Lists", domain=[('entry_type','in',['deposit', 'withdraw'])])
    # interest_list_ids = fields.One2many('principal.base', 'entry_no', string="Interest Lists", domain=[('entry_type','=','interest')])
    total_principal = fields.Integer(compute='_compute_total_principal', string='Principal')
    # total_interest = fields.Char(compute='_calculate_total_interest', string='Interest')
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
        # total_principal = rec.env['principal.base'].search_count([('account_id','=',rec.id), ('entry_type','in',['deposit', 'withdraw'])])
        print(rec.principal_list_ids.principal_amount)
        total_principal = sum([rec.principal_list_ids.principal_amount])
        print(total_principal)
        rec.total_principal = total_principal
    