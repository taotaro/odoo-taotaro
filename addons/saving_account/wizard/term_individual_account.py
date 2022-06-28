from odoo import models, fields, api

class TermIndividualAccountWizard(models.TransientModel):
  _name="term_individual_account.report.wizard"
  _description="Print Term Individual Account Report Wizard"

  account_id = fields.Many2one('saving_account', string='Account')
  date_from=fields.Date(string="Date From")
  date_to=fields.Date(string="Date To")

  def action_print_report(self):
    entry = self.env['saving_account.entry'].search_read([('account_id','=', self.account_id.id)])
    data = { 
      'form': self.read()[0],
      'entry': entry
    }
    print("test...", data)
    return self.env.ref('saving_account.action_term_individual_account_report').report_action(self, data=data)