# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SavingAccount(models.Model):
    _name = 'saving_account'
    _description = 'Saving Account'

    name = fields.Char(string='Account Name')
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone Number')
    open_date = fields.Date(string='Open Date')
    close_date = fields.Date(string='Close Date')

