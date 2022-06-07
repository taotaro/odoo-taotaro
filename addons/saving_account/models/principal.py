# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Principal(models.Model):
  _name = "principal"
  _description = "Principal"

  entry_date = fields.Date(string='Entry Date')
  entry_type = fields.Selection([
    ('deposit', 'Deposit'),
    ('withdraw', 'Withdraw'),
    ('interest2principal', 'Interest2Principal')
  ], string='Entry Type')
  entry_no = fields.Char(string='Entry No')
  account_id = fields.Char(string='Account ID')
  # account_name = fields.Many2one('hr.employee.name', string='Account Name')
  base_amount = fields.Integer(string='Base Amount')
  add_amount = fields.Integer(string='Added Amount')
  ledger = fields.Selection([
    ('principal', 'Principal'), 
    ('interest', 'Interest')
  ], string='Ledger')
  ref_no = fields.Char(string='Reference No')