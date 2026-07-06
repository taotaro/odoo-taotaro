from odoo import models, fields, api, _
from odoo.exceptions import UserError
from ..helper import truncate_number, find_date_from

from collections import defaultdict
import base64
import logging

_logger = logging.getLogger(__name__)


class TermIndividualAccountWizard(models.TransientModel):
  _name = "term_individual_account.report.wizard"
  _description = "Print Term Individual Account Report Wizard"

  account_id = fields.Many2one('saving_account', string='Account')
  date_from = fields.Date(string="Date From")
  date_to = fields.Date(string="Date To", default=fields.Date.today())
  email_to = fields.Char(string="Email To")

  @api.model
  def default_get(self, fields_list):
    res = super().default_get(fields_list)

    setup = self.env['email_setup'].search(
      [],
      limit=1,
      order='create_date desc'
    )

    if setup:
      res['email_to'] = setup.email_to

    return res

  def generate_report(self, account_id=False):
    from_date = self.date_from or find_date_from()
    to_date = self.date_to or fields.Date.today()
    account_id = account_id or self.account_id

    if not account_id:
      raise UserError(_("Please select an account."))

    all_entries = self.env['saving_account.entry'].search_read([
      ('account_id', '=', account_id.id),
      ('ledger', '=', 'principal'),
    ])

    initial_balance = 0
    entries = []
    total_values = defaultdict(int)

    for entry in all_entries:
      if from_date <= entry['entry_date'] <= to_date:
        entries.append(entry)
      elif entry['entry_date'] < from_date:
        if entry['entry_type'] == 'withdraw':
          initial_balance -= entry['amount']
        else:
          initial_balance += entry['amount']

    initial_entry = {
      "entry_type": "initial",
      "amount": 0,
      "balance": truncate_number(initial_balance, 2),
      "create_date": from_date,
      "entry_date": from_date,
      "ref_no": "BF",
    }

    entries.insert(0, initial_entry)

    running_balance = initial_balance

    for entry in entries:
      if entry['entry_type'] in {'withdraw', 'deposit', 'credit_interest'}:
        amount = entry['amount']

        if entry['entry_type'] == 'withdraw':
          running_balance -= amount
        else:
          running_balance += amount

        total_values[entry['entry_type']] += amount

        entry['amount'] = truncate_number(amount, 2)
        entry['balance'] = truncate_number(running_balance, 2)

    account = self.env['saving_account'].search_read([
      ('id', '=', account_id.id)
    ])

    form_data = {
      'date_from': from_date,
      'date_to': to_date,
      'account_id': [account_id.id, account_id.name],
    }

    data = {
      'form': form_data,
      'entry': entries,
      'account_no': account[0]['account_no_signed'] if account else account_id.account_no,
      'total_withdraw': truncate_number(total_values['withdraw'], 2),
      'total_deposit': truncate_number(total_values['deposit'], 2),
      'total_interest': truncate_number(total_values['credit_interest'], 2),
    }

    return data

  def action_print_report(self):
    data = self.generate_report()

    return self.env.ref(
      'saving_account.action_term_individual_account_report'
    ).report_action(self, data=data)

  def action_send_email(self):
    self.ensure_one()

    if not self.account_id:
      raise UserError(_("Please select an account before sending email."))

    data = self.generate_report()

    report = self.env.ref(
      'saving_account.action_term_individual_account_report'
    )

    pdf_content, report_type = report._render_qweb_pdf(
      report.report_name,
      res_ids=self.ids,
      data=data
    )

    report_b64 = base64.b64encode(pdf_content)

    now = fields.Datetime.today().strftime('%Y%m%d')
    report_name = now + '_' + str(self.account_id.account_no) + '_term_individual_account.pdf'

    attachment = self.env['ir.attachment'].create({
      'name': report_name,
      'type': 'binary',
      'datas': report_b64,
      'mimetype': 'application/pdf',
    })

    email_to_send = self.email_to or self.env['email_setup'].search(
      [],
      limit=1,
      order='create_date desc'
    ).email_to

    if not email_to_send:
      return {
        'type': 'ir.actions.client',
        'tag': 'display_notification',
        'params': {
          'title': _('Warning'),
          'message': 'No email recipient configured.',
          'sticky': True,
        }
      }

    email_values = {
      'email_to': email_to_send,
      'attachment_ids': [(4, attachment.id)],
    }

    _logger.info(
      "Sending term individual account email for account %s to %s",
      self.account_id.account_no,
      email_to_send
    )

    report_template_id = self.env.ref(
      'saving_account.mail_template_term_individual_account'
    )

    try:
      report_template_id.send_mail(
        self.id,
        email_values=email_values,
        force_send=True
      )

      return {
        'type': 'ir.actions.client',
        'tag': 'display_notification',
        'params': {
          'title': _('Success'),
          'message': 'Email sent!',
          'sticky': True,
        }
      }

    except Exception as e:
      _logger.exception(
        "Term individual account email send failed: %s",
        e
      )

      return {
        'type': 'ir.actions.client',
        'tag': 'display_notification',
        'params': {
          'title': _('Warning'),
          'message': 'Email failed to send: %s' % str(e),
          'sticky': True,
        }
      }

  def get_all_reports(self, account_ids):
    reports = []

    for account_id in account_ids:
      data = self.generate_report(account_id=account_id)
      reports.append(data)

    return reports

  def get_all_pdfs(self, reports, report_id_ref):
    pdfs = []

    for report_data in reports:
      try:
        pdf_content, report_type = report_id_ref._render_qweb_pdf(
          report_id_ref.report_name,
          res_ids=self.ids,
          data=report_data
        )

        report_b64 = base64.b64encode(pdf_content)
        pdfs.append(report_b64)

      except Exception as e:
        _logger.exception(
          "Failed to generate individual account PDF: %s",
          e
        )
        continue

    return pdfs

  def action_send_all_emails(self):
    self.ensure_one()

    _logger.info("Start sending all term individual account emails")

    account_ids = self.env['saving_account'].search([])

    email_to_send = self.email_to or self.env['email_setup'].search(
      [],
      limit=1,
      order='create_date desc'
    ).email_to

    if not email_to_send:
      raise UserError(_("No email recipient configured."))

    sent_count = 0
    failed_count = 0

    for account in account_ids:
      try:
        wizard = self.create({
          'account_id': account.id,
          'date_from': self.date_from or find_date_from(),
          'date_to': self.date_to or fields.Date.today(),
          'email_to': email_to_send,
        })

        wizard.action_send_email()
        sent_count += 1

        _logger.info(
          "Sent term individual account email for account %s",
          account.account_no
        )

      except Exception as e:
        failed_count += 1

        _logger.exception(
          "Failed to send term individual account email for account %s: %s",
          account.account_no,
          e
        )

        continue

    return {
      'type': 'ir.actions.client',
      'tag': 'display_notification',
      'params': {
        'title': _('Completed'),
        'message': 'Emails sent: %s, failed: %s' % (sent_count, failed_count),
        'sticky': True,
      }
    }

  @api.model
  def _cron_send_email(self):
    try:
      _logger.info("Sending scheduled term individual account emails...")

      setup = self.env['email_setup'].search(
        [],
        limit=1,
        order='create_date desc'
      )

      wizard = self.create({
        'date_from': find_date_from(),
        'date_to': fields.Date.today(),
        'email_to': setup.email_to if setup else False,
      })

      wizard.action_send_all_emails()

    except Exception as e:
      _logger.exception(
        "Scheduled term individual account email failed: %s",
        e
      )