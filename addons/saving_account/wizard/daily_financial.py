from odoo import models, fields, api
from markupsafe import escape
import base64

class DailyFinancialWizard(models.TransientModel):
  _name="daily_financial.report.wizard"
  _description="Print Daily Financial Summary Report Wizard"

  date_from=fields.Date(string="Date From", default=fields.Date.today())
  date_to=fields.Date(string="Date To", default=fields.Date.today())
  email_to=fields.Date(string="Email To")

  def generate_report(self):
    accounts = self.env['saving_account'].search_read([
      ('open_date','>=',self.date_from), 
      ('open_date','<=',self.date_to)
    ])

    account_total_principal_amount, account_total_interest_amount = 0, 0
    vip_total_principal_amount, normal_total_principal_amount = 0, 0


    for account in accounts:
      if account['total_principal']:
        account_total_principal_amount += account['total_principal']
        if account['account_type'] == 'normal':
          normal_total_principal_amount += account_total_principal_amount
        if account['account_type'] == 'vip':
          vip_total_principal_amount += account_total_principal_amount

      if account['total_interest']:
        account_total_interest_amount += account['total_interest']

    cash_in_amount, cash_out_amount, total_interest_amount, credit_interest_amount = 0, 0, 0, 0
    cash_in_vip, cash_in_normal, cash_out_vip, cash_out_normal = 0, 0, 0, 0
    cash_in_transaction, cash_out_transaction, total_interest_transaction, credit_interest_transaction = 0, 0, 0, 0
    total_interest_vip, total_interest_normal, credit_interest_vip, credit_interest_normal = 0, 0, 0, 0

    entries = self.env['saving_account.entry'].search_read([('create_date','>=',self.date_from)])
    
    for entry in entries:
      if entry['entry_type'] == 'deposit':
        cash_in_transaction += 1
        cash_in_amount += entry['amount']
        if entry['account_type'] == 'normal':
          cash_in_normal += entry['amount']
        if entry['account_type'] == 'vip':
          cash_in_vip += entry['amount']

      if entry['entry_type'] == 'withdraw':
        cash_out_transaction += 1
        cash_out_amount += entry['amount']
        if entry['account_type'] == 'normal':
          cash_out_normal += entry['amount']
        if entry['account_type'] == 'vip':
          cash_out_vip += entry['amount']

      if entry['entry_type'] == 'interest':
        total_interest_transaction += 1
        total_interest_amount += entry['amount']
        if entry['account_type'] == 'normal':
          total_interest_normal += entry['amount']
        if entry['account_type'] == 'vip':
          total_interest_vip += entry['amount']

      if entry['entry_type'] == 'credit_interest':
        credit_interest_transaction += 1
        credit_interest_amount += entry['amount']
        if entry['account_type'] == 'normal':
          credit_interest_normal += entry['amount']
        if entry['account_type'] == 'vip':
          credit_interest_vip += entry['amount']

    report = {
     "account_transaction": len(accounts),
     "account_amount": account_total_principal_amount,
     "account_vip": vip_total_principal_amount,
     "account_normal": normal_total_principal_amount,
     "cash_in_transaction": cash_in_transaction,
     "cash_in_amount": cash_in_amount,
     "cash_in_vip": cash_in_vip,
     "cash_in_normal": cash_in_normal,
     "cash_out_transaction": cash_out_transaction,
     "cash_out_amount": cash_out_amount,
     "cash_out_vip": cash_out_vip,
     "cash_out_normal": cash_out_normal,
     "total_interest_transaction": total_interest_transaction,
     "total_interest_amount": total_interest_amount, 
     "total_interest_vip": total_interest_vip,
     "total_interest_normal": total_interest_normal,
     "accrued_interest_transaction": len(accounts),
     "accrued_interest_amount": account_total_interest_amount,
     "accrued_interest_vip": vip_total_principal_amount,
     "accrued_interest_normal": normal_total_principal_amount,
     "interest_credit_transaction": credit_interest_transaction,
     "interest_credit_amount": credit_interest_amount,
     "interest_credit_vip": credit_interest_vip,
     "interest_credit_normal": credit_interest_normal
    }

    data = { 
      'form': self.read()[0],
      'report': report
    }

    return data

  def action_print_report(self):
    data = self.generate_report()

    return self.env.ref('saving_account.action_daily_financial_report').report_action(self, data=data)

  def action_send_email(self):
    data = self.generate_report()
    report_id = self.env.ref('saving_account.action_daily_financial_report')._render(self.ids, data)
    report_b64 = base64.b64encode(report_id[0])
    now = fields.Datetime.today().strftime('%Y%m%d')
    report_name = now + '_daily_financial_statement.pdf'
    
    attachment = self.env['ir.attachment'].create({
            'name': report_name,
            'type': 'binary',
            'datas': report_b64,
            'store_fname': report_name,
            'mimetype': 'application/x-pdf'
        })

    report_template_id = self.env.ref('saving_account.mail_template_daily_financial_statement')
    report_template_id.attachment_ids = [(6, 0, [attachment.id])]
    report_template_id.send_mail(self.id, force_send=True)
    return

