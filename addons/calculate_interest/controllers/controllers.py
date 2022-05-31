# -*- coding: utf-8 -*-
from odoo import http


class CalculateInterestController(http.Controller):
    @http.route('/calculate_interest', auth='public')
    def index(self, **kw):
        return "Hello, world"

    @http.route('/calculate_interest/objects', auth='public')
    def list(self, **kw):
        return http.request.render('calculate_interest.listing', {
            'root': '/calculate_interest',
            'objects': http.request.env['calculate_interest'].search([]),
        })

    @http.route('/calculate_interest/objects/<model("calculate_interest"):obj>', auth='public')
    def object(self, obj, **kw):
        return http.request.render('calculate_interest.object', {
            'object': obj
        })
