# -*- coding: utf-8 -*-

from odoo import models, fields, api


class calculate_interest(models.Model):
    _name = 'calculate_interest'
    _description = 'calculate_interest'

    entry_date = fields.Date('Entry Date')
    entry_type = fields.Selection([
      ('withdraw', 'Withdraw'),
      ('interest2principal', 'Interest2Principal')
    ])
    entry_no = fields.Char()
    account_id = fields.Char()
    amount = fields.Integer()
    base_amount = fields.Integer()
    ledger = fields.Selection([
      ('principal', 'Principal'), 
      ('interest', 'Interest')
    ])

    @api.depends('value')
    def _value_pc(self):
        for record in self:
            record.value2 = float(record.value) / 100
