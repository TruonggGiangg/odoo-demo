from odoo import http
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)

class WebsiteLoanController(http.Controller):
    @http.route(['/loans'], type='http', auth='public', website=True)
    def loan_list(self, **kwargs):
        # Lấy dữ liệu từ model đúng với _name và sequence
        loans = request.env['p2p.loan'].sudo().search([], limit=10)
        _logger.info(f"[DEBUG] Loans found: {loans}")
        for loan in loans:
            _logger.info(f"[DEBUG] Loan: {loan.contractId} - {loan.capital} - {loan.status}")
        if not loans:
            _logger.warning("[DEBUG] Không có khoản vay nào được tìm thấy!")
        return request.render('website_custom_snippet.loan_list_template', {
            'loans': loans
        })