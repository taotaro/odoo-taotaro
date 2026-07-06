from ..helper import truncate_number, find_last_1april
from odoo import models, fields, api, _
import base64
import logging

_logger = logging.getLogger(__name__)


class TermAccountWizard(models.TransientModel):
  _name = "term_account.report.wizard"
  _description = "Print Term Account Report Wizard"

  account_type = fields.Selection([
    ('all', 'All'),
    ('normal', 'Normal'),
    ('vip', 'VIP')
  ], default='all', string="Account Type")

  date_from = fields.Date(string="Date as of", default=fields.Date.today())
  date_to = fields.Date(string="Date To")
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

  def generate_report(self):
    from_date = ""
    type_account = ""

    if not self.date_from:
      from_date = fields.Date.today()
    else:
      from_date = self.date_from

    _logger.info("Term account report date from: %s", from_date)

    if not self.account_type:
      type_account = 'all'
    else:
      type_account = self.account_type

    april = find_last_1april(from_date)

    accounts = []

    account_401 = self.env['saving_account'].search_read([
      ('account_no', '=', '401')
    ])
    _logger.info("Found account 401: %s", account_401)

    if type_account != 'all':
      accounts = self.env['saving_account'].search_read([
        ('account_type', '=', type_account),
        ('open_date', '<=', from_date),
      ])
    else:
      accounts = self.env['saving_account'].search_read([
        ('open_date', '<=', from_date),
      ])

    for account in accounts:
      close_date = account['close_date']
      account_no = account['account_no']

      _logger.info(
        "Processing account %s, close date: %s",
        account_no,
        close_date
      )

      interest_credit = self.env['saving_account.entry'].search([
        ('account_id', '=', account['id']),
        ('entry_type', '=', 'credit_interest'),
        ('ledger', '=', 'principal'),
        ('entry_date', '<=', from_date)
      ])

      if interest_credit:
        account['last_interest_credit'] = interest_credit[-1].amount
      else:
        account['last_interest_credit'] = 0.0

      _logger.info(
        "Last interest credit for account %s: %s",
        account_no,
        account['last_interest_credit']
      )

      principal_list = self.env['saving_account.entry'].search([
        ('account_id', '=', account['id']),
        ('ledger', '=', 'principal'),
        ('entry_date', '<=', from_date)
      ])

      current_total = 0

      if principal_list:
        for principal in principal_list:
          if principal.entry_type == "deposit":
            current_total += principal.amount
          elif principal.entry_type == "withdraw":
            current_total -= principal.amount
          elif principal.entry_type == "credit_interest":
            current_total += principal.amount

      account['total_principal'] = truncate_number(current_total, 2)

      entries = self.env['saving_account.entry'].search_read([
        ('account_id', '=', account['id']),
        ('entry_type', '=', 'credit_interest'),
        ('ledger', '=', 'principal'),
        ('entry_date', '>=', april),
        ('entry_date', '<=', from_date)
      ])

      total_interest_credit = 0

      for entry in entries:
        total_interest_credit += entry['amount']

      account['total_interest_credit'] = truncate_number(
        total_interest_credit,
        2
      )

    if self.read():
      data = {
        'form': self.read()[0],
        'accounts': accounts
      }
    else:
      data = {
        'form': {
          'date_from': from_date
        },
        'accounts': accounts
      }

    return data

  def action_print_report(self):
    data = self.generate_report()

    return self.env.ref(
      'saving_account.action_term_account_report'
    ).report_action(self, data=data)

  def action_send_email(self):
    self.ensure_one()

    data = self.generate_report()

    report = self.env.ref(
      'saving_account.action_term_account_report'
    )

    pdf_content, report_type = report._render_qweb_pdf(
      report.report_name,
      res_ids=self.ids,
      data=data
    )

    report_b64 = base64.b64encode(pdf_content)

    now = fields.Datetime.today().strftime('%Y%m%d')
    report_name = now + '_term_account.pdf'

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

    _logger.info("Sending term account email to %s", email_to_send)

    report_template_id = self.env.ref(
      'saving_account.mail_template_term_account'
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
      _logger.exception("Term account email send failed: %s", e)

      return {
        'type': 'ir.actions.client',
        'tag': 'display_notification',
        'params': {
          'title': _('Warning'),
          'message': 'Email failed to send: %s' % str(e),
          'sticky': True,
        }
      }

  @api.model
  def _cron_send_email(self):
    try:
      _logger.info("Sending scheduled term account email...")

      wizard = self.create({
        'date_from': fields.Date.today(),
      })

      wizard.action_send_email()

    except Exception as e:
      _logger.exception("Term Account Email Error: %s", e)