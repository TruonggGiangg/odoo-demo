from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json

class LoanConfiguration(models.Model):
    _name = 'loan.config'
    _description = 'Loan Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Tên cấu hình', required=True, tracking=True)
    active = fields.Boolean('Hoạt động', default=True, tracking=True)
    is_active = fields.Boolean('Hoạt động', related='active', store=True)
    
    # General settings
    default_currency_id = fields.Many2one('res.currency', string='Tiền tệ mặc định', 
                                         default=lambda self: self.env.company.currency_id, tracking=True)
    min_loan_amount = fields.Float('Số tiền vay tối thiểu', default=1000000, tracking=True)
    max_loan_amount = fields.Float('Số tiền vay tối đa', default=1000000000, tracking=True)
    
    # Interest rate settings
    base_interest_rate = fields.Float('Lãi suất cơ bản (%)', default=12.0, tracking=True)
    max_interest_rate = fields.Float('Lãi suất tối đa (%)', default=36.0, tracking=True)
    
    # Fee settings
    service_fee_rate = fields.Float('Phí dịch vụ (%)', default=5.0, tracking=True)
    late_fee_rate = fields.Float('Phí trễ hạn (%)', default=2.0, tracking=True)
    processing_fee = fields.Float('Phí xử lý hồ sơ', default=50000, tracking=True)
    
    # Server integration settings
    server_enabled = fields.Boolean('Kích hoạt tích hợp Server', default=True, tracking=True)
    server_api_url = fields.Char('Server API URL', default='http://192.168.1.6:3000', tracking=True)
    server_api_key = fields.Char('Server API Key', tracking=True)
    server_sync_interval = fields.Integer('Chu kỳ đồng bộ (phút)', default=30, tracking=True)
    

    
    # Notification settings
    email_notifications = fields.Boolean('Thông báo email', default=True, tracking=True)
    sms_notifications = fields.Boolean('Thông báo SMS', default=False, tracking=True)
    
    # Advanced settings
    auto_approval_limit = fields.Float('Giới hạn tự động phê duyệt', default=5000000, tracking=True)
    max_concurrent_loans = fields.Integer('Số khoản vay đồng thời tối đa', default=3, tracking=True)
    factor_constant = fields.Float('Hệ số tính toán', default=1.0, tracking=True)
    
    # Hệ số cấu hình
    risk_factor = fields.Float('Hệ số rủi ro', default=1.2, tracking=True, help='Hệ số điều chỉnh lãi suất theo mức độ rủi ro')
    credit_score_factor = fields.Float('Hệ số điểm tín dụng', default=0.8, tracking=True, help='Hệ số giảm lãi suất cho khách hàng có điểm tín dụng tốt')
    loan_term_factor = fields.Float('Hệ số kỳ hạn vay', default=1.1, tracking=True, help='Hệ số tăng lãi suất theo kỳ hạn vay')
    collateral_factor = fields.Float('Hệ số tài sản đảm bảo', default=0.9, tracking=True, help='Hệ số giảm lãi suất khi có tài sản đảm bảo')
    early_repayment_discount = fields.Float('Giảm giá trả sớm (%)', default=2.0, tracking=True, help='Phần trăm giảm lãi suất khi trả sớm')
    late_payment_penalty = fields.Float('Phạt trả chậm (%)', default=5.0, tracking=True, help='Phần trăm phạt khi trả chậm')
    
    @api.constrains('min_loan_amount', 'max_loan_amount', 'base_interest_rate', 'max_interest_rate')
    def _check_values(self):
        for record in self:
            if record.min_loan_amount <= 0:
                raise ValidationError(_('Số tiền vay tối thiểu phải lớn hơn 0'))
            
            if record.max_loan_amount <= record.min_loan_amount:
                raise ValidationError(_('Số tiền vay tối đa phải lớn hơn số tiền tối thiểu'))
            
            if record.base_interest_rate < 0:
                raise ValidationError(_('Lãi suất cơ bản không được âm'))
            
            if record.max_interest_rate < record.base_interest_rate:
                raise ValidationError(_('Lãi suất tối đa phải lớn hơn lãi suất cơ bản'))
    
    def get_server_config(self):
        """Lấy cấu hình server"""
        config = self.search([('active', '=', True)], limit=1)
        if config and config.server_enabled:
            return {
                'api_url': config.server_api_url,
                'api_key': config.server_api_key,
                'sync_interval': config.server_sync_interval
            }
        return None
    

    
    def get_loan_limits(self):
        """Lấy giới hạn khoản vay"""
        config = self.search([('active', '=', True)], limit=1)
        if config:
            return {
                'min_amount': config.min_loan_amount,
                'max_amount': config.max_loan_amount,
                'auto_approval_limit': config.auto_approval_limit,
                'max_concurrent_loans': config.max_concurrent_loans
            }
        return None
    
    def get_fee_rates(self):
        """Lấy tỷ lệ phí"""
        config = self.search([('active', '=', True)], limit=1)
        if config:
            return {
                'service_fee_rate': config.service_fee_rate,
                'late_fee_rate': config.late_fee_rate,
                'processing_fee': config.processing_fee
            }
        return None
    
    def calculate_interest_rate(self, base_amount, credit_score=None, loan_term=None, has_collateral=False, risk_level='normal'):
        """Tính toán lãi suất dựa trên các hệ số"""
        config = self.search([('active', '=', True)], limit=1)
        if not config:
            return config.base_interest_rate
        
        # Lãi suất cơ bản
        interest_rate = config.base_interest_rate
        
        # Điều chỉnh theo điểm tín dụng
        if credit_score and credit_score >= 700:
            interest_rate *= config.credit_score_factor
        
        # Điều chỉnh theo kỳ hạn vay
        if loan_term and loan_term > 12:
            interest_rate *= config.loan_term_factor
        
        # Điều chỉnh theo tài sản đảm bảo
        if has_collateral:
            interest_rate *= config.collateral_factor
        
        # Điều chỉnh theo mức độ rủi ro
        if risk_level == 'high':
            interest_rate *= config.risk_factor
        elif risk_level == 'low':
            interest_rate *= (1 / config.risk_factor)
        
        # Đảm bảo không vượt quá lãi suất tối đa
        return min(interest_rate, config.max_interest_rate)
    
    def get_all_factors(self):
        """Lấy tất cả hệ số cấu hình"""
        config = self.search([('active', '=', True)], limit=1)
        if config:
            return {
                'risk_factor': config.risk_factor,
                'credit_score_factor': config.credit_score_factor,
                'loan_term_factor': config.loan_term_factor,
                'collateral_factor': config.collateral_factor,
                'early_repayment_discount': config.early_repayment_discount,
                'late_payment_penalty': config.late_payment_penalty,
                'factor_constant': config.factor_constant
            }
        return None
    
    def test_server_connection(self):
        """Test kết nối với server"""
        for record in self:
            try:
                import requests
                
                if not record.server_api_url or not record.server_api_key:
                    raise ValidationError(_('Vui lòng cấu hình Server API URL và API Key'))
                
                # Test API connection - sử dụng endpoint đúng
                test_url = f"{record.server_api_url}/api/config/health"
                if not test_url.startswith('http'):
                    test_url = f"http://{record.server_api_url}/api/config/health"
                
                response = requests.get(
                    test_url,
                    headers={
                        'Content-Type': 'application/json'
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Thành công',
                            'message': 'Kết nối server thành công!',
                            'type': 'success',
                        }
                    }
                else:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Lỗi',
                            'message': f'Lỗi kết nối server: {response.status_code}',
                            'type': 'danger',
                        }
                    }
                    
            except requests.exceptions.ConnectionError as e:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Lỗi kết nối',
                        'message': 'Không thể kết nối đến server. Vui lòng kiểm tra URL và đảm bảo server đang chạy. ' + str(e),
                        'type': 'danger',
                    }
                }
            except Exception as e:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Lỗi',
                        'message': f'Lỗi test kết nối: {str(e)}',
                        'type': 'danger',
                    }
                }
    
    def sync_config_to_server(self):
        """Đồng bộ cấu hình lên server"""
        for record in self:
            try:
                import requests
                
                if not record.server_api_url or not record.server_api_key:
                    raise ValidationError(_('Vui lòng cấu hình Server API URL và API Key'))
                
                # Chuẩn bị dữ liệu cấu hình
                config_data = {
                    'external_id': str(record.id),
                    'name': record.name,
                    'min_loan_amount': record.min_loan_amount,
                    'max_loan_amount': record.max_loan_amount,
                    'base_interest_rate': record.base_interest_rate,
                    'max_interest_rate': record.max_interest_rate,
                    'service_fee_rate': record.service_fee_rate,
                    'late_fee_rate': record.late_fee_rate,
                    'processing_fee': record.processing_fee,
                    'auto_approval_limit': record.auto_approval_limit,
                    'max_concurrent_loans': record.max_concurrent_loans,
                    'risk_factor': record.risk_factor,
                    'credit_score_factor': record.credit_score_factor,
                    'loan_term_factor': record.loan_term_factor,
                    'collateral_factor': record.collateral_factor,
                    'early_repayment_discount': record.early_repayment_discount,
                    'late_payment_penalty': record.late_payment_penalty,
                    'factor_constant': record.factor_constant
                }
                
                # Gửi cấu hình lên server - sử dụng endpoint đơn giản hơn
                sync_url = f"{record.server_api_url}/api/config/sync"
                if not sync_url.startswith('http'):
                    sync_url = f"http://{record.server_api_url}/api/config/sync"
                
                response = requests.post(
                    sync_url,
                    json=config_data,
                    headers={
                        'Authorization': f"Bearer {record.server_api_key}",
                        'Content-Type': 'application/json'
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Thành công',
                            'message': 'Đồng bộ cấu hình thành công!',
                            'type': 'success',
                        }
                    }
                else:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Lỗi',
                            'message': f'Lỗi đồng bộ cấu hình: {response.status_code}',
                            'type': 'danger',
                        }
                    }
                    
            except requests.exceptions.ConnectionError:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Lỗi kết nối',
                        'message': 'Không thể kết nối đến server. Vui lòng kiểm tra URL và đảm bảo server đang chạy.',
                        'type': 'danger',
                    }
                }
            except Exception as e:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Lỗi',
                        'message': f'Lỗi đồng bộ cấu hình: {str(e)}',
                        'type': 'danger',
                    }
                }
