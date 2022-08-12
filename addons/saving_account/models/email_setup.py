# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class EmailSetup(models.Model):
  _name = "email_setup"
  _description = "Setup email for scheduled actions"

  email_to=fields.Char(string="Email To")