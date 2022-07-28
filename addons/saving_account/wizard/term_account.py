from odoo import models, fields, api
import base64

class TermAccountWizard(models.TransientModel):
  _name="term_account.report.wizard"
  _description="Print Term Account Report Wizard"

  date_from=fields.Date(string="Date From")
  date_to=fields.Date(string="Date To")
  email_to=fields.Char(string="Email To")

  def generate_report(self):
    accounts = self.env['saving_account'].search_read([('open_date','>=',self.date_from), ('open_date','<=',self.date_to)])
    data = { 
      'form': self.read()[0],
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

    email_values = {'email_to': self.email_to}

    report_template_id = self.env.ref('saving_account.mail_template_term_account')
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