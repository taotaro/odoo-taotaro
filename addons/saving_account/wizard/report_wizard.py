
from odoo import models, fields


class XTermIndividualAccountReportWizard(models.TransientModel):
    _name = "x_term_individual_account.report.wizard"
    _description = "Term Individual Account Report Wizard"
    _rec_name = "create_date"

    create_date = fields.Datetime(readonly=True)