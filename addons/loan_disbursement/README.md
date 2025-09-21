# Loan Disbursement Management Module

Module quản lý giải ngân khoản vay cho hệ thống P2P Lending trên Odoo 18.

## Tính năng chính

### 1. Quản lý giải ngân (Loan Disbursement)
- Tạo yêu cầu giải ngân
- Workflow phê duyệt: Draft → Pending → Approved → Processing → Disbursed
- Hỗ trợ nhiều phương thức giải ngân:
  - Chuyển khoản ngân hàng
  - Tiền mặt
  - Blockchain Transfer
- Tích hợp blockchain với transaction tracking
- Lịch sử và audit trail

### 2. Quản lý đơn vay (Loan Application)
- Tạo và quản lý đơn vay
- Tính toán tự động: lãi suất, kỳ hạn, trả góp
- Workflow: Draft → Submitted → Under Review → Approved → Disbursed
- Liên kết với giải ngân

### 3. Cấu hình hệ thống (Loan Configuration)
- Cấu hình loại khoản vay
- Thiết lập lãi suất, phí dịch vụ
- Cấu hình blockchain
- Giới hạn khoản vay
- Cấu hình KYC

### 4. API Integration
- REST API cho mobile app
- Endpoints cho quản lý giải ngân
- Authentication và authorization
- Real-time status updates

## Cài đặt

### 1. Cài đặt module
```bash
# Copy module vào thư mục addons
cp -r loan_disbursement /path/to/odoo/addons/
cp -r loan_config /path/to/odoo/addons/

# Cài đặt module trong Odoo
# Apps → Update Apps List → Search "Loan Disbursement" → Install
```

### 2. Cấu hình ban đầu
1. **Tạo loại khoản vay:**
   - Vào P2P Lending → Quản lý khoản vay → Cấu hình
   - Tạo các loại khoản vay với lãi suất và kỳ hạn

2. **Cấu hình hệ thống:**
   - Vào P2P Lending → Cấu hình
   - Thiết lập giới hạn khoản vay, phí dịch vụ
   - Cấu hình blockchain API

3. **Phân quyền:**
   - Tạo user groups cho admin và staff
   - Phân quyền truy cập các chức năng

## Sử dụng

### 1. Quy trình giải ngân
```
1. Tạo đơn vay (Loan Application)
2. Phê duyệt đơn vay
3. Tạo yêu cầu giải ngân
4. Phê duyệt giải ngân
5. Xử lý giải ngân (tự động hoặc thủ công)
6. Xác nhận hoàn thành
```

### 2. API Usage

#### Lấy danh sách giải ngân
```bash
GET /api/loan/disbursements
{
  "status": "pending",
  "limit": 20,
  "offset": 0
}
```

#### Phê duyệt giải ngân
```bash
POST /api/loan/disbursements/approve
{
  "disbursement_id": 123
}
```

#### Xử lý giải ngân
```bash
POST /api/loan/disbursements/process
{
  "disbursement_id": 123
}
```

#### Lấy cấu hình
```bash
GET /api/loan/config
```

## Tích hợp Blockchain

### 1. Cấu hình Blockchain
- Thiết lập API URL và API Key
- Chọn mạng blockchain (Ethereum, Polygon, BSC, Testnet)
- Cấu hình smart contract address

### 2. Quy trình Blockchain
```
1. Tạo disbursement với method = 'blockchain'
2. Khi approve → gọi blockchain API
3. Nhận transaction ID
4. Update status dựa trên blockchain confirmation
```

## Bảo mật

### 1. Authentication
- Sử dụng Odoo user authentication
- API endpoints yêu cầu user login

### 2. Authorization
- Role-based access control
- Phân quyền theo user groups
- Audit trail cho mọi thay đổi

### 3. Data Protection
- Encryption cho sensitive data
- Secure API communication
- Logging cho security events

## Monitoring & Reporting

### 1. Dashboard
- Tổng quan khoản vay và giải ngân
- Thống kê theo trạng thái
- Biểu đồ xu hướng

### 2. Reports
- Báo cáo giải ngân theo thời gian
- Thống kê theo phương thức
- Audit trail reports

### 3. Notifications
- Email notifications cho status changes
- SMS notifications (tùy chọn)
- In-app notifications

## Troubleshooting

### 1. Common Issues
- **Blockchain API errors:** Kiểm tra API URL và key
- **Permission errors:** Kiểm tra user groups và access rights
- **Calculation errors:** Verify loan configuration

### 2. Logs
- Check Odoo logs: `/var/log/odoo/odoo.log`
- API logs: Check controller logs
- Blockchain logs: Check transaction status

### 3. Support
- Documentation: Check module documentation
- Community: Odoo Community Forum
- Technical support: Contact development team

## Development

### 1. Customization
- Extend models for additional fields
- Customize workflows
- Add new API endpoints

### 2. Testing
- Unit tests for models
- Integration tests for API
- End-to-end workflow testing

### 3. Deployment
- Production deployment checklist
- Database migration
- Performance optimization

## License

LGPL-3 License - See LICENSE file for details.
