from odoo import http
from odoo.http import request
import json
import logging
import requests

_logger = logging.getLogger(__name__)

class LoanDisbursementWebController(http.Controller):

    @http.route('/loan/disbursement/web', type='http', auth='user', website=True)
    def loan_disbursement_dashboard(self, **kwargs):
        try:
            disbursements = request.env['loan.disbursement'].search([])

            stats = {
                'total_loans': len(disbursements),
                'pending_disbursements': len(disbursements.filtered(lambda d: d.status != 'disbursed')),
                'disbursed_count': len(disbursements.filtered(lambda d: d.status == 'disbursed')),
                'total_amount': sum(disbursements.mapped('amount'))
            }
            return request.render('loan_disbursement.dashboard_template', {
                'disbursements': disbursements,
                'stats': stats,
                'user': request.env.user,
            })
        except Exception as e:
            _logger.error(f'Error getting disbursement dashboard: {str(e)}')
            return request.render('loan_disbursement.error_template', {
                'error': str(e),
            })

    @http.route('/loan/disbursement/sync', type='json', auth='user', methods=['POST'], csrf=False)
    def loan_disbursement_sync(self, **kwargs):
        """Đồng bộ dữ liệu giải ngân từ Server (pull từ /loan/odoo/export/loans)"""
        try:
            server_config = request.env['loan.config'].get_server_config()
            response = requests.get(
                f"{server_config['api_url']}/loan/odoo/export/loans",
                headers={'x-auth': server_config['api_key']},
                timeout=5
            )

            if response.status_code != 200:
                return {'success': False, 'message': f'Lỗi đồng bộ giải ngân: {response.status_code}'}

            body = response.json() or {}
            result = body.get('data') or {}
            server_loans = result.get('loans') or []

            created_count = 0
            updated_count = 0

            for loan in server_loans:
                contract_id = loan.get('id')
                if not contract_id:
                    continue
                existing = request.env['loan.disbursement'].search([
                    ('server_loan_id', '=', contract_id)
                ], limit=1)

                borrower_data = (loan.get('borrower') or {})
                borrower = None
                if borrower_data:
                    partner_model = request.env['res.partner'].sudo()
                    # Tìm theo ref trước
                    borrower = partner_model.search([('ref', '=', str(borrower_data.get('id')))], limit=1)
                    # Fallback theo phone
                    if not borrower and borrower_data.get('phone'):
                        borrower = partner_model.search([('phone', '=', borrower_data.get('phone'))], limit=1)
                    # Nếu vẫn chưa có, tạo mới partner tối thiểu
                    if not borrower:
                        vals_partner = {
                            'name': borrower_data.get('name') or borrower_data.get('phone') or 'Unknown',
                            'ref': str(borrower_data.get('id') or ''),
                        }
                        if borrower_data.get('phone'):
                            vals_partner['phone'] = borrower_data.get('phone')
                        borrower = partner_model.create(vals_partner)

                # Tìm hoặc tạo loan.application liên quan
                app_model = request.env['loan.application'].sudo()
                application = app_model.search([
                    '|', ('blockchain_contract_id', '=', contract_id),
                         ('name', '=', contract_id)
                ], limit=1)

                if not application:
                    # Yêu cầu loan_type_id NOT NULL: đảm bảo có loan.type
                    loan_type_model = request.env['loan.type'].sudo()
                    loan_type = loan_type_model.search([], limit=1)
                    if not loan_type:
                        # Tạo mặc định nếu chưa có
                        default_vals = {
                            'name': 'Default',
                            'code': 'DEFAULT',
                            'term_months': (loan.get('term_months') or 6),
                            'interest_rate': (loan.get('interest_rate') or 0.0),
                            'service_fee_rate': 0.0,
                            'late_fee_rate': 0.0,
                            'min_amount': 0.0,
                            'max_amount': 0.0,
                        }
                        try:
                            loan_type = loan_type_model.create(default_vals)
                        except Exception:
                            # Nếu tạo thất bại do thiếu field, chỉ tạo tối thiểu name/code
                            loan_type = loan_type_model.create({'name': 'Default', 'code': 'DEFAULT'})

                    app_vals = {
                        'name': contract_id,
                        'borrower_id': borrower.id if borrower else False,
                        'requested_amount': loan.get('amount') or 0.0,
                        'approved_amount': loan.get('amount') or 0.0,
                        'interest_rate': loan.get('interest_rate') or 0.0,
                        'term_months': loan.get('term_months') or 0,
                        'purpose': '',
                        'status': self._map_p2p_status_to_application(loan.get('status')),
                        'application_date': loan.get('created_date') or False,
                        'blockchain_contract_id': contract_id,
                        'loan_type_id': loan_type.id,
                    }
                    application = app_model.create(app_vals)

                vals = {
                    'server_loan_id': contract_id,
                    'borrower_id': borrower.id if borrower else False,
                    'loan_application_id': application.id,
                    'amount': loan.get('amount') or 0.0,
                    'disbursement_date': loan.get('created_date') or False,
                    'status': self._map_server_status_to_disbursement(loan.get('status')),
                }
                if existing:
                    existing.write(vals)
                    updated_count += 1
                else:
                    request.env['loan.disbursement'].create(vals)
                    created_count += 1

            return {
                'success': True,
                'message': f'Đồng bộ thành công {created_count} mới, {updated_count} cập nhật',
                'created_count': created_count,
                'updated_count': updated_count
            }
        except Exception as e:
            _logger.error(f'Error syncing disbursement: {str(e)}')
            return {'success': False, 'message': str(e)}

    @http.route('/loan/disbursement/process', type='json', auth='user', methods=['POST'], csrf=False)
    def process_loan_actions(self, **kwargs):
        """API xử lý giải ngân"""
        try:
            action = kwargs.get('action')
            loan_ids = kwargs.get('loan_ids', [])
            reason = kwargs.get('reason', '')

            if not action or not loan_ids:
                return {'success': False, 'error': 'action and loan_ids are required'}

            server_config = request.env['loan.config'].get_server_config()

            # Chỉ hỗ trợ giải ngân (disburse) lên server
            if action == 'disburse':
                processed = 0
                for loan_id in loan_ids:
                    disb = request.env['loan.disbursement'].search([('server_loan_id', '=', loan_id)], limit=1)
                    if not disb:
                        continue
                    payload = {
                        'disbursement_id': f"{loan_id}-{int(http.request.httprequest.timestamp())}",
                        'loan_application_id': loan_id,
                        'borrower_id': disb.borrower_id.id if disb.borrower_id else None,
                        'amount': disb.amount or 0.0,
                        'disbursement_date': str(disb.disbursement_date or ''),
                        'disbursement_method': disb.disbursement_method or 'bank_transfer',
                        'bank_account': disb.bank_account or '',
                        'bank_name': disb.bank_name or '',
                        'notes': disb.notes or ''
                    }
                    resp = requests.post(
                        f"{server_config['api_url']}/loan/disburse",
                        json=payload,
                        headers={'x-auth': server_config['api_key']},
                        timeout=6
                    )
                    if resp.status_code == 200:
                        disb.status = 'disbursed'
                        processed += 1
                    else:
                        _logger.error(f"Disburse API error {resp.status_code}: {resp.text}")

                if processed > 0:
                    return {
                        'success': True,
                        'message': f'Giải ngân thành công {processed} khoản vay'
                    }
                return {'success': False, 'message': 'Không giải ngân được khoản vay nào'}

            # Hủy/Reject: cập nhật cục bộ
            if action in ('reject', 'cancel'):
                for loan_id in loan_ids:
                    disbursement = request.env['loan.disbursement'].search([('server_loan_id', '=', loan_id)], limit=1)
                    if disbursement:
                        disbursement.status = 'rejected'
                        disbursement.notes = reason
                return {'success': True, 'message': f'Đã hủy {len(loan_ids)} khoản vay'}

            return {'success': False, 'message': f'Action không hỗ trợ: {action}'}
        except Exception as e:
            _logger.error(f"error processing loan actions: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _find_borrower(self, borrower_data):
        phone = (borrower_data or {}).get('phone')
        return request.env['res.partner'].search([('phone', '=', phone)], limit=1)

    def _map_p2p_status_to_application(self, p2p_status: str) -> str:
        status = (p2p_status or '').lower()
        return {
            'waiting': 'submitted',
            'success': 'approved',
            'clean': 'disbursed',
            'fail': 'rejected'
        }.get(status, 'submitted')

    def _map_server_status_to_disbursement(self, server_status: str) -> str:
        """Map trạng thái từ server sang trạng thái hợp lệ của loan.disbursement"""
        status = (server_status or '').lower()
        mapping = {
            'waiting': 'pending',
            'success': 'approved',
            'clean': 'disbursed',
            'fail': 'rejected',
        }
        return mapping.get(status, 'pending')

    @http.route('/loan/disbursement/import_p2p', type='json', auth='user', methods=['POST'], csrf=False)
    def import_from_p2p(self, **kwargs):
        """Kết nối dữ liệu từ p2p_bridge sang loan_disbursement"""
        try:
            p2p_loans = request.env['p2p.loan'].sudo().search([])
            app_model = request.env['loan.application'].sudo()
            disb_model = request.env['loan.disbursement'].sudo()
            partner_model = request.env['res.partner'].sudo()

            created_apps = updated_apps = created_disbs = 0

            for loan in p2p_loans:
                contract_id = loan.contractId or loan.loan_id
                if not contract_id:
                    continue

                borrower = None
                if loan.borrower_id:
                    borrower = partner_model.search([('ref', '=', loan.borrower_id)], limit=1)
                    if not borrower:
                        borrower = partner_model.create({
                            'name': loan.borrower_id,
                            'ref': loan.borrower_id,
                            'company_type': 'person',
                        })

                application = app_model.search([
                    '|', ('blockchain_contract_id', '=', contract_id),
                         ('name', '=', contract_id)
                ], limit=1)

                app_vals = {
                    'name': contract_id,
                    'borrower_id': borrower.id if borrower else False,
                    'requested_amount': loan.capital or 0.0,
                    'approved_amount': loan.capital or 0.0,
                    'interest_rate': loan.interest_rate or 0.0,
                    'term_months': loan.term_months or 0,
                    'purpose': loan.willing or loan.description or '',
                    'status': self._map_p2p_status_to_application(loan.status),
                    'application_date': (loan.created_at and str(loan.created_at)) or False,
                    'blockchain_contract_id': contract_id,
                }
                if application:
                    application.write(app_vals)
                    updated_apps += 1
                else:
                    application = app_model.create(app_vals)
                    created_apps += 1

                if loan.status == 'clean':
                    existing_disb = disb_model.search([('server_loan_id', '=', contract_id)], limit=1)
                    if not existing_disb:
                        disb_model.create({
                            'server_loan_id': contract_id,
                            'loan_application_id': application.id,
                            'borrower_id': borrower.id if borrower else False,
                            'amount': loan.capital or 0.0,
                            'disbursement_date': (loan.created_at and str(loan.created_at.date())
                                                  if hasattr(loan.created_at, 'date')
                                                  else loan.created_date) or False,
                            'status': 'disbursed',
                            'disbursement_method': 'bank_transfer',
                        })
                        created_disbs += 1

            return {
                'success': True,
                'message': 'Imported from p2p successfully',
                'created_applications': created_apps,
                'updated_applications': updated_apps,
                'created_disbursements': created_disbs,
            }
        except Exception as e:
            _logger.error(f'Error importing from p2p: {str(e)}')
            return {'success': False, 'message': str(e)}

    # --- Legacy routes (http, wrap json result) ---
    @http.route('/loan-disbursement/sync', type='http', auth='user', methods=['POST'], csrf=False)
    def legacy_sync_route(self, **kwargs):
        try:
            result = self.loan_disbursement_sync(**kwargs) or {}
            # đảm bảo luôn có 2 key
            result.setdefault('success', True)
            result.setdefault('message', 'Sync completed')
            return request.make_response(
                json.dumps(result),
                headers={'Content-Type': 'application/json'}
            )
        except Exception as e:
            _logger.error(f'Legacy sync error: {str(e)}')
            return request.make_response(
                json.dumps({'success': False, 'message': str(e)}),
                headers={'Content-Type': 'application/json'}
            )

    @http.route('/loan-disbursement/import', type='http', auth='user', methods=['POST'], csrf=False)
    def legacy_import_route(self, **kwargs):
        try:
            result = self.import_from_p2p(**kwargs) or {}
            result.setdefault('success', True)
            result.setdefault('message', 'Import completed')
            return request.make_response(
                json.dumps(result),
                headers={'Content-Type': 'application/json'}
            )
        except Exception as e:
            _logger.error(f'Legacy import error: {str(e)}')
            return request.make_response(
                json.dumps({'success': False, 'message': str(e)}),
                headers={'Content-Type': 'application/json'}
            )
