from odoo import models, fields, api
import pysftp
import tempfile
import base64
import os

class DailyFinancialWizard(models.TransientModel):
  _name="daily_financial.report.wizard"
  _description="Print Daily Financial Summary Report Wizard"

  date_from=fields.Date(string="Date From")
  date_to=fields.Date(string="Date To")

  def action_print_report(self):
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

    return self.env.ref('saving_account.action_daily_financial_report').report_action(self, data=data)

  def action_sftp_transfer(self):
    sftp_ids = self.env['sftp'].search([])[-1]
    report = self.action_print_report()
    print("reports", report)
    
    for rec in sftp_ids:
      try:
        cnopt = pysftp.CnOpts()
        if rec.sftp_hostkeys:
          cnopt.hostkeys.load(rec.sftp_hostkeys)
        else:
          cnopt.hostkeys = None

        try:
          with pysftp.Connection(
            host=rec.sftp_host, 
            username=rec.sftp_user, 
            password=rec.sftp_password, 
            port=rec.sftp_port,
            cnopts=cnopt,
          ) as sftp:
            temp = tempfile.NamedTemporaryFile(mode='w+t')
            temp.writelines(report)
            temp.seek(0)
            filename = 'Daily_Financial.pdf'
            try:
              sftp.put(temp.name, os.path.join(rec.sftp_path, filename))
            except Exception as e:
              raise Warning('Exception! We couldn\'t back up to the SFTP server..' + str(e))

        finally:
          temp.close()

      except Exception as e:
        raise Warning('Exception! We couldn\'t back up to the SFTP server..' + str(e))


