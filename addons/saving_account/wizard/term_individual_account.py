from odoo import models, fields, api, _
import base64
from ..helper import truncate_number

class TermIndividualAccountWizard(models.TransientModel):
  _name="term_individual_account.report.wizard"
  _description="Print Term Individual Account Report Wizard"

  account_id = fields.Many2one('saving_account', string='Account')
  date_from=fields.Date(string="Date From", default=fields.Date.today())
  date_to=fields.Date(string="Date To", default=fields.Date.today())
  email_to=fields.Char(string="Email To")

  def generate_report(self):
    # find entries within the specified date
    entries = self.env['saving_account.entry'].search_read([
      ('account_id','=', self.account_id.id), 
      ('ledger','=','principal'), 
      ('entry_date','>=',self.date_from), 
      ('entry_date','<=',self.date_to)
    ])
    # find account information
    account = self.env['saving_account'].search_read([('id','=',self.account_id.id)])
    
    # find entries from before the specified time to calculate initial balance
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

    # declare first entry with initial balance
    initial_entry = {
      "entry_type": "initial",
      "amount": 0,
      "balance": 0,
      "create_date": self.date_from,
      "ref_no": "BF"
      }
    entries.insert(0, initial_entry)

    # arrange entries according to type
    for entry in entries:
      if entry['entry_type'] == 'withdraw':
        initial_balance -= entry['amount']
      elif entry['entry_type'] == 'deposit':
        initial_balance += entry['amount']
      elif entry['entry_type'] == 'credit_interest':
        initial_balance += entry['amount']
      else:
        continue
      entry['balance'] = truncate_number(initial_balance, 2)

    data = { 
      'form': self.read()[0],
      'entry': entries,
      'account_no': account[0]['account_no_signed']
    }
    
    return data

  def action_print_report(self):
    data = self.generate_report()

    return self.env.ref('saving_account.action_term_individual_account_report').report_action(self, data=data)

  def action_send_email(self):
    data = self.generate_report()
    report_id = self.env.ref('saving_account.action_term_individual_account_report')._render(self.ids, data)
    report_b64 = base64.b64encode(report_id[0])
    now = fields.Datetime.today().strftime('%Y%m%d')
    report_name = now + '_term_individual_account.pdf'
    
    attachment = self.env['ir.attachment'].create({
            'name': report_name,
            'type': 'binary',
            'datas': report_b64,
            'store_fname': report_name,
            'mimetype': 'application/x-pdf'
        })

    email_values = {'email_to': self.email_to}

    report_template_id = self.env.ref('saving_account.mail_template_term_individual_account')
    report_template_id.attachment_ids = [(6, 0, [attachment.id])]
    report_template_id.send_mail(self.id, email_values=email_values, force_send=True)
    return {
      'type': 'ir.actions.client',
      'tag': 'display_notification',
      'params': {
        'title': _('Success'),
        'message': 'Email sent!',
        'sticky': True,
      }
    }

  @api.model
  def _cron_send_email(self):
    try:
      self.action_send_email()
    except:
      return {
          'type': 'ir.actions.client',
          'tag': 'display_notification',
          'params': {
            'title': _('Warning'),
            'message': 'Email failed to send',
            'sticky': True,
          }
      }