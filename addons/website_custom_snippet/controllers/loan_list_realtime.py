from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class LoanListRealtimeController(http.Controller):
    @http.route(['/loan_list/realtime', '/loan_list/realtime/'], type='http', auth='public', website=True, csrf=False)
    def loan_list_realtime(self, **kwargs):
        _logger.info("[loan_list_realtime] Rendering HTML partial for loan list")
        loans = request.env['p2p.loan'].sudo().search([], limit=10)
        _logger.info("[loan_list_realtime] Loans fetched: %s", len(loans))
        # Render only the template content without wrapping website layout
        html = request.env['ir.ui.view']._render_template(
            'website_custom_snippet.loan_list_table_partial', {'loans': loans}
        )
        return request.make_response(html, headers=[('Content-Type', 'text/html; charset=utf-8')])

    @http.route(['/loan_list/realtime/data', '/loan_list/realtime/data/'], type='json', auth='public', website=True, csrf=False)
    def loan_list_realtime_json(self, **kwargs):
        """Optional: JSON endpoint for debugging or alternative consumption."""
        _logger.info("[loan_list_realtime_json] Returning JSON for loan list")
        loans = request.env['p2p.loan'].sudo().search([], limit=10)
        return {
            'count': len(loans),
            'items': [
                {
                    'name': l.contractId or l.loan_id or f"Loan-{l.id}",
                    'borrower': l.borrower_id,
                    'amount': l.capital,
                    'interest_rate': l.interest_rate,
                    'term': l.term_months,
                    'start_date': str(l.created_date) if l.created_date else None,
                }
                for l in loans
            ],
        }

    @http.route(['/loan_list/realtime/ping'], type='http', auth='public', website=False, csrf=False)
    def loan_list_realtime_ping(self):
        return http.Response("OK", status=200, content_type='text/plain')
