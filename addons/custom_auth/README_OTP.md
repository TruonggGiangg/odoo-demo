# Tính năng OTP cho Đăng ký Tài khoản

## Mô tả
Module này đã được mở rộng để bao gồm tính năng xác thực OTP (One-Time Password) khi đăng ký tài khoản mới. Thay vì chuyển hướng ngay lập tức sau khi điền form đăng ký, hệ thống sẽ hiển thị một popup OTP để người dùng nhập mã xác thực.

## Tính năng chính

### 1. Popup OTP
- Giao diện popup hiện đại với Tailwind CSS
- 6 ô nhập mã OTP với tự động focus
- Timer đếm ngược 5 phút
- Nút gửi lại OTP
- Hiển thị email đã gửi OTP

### 2. Xác thực Form
- Kiểm tra tính hợp lệ của tất cả trường
- Hiển thị độ mạnh mật khẩu
- Kiểm tra khớp mật khẩu xác nhận
- Validation real-time

### 3. Bảo mật
- OTP 6 số ngẫu nhiên
- Lưu trữ tạm thời trong session
- Tự động hết hạn sau 5 phút
- Chỉ cho phép nhập số trong ô OTP

## Cách hoạt động

### 1. Quy trình đăng ký
1. Người dùng điền form đăng ký
2. Bấm "Đăng ký tài khoản"
3. Hệ thống kiểm tra tính hợp lệ
4. Gửi OTP qua email (hiện tại trả về để test)
5. Hiển thị popup OTP
6. Người dùng nhập mã OTP
7. Xác thực và tạo tài khoản
8. Chuyển hướng đến trang đăng nhập

### 2. API Endpoints
- `POST /web/signup/otp`: Gửi OTP
- `POST /web/signup/verify-otp`: Xác thực OTP và tạo tài khoản

## Cài đặt và Sử dụng

### 1. Cài đặt Module
```bash
# Copy module vào thư mục addons
# Cập nhật module trong Odoo
```

### 2. Cấu hình Email (Tùy chọn)
Để gửi OTP thực sự qua email, cần implement hàm `_send_otp_email` trong controller:
```python
def _send_otp_email(self, email, otp):
    # Implement gửi email OTP
    # Có thể sử dụng Odoo's email template system
    pass
```

### 3. Tùy chỉnh
- Thay đổi thời gian hết hạn OTP trong `controllers/main.py`
- Tùy chỉnh giao diện popup trong `views/otp_popup_template.xml`
- Thay đổi styling trong `static/src/css/otp_popup.css`

## Cấu trúc Files

```
custom_auth/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   └── main.py
├── views/
│   ├── custom_signup_template.xml
│   └── otp_popup_template.xml
├── static/
│   ├── src/
│   │   ├── css/
│   │   │   └── otp_popup.css
│   │   └── js/
│   │       └── signup/
│   │           └── signup_with_otp.js
└── README_OTP.md
```

## Tính năng bổ sung

### 1. Responsive Design
- Popup tương thích với mobile
- Tự động điều chỉnh kích thước

### 2. Accessibility
- Hỗ trợ keyboard navigation
- Focus management
- ARIA labels

### 3. UX/UI
- Animations mượt mà
- Loading states
- Error handling
- Success feedback

## Lưu ý bảo mật

### 1. Production
- Xóa dòng trả về OTP trong response
- Implement gửi email thực sự
- Thêm rate limiting cho API
- Sử dụng HTTPS

### 2. Session Management
- OTP được lưu trong session
- Tự động xóa sau khi sử dụng
- Có thể migrate sang database với TTL

## Troubleshooting

### 1. OTP không hiển thị
- Kiểm tra console errors
- Verify JavaScript loading
- Check template inheritance

### 2. API không hoạt động
- Kiểm tra controller routes
- Verify CSRF token
- Check Odoo logs

### 3. Styling issues
- Clear browser cache
- Check CSS loading
- Verify Tailwind CSS

## Tương lai

### 1. Tính năng có thể thêm
- SMS OTP
- Google Authenticator
- Backup codes
- Remember device

### 2. Cải tiến
- Database storage cho OTP
- Email templates
- Rate limiting
- Audit logs 