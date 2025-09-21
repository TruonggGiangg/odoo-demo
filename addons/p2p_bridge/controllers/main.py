import json
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class P2PCustomController(http.Controller):

    @http.route('/p2p', type='http', auth='user', website=True)
    def index(self):
        """P2P Home Page - Redirect to dashboard"""
        return request.redirect('/p2p/dashboard')

    @http.route('/p2p/dashboard', type='http', auth='user', website=True)
    def dashboard(self):
        """Custom P2P Dashboard"""
        try:
            # Get data from models
            wallets = request.env['p2p.wallet'].search([])
            loans = request.env['p2p.loan'].search([])
            borrowers = request.env['p2p.borrower'].search([])
            investors = request.env['p2p.investor'].search([])
            
            # Calculate statistics
            total_wallets = len(wallets)
            total_loans = len(loans)
            total_borrowers = len(borrowers)
            total_investors = len(investors)
            
            active_loans = len(loans.filtered(lambda l: l.status == 'waiting'))
            total_capital = sum(loans.mapped('capital'))
            
            values = {
                'total_wallets': total_wallets,
                'total_loans': total_loans,
                'total_borrowers': total_borrowers,
                'total_investors': total_investors,
                'active_loans': active_loans,
                'total_capital': total_capital,
                'wallets': wallets,
                'loans': loans[:10],  # Latest 10 loans
                'borrowers': borrowers[:10],  # Latest 10 borrowers
                'investors': investors[:10],  # Latest 10 investors
            }
            
            return request.render('p2p_bridge.custom_dashboard', values)
            
        except Exception as e:
            _logger.error(f"Error in dashboard: {e}")
            return request.render('p2p_bridge.error_page', {'error': str(e)})

    @http.route('/p2p/borrowers', type='http', auth='user', website=True)
    def borrowers(self):
        """Custom Borrowers Management"""
        try:
            borrowers = request.env['p2p.borrower'].search([])
            return request.render('p2p_bridge.custom_borrowers', {'borrowers': borrowers})
        except Exception as e:
            _logger.error(f"Error in borrowers: {e}")
            return request.render('p2p_bridge.error_page', {'error': str(e)})

    @http.route('/p2p/investors', type='http', auth='user', website=True)
    def investors(self):
        """Custom Investors Management"""
        try:
            investors = request.env['p2p.investor'].search([])
            return request.render('p2p_bridge.custom_investors', {'investors': investors})
        except Exception as e:
            _logger.error(f"Error in investors: {e}")
            return request.render('p2p_bridge.error_page', {'error': str(e)})

    @http.route('/p2p/loans', type='http', auth='user', website=True)
    def loans(self):
        """Custom Loans Management"""
        try:
            loans = request.env['p2p.loan'].search([])
            return request.render('p2p_bridge.custom_loans', {'loans': loans})
        except Exception as e:
            _logger.error(f"Error in loans: {e}")
            return request.render('p2p_bridge.error_page', {'error': str(e)})

    @http.route('/p2p/api/borrower/<int:borrower_id>/activate', type='json', auth='user')
    def activate_borrower(self, borrower_id):
        """API to activate borrower"""
        try:
            borrower = request.env['p2p.borrower'].browse(borrower_id)
            if borrower.exists():
                borrower.action_activate()
                return {'success': True, 'message': 'Borrower activated successfully'}
            return {'success': False, 'message': 'Borrower not found'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @http.route('/p2p/api/borrower/<int:borrower_id>/deactivate', type='json', auth='user')
    def deactivate_borrower(self, borrower_id):
        """API to deactivate borrower"""
        try:
            borrower = request.env['p2p.borrower'].browse(borrower_id)
            if borrower.exists():
                borrower.action_deactivate()
                return {'success': True, 'message': 'Borrower deactivated successfully'}
            return {'success': False, 'message': 'Borrower not found'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @http.route('/p2p/api/investor/<int:investor_id>/activate', type='json', auth='user')
    def activate_investor(self, investor_id):
        """API to activate investor"""
        try:
            investor = request.env['p2p.investor'].browse(investor_id)
            if investor.exists():
                investor.action_activate()
                return {'success': True, 'message': 'Investor activated successfully'}
            return {'success': False, 'message': 'Investor not found'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @http.route('/p2p/api/investor/<int:investor_id>/deactivate', type='json', auth='user')
    def deactivate_investor(self, investor_id):
        """API to deactivate investor"""
        try:
            investor = request.env['p2p.investor'].browse(investor_id)
            if investor.exists():
                investor.action_deactivate()
                return {'success': True, 'message': 'Investor deactivated successfully'}
            return {'success': False, 'message': 'Investor not found'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
