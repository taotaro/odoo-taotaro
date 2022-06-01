# -*- coding: utf-8 -*-

from odoo import models, fields, api


class calculate_interest(models.Model):
    _name = 'calculate_interest'
    _description = 'Calculate Interest'

    entry_date = fields.Date(string='Entry Date')
    entry_type = fields.Selection([
      ('withdraw', 'Withdraw'),
      ('interest2principal', 'Interest2Principal')
    ], string='Entry Type')
    entry_no = fields.Char(string='Entry No')
    account_id = fields.Char(string='Account ID')
    amount = fields.Integer(string='Amount')
    base_amount = fields.Integer(string='Base Amount')
    ledger = fields.Selection([
      ('principal', 'Principal'), 
      ('interest', 'Interest')
    ], string='Ledger')
