from ..helper import truncate_number, find_last_1april
from odoo import models, fields, api, _
import base64
import logging
_logger = logging.getLogger(__name__)


class TermAccountWizard(models.TransientModel):
  _name="term_account.report.wizard"
  _description="Print Term Account Report Wizard"

  account_type = fields.Selection([
    ('all', 'All'),
    ('normal', 'Normal'), 
    ('vip', 'VIP')
  ], default='all', string="Account Type")
  date_from=fields.Date(string="Date as of", default=fields.Date.today())
  date_to=fields.Date(string="Date To")
  email_to=fields.Char(string="Email To", _compute="_get_default_email")

  @api.onchange('email_to')
  def _get_default_email(self):
    email_to_send = self.env['email_setup'].search([], limit=1, order='create_date desc').email_to
    for rec in self:
      rec.email_to = email_to_send

  def generate_report(self):
    from_date = ""
    type_account = ""
    if not self.date_from:
      from_date = fields.Date.today()
    else:
      from_date = self.date_from

    _logger.info(f'logger from date {from_date}')

    if not self.account_type:
      type_account = 'all'
    else:
      type_account = self.account_type

    #find last 1 april
    april = find_last_1april(from_date)
    
    # find accounts in specified term and types
    accounts = []
    account_401 = self.env['saving_account'].search_read([
      ('account_no', '=', '401')
    ])
    _logger.info(f'found: account 401 {account_401}')
    if type_account != 'all':
      accounts = self.env['saving_account'].search_read([
        ('account_type','=',type_account),
        ('open_date','<=',from_date),
        ('close_date','=',False)
      ])
    else:
      accounts = self.env['saving_account'].search_read([
        ('open_date','<=',from_date),
        ('close_date','=',False)
      ])

    # truncate properly
    for account in accounts:
      account_no = account['account_no']
      close_date = account['close_date']
      
      total_principal = truncate_number(account['total_principal'], 2)
      last_interest_credit = truncate_number(account['last_interest_credit'], 2)
      # account['total_principal'] = truncate_number(account['total_principal'], 2)
      account['last_interest_credit'] = truncate_number(account['last_interest_credit'], 2)

      _logger.info(f'account id: {account_no}, close date: {close_date}, last interest credit: {last_interest_credit} ')
      
      # calculate balance upto given date
      principal_list = self.env['saving_account.entry'].search([
      ('account_id','=',account['id']), 
      ('ledger','=','principal'),
      ('entry_date','<=',from_date)
      ])
      current_total = 0
      if principal_list:
        for principal in principal_list:
          if principal.entry_type == "deposit":
            current_total = current_total + principal.amount
          elif principal.entry_type == "withdraw":
            current_total = current_total - principal.amount
          elif principal.entry_type == "credit_interest":
            current_total = current_total + principal.amount
      # _logger.info(f'principal current: {current_total}')
      # _logger.info(f'total principal: {total_principal}')
      account['total_principal'] = truncate_number(current_total, 2)

      # find total interest credit
      entries = self.env['saving_account.entry'].search_read([
        ('account_id','=', account['id']),
        ('entry_type','=','credit_interest'), 
        ('ledger','=','principal'),
        ('entry_date','>=',april), 
        ('entry_date','<=',from_date)
      ])
      total_interest_credit = 0
      for entry in entries:
        total_interest_credit += entry['amount']

      account['total_interest_credit'] = truncate_number(total_interest_credit, 2)
    
    if self.read():
      data = { 
        'form': self.read()[0],
        'accounts': accounts
      }
    else:
      data = {
        'form': { 'date_from': from_date },
        'accounts': accounts
      }

    return data

  def action_print_report(self):
    data = self.generate_report()
    return self.env.ref('saving_account.action_term_account_report').report_action(self, data=data)

  def action_send_email(self):
    data = self.generate_report()
    report_id = self.env.ref('saving_account.action_term_account_report')._render(self.ids, data)
    report_b64 = base64.b64encode(report_id[0])
    now = fields.Datetime.today().strftime('%Y%m%d')
    report_name = now + '_term_account.pdf'
    
    attachment = self.env['ir.attachment'].create({
            'name': report_name,
            'type': 'binary',
            'datas': report_b64,
            'store_fname': report_name,
            'mimetype': 'application/x-pdf'
        })

    email_to_send = self.env['email_setup'].search([], limit=1, order='create_date desc').email_to
    email_values = {'email_to': email_to_send}
    print("Sending email to", email_to_send)

    report_template_id = self.env.ref('saving_account.mail_template_term_account')
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
      print("Sending scheduled email...")
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