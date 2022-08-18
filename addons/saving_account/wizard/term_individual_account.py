from odoo import models, fields, api, _
import base64
from ..helper import truncate_number

class TermIndividualAccountWizard(models.TransientModel):
  _name="term_individual_account.report.wizard"
  _description="Print Term Individual Account Report Wizard"

  account_id = fields.Many2one('saving_account', string='Account')
  date_from=fields.Date(string="Date From", default=fields.Date.today())
  date_to=fields.Date(string="Date To", default=fields.Date.today())
  email_to=fields.Char(string="Email To", _compute="_get_default_email")

  @api.onchange('email_to')
  def _get_default_email(self):
    email_to_send = self.env['email_setup'].search([], limit=1, order='create_date desc').email_to
    for rec in self:
      rec.email_to = email_to_send

  def generate_report(self):
    from_date = ""
    to_date = ""

    if not self.date_from:
      from_date = fields.Date.today()
    else:
      from_date = self.date_from

    if not self.date_to:
      to_date = fields.Date.today()
    else:
      to_date = self.date_to

    # find entries within the specified date
    entries = self.env['saving_account.entry'].search_read([
      ('account_id','=', self.account_id.id), 
      ('ledger','=','principal'), 
      ('entry_date','>=',from_date), 
      ('entry_date','<=',to_date)
    ])
    # find account information
    account = self.env['saving_account'].search_read([('id','=',self.account_id.id)])
    
    # find entries from before the specified time to calculate initial balance
    initial_entries = self.env['saving_account.entry'].search_read([
      ('account_id','=', self.account_id.id),
      ('ledger','=','principal'), 
      ('entry_date','<',from_date)
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
      "balance": initial_balance,
      "create_date": from_date,
      "ref_no": "BF"
      }
    entries.insert(0, initial_entry)

    #initialize total values
    total_withdraw, total_deposit, total_interest = 0, 0, 0

    # arrange entries according to type
    for entry in entries:
      if entry['entry_type'] == 'withdraw':
        initial_balance -= entry['amount']
        total_withdraw += entry['amount']
      elif entry['entry_type'] == 'deposit':
        initial_balance += entry['amount']
        total_deposit += entry['amount']
      elif entry['entry_type'] == 'credit_interest':
        initial_balance += entry['amount']
        total_interest += entry['amount']
      else:
        continue
      # truncate for display
      entry['amount'] = truncate_number(entry['amount'], 2)
      entry['balance'] = truncate_number(initial_balance, 2)

    data = { 
      'form': self.read()[0],
      'entry': entries,
      'account_no': account[0]['account_no_signed'],
      'total_withdraw': truncate_number(total_withdraw, 2),
      'total_deposit': truncate_number(total_deposit, 2),
      'total_interest': truncate_number(total_interest, 2)
    }
    
    return data

  def action_print_report(self):
    data = self.generate_report()

    return self.env.ref('saving_account.action_term_individual_account_report').report_action(self, data=data)

  def action_send_email(self):
    data = self.generate_report()
    report_id = self.env.ref('saving_account.action_term_individual_account_report')._render(self.ids, data=data)
    report_b64 = base64.b64encode(report_id[0])
    now = fields.Datetime.today().strftime('%Y%m%d')
    report_name = now + '_term_individual_account.pdf'
    
    # create email attachment
    attachment = self.env['ir.attachment'].create({
            'name': report_name,
            'type': 'binary',
            'datas': report_b64,
            'store_fname': report_name,
            'mimetype': 'application/x-pdf'
        })

    # find email to send to
    email_to_send = self.env['email_setup'].search([], limit=1, order='create_date desc').email_to
    email_values = {'email_to': email_to_send}
    print("Sending email to", email_to_send)

    # send email template
    report_template_id = self.env.ref('saving_account.mail_template_term_individual_account')
    report_template_id.attachment_ids = [(6, 0, [attachment.id])]
    try:
      # send confirmation message when successful
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
    except:
      # send warning message when fail
      return {
          'type': 'ir.actions.client',
          'tag': 'display_notification',
          'params': {
            'title': _('Warning'),
            'message': 'Email failed to send',
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