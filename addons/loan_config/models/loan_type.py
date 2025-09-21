from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class LoanType(models.Model):
    _name = 'loan.type'
    _description = 'Loan Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Tên loại khoản vay', required=True, tracking=True)
    code = fields.Char('Mã loại', required=True, tracking=True)
    
    interest_rate = fields.Float('Lãi suất (%)', required=True, tracking=True)
    term_months = fields.Integer('Kỳ hạn (tháng)', required=True, tracking=True)
    
    min_amount = fields.Float('Số tiền tối thiểu', tracking=True)
    max_amount = fields.Float('Số tiền tối đa', tracking=True)
    
    service_fee_rate = fields.Float('Phí dịch vụ (%)', default=5.0, tracking=True)
    late_fee_rate = fields.Float('Phí trễ hạn (%)', default=2.0, tracking=True)
    
    description = fields.Text('Mô tả')
    active = fields.Boolean('Hoạt động', default=True, tracking=True)
    

    
    @api.constrains('interest_rate', 'term_months', 'min_amount', 'max_amount')
    def _check_values(self):
        for record in self:
            if record.interest_rate < 0:
                raise ValidationError(_('Lãi suất không được âm'))
            
            if record.term_months <= 0:
                raise ValidationError(_('Kỳ hạn phải lớn hơn 0'))
            
            if record.min_amount and record.max_amount and record.min_amount > record.max_amount:
                raise ValidationError(_('Số tiền tối thiểu không được lớn hơn số tiền tối đa'))
    
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.name} ({record.interest_rate}% - {record.term_months} tháng)"
            result.append((record.id, name))
        return result
