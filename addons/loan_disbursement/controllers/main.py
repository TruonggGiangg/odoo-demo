from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class LoanDisbursementController(http.Controller):
    
    @http.route('/api/loan/disbursements', type='json', auth='user', methods=['GET'])
    def get_disbursements(self, **kwargs):
        """API lấy danh sách giải ngân"""
        try:
            domain = []
            
            # Filter theo status
            if kwargs.get('status'):
                domain.append(('status', '=', kwargs['status']))
            
            # Filter theo borrower
            if kwargs.get('borrower_id'):
                domain.append(('borrower_id', '=', int(kwargs['borrower_id'])))
            
            # Limit và offset
            limit = kwargs.get('limit', 500)
            offset = kwargs.get('offset', 0)
            
            disbursements = request.env['loan.disbursement'].search_read(
                domain,
                fields=['name', 'borrower_id', 'amount', 'disbursement_date', 'status', 
                       'disbursement_method', 'blockchain_status', 'blockchain_tx_id'],
                limit=limit,
                offset=offset,
                order='create_date desc'
            )
            
            return {
                'success': True,
                'data': disbursements,
                'total': len(disbursements)
            }
            
        except Exception as e:
            _logger.error(f"Error getting disbursements: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/api/loan/disbursements/<int:disbursement_id>', type='json', auth='user', methods=['GET'])
    def get_disbursement_detail(self, disbursement_id, **kwargs):
        """API lấy chi tiết giải ngân"""
        try:
            disbursement = request.env['loan.disbursement'].browse(disbursement_id)
            
            if not disbursement.exists():
                return {
                    'success': False,
                    'error': 'Disbursement not found'
                }
            
            data = {
                'id': disbursement.id,
                'name': disbursement.name,
                'borrower_id': disbursement.borrower_id.id,
                'borrower_name': disbursement.borrower_id.name,
                'amount': disbursement.amount,
                'interest_amount': disbursement.interest_amount,
                'total_amount': disbursement.total_amount,
                'disbursement_date': disbursement.disbursement_date.strftime('%Y-%m-%d') if disbursement.disbursement_date else None,
                'due_date': disbursement.due_date.strftime('%Y-%m-%d') if disbursement.due_date else None,
                'status': disbursement.status,
                'disbursement_method': disbursement.disbursement_method,
                'bank_name': disbursement.bank_name,
                'bank_account': disbursement.bank_account,
                'blockchain_tx_id': disbursement.blockchain_tx_id,
                'blockchain_status': disbursement.blockchain_status,
                'notes': disbursement.notes,
                'loan_application': {
                    'id': disbursement.loan_application_id.id,
                    'name': disbursement.loan_application_id.name,
                    'interest_rate': disbursement.loan_application_id.interest_rate,
                    'term_months': disbursement.loan_application_id.term_months
                }
            }
            
            return {
                'success': True,
                'data': data
            }
            
        except Exception as e:
            _logger.error(f"Error getting disbursement detail: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/api/loan/disbursements/approve', type='json', auth='user', methods=['POST'])
    def approve_disbursement(self, **kwargs):
        """API phê duyệt giải ngân"""
        try:
            disbursement_id = kwargs.get('disbursement_id')
            if not disbursement_id:
                return {
                    'success': False,
                    'error': 'disbursement_id is required'
                }
            
            disbursement = request.env['loan.disbursement'].browse(int(disbursement_id))
            
            if not disbursement.exists():
                return {
                    'success': False,
                    'error': 'Disbursement not found'
                }
            
            if disbursement.status != 'pending':
                return {
                    'success': False,
                    'error': 'Disbursement is not in pending status'
                }
            
            # Phê duyệt giải ngân
            disbursement.action_approve()
            
            return {
                'success': True,
                'message': 'Disbursement approved successfully',
                'data': {
                    'id': disbursement.id,
                    'status': disbursement.status,
                    'approval_date': disbursement.approval_date.strftime('%Y-%m-%d %H:%M:%S') if disbursement.approval_date else None
                }
            }
            
        except Exception as e:
            _logger.error(f"Error approving disbursement: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/api/loan/disbursements/reject', type='json', auth='user', methods=['POST'])
    def reject_disbursement(self, **kwargs):
        """API từ chối giải ngân"""
        try:
            disbursement_id = kwargs.get('disbursement_id')
            reason = kwargs.get('reason', '')
            
            if not disbursement_id:
                return {
                    'success': False,
                    'error': 'disbursement_id is required'
                }
            
            disbursement = request.env['loan.disbursement'].browse(int(disbursement_id))
            
            if not disbursement.exists():
                return {
                    'success': False,
                    'error': 'Disbursement not found'
                }
            
            if disbursement.status != 'pending':
                return {
                    'success': False,
                    'error': 'Disbursement is not in pending status'
                }
            
            # Từ chối giải ngân
            disbursement.action_reject()
            
            if reason:
                disbursement.message_post(body=f"Lý do từ chối: {reason}")
            
            return {
                'success': True,
                'message': 'Disbursement rejected successfully',
                'data': {
                    'id': disbursement.id,
                    'status': disbursement.status
                }
            }
            
        except Exception as e:
            _logger.error(f"Error rejecting disbursement: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/api/loan/disbursements/process', type='json', auth='user', methods=['POST'])
    def process_disbursement(self, **kwargs):
        """API xử lý giải ngân"""
        try:
            disbursement_id = kwargs.get('disbursement_id')
            
            if not disbursement_id:
                return {
                    'success': False,
                    'error': 'disbursement_id is required'
                }
            
            disbursement = request.env['loan.disbursement'].browse(int(disbursement_id))
            
            if not disbursement.exists():
                return {
                    'success': False,
                    'error': 'Disbursement not found'
                }
            
            if disbursement.status != 'approved':
                return {
                    'success': False,
                    'error': 'Disbursement is not approved'
                }
            
            # Xử lý giải ngân
            disbursement.action_process_disbursement()
            
            return {
                'success': True,
                'message': 'Disbursement processed successfully',
                'data': {
                    'id': disbursement.id,
                    'status': disbursement.status,
                    'blockchain_tx_id': disbursement.blockchain_tx_id,
                    'blockchain_status': disbursement.blockchain_status
                }
            }
            
        except Exception as e:
            _logger.error(f"Error processing disbursement: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/api/loan/config', type='json', auth='user', methods=['GET'])
    def get_loan_config(self, **kwargs):
        """API lấy cấu hình khoản vay"""
        try:
            config = request.env['loan.config'].search([('active', '=', True)], limit=1)
            
            if not config:
                return {
                    'success': False,
                    'error': 'No active configuration found'
                }
            
            data = {
                'min_loan_amount': config.min_loan_amount,
                'max_loan_amount': config.max_loan_amount,
                'base_interest_rate': config.base_interest_rate,
                'max_interest_rate': config.max_interest_rate,
                'service_fee_rate': config.service_fee_rate,
                'late_fee_rate': config.late_fee_rate,
                'processing_fee': config.processing_fee,
                'blockchain_enabled': config.blockchain_enabled,
                'kyc_required': config.kyc_required,
                'auto_approval_limit': config.auto_approval_limit,
                'max_concurrent_loans': config.max_concurrent_loans
            }
            
            return {
                'success': True,
                'data': data
            }
            
        except Exception as e:
            _logger.error(f"Error getting loan config: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
