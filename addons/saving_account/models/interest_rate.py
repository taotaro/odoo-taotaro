from odoo import models, fields, api

class InterestRate(models.Model):
    _name = 'interest.rate'
    _description = 'Interest Rate Setup'

    start_date = fields.Date(string='Starting Date', default=fields.Date.today())
    account_type = fields.Selection([
      ('normal', 'Normal'), 
      ('vip', 'VIP')
    ], string='Account Type')
    annual_rate = fields.Float(string='Annual Interest Rate', digits=(16, 4))