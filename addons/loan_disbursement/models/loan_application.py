from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class LoanApplication(models.Model):
    _name = 'loan.application'
    _description = 'Loan Application'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char('Mã khoản vay', required=True, copy=False, readonly=True, 
                      default=lambda self: _('New'))
    
    borrower_id = fields.Many2one('res.partner', string='Người vay', required=True, tracking=True)
    loan_type_id = fields.Many2one('loan.type', string='Loại khoản vay', required=True)
    
    requested_amount = fields.Float('Số tiền yêu cầu', required=True, tracking=True)
    approved_amount = fields.Float('Số tiền được phê duyệt', tracking=True)
    
    interest_rate = fields.Float('Lãi suất (%)', related='loan_type_id.interest_rate', store=True)
    term_months = fields.Integer('Kỳ hạn (tháng)', related='loan_type_id.term_months', store=True)
    
    purpose = fields.Text('Mục đích vay', tracking=True)
    
    status = fields.Selection([
        ('draft', 'Nháp'),
        ('submitted', 'Đã nộp'),
        ('under_review', 'Đang xem xét'),
        ('approved', 'Đã phê duyệt'),
        ('rejected', 'Từ chối'),
        ('disbursed', 'Đã giải ngân'),
        ('active', 'Đang hoạt động'),
        ('completed', 'Hoàn thành'),
        ('defaulted', 'Quá hạn')
    ], string='Trạng thái', default='draft', tracking=True)
    
    application_date = fields.Date('Ngày nộp đơn', default=fields.Date.today, tracking=True)
    approval_date = fields.Date('Ngày phê duyệt', tracking=True)
    disbursement_date = fields.Date('Ngày giải ngân', tracking=True)
    due_date = fields.Date('Ngày đáo hạn', compute='_compute_due_date', store=True)
    
    # Blockchain fields
    blockchain_contract_id = fields.Char('Blockchain Contract ID', tracking=True)
    blockchain_status = fields.Selection([
        ('pending', 'Chờ xử lý'),
        ('active', 'Đang hoạt động'),
        ('completed', 'Hoàn thành'),
        ('defaulted', 'Quá hạn')
    ], string='Trạng thái Blockchain', default='pending', tracking=True)
    
    # Computed fields
    monthly_payment = fields.Float('Trả hàng tháng', compute='_compute_monthly_payment', store=True)
    total_interest = fields.Float('Tổng tiền lãi', compute='_compute_total_interest', store=True)
    total_amount = fields.Float('Tổng tiền phải trả', compute='_compute_total_amount', store=True)
    
    # Related fields
    disbursement_ids = fields.One2many('loan.disbursement', 'loan_application_id', string='Giải ngân')
    disbursement_count = fields.Integer('Số lần giải ngân', compute='_compute_disbursement_count')
    
    @api.depends('approved_amount', 'interest_rate', 'term_months')
    def _compute_monthly_payment(self):
        for record in self:
            if record.approved_amount and record.interest_rate and record.term_months:
                # Công thức tính trả góp hàng tháng
                monthly_rate = record.interest_rate / 100 / 12
                if monthly_rate > 0:
                    record.monthly_payment = (record.approved_amount * monthly_rate * (1 + monthly_rate) ** record.term_months) / ((1 + monthly_rate) ** record.term_months - 1)
                else:
                    record.monthly_payment = record.approved_amount / record.term_months
            else:
                record.monthly_payment = 0
    
    @api.depends('monthly_payment', 'term_months', 'approved_amount')
    def _compute_total_interest(self):
        for record in self:
            if record.monthly_payment and record.term_months and record.approved_amount:
                record.total_interest = (record.monthly_payment * record.term_months) - record.approved_amount
            else:
                record.total_interest = 0
    
    @api.depends('approved_amount', 'total_interest')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = record.approved_amount + record.total_interest
    
    @api.depends('application_date', 'term_months')
    def _compute_due_date(self):
        for record in self:
            if record.application_date and record.term_months:
                record.due_date = fields.Date.add(record.application_date, months=record.term_months)
            else:
                record.due_date = False
    
    @api.depends('disbursement_ids')
    def _compute_disbursement_count(self):
        for record in self:
            record.disbursement_count = len(record.disbursement_ids)
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('loan.application') or _('New')
        return super(LoanApplication, self).create(vals)
    
    def action_submit(self):
        """Nộp đơn vay"""
        for record in self:
            if record.status == 'draft':
                record.status = 'submitted'
                record.message_post(body=_('Đơn vay đã được nộp'))
    
    def action_approve(self):
        """Phê duyệt khoản vay"""
        for record in self:
            if record.status in ['submitted', 'under_review']:
                record.status = 'approved'
                record.approval_date = fields.Date.today()
                record.message_post(body=_('Khoản vay đã được phê duyệt'))
    
    def action_reject(self):
        """Từ chối khoản vay"""
        for record in self:
            if record.status in ['submitted', 'under_review']:
                record.status = 'rejected'
                record.message_post(body=_('Khoản vay đã bị từ chối'))
    
    def action_disburse(self):
        """Tạo yêu cầu giải ngân"""
        for record in self:
            if record.status == 'approved':
                # Tạo disbursement record
                disbursement_vals = {
                    'loan_application_id': record.id,
                    'amount': record.approved_amount,
                    'disbursement_date': fields.Date.today(),
                }
                self.env['loan.disbursement'].create(disbursement_vals)
                record.message_post(body=_('Đã tạo yêu cầu giải ngân'))
    
    @api.constrains('requested_amount', 'approved_amount')
    def _check_amounts(self):
        for record in self:
            if record.requested_amount <= 0:
                raise ValidationError(_('Số tiền yêu cầu phải lớn hơn 0'))
            
            if record.approved_amount and record.approved_amount > record.requested_amount:
                raise ValidationError(_('Số tiền phê duyệt không được vượt quá số tiền yêu cầu'))
    
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.name} - {record.borrower_id.name} - {record.requested_amount:,.0f}"
            result.append((record.id, name))
        return result
