from mimetypes import init
from odoo import models, fields, api

class TermIndividualAccountWizard(models.TransientModel):
  _name="term_individual_account.report.wizard"
  _description="Print Term Individual Account Report Wizard"

  account_id = fields.Many2one('saving_account', string='Account')
  date_from=fields.Date(string="Date From", default=fields.Date.today())
  date_to=fields.Date(string="Date To", default=fields.Date.today())

  def action_print_report(self):
    entries = self.env['saving_account.entry'].search_read([('account_id','=', self.account_id.id)])
    account = self.env['saving_account'].search_read([('account_id', '=', self.account_id.id)])
    initial_balance = account[0]['total_principal']
    initial_entry = {
      "entry_type": "initial",
      "balance": 0,
      "create_date": account[0]['create_date'],
      "ref_no": ""
      }
    entries.insert(0, initial_entry)

    for entry in entries:
      if entry['entry_type'] == 'withdraw':
        initial_balance -= entry['amount']
      elif entry['entry_type'] == 'deposit':
        initial_balance += entry['amount']
      elif entry['entry_type'] == 'interest':
        initial_balance += entry['amount']
      entry['balance'] = initial_balance

    data = { 
      'form': self.read()[0],
      'entry': entries,
    }
    return self.env.ref('saving_account.action_term_individual_account_report').report_action(self, data=data)