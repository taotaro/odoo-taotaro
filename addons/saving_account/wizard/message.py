from odoo import models, fields, api

class MessageWizard(models.TransientModel):
  _name="message.wizard"
  _description="Pop-up Message Wizard"

  message=fields.Text(string="Message", required=True)

  @api.model
  def action_close(self, vals):
    return { 'type': 'ir.actions.act_window_close' }