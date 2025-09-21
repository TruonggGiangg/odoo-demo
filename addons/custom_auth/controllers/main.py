import json
import random
import string
import logging

from odoo import http, _
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class CustomAuthController(AuthSignupHome):
    
    @http.route('/web/signup/otp', type='json', auth='public', methods=['POST'])
    def send_otp(self, **post):
        """Gửi mã OTP qua SMS"""
        try:
            phone = post.get('phone')
            if not phone:
                return {'success': False, 'message': 'Số điện thoại không hợp lệ'}
            
            # Tạo mã OTP 6 số
            otp = ''.join(random.choices(string.digits, k=6))
            
            # Lưu OTP vào session
            request.session['signup_otp'] = otp
            request.session['signup_phone'] = phone
            request.session['signup_data'] = post
            
            _logger.info("Generated OTP %s for phone %s", otp, phone)
            
            return {
                'success': True, 
                'message': 'Mã OTP đã được gửi đến số điện thoại của bạn',
                'otp': otp,
                'phone': phone
            }
            
        except Exception as e:
            _logger.error("Error sending OTP: %s", str(e), exc_info=True)
            return {'success': False, 'message': 'Có lỗi xảy ra khi gửi OTP.'}
    
    @http.route('/web/signup/verify-otp', type='json', auth='public', methods=['POST'])
    def verify_otp(self, **post):
        """Xác thực mã OTP và tạo tài khoản"""
        signup_data = request.session.get('signup_data')
        if not signup_data:
            return {'success': False, 'message': _('Không có dữ liệu đăng ký trong phiên. Vui lòng thử lại.')}

        try:
            otp = post.get('otp')
            
            if not otp or len(otp) != 6:
                return {'success': False, 'message': 'Vui lòng nhập đủ 6 số OTP'}
            
            # Create user
            user = self._create_user_from_data(signup_data)
            
            # Clean session
            request.session.pop('signup_otp', None)
            request.session.pop('signup_phone', None)
            request.session.pop('signup_data', None)
            
            return {
                'success': True, 
                'message': 'Đăng ký thành công! Bạn sẽ được chuyển hướng đến trang đăng nhập.',
                'redirect_url': '/web/login'
            }
            
        except UserError as e:
            return {'success': False, 'message': str(e)}
        except Exception as e:
            _logger.error("Error during OTP verification/signup: %s", str(e), exc_info=True)
            return {'success': False, 'message': _('Đã xảy ra lỗi không mong muốn. Vui lòng liên hệ quản trị viên.')}

    def _create_user_from_data(self, data):
        """Tạo người dùng từ dữ liệu đăng ký. Raises UserError on failure."""
        if not all(data.get(key) for key in ['email', 'password', 'name', 'phone']):
             raise UserError(_("Vui lòng điền đầy đủ thông tin: Tên, Email, Điện thoại và Mật khẩu."))

        if request.env['res.users'].sudo().search_count([('login', '=', data.get('email'))]):
            raise UserError(_("Một người dùng khác đã được đăng ký với địa chỉ email này."))

        user_values = {
            'name': data.get('name'),
            'login': data.get('email'),
            'email': data.get('email'),
            'password': data.get('password'),
            'groups_id': [(6, 0, [request.env.ref('base.group_portal').id])],
        }
        
        try:
            user = request.env['res.users'].with_context(no_reset_password=True).sudo().create(user_values)
            user.partner_id.sudo().write({'phone': data.get('phone')})
            _logger.info("Successfully created new portal user: %s (ID: %s)", user.login, user.id)
            return user
        except Exception as e:
            _logger.error("Failed to create user for login %s: %s", data.get('email'), str(e), exc_info=True)
            raise UserError(_("Không thể tạo người dùng mới. Vui lòng liên hệ quản trị viên."))
    
    def _send_sms_otp(self, phone, otp):
        """Gửi SMS OTP (cần implement)"""
        # Implement gửi SMS OTP ở đây
        # Có thể sử dụng các dịch vụ SMS như Twilio, Nexmo, etc.
        pass 