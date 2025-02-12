from odoo import models, fields, api, _
import base64
from ..helper import truncate_number, find_last_1april

class DailyFinancialWizard(models.TransientModel):
  _name="daily_financial.report.wizard"
  _description="Print Daily Financial Summary Report Wizard"

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
    if not self.date_from:
      from_date = fields.Date.today()
    else:
      from_date = self.date_from
    
    # get record of total accounts
    accounts = self.env['saving_account'].search_read([
      ('open_date','<=',from_date), 
      ('close_date','=',False)
    ])

    # initialize
    account_total_principal_amount, vip_total_principal_amount, normal_total_principal_amount = 0, 0, 0
    cash_in_amount, cash_out_amount, total_interest_amount, credit_interest_amount = 0, 0, 0, 0
    cash_in_vip, cash_in_normal, cash_out_vip, cash_out_normal = 0, 0, 0, 0
    cash_in_transaction, cash_out_transaction, total_interest_transaction, credit_interest_transaction = 0, 0, 0, 0
    total_interest_vip, total_interest_normal, credit_interest_vip, credit_interest_normal = 0, 0, 0, 0
    accrued_interest_transaction, accrued_interest_amount, accrued_interest_vip, accrued_interest_normal = 0, 0, 0, 0

    #get record of entries
    entries = self.env['saving_account.entry'].search_read([('entry_date','=',from_date)])
    
    for entry in entries:
      # cash in fields
      if entry['entry_type'] == 'deposit':
        cash_in_transaction += 1
        cash_in_amount += entry['amount']
        if entry['account_type'] == 'normal':
          cash_in_normal += entry['amount']
        if entry['account_type'] == 'vip':
          cash_in_vip += entry['amount']

      # cash out fields
      if entry['entry_type'] == 'withdraw':
        cash_out_transaction += 1
        cash_out_amount -= entry['amount']
        if entry['account_type'] == 'normal':
          cash_out_normal -= entry['amount']
        if entry['account_type'] == 'vip':
          cash_out_vip -= entry['amount']

      # total interest fields
      if entry['entry_type'] == 'interest':
        total_interest_transaction += 1
        total_interest_amount += entry['amount']
        if entry['account_type'] == 'normal':
          total_interest_normal += entry['amount']
        if entry['account_type'] == 'vip':
          total_interest_vip += entry['amount']
      
      # credit interest fields
      if entry['entry_type'] == 'credit_interest' and entry['ledger'] == 'principal':
        credit_interest_transaction += 1
        credit_interest_amount += entry['amount']
        if entry['account_type'] == 'normal':
          credit_interest_normal += entry['amount']
        elif entry['account_type'] == 'vip':
          credit_interest_vip += entry['amount']
        else:
          print("account skip", entry)
    
    # accrued interest fields
    for account in accounts:
      if account['total_interest']:
        accrued_interest_transaction += 1
        accrued_interest_amount += account['total_interest']
        if account['account_type'] == 'normal':
          accrued_interest_normal += account['total_interest']
        if account['account_type'] == 'vip':
          accrued_interest_vip += account['total_interest']

    # calculate total accounts
    normal_total_principal_amount = cash_out_normal - cash_in_normal
    vip_total_principal_amount = cash_out_vip - cash_in_vip
    account_total_principal_amount = normal_total_principal_amount + vip_total_principal_amount

    # initialize total interest credit and total amount
    total_interest_credit_amount, total_interest_credit_vip, total_interest_credit_normal = 0, 0, 0
    total_amount_amount, total_amount_vip, total_amount_normal = 0, 0, 0

    #find last 1 april
    april = find_last_1april(from_date)

    # find interest credit entries and calculate total
    interest_entries = self.env['saving_account.entry'].search_read([
      ('entry_type','=','credit_interest'),
      ('ledger','=','principal'),
      ('entry_date','>=',april), 
      ('entry_date','<=',from_date)
    ])

    for entry in interest_entries:
      if entry['account_type'] == 'normal':
        if entry['entry_type'] != 'withdraw':
          total_interest_credit_normal += entry['amount']
        else:
          total_interest_credit_normal -= entry['amount']
      if entry['account_type'] == 'vip':
        if entry['entry_type'] != 'withdraw':
          total_interest_credit_vip += entry['amount']
        else:
          total_interest_credit_vip -= entry['amount']

    # find principal entries and calculate total
    total_entries = self.env['saving_account.entry'].search_read([
      ('ledger','=','principal'),
      ('entry_date','<=',from_date)
    ])

    for entry in total_entries:
      if entry['account_type'] == 'normal':
        if entry['entry_type'] != 'withdraw':
          total_amount_normal += entry['amount']
        else:
          total_amount_normal -= entry['amount']
      if entry['account_type'] == 'vip':
        if entry['entry_type'] != 'withdraw':
          total_amount_vip += entry['amount']
        else:
          total_amount_vip -= entry['amount']

    total_interest_credit_amount = total_interest_credit_vip + total_interest_credit_normal
    total_amount_amount = total_amount_vip + total_amount_normal

    report = {
     "account_transaction": len(accounts),
     "account_amount": truncate_number(account_total_principal_amount, 2),
     "account_vip": truncate_number(vip_total_principal_amount, 2),
     "account_normal": truncate_number(normal_total_principal_amount, 2),
     "cash_in_transaction": cash_in_transaction,
     "cash_in_amount": truncate_number(cash_in_amount, 2),
     "cash_in_vip": truncate_number(cash_in_vip, 2),
     "cash_in_normal": truncate_number(cash_in_normal, 2),
     "cash_out_transaction": cash_out_transaction,
     "cash_out_amount": truncate_number(cash_out_amount, 2),
     "cash_out_vip": truncate_number(cash_out_vip, 2),
     "cash_out_normal": truncate_number(cash_out_normal, 2),
     "total_interest_transaction": total_interest_transaction,
     "total_interest_amount": truncate_number(total_interest_amount, 2), 
     "total_interest_vip": truncate_number(total_interest_vip, 2),
     "total_interest_normal": truncate_number(total_interest_normal, 2),
     "accrued_interest_transaction": accrued_interest_transaction,
     "accrued_interest_amount": truncate_number(accrued_interest_amount, 2),
     "accrued_interest_vip": truncate_number(accrued_interest_vip, 2),
     "accrued_interest_normal": truncate_number(accrued_interest_normal, 2),
     "interest_credit_transaction": credit_interest_transaction,
     "interest_credit_amount": truncate_number(credit_interest_amount, 2),
     "interest_credit_vip": truncate_number(credit_interest_vip, 2),
     "interest_credit_normal": truncate_number(credit_interest_normal, 2),
     "total_interest_credit_amount": truncate_number(total_interest_credit_amount, 2),
     "total_interest_credit_vip": truncate_number(total_interest_credit_vip, 2),
     "total_interest_credit_normal": truncate_number(total_interest_credit_normal, 2),
     "total_amount_amount": truncate_number(total_amount_amount, 2),
     "total_amount_vip": truncate_number(total_amount_vip, 2),
     "total_amount_normal": truncate_number(total_amount_normal, 2)
    }

    if self.read():
      data = { 
        'form': self.read()[0],
        'report': report
      }
    else:
      data = {
        'form': { 'date_from': from_date },
        'report': report
      }
    

    return data

  def action_print_report(self):
    data = self.generate_report()

    return self.env.ref('saving_account.action_daily_financial_report').report_action(self, data=data)

  def action_send_email(self):
    # generate report template with filename
    data = self.generate_report()
    report_id = self.env.ref('saving_account.action_daily_financial_report')._render(self.ids, data=data)
    report_b64 = base64.b64encode(report_id[0])
    now = fields.Datetime.today().strftime('%Y%m%d')
    report_name = now + '_daily_financial_statement.pdf'
    
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
    report_template_id = self.env.ref('saving_account.mail_template_daily_financial_statement')
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
    # send scheduled email
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
            'sticky': False,
          }
      }
    
