from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging
import requests
import json
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class LoanDisbursement(models.Model):
    _name = 'loan.disbursement'
    _description = 'Loan Disbursement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char('Mã giải ngân', required=True, copy=False, readonly=True, 
                      default=lambda self: _('New'))
    
    # Liên kết với server hiện tại
    server_loan_id = fields.Char('Server Loan ID', tracking=True)
    server_investment_id = fields.Char('Server Investment ID', tracking=True)
    
    loan_application_id = fields.Many2one('loan.application', string='Khoản vay', required=True)
    borrower_id = fields.Many2one('res.partner', string='Người vay', related='loan_application_id.borrower_id', store=True)
    
    amount = fields.Float('Số tiền giải ngân', required=True, tracking=True)
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', default=lambda self: self.env.company.currency_id)
    
    disbursement_date = fields.Date('Ngày giải ngân', default=fields.Date.today, tracking=True)
    due_date = fields.Date('Ngày đáo hạn', related='loan_application_id.due_date', store=True)
    
    status = fields.Selection([
        ('draft', 'Nháp'),
        ('pending', 'Chờ phê duyệt'),
        ('approved', 'Đã phê duyệt'),
        ('processing', 'Đang xử lý'),
        ('disbursed', 'Đã giải ngân'),
        ('rejected', 'Từ chối'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái', default='draft', tracking=True)
    
    approval_user_id = fields.Many2one('res.users', string='Người phê duyệt', tracking=True)
    approval_date = fields.Datetime('Ngày phê duyệt', tracking=True)
    
    disbursement_method = fields.Selection([
        ('bank_transfer', 'Chuyển khoản ngân hàng'),
        ('cash', 'Tiền mặt'),
        ('blockchain', 'Blockchain Transfer')
    ], string='Phương thức giải ngân', default='bank_transfer', tracking=True)
    
    bank_account = fields.Char('Tài khoản ngân hàng', tracking=True)
    bank_name = fields.Char('Tên ngân hàng', tracking=True)
    
    # Blockchain fields
    blockchain_tx_id = fields.Char('Blockchain Transaction ID', tracking=True)
    blockchain_status = fields.Selection([
        ('pending', 'Chờ xử lý'),
        ('confirmed', 'Đã xác nhận'),
        ('failed', 'Thất bại')
    ], string='Trạng thái Blockchain', default='pending', tracking=True)
    
    notes = fields.Text('Ghi chú')
    
    # Computed fields
    interest_amount = fields.Float('Tiền lãi', compute='_compute_interest', store=True)
    total_amount = fields.Float('Tổng tiền', compute='_compute_total', store=True)
    
    @api.depends('amount', 'loan_application_id.interest_rate')
    def _compute_interest(self):
        for record in self:
            if record.loan_application_id and record.loan_application_id.interest_rate:
                record.interest_amount = record.amount * (record.loan_application_id.interest_rate / 100)
            else:
                record.interest_amount = 0
    
    @api.depends('amount', 'interest_amount')
    def _compute_total(self):
        for record in self:
            record.total_amount = record.amount + record.interest_amount
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('loan.disbursement') or _('New')
        return super(LoanDisbursement, self).create(vals)
    
    def action_submit_for_approval(self):
        """Gửi yêu cầu phê duyệt"""
        for record in self:
            if record.status == 'draft':
                record.status = 'pending'
                record.message_post(body=_('Yêu cầu phê duyệt đã được gửi'))
    
    def action_approve(self):
        """Phê duyệt giải ngân"""
        for record in self:
            if record.status == 'pending':
                record.status = 'approved'
                record.approval_user_id = self.env.user.id
                record.approval_date = fields.Datetime.now()
                record.message_post(body=_('Đã được phê duyệt bởi %s') % self.env.user.name)
    
    def action_reject(self):
        """Từ chối giải ngân"""
        for record in self:
            if record.status == 'pending':
                record.status = 'rejected'
                record.message_post(body=_('Đã bị từ chối bởi %s') % self.env.user.name)
    
    def action_process_disbursement(self):
        """Xử lý giải ngân - tích hợp với server hiện tại"""
        for record in self:
            if record.status == 'approved':
                record.status = 'processing'
                
                try:
                    # Gọi API server để xử lý giải ngân
                    success = record._process_server_disbursement()
                    if success:
                        record.status = 'disbursed'
                        record.message_post(body=_('Giải ngân thành công qua server'))
                    else:
                        record.status = 'approved'  # Rollback
                        record.message_post(body=_('Giải ngân thất bại qua server'))
                        
                except Exception as e:
                    record.status = 'approved'  # Rollback
                    record.message_post(body=_('Lỗi xử lý giải ngân: %s') % str(e))
                    _logger.error(f"Error processing disbursement: {str(e)}")
    
    def _process_server_disbursement(self):
        """Xử lý giải ngân qua server hiện tại"""
        try:
            # Lấy cấu hình server
            server_config = self.env['loan.config'].get_server_config()
            if not server_config:
                _logger.error("Server configuration not found")
                return False
            
            # Chuẩn bị dữ liệu cho server
            disbursement_data = {
                'disbursement_id': self.name,
                'loan_application_id': self.loan_application_id.name,
                'borrower_id': str(self.borrower_id.id),
                'amount': self.amount,
                'disbursement_date': self.disbursement_date.strftime('%Y-%m-%d'),
                'disbursement_method': self.disbursement_method,
                'bank_account': self.bank_account,
                'bank_name': self.bank_name,
                'notes': self.notes
            }
            
            # Gọi API server
            response = requests.post(
                f"{server_config['api_url']}/loan/disburse",
                json=disbursement_data,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f"Bearer {server_config['api_key']}"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    # Cập nhật thông tin từ server
                    self.server_loan_id = result.get('data', {}).get('loan_id')
                    self.server_investment_id = result.get('data', {}).get('investment_id')
                    self.blockchain_tx_id = result.get('data', {}).get('blockchain_tx_id')
                    return True
                else:
                    _logger.error(f"Server disbursement failed: {result.get('message')}")
                    return False
            else:
                _logger.error(f"Server API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            _logger.error(f"Error processing server disbursement: {str(e)}")
            return False
    
    def action_cancel(self):
        """Hủy giải ngân"""
        for record in self:
            if record.status in ['draft', 'pending']:
                record.status = 'cancelled'
                record.message_post(body=_('Đã hủy bởi %s') % self.env.user.name)
    
    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError(_('Số tiền giải ngân phải lớn hơn 0'))
            
            if record.loan_application_id and record.amount > record.loan_application_id.approved_amount:
                raise ValidationError(_('Số tiền giải ngân không được vượt quá số tiền được phê duyệt'))
    
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.name} - {record.borrower_id.name} - {record.amount:,.0f}"
            result.append((record.id, name))
        return result
    
    # API methods để đồng bộ với server
    def sync_with_server(self):
        """Đồng bộ dữ liệu với server"""
        for record in self:
            try:
                server_config = self.env['loan.config'].get_server_config()
                if not server_config:
                    continue
                
                # Gửi dữ liệu cập nhật lên server
                sync_data = {
                    'disbursement_id': record.name,
                    'status': record.status,
                    'approval_date': record.approval_date.strftime('%Y-%m-%d %H:%M:%S') if record.approval_date else None,
                    'disbursement_date': record.disbursement_date.strftime('%Y-%m-%d') if record.disbursement_date else None,
                    'blockchain_tx_id': record.blockchain_tx_id
                }
                
                response = requests.put(
                    f"{server_config['api_url']}/loan/disbursement/sync",
                    json=sync_data,
                    headers={
                        'Content-Type': 'application/json',
                        'Authorization': f"Bearer {server_config['api_key']}"
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    record.message_post(body=_('Đồng bộ thành công với server'))
                else:
                    record.message_post(body=_('Lỗi đồng bộ với server'))
                    
            except Exception as e:
                _logger.error(f"Error syncing disbursement: {str(e)}")
                record.message_post(body=_('Lỗi đồng bộ: %s') % str(e))
