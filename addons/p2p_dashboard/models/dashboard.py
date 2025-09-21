# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
import json
import logging

logger = logging.getLogger(__name__)

class P2PDashboard(models.Model):
    _name = 'p2p.dashboard'
    _description = 'Bảng điều khiển P2P Lending'
    _rec_name = 'name'

    name = fields.Char('Tên', required=True, default="Bảng điều khiển P2P")
    date_from = fields.Date('Từ ngày', default=lambda self: (date.today().replace(day=1) - timedelta(days=180)))
    date_to = fields.Date('Đến ngày', default=fields.Date.today)
    company_id = fields.Many2one('res.company', string='Công ty', default=lambda self: self.env.company)
    
    # ----- Loan Stats -----
    total_loans = fields.Integer('Tổng số khoản vay', compute='_compute_loan_stats')
    total_loans_empty = fields.Char(string='', default="(Chưa có dữ liệu)")
    total_loan_amount = fields.Float('Tổng giá trị khoản vay', compute='_compute_loan_stats')
    total_loan_amount_empty = fields.Char(string='', default="(Chưa có dữ liệu)")
    active_loans = fields.Integer('Khoản vay đang hoạt động', compute='_compute_loan_stats')
    active_loans_empty = fields.Char(string='', default="(Chưa có dữ liệu)")
    funded_loans = fields.Integer('Khoản vay đã được tài trợ', compute='_compute_loan_stats')
    funded_loans_empty = fields.Char(string='', default="(Chưa có dữ liệu)")
    defaulted_loans = fields.Integer('Khoản vay quá hạn', compute='_compute_loan_stats')
    defaulted_loans_empty = fields.Char(string='', default="(Chưa có dữ liệu)")
    completed_loans = fields.Integer('Khoản vay hoàn thành', compute='_compute_loan_stats')
    completed_loans_empty = fields.Char(string='', default="(Chưa có dữ liệu)")
    loan_funding_rate = fields.Float('Tỷ lệ gọi vốn thành công (%)', compute='_compute_loan_stats')
    loan_funding_rate_empty = fields.Char(string='', default="(Chưa có dữ liệu)")
    average_loan_amount = fields.Float('Giá trị khoản vay trung bình', compute='_compute_loan_stats')
    average_loan_amount_empty = fields.Char(string='', default="(Chưa có dữ liệu)")
    average_interest_rate = fields.Float('Lãi suất trung bình (%)', compute='_compute_loan_stats')
    average_interest_rate_empty = fields.Char(string='', default="(Chưa có dữ liệu)")
    loans_by_purpose = fields.Json('Phân loại theo mục đích', compute='_compute_loan_stats')
    loans_by_state = fields.Json('Phân loại theo trạng thái', compute='_compute_loan_stats')
    chart_loan_status = fields.Json('Trạng thái khoản vay', compute='_compute_loan_stats')
    loan_trend_data = fields.Json('Dữ liệu xu hướng khoản vay', compute='_compute_loan_trend_data')
    loan_amount_trend_data = fields.Json('Dữ liệu xu hướng giá trị khoản vay', compute='_compute_loan_trend_data')

    # ----- User Stats -----
    total_borrowers = fields.Integer('Tổng số người vay', compute='_compute_user_stats')
    total_borrowers_empty = fields.Char(string='', default="(Chưa có dữ liệu)")
    active_borrowers = fields.Integer('Người vay đang hoạt động', compute='_compute_user_stats')
    active_borrowers_empty = fields.Char(string='', default="(Chưa có dữ liệu)")
    top_borrowers = fields.Json('Top người vay', compute='_compute_user_stats')

    # ----- Risk Stats -----
    default_rate = fields.Float('Tỷ lệ vỡ nợ (%)', compute='_compute_risk_stats')
    default_rate_empty = fields.Char(string='', default="(Chưa có dữ liệu)")
    risk_return_data = fields.Json('Dữ liệu rủi ro và lợi nhuận', compute='_compute_risk_stats')

    @api.depends('date_from', 'date_to')
    def _compute_loan_stats(self):
        for dashboard in self:
            # Lấy dữ liệu từ p2p_bridge.p2p.loan: dùng created_date/created_at thay cho start_date
            # Domain: (created_date trong khoảng) OR (created_at trong khoảng)
            loan_domain = [
                '|',
                    '&', ('created_date', '>=', dashboard.date_from), ('created_date', '<=', dashboard.date_to),
                    '&', ('created_at', '>=', fields.Datetime.to_datetime(dashboard.date_from)), ('created_at', '<=', fields.Datetime.to_datetime(dashboard.date_to)),
            ]
            
            try:
                # Tính tổng số khoản vay và các trạng thái
                loans = self.env['p2p.loan'].search(loan_domain)
                dashboard.total_loans = len(loans)
                # Trường p2p_bridge dùng 'capital' thay cho 'amount'
                dashboard.total_loan_amount = sum(loan.capital for loan in loans if loan.capital)
                
                # Các trạng thái
                # p2p_bridge.status: waiting, success, clean, fail
                dashboard.active_loans = len(loans.filtered(lambda l: l.status in ['waiting', 'success']))
                dashboard.funded_loans = len(loans.filtered(lambda l: l.status in ['success', 'clean']))
                dashboard.defaulted_loans = len(loans.filtered(lambda l: l.status == 'fail'))
                dashboard.completed_loans = len(loans.filtered(lambda l: l.status == 'clean'))
                
                # Tỷ lệ gọi vốn thành công
                waiting_or_funding = len(loans.filtered(lambda l: l.status in ['waiting']))
                if waiting_or_funding > 0:
                    dashboard.loan_funding_rate = (dashboard.funded_loans / (dashboard.funded_loans + waiting_or_funding)) * 100
                else:
                    dashboard.loan_funding_rate = 0
                
                # Giá trị khoản vay trung bình
                dashboard.average_loan_amount = dashboard.total_loan_amount / dashboard.total_loans if dashboard.total_loans > 0 else 0
                
                # Lãi suất trung bình
                if dashboard.total_loans > 0:
                    interest_rates = [loan.interest_rate for loan in loans if loan.interest_rate]
                    dashboard.average_interest_rate = sum(interest_rates) / len(interest_rates) if interest_rates else 0
                else:
                    dashboard.average_interest_rate = 0
                
                # Phân loại theo trạng thái (dựa theo p2p_bridge.status)
                state_data = {}
                status_field = self.env['p2p.loan']._fields.get('status')
                if status_field and status_field.type == 'selection':
                    selection_dict = dict(status_field.selection)
                    for state in selection_dict.keys():
                        state_count = len(loans.filtered(lambda l, s=state: l.status == s))
                        if state_count > 0:
                            state_data[selection_dict[state]] = state_count
                else:
                    # Nếu không phải selection field, dùng trực tiếp giá trị
                    status_counts = {}
                    for loan in loans:
                        status = loan.status
                        status_counts[status] = status_counts.get(status, 0) + 1
                    
                    for status, count in status_counts.items():
                        state_data[status or 'Không xác định'] = count
                
                # Nếu không có dữ liệu, thêm một mục "Không có dữ liệu"
                if not state_data:
                    state_data = {"Không có dữ liệu": 1}
                
                # Cấu trúc JSON cho Chart.js - Biểu đồ phân loại theo trạng thái
                colors = self._get_chart_colors(len(state_data))
                dashboard.loans_by_state = json.dumps({
                    'labels': list(state_data.keys()),
                    'datasets': [{
                        'label': 'Khoản vay theo trạng thái',
                        'data': list(state_data.values()),
                        'backgroundColor': colors['backgroundColor'],
                        'borderColor': colors['borderColor'],
                        'borderWidth': 1
                    }]
                })
                
                # Cấu trúc JSON cho Chart.js - Biểu đồ trạng thái khoản vay
                dashboard.chart_loan_status = json.dumps({
                    'labels': list(state_data.keys()),
                    'datasets': [{
                        'label': 'Trạng thái khoản vay',
                        'data': list(state_data.values()),
                        'backgroundColor': colors['backgroundColor'],
                        'borderColor': colors['borderColor'],
                        'borderWidth': 1
                    }]
                })
                
                # Tạo biểu đồ phân loại theo mục đích (từ description hoặc willing)
                # Nếu p2p.loan có trường 'willing', dùng làm mục đích
                purpose_data = {}
                if 'willing' in self.env['p2p.loan']._fields:
                    # Lấy giá trị unique từ willing
                    purpose_values = set(loan.willing for loan in loans if loan.willing)
                    for purpose in purpose_values:
                        purpose_count = len(loans.filtered(lambda l: l.willing == purpose))
                        if purpose_count > 0:
                            purpose_name = purpose if len(purpose) < 30 else purpose[:27] + '...'
                            purpose_data[purpose_name] = purpose_count
                else:
                    # Thử dùng trường description nếu không có willing
                    purpose_data = {"Cho vay": dashboard.total_loans}
                
                # Nếu không có dữ liệu, thêm một mục "Không có dữ liệu"
                if not purpose_data:
                    purpose_data = {"Không có dữ liệu": 1}
                
                # Cấu trúc JSON cho Chart.js
                colors = self._get_chart_colors(len(purpose_data))
                dashboard.loans_by_purpose = json.dumps({
                    'labels': list(purpose_data.keys()),
                    'datasets': [{
                        'label': 'Khoản vay theo mục đích',
                        'data': list(purpose_data.values()),
                        'backgroundColor': colors['backgroundColor'],
                        'borderColor': colors['borderColor'],
                        'borderWidth': 1
                    }]
                })
            except Exception as e:
                logger.warning(f"_compute_loan_stats skipped due to: {e}")
                dashboard.total_loans = 0
                dashboard.total_loan_amount = 0
                dashboard.active_loans = 0
                dashboard.funded_loans = 0
                dashboard.defaulted_loans = 0
                dashboard.completed_loans = 0
                dashboard.loan_funding_rate = 0
                dashboard.average_loan_amount = 0
                dashboard.average_interest_rate = 0
                dashboard.loans_by_purpose = json.dumps({})
                dashboard.loans_by_state = json.dumps({})
                dashboard.chart_loan_status = json.dumps({})

    @api.depends('date_from', 'date_to')
    def _compute_loan_trend_data(self):
        for dashboard in self:
            try:
                # Tính khoảng thời gian theo tháng
                months = self._get_months_between(dashboard.date_from, dashboard.date_to)
                
                # Đảm bảo luôn có dữ liệu cho biểu đồ
                if not months:
                    months = [
                        (dashboard.date_from, dashboard.date_to, "Không có dữ liệu")
                    ]
                
                # Dữ liệu xu hướng khoản vay
                loan_counts = []
                loan_amounts = []
                
                for month_start, month_end, month_label in months:
                    loans_in_month = self.env['p2p.loan'].search([
                        '|',
                            '&', ('created_date', '>=', month_start), ('created_date', '<=', month_end),
                            '&', ('created_at', '>=', fields.Datetime.to_datetime(month_start)), ('created_at', '<=', fields.Datetime.to_datetime(month_end)),
                    ])
                    
                    loan_counts.append(len(loans_in_month))
                    loan_amounts.append(sum(loan.capital for loan in loans_in_month if loan.capital))
                
                # Dữ liệu xu hướng số lượng khoản vay - Cấu trúc JSON cho Chart.js
                dashboard.loan_trend_data = json.dumps({
                    'labels': [m[2] for m in months],
                    'datasets': [{
                        'label': 'Số khoản vay',
                        'data': loan_counts,
                        'backgroundColor': 'rgba(75, 192, 192, 0.6)',
                        'borderColor': 'rgb(75, 192, 192)',
                        'borderWidth': 1,
                        'tension': 0.1
                    }]
                })
                
                # Dữ liệu xu hướng giá trị khoản vay - Cấu trúc JSON cho Chart.js
                dashboard.loan_amount_trend_data = json.dumps({
                    'labels': [m[2] for m in months],
                    'datasets': [{
                        'label': 'Giá trị khoản vay',
                        'data': loan_amounts,
                        'backgroundColor': 'rgba(153, 102, 255, 0.6)',
                        'borderColor': 'rgb(153, 102, 255)',
                        'borderWidth': 1,
                        'tension': 0.1
                    }]
                })
            except Exception as e:
                logger.warning(f"_compute_loan_trend_data skipped due to: {e}")
                dashboard.loan_trend_data = json.dumps({})
                dashboard.loan_amount_trend_data = json.dumps({})

