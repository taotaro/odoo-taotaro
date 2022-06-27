from odoo import models, fields, api

class TermAccountWizard(models.TransientModel):
  _name="term_account.report.wizard"
  _description="Print Term Account Report Wizard"

  account_ids=fields.Many2many('saving_account')
  date_from=fields.Date(string="Date From")
  date_to=fields.Date(string="Date To")

  def action_print_report(self):
    data = { 'form': self.read()[0] }
    print("data", data)
    return self.env.ref('term_account_report').report_action(self, data=data)