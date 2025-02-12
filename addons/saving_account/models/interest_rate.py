from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class InterestRate(models.Model):
    _name = 'interest.rate'
    _description = 'Interest Rate Setup'

    start_date = fields.Date(string='Starting Date', default=fields.Date.today())
    account_type = fields.Selection([
      ('normal', 'Normal'), 
      ('vip', 'VIP')
    ], string='Account Type')
    annual_rate = fields.Float(string='Annual Interest Rate', digits=(16, 4))

    @api.constrains('annual_rate')
    def _check_annual_rate(self):
      for rec in self:
        if rec.annual_rate < 0:
          raise ValidationError(_("Value must not be negative. 數值不能為負值。"))