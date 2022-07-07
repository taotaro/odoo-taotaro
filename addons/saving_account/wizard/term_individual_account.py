from odoo import models, fields, api
import math

class TermIndividualAccountWizard(models.TransientModel):
  _name="term_individual_account.report.wizard"
  _description="Print Term Individual Account Report Wizard"

  account_id = fields.Many2one('saving_account', string='Account')
  date_from=fields.Date(string="Date From", default=fields.Date.today())
  date_to=fields.Date(string="Date To", default=fields.Date.today())

  def action_print_report(self):
    entries = self.env['saving_account.entry'].search_read([
      ('account_id','=', self.account_id.id), 
      ('ledger','=','principal'), 
      ('entry_date','>=',self.date_from), 
      ('entry_date','<=',self.date_to)
    ])
    account = self.env['saving_account'].search_read([('id', '=', self.account_id.id)])
    
    initial_entries = self.env['saving_account.entry'].search_read([
      ('account_id','=', self.account_id.id),
      ('ledger','=','principal'), 
      ('entry_date','<',self.date_from)
    ])
    initial_balance = 0
    for entry in initial_entries:
      if entry['ledger'] == 'principal':
        if entry['entry_type'] == 'withdraw':
          initial_balance -= entry['amount']
        else:
          initial_balance += entry['amount']

    for entry in entries:
      if entry['entry_type'] == 'withdraw':
        initial_balance -= entry['amount']
      elif entry['entry_type'] == 'deposit':
        initial_balance += entry['amount']
      elif entry['entry_type'] == 'interest':
        initial_balance += entry['amount']
      elif entry['entry_type'] == 'credit_interest':
        initial_balance += entry['amount']
      else:
        continue
      entry['balance'] = math.floor(initial_balance * 100) / 100.0

    initial_entry = {
      "entry_type": "initial",
      "balance": 0,
      "create_date": self.date_from,
      "ref_no": "BF"
      }
    entries.insert(0, initial_entry)

    data = { 
      'form': self.read()[0],
      'entry': entries,
      'account_no': account[0]['account_no_signed']
    }
    return self.env.ref('saving_account.action_term_individual_account_report').report_action(self, data=data)