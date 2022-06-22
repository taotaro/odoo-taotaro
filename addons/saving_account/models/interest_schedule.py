from odoo import models, fields, api

class Schedule(models.Model):
    _name = 'interest.schedule'
    _description = 'Interest Schedule Setup'

    interest_calculation_time = fields.Date(string='Interest Calculation Time')
    credit_interest_day = fields.Date(string='Credit Interest Day')
    credit_interest_time = fields.Date(string='Credit Interest Time')
    