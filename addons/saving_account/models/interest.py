# -*- coding: utf-8 -*-

from email.policy import default
from odoo import models, fields, api

class PrincipalInterest(models.Model):
  _name = "principal.interest"
  _description = "Interest accumulated"
  _inherit = "principal.base"

  add_amount = fields.Integer(string='Added Amount')

  @api.model
  def calculate_daily_interest(self):
    print("test")