# -*- coding: utf-8 -*-
{
    'name': "Saving Account",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "TaoTaro Group Ltd",
    'website': "http://tech.taotaro.app",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
      'security/ir.model.access.csv',
      'data/sequence_data.xml',
      'data/cron.xml',
      'data/saving_account_demo.xml',
      'data/principal_demo.xml',
      'data/interest_rate_demo.xml',
      # 'data/interest_schedule_demo.xml',
      'wizard/term_account_view.xml',
      'wizard/term_individual_account_view.xml',
      'wizard/daily_financial_view.xml',
      'views/saving_account_view.xml',
      'views/principal_view.xml',
      'views/rate_view.xml',
      # 'views/schedule_view.xml',
      'views/menu.xml',
      'report/term_account_template.xml',
      'report/term_individual_account_template.xml',
      'report/daily_financial_template.xml',
      'report/report.xml'
    ],

    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],

    'application': True,
    'sequence': -100,

     'license': 'LGPL-3',
}