# Removed investment stats compute method as it's no longer needed

# Removed investment trend data compute method as it's no longer needed

    @api.depends('date_from', 'date_to')
    def _compute_user_stats(self):
        for dashboard in self:
            try:
                # Lấy tất cả khoản vay trong khoảng thời gian
                loans = self.env['p2p.loan'].search([
                    '|',
                        '&', ('created_date', '>=', dashboard.date_from), ('created_date', '<=', dashboard.date_to),
                        '&', ('created_at', '>=', fields.Datetime.to_datetime(dashboard.date_from)), ('created_at', '<=', fields.Datetime.to_datetime(dashboard.date_to)),
                ])
                
                # Tính unique borrowers
                unique_borrowers = set(loan.borrower_id for loan in loans if loan.borrower_id)
                dashboard.total_borrowers = len(unique_borrowers)
                
                # Người vay đang hoạt động (có khoản vay đang ở trạng thái success)
                active_loans = loans.filtered(lambda l: l.status == 'success')
                active_borrowers = set(loan.borrower_id for loan in active_loans if loan.borrower_id)
                dashboard.active_borrowers = len(active_borrowers)
                
                # Top người vay
                top_borrowers_data = {}
                
                # Trước tiên, tính tổng số tiền vay của mỗi người
                for loan in loans:
                    if not loan.borrower_id or not loan.capital:
                        continue
                    
                    borrower_id = loan.borrower_id
                    capital = loan.capital or 0
                    
                    if borrower_id in top_borrowers_data:
                        top_borrowers_data[borrower_id]['total_borrowed'] += capital
                    else:
                        # Hiện tạm ID, sau đó cố gắng lấy tên thật
                        top_borrowers_data[borrower_id] = {
                            'borrower_id': borrower_id,
                            'borrower_name': f"Người vay {borrower_id[:8]}...",  # Hiển thị ID ngắn gọn
                            'total_borrowed': capital
                        }
                
                # Cố gắng lấy tên thật từ Odoo
                try:
                    # Kiểm tra xem p2p.user model có tồn tại không
                    if 'p2p.user' in self.env:
                        user_model = self.env['p2p.user']
                        for borrower_id in top_borrowers_data:
                            p2p_user = user_model.search([('user_id', '=', borrower_id)], limit=1)
                            if p2p_user:
                                display_name = p2p_user.display_name or p2p_user.name or p2p_user.username
                                if display_name:
                                    top_borrowers_data[borrower_id]['borrower_name'] = display_name
                except Exception as e:
                    logger.warning(f"Could not get user names from Odoo: {e}")
                            
                
                # Chuyển dict thành list và sắp xếp
                top_borrowers_list = list(top_borrowers_data.values())
                top_borrowers_list = sorted(top_borrowers_list, key=lambda x: x['total_borrowed'], reverse=True)[:5]
                
                # Tạo biểu đồ top borrowers
                labels = [item['borrower_name'] for item in top_borrowers_list]
                values = [item['total_borrowed'] for item in top_borrowers_list]
                
                if labels:
                    colors = self._get_chart_colors(len(labels))
                    dashboard.top_borrowers = json.dumps({
                        'labels': labels,
                        'datasets': [{
                            'label': 'Tổng số tiền vay',
                            'data': values,
                            'backgroundColor': colors['backgroundColor'],
                            'borderColor': colors['borderColor'],
                            'borderWidth': 1
                        }]
                    })
                else:
                    dashboard.top_borrowers = json.dumps({
                        'labels': ["Không có dữ liệu"],
                        'datasets': [{
                            'label': 'Tổng số tiền vay',
                            'data': [0],
                            'backgroundColor': ['rgba(200, 200, 200, 0.6)'],
                            'borderColor': ['rgb(200, 200, 200)'],
                            'borderWidth': 1
                        }]
                    })
            except Exception as e:
                logger.warning(f"_compute_user_stats skipped due to: {e}")
                dashboard.total_borrowers = 0
                dashboard.active_borrowers = 0
                dashboard.top_borrowers = json.dumps({
                    'labels': ["Không có dữ liệu"],
                    'datasets': [{
                        'label': 'Tổng số tiền vay',
                        'data': [0],
                        'backgroundColor': ['rgba(200, 200, 200, 0.6)'],
                        'borderColor': ['rgb(200, 200, 200)'],
                        'borderWidth': 1
                    }]
                })

    @api.depends('date_from', 'date_to')
    def _compute_risk_stats(self):
        for dashboard in self:
            try:
                # Lấy tất cả khoản vay trong khoảng thời gian
                all_loans = self.env['p2p.loan'].search([
                    '|',
                        '&', ('created_date', '>=', dashboard.date_from), ('created_date', '<=', dashboard.date_to),
                        '&', ('created_at', '>=', fields.Datetime.to_datetime(dashboard.date_from)), ('created_at', '<=', fields.Datetime.to_datetime(dashboard.date_to)),
                ])

                # Tỷ lệ vỡ nợ dựa trên status của p2p_bridge
                completed_loans = all_loans.filtered(lambda l: l.status in ['clean', 'fail'])
                if completed_loans:
                    defaulted_loans = all_loans.filtered(lambda l: l.status == 'fail')
                    dashboard.default_rate = (len(defaulted_loans) / len(completed_loans)) * 100
                else:
                    dashboard.default_rate = 0

                # Dữ liệu biểu đồ rủi ro
                risk_return_data = [{
                    'label': 'Tổng hợp',
                    'default_rate': dashboard.default_rate,
                    'interest_rate': sum(loan.interest_rate for loan in all_loans if loan.interest_rate) / len(all_loans) if all_loans else 0
                }]

                dashboard.risk_return_data = json.dumps({
                    'labels': [d['label'] for d in risk_return_data],
                    'datasets': [
                        {
                            'label': 'Tỷ lệ vỡ nợ (%)',
                            'data': [d['default_rate'] for d in risk_return_data],
                            'backgroundColor': 'rgba(255, 99, 132, 0.6)',
                            'borderColor': 'rgb(255, 99, 132)',
                            'borderWidth': 1
                        },
                        {
                            'label': 'Lãi suất trung bình (%)',
                            'data': [d['interest_rate'] for d in risk_return_data],
                            'backgroundColor': 'rgba(54, 162, 235, 0.6)',
                            'borderColor': 'rgb(54, 162, 235)',
                            'borderWidth': 1
                        }
                    ]
                })
            except Exception as e:
                logger.warning(f"_compute_risk_stats skipped due to: {e}")
                dashboard.default_rate = 0
                dashboard.risk_return_data = json.dumps({
                    'labels': ["Không có dữ liệu"],
                    'datasets': [
                        {
                            'label': 'Tỷ lệ vỡ nợ (%)',
                            'data': [0],
                            'backgroundColor': 'rgba(255, 99, 132, 0.6)',
                            'borderColor': 'rgb(255, 99, 132)',
                            'borderWidth': 1
                        },
                        {
                            'label': 'Lãi suất trung bình (%)',
                            'data': [0],
                            'backgroundColor': 'rgba(54, 162, 235, 0.6)',
                            'borderColor': 'rgb(54, 162, 235)',
                            'borderWidth': 1
                        }
                    ]
                })

    def _get_months_between(self, date_from, date_to):
        """Trả về danh sách các tháng giữa hai ngày"""
        months = []
        current_date = date_from.replace(day=1)
        
        while current_date <= date_to:
            # Ngày cuối tháng
            if current_date.month == 12:
                next_month = current_date.replace(year=current_date.year + 1, month=1)
            else:
                next_month = current_date.replace(month=current_date.month + 1)
            
            last_day = (next_month - timedelta(days=1)).day
            month_end = current_date.replace(day=last_day)
            
            # Định dạng tên tháng
            month_label = f"{current_date.month}/{current_date.year}"
            
            months.append((current_date, month_end, month_label))
            
            # Chuyển sang tháng tiếp theo
            current_date = next_month
        
        return months

    def _get_chart_colors(self, count):
        """Trả về danh sách màu cho biểu đồ"""
        colors = [
            'rgba(255, 99, 132, 0.6)',   # Đỏ
            'rgba(54, 162, 235, 0.6)',   # Xanh dương
            'rgba(255, 206, 86, 0.6)',   # Vàng
            'rgba(75, 192, 192, 0.6)',   # Xanh lá
            'rgba(153, 102, 255, 0.6)',  # Tím
            'rgba(255, 159, 64, 0.6)',   # Cam
            'rgba(199, 199, 199, 0.6)',  # Xám
            'rgba(83, 102, 255, 0.6)',   # Xanh tím
            'rgba(255, 99, 255, 0.6)',   # Hồng
            'rgba(34, 207, 207, 0.6)'    # Xanh ngọc
        ]
        
        border_colors = [
            'rgb(255, 99, 132)',   # Đỏ
            'rgb(54, 162, 235)',   # Xanh dương
            'rgb(255, 206, 86)',   # Vàng
            'rgb(75, 192, 192)',   # Xanh lá
            'rgb(153, 102, 255)',  # Tím
            'rgb(255, 159, 64)',   # Cam
            'rgb(199, 199, 199)',  # Xám
            'rgb(83, 102, 255)',   # Xanh tím
            'rgb(255, 99, 255)',   # Hồng
            'rgb(34, 207, 207)'    # Xanh ngọc
        ]
        
        # Lặp lại danh sách màu nếu cần nhiều hơn
        bg_colors = []
        border_color_list = []
        for i in range(count):
            bg_colors.append(colors[i % len(colors)])
            border_color_list.append(border_colors[i % len(border_colors)])
        
        return {
            'backgroundColor': bg_colors,
            'borderColor': border_color_list
        }

    def action_refresh_dashboard(self):
        """Làm mới dữ liệu bảng điều khiển"""
        self.ensure_one()
        return True
        
    def action_this_month(self):
        """Thiết lập khoảng thời gian là tháng hiện tại"""
        self.ensure_one()
        today = date.today()
        self.write({
            'date_from': today.replace(day=1),
            'date_to': today
        })
        return True
        
    def action_last_month(self):
        """Thiết lập khoảng thời gian là tháng trước"""
        self.ensure_one()
        today = date.today()
        
        # Tháng trước
        if today.month == 1:
            last_month_start = today.replace(year=today.year-1, month=12, day=1)
        else:
            last_month_start = today.replace(month=today.month-1, day=1)
            
        # Ngày cuối tháng trước
        if last_month_start.month == 12:
            last_month_end = last_month_start.replace(day=31)
        else:
            last_month_end = today.replace(day=1) - timedelta(days=1)
            
        self.write({
            'date_from': last_month_start,
            'date_to': last_month_end
        })
        return True
        
    def action_last_3_months(self):
        """Thiết lập khoảng thời gian là 3 tháng gần nhất"""
        self.ensure_one()
        today = date.today()
        three_months_ago = today - relativedelta(months=3)
        
        self.write({
            'date_from': three_months_ago,
            'date_to': today
        })
        return True
        
    def action_this_year(self):
        """Thiết lập khoảng thời gian là năm hiện tại"""
        self.ensure_one()
        today = date.today()
        
        self.write({
            'date_from': today.replace(month=1, day=1),
            'date_to': today
        })
        return True
        
    @api.model_create_multi
    def create(self, vals_list):
        """Ghi đè phương thức create để đảm bảo name luôn được tạo"""
        for vals in vals_list:
            if not vals.get('name'):
                today = fields.Date.today()
                vals['name'] = f"Bảng điều khiển P2P - {today.strftime('%d/%m/%Y')}"
        return super(P2PDashboard, self).create(vals_list)