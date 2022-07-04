from odoo import models, fields, api

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
    for account in accounts:
      account_total_principal_amount += account.total_principal
      account_total_interest_amount += account.total_interest

    cash_in_amount, cash_out_amount, total_interest_amount, credit_interest_amount = 0, 0, 0, 0
    cash_in_transaction, cash_out_transaction, total_interest_transaction, credit_interest_transaction = 0, 0, 0, 0
    entries = self.env['saving_account.entry'].search_read([('create_date','>=',self.date_from)])
    for entry in entries:
      if entry['entry_type'] == 'deposit':
        cash_in_transaction += 1
        cash_in_amount += entry['amount']
      elif entry['entry_type'] == 'withdraw':
        cash_out_transaction += 1
        cash_out_amount += entry['amount']
      elif entry['entry_type'] == 'interest':
        total_interest_transaction += 1
        total_interest_amount += entry['amount']
      elif entry['entry_type'] == 'credit_interest':
        credit_interest_transaction += 1
        credit_interest_amount += entry['amount']

    report = {
     "account_transaction": len(accounts),
     "account_amount": account_total_principal_amount,
     "cash_in_transaction": cash_in_transaction,
     "cash_in_amount": cash_in_amount,
     "cash_out_transaction": cash_out_transaction,
     "cash_out_amount": cash_out_amount,
     "total_interest_transaction": total_interest_transaction,
     "total_interest_amount": total_interest_amount, 
     "accrued_interest_transaction": len(accounts),
     "accrued_interest_amount": account_total_interest_amount,
     "interest_credit_transaction": credit_interest_transaction,
     "interest_credit_amount": credit_interest_amount,
    }

    data = { 
      'form': self.read()[0],
      'report': report
    }

    return self.env.ref('saving_account.action_daily_financial_report').report_action(self, data=data)