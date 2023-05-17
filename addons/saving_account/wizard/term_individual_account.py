from datetime import datetime
from odoo import models, fields, api, _
import base64
from ..helper import find_last_1april, find_last_1oct, truncate_number, find_date_from
from collections import defaultdict
import time
# import threading
import logging
_logger = logging.getLogger(__name__)

class TermIndividualAccountWizard(models.TransientModel):
  _name="term_individual_account.report.wizard"
  _description="Print Term Individual Account Report Wizard"

  account_id = fields.Many2one('saving_account', string='Account')
  # date_from=fields.Date(string="Date From", _compute='_compute_date_from', compute_sudo=True)
  date_from=fields.Date(string="Date From")
  date_to=fields.Date(string="Date To", default=fields.Date.today())
  email_to=fields.Char(string="Email To", _compute="_get_default_email")

  # find the financial term start date (if date is after april and before sept, then start date is april, else october)
  # @api.onchange('date_from')
  # def _compute_date_from(self):
  #   for rec in self:
  #     from_date = fields.Date.today()
  #     april = find_last_1april(from_date)
  #     oct = find_last_1oct(from_date)
  #     sept = datetime(year=april.year, month=9, day=30).date()
  #     mar = datetime(year=oct.year+1, month=3, day=31).date()
      
  #     ### CHATGPT- rephrased to remove if else statement
  #     if april <= from_date and from_date <= sept:
  #       rec.date_from = april
  #     elif oct <= from_date and from_date <= mar:
  #       rec.date_from = oct
      
  # set email address
  @api.onchange('email_to')
  def _get_default_email(self):
    email_to_send = self.env['email_setup'].search([], limit=1, order='create_date desc').email_to
    for rec in self:
      rec.email_to = email_to_send

 


  def generate_report(self, account_id=False):
    from_date = self.date_from or find_date_from()
    to_date = self.date_to or fields.Date.today()
    account_id = account_id or self.account_id

    
    # for acc in account_id:
        # find all entries for the account
    all_entries = self.env['saving_account.entry'].search_read([
        ('account_id','=', account_id.id), 
        ('ledger','=','principal'), 
    ])

    # partition entries into those within the specified date and those before it
    initial_balance = 0
    entries = []
    total_values = defaultdict(int)

    # get initial balance and entries before specified date
    for entry in all_entries:
      if from_date <= entry['entry_date'] <= to_date:
        entries.append(entry)
      elif entry['entry_date'] < from_date:
        # initial_entries.append(entry)
        if entry['entry_type'] == 'withdraw':
          initial_balance -= entry['amount']
        else:
          initial_balance += entry['amount']

    # entries = [entry for entry in all_entries if from_date <= entry['entry_date'] <= to_date]
    # initial_entries = [entry for entry in all_entries if entry['entry_date'] < from_date]

    # initial_balance = sum(entry['amount'] if entry['entry_type'] != 'withdraw' else -entry['amount'] for entry in initial_entries)

    initial_entry = {
        "entry_type": "initial",
        "amount": 0,
        "balance": initial_balance,
        "create_date": from_date,
        "ref_no": "BF"
    }
    entries.insert(0, initial_entry)

    total_values = defaultdict(int)
    for entry in entries:
        if entry['entry_type'] in {'withdraw', 'deposit', 'credit_interest'}:
            amount = entry['amount']
            if entry['entry_type'] == 'withdraw':
                initial_balance -= amount
            else:
                initial_balance += amount
            total_values[entry['entry_type']] += amount
            entry['amount'] = truncate_number(amount, 2)
            entry['balance'] = truncate_number(initial_balance, 2)

    account = self.env['saving_account'].search_read([('id','=',account_id.id)])
    form_data = self.read()[0] if self.read() else {
        'date_from': from_date,
        'date_to': to_date,
        'account_id': [account_id.id, account_id.name]
    }

    data = {
        'form': form_data,
        'entry': entries,
        'account_no': account[0]['account_no_signed'],
        'total_withdraw': truncate_number(total_values['withdraw'], 2),
        'total_deposit': truncate_number(total_values['deposit'], 2),
        'total_interest': truncate_number(total_values['credit_interest'], 2),
    }

    return data



    # # if from date not specified
    # if not self.date_from or self.date_from == False:
    #   from_date = find_date_from()
    # else:
    #   from_date = self.date_from

    # # if to date not specified
    # if not self.date_to:
    #   to_date = fields.Date.today()
    # else:
    #   to_date = self.date_to

    # # if account id not specified
    # if not account_id:
    #   account_id = self.account_id 

    # for acc in account_id:
    #   # find entries within the specified date
    #   entries = self.env['saving_account.entry'].search_read([
    #     ('account_id','=', acc.id), 
    #     ('ledger','=','principal'), 
    #     ('entry_date','>=',from_date), 
    #     ('entry_date','<=',to_date)
    #   ])
    #   # find account information
    #   account = self.env['saving_account'].search_read([('id','=',acc.id)])
      
    #   # find entries from before the specified time to calculate initial balance
    #   initial_entries = self.env['saving_account.entry'].search_read([
    #     ('account_id','=', acc.id),
    #     ('ledger','=','principal'), 
    #     ('entry_date','<',from_date)
    #   ])

    #   initial_balance = 0
    #   for entry in initial_entries:
    #     if entry['ledger'] == 'principal':
    #       if entry['entry_type'] == 'withdraw':
    #         initial_balance -= entry['amount']
    #       else:
    #         initial_balance += entry['amount']

    #   # declare first entry with initial balance
    #   initial_entry = {
    #     "entry_type": "initial",
    #     "amount": 0,
    #     "balance": initial_balance,
    #     "create_date": from_date,
    #     "ref_no": "BF"
    #     }
    #   entries.insert(0, initial_entry)

    #   #initialize total values
    #   total_withdraw, total_deposit, total_interest = 0, 0, 0

    #   # arrange entries according to type
    #   for entry in entries:
    #     if entry['entry_type'] == 'withdraw':
    #       initial_balance -= entry['amount']
    #       total_withdraw += entry['amount']
    #     elif entry['entry_type'] == 'deposit':
    #       initial_balance += entry['amount']
    #       total_deposit += entry['amount']
    #     elif entry['entry_type'] == 'credit_interest':
    #       initial_balance += entry['amount']
    #       total_interest += entry['amount']
    #     else:
    #       continue
    #     # truncate for display
    #     entry['amount'] = truncate_number(entry['amount'], 2)
    #     entry['balance'] = truncate_number(initial_balance, 2)

    #   data = []
    #   # if values are already set in self
    #   if self.read():
    #     data = { 
    #       'form': self.read()[0],
    #       'entry': entries,
    #       'account_no': account[0]['account_no_signed'],
    #       'total_withdraw': truncate_number(total_withdraw, 2),
    #       'total_deposit': truncate_number(total_deposit, 2),
    #       'total_interest': truncate_number(total_interest, 2)
    #     }
    #   else:
    #     data = {
    #       'form': {
    #         'date_from': from_date,
    #         'date_to': to_date,
    #         'account_id': [acc.id, acc.name]
    #       },
    #       'entry': entries,
    #       'account_no': account[0]['account_no_signed'],
    #       'total_withdraw': truncate_number(total_withdraw, 2),
    #       'total_deposit': truncate_number(total_deposit, 2),
    #       'total_interest': truncate_number(total_interest, 2)
    #     }
        
      # return data

  def action_print_report(self):
    data = self.generate_report()
    return self.env.ref('saving_account.action_term_individual_account_report').report_action(self, data=data)

  def action_send_email(self):
    data = self.generate_report()
    try:
      ### CHATGPT used 'render_qweb_pdf' method to generate PDF report directly (could make it faster)
      report_id = self.env.ref('saving_account.action_term_individual_account_report')._render(self.ids, data=data)
    except Exception as e:
      print(e)
    report_b64 = base64.b64encode(report_id[0])
    now = fields.Datetime.today().strftime('%Y%m%d')
    report_name = now + '_' + str(self.account_id.account_no) + '_term_individual_account.pdf'
    
    # create email attachment
    attachment = self.env['ir.attachment'].create({
            'name': report_name,
            'type': 'binary',
            'datas': report_b64,
            'store_fname': report_name,
            'mimetype': 'application/x-pdf'
        })

    # find email to send to
    ### CHATGPT use sudo method to search for email setup (ensure user has necessary access rights to read email setup record)
    email_to_send = self.env['email_setup'].search([], limit=1, order='create_date desc').email_to
    email_values = {'email_to': email_to_send}
    print("Sending email to", email_to_send)

    # send email template
    report_template_id = self.env.ref('saving_account.mail_template_term_individual_account')
    report_template_id.attachment_ids = [(6, 0, [attachment.id])]
    try:
      # send confirmation message when successful
      ### CHATGPT used 'with_context' method to add data dictionary to email template's context (easier to access data)
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

  # get all accounts under self, generate report for each account, create email template and send out emails
  # def action_send_all_emails(self):
  #   account_ids = self.env['saving_account'].search([])
  #   report_id_ref = self.env.ref('saving_account.action_term_individual_account_report')
  #   email_to_send = self.env['email_setup'].search([], limit=1, order='create_date desc').email_to
  #   report_template_id = self.env.ref('saving_account.mail_template_term_individual_account')

  #   time_limit = 800
  #   start_time = time.time()
  #   current_time = time.time()
  #   remaining_account_ids = account_ids

  #   while len(remaining_account_ids) > 0:
  #       loop_start_time = time.time()
  #       for account_id in remaining_account_ids:
  #           current_time = time.time()
  #           if current_time - loop_start_time >= time_limit:
  #               break

  #           data = self.generate_report(account_id=account_id)
  #           try:
  #               report_id = report_id_ref._render(self.ids, data=data)
  #               report_b64 = base64.b64encode(report_id[0])
  #               now = fields.Datetime.today().strftime('%Y%m%d')
  #               report_name = now + '_' + str(account_id.account_no) + '_term_individual_account.pdf'

  #               # create email attachment
  #               attachment = self.env['ir.attachment'].create({
  #                   'name': report_name,
  #                   'type': 'binary',
  #                   'datas': report_b64,
  #                   'store_fname': report_name,
  #                   'mimetype': 'application/x-pdf'
  #               })
  #               print("Attachment made:", report_name)
  #               email_values = {'email_to': email_to_send}
  #               print("Sending email to:", email_to_send)
  #               report_template_id.attachment_ids = [(6, 0, [attachment.id])]
  #               try:
  #                   report_template_id.send_mail(self.id, email_values=email_values, force_send=True)
  #                   print("Sent email to:", email_to_send)
  #               except:
  #                   # send warning message when failed
  #                   print("Email failed to send")
  #           except Exception as e:
  #               print(e)
  #               continue

  #       remaining_account_ids = account_ids[len(remaining_account_ids):]  # Update the remaining account IDs

  #       current_time = time.time()
  #       if current_time - start_time >= time_limit:
  #           break

  #   return

  def action_send_all_emails(self):
    # _logger.debug('this is a test message')
    _logger.info('this is a test message')
    account_ids = self.env['saving_account'].search([])
    report_id_ref = self.env.ref('saving_account.action_term_individual_account_report')
    email_to_send = self.env['email_setup'].search([], limit=1, order='create_date desc').email_to
   

    for account_id in account_ids:
        print("account id here", account_id)
        data = self.generate_report(account_id=account_id)
        try:
            report_id = report_id_ref._render(self.ids, data=data)
        except Exception as e:
            print(e)
            continue

        report_b64 = base64.b64encode(report_id[0])
        now = fields.Datetime.today().strftime('%Y%m%d')
        report_name = now + '_' + str(account_id.account_no) + '_term_individual_account.pdf'

        # create email attachment
        attachment = self.env['ir.attachment'].create({
            'name': report_name,
            'type': 'binary',
            'datas': report_b64,
            'store_fname': report_name,
            'mimetype': 'application/x-pdf'
        })
        print("attachment made", report_name)
        email_values = {'email_to': email_to_send}
        print("Sending email to", email_to_send)
        report_template_id = self.env.ref('saving_account.mail_template_term_individual_account')
        report_template_id.attachment_ids = [(6, 0, [attachment.id])]
        try:
            report_template_id.send_mail(self.id, email_values=email_values, force_send=True)
            print("Sent email to", email_to_send)
        except:
            # send warning message when fail
            print("Email failed to send")


  @api.model
  def _cron_send_email(self):
    try:
      print("Sending scheduled email...")
      self.action_send_all_emails()
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


  # def thread_test(self):
  #   test = threading.Thread(target=self.action_send_all_emails)
  #   test.start()
  #   return True
