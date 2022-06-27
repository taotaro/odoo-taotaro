from odoo import models, fields, api

class TermAccountWizard(models.TransientModel):
  _name="term_account.report.wizard"
  _description="Print Term Account Report Wizard"

  date_from=fields.Date(string="Date From")
  date_to=fields.Date(string="Date To")

  def action_print_report(self):
    accounts = self.env['saving_account'].search_read([])
    data = { 
      'form': self.read()[0],
      'accounts': accounts
    }
    print("test...", data)
    return self.env.ref('saving_account.action_term_account_report').report_action(self, data=data)