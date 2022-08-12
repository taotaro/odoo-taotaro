# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class EmailSetup(models.Model):
  _name = "email_setup"
  _description = "Setup email for scheduled actions"

  email_to=fields.Char(string="Email To")

  # @api.model
  # def create(self, cr, uid, vals, context=None):
  #   limit = len(self.search(cr, uid, [], context=context))
  #   if(limit <= 1):
  #     return super(EmailSetup, self).create(cr, uid, vals, context=context)