from odoo import models, fields, api

class DailyFinancialWizard(models.TransientModel):
  _name="daily_financial.report.wizard"
  _description="Print Daily Financial Summary Report Wizard"

  date=fields.Date(string="Date", default=fields.Date.today())

  def action_print_report(self):
    data = { 
      'form': self.read()[0],
    }
    print("test...", data)
    return self.env.ref('saving_account.action_daily_financial_report').report_action(self, data=data)