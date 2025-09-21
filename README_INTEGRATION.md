# Hướng dẫn tích hợp Odoo 18 với Server P2P Lending

## Tổng quan

Hệ thống tích hợp Odoo 18 với server Node.js hiện tại để quản lý giải ngân và cấu hình khoản vay một cách hiệu quả.

## Kiến trúc tích hợp

```
┌─────────────────┐    API Calls    ┌─────────────────┐
│   Odoo 18       │ ◄─────────────► │  Node.js Server │
│   (Admin Web)   │                 │   (Mobile API)  │
└─────────────────┘                 └─────────────────┘
         │                                    │
         │                                    │
         ▼                                    ▼
┌─────────────────┐                 ┌─────────────────┐
│  PostgreSQL     │                 │    MongoDB      │
│  (Odoo DB)      │                 │  (Server DB)    │
└─────────────────┘                 └─────────────────┘
```

## Các module đã tạo

### 1. `loan_disbursement` - Module chính
- **Model**: `loan.disbursement` - Quản lý giải ngân
- **Model**: `loan.application` - Quản lý đơn vay
- **API**: REST endpoints cho mobile app
- **Tích hợp**: Đồng bộ với server Node.js

### 2. `loan_config` - Module cấu hình
- **Model**: `loan.type` - Loại khoản vay
- **Model**: `loan.configuration` - Cấu hình hệ thống
- **Tích hợp**: Đồng bộ cấu hình với server

## Cài đặt và cấu hình

### 1. Cài đặt Odoo modules

```bash
# Copy modules vào thư mục addons
cp -r odoo-18-docker-compose/addons/loan_disbursement /path/to/odoo/addons/
cp -r odoo-18-docker-compose/addons/loan_config /path/to/odoo/addons/

# Restart Odoo
docker-compose restart odoo
```

### 2. Cài đặt modules trong Odoo
1. Vào **Apps** → **Update Apps List**
2. Tìm và cài đặt:
   - **Loan Disbursement Management**
   - **Loan Configuration**

### 3. Cấu hình tích hợp server

#### Trong Odoo:
1. Vào **P2P Lending** → **Cấu hình**
2. Tạo cấu hình mới với:
   - **Server API URL**: `http://localhost:3000` (hoặc URL server)
   - **Server API Key**: API key từ server
   - **Chu kỳ đồng bộ**: 30 phút

#### Trong Server:
1. Đảm bảo server đang chạy trên port 3000
2. Kiểm tra API endpoints mới đã được thêm:
   - `POST /loan/disburse` - Xử lý giải ngân
   - `PUT /loan/disbursement/sync` - Đồng bộ trạng thái
   - `GET /loan/odoo/data` - Lấy dữ liệu cho Odoo

## Quy trình làm việc

### 1. Quy trình giải ngân tích hợp

```
1. Admin tạo đơn vay trong Odoo
   ↓
2. Phê duyệt đơn vay
   ↓
3. Tạo yêu cầu giải ngân
   ↓
4. Phê duyệt giải ngân
   ↓
5. Odoo gọi API server để xử lý
   ↓
6. Server tạo investment contract
   ↓
7. Cập nhật trạng thái loan
   ↓
8. Đồng bộ kết quả về Odoo
```

### 2. Đồng bộ dữ liệu

#### Từ Odoo → Server:
- Cấu hình hệ thống
- Trạng thái giải ngân
- Thông tin phê duyệt

#### Từ Server → Odoo:
- Dữ liệu khoản vay
- Thông tin investment
- Trạng thái blockchain

## API Endpoints

### Odoo → Server

#### 1. Xử lý giải ngân
```bash
POST /loan/disburse
{
  "disbursement_id": "DIS/2024/00001",
  "loan_application_id": "LOAN/2024/00001",
  "borrower_id": "507f1f77bcf86cd799439011",
  "amount": 10000000,
  "disbursement_date": "2024-01-15",
  "disbursement_method": "bank_transfer",
  "bank_account": "1234567890",
  "bank_name": "Vietcombank",
  "notes": "Giải ngân khoản vay"
}
```

#### 2. Đồng bộ trạng thái
```bash
PUT /loan/disbursement/sync
{
  "disbursement_id": "DIS/2024/00001",
  "status": "disbursed",
  "approval_date": "2024-01-15 10:30:00",
  "disbursement_date": "2024-01-15",
  "blockchain_tx_id": "TX_123456"
}
```

#### 3. Lấy dữ liệu khoản vay
```bash
GET /loan/odoo/data?status=success&limit=20&offset=0
```

### Server → Odoo

#### 1. Cập nhật cấu hình
```bash
PUT /loan/config
{
  "min_loan_amount": 1000000,
  "max_loan_amount": 1000000000,
  "base_interest_rate": 12.0,
  "max_interest_rate": 36.0,
  "service_fee_rate": 5.0,
  "late_fee_rate": 2.0,
  "processing_fee": 50000
}
```

## Cấu hình bảo mật

### 1. Authentication
- Sử dụng API Key cho giao tiếp giữa Odoo và Server
- Odoo user authentication cho admin access
- Server middleware cho API protection

### 2. Authorization
- Role-based access control trong Odoo
- Admin-only access cho các API quan trọng
- Audit trail cho mọi thay đổi

## Monitoring và Troubleshooting

### 1. Logs
- **Odoo logs**: `/var/log/odoo/odoo.log`
- **Server logs**: Console output hoặc log files
- **API logs**: Check network requests

### 2. Kiểm tra kết nối
```bash
# Test server connection từ Odoo
curl -X GET "http://localhost:3000/auth/test" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### 3. Đồng bộ dữ liệu
- Kiểm tra cron job đồng bộ trong Odoo
- Verify API responses
- Check database consistency

## Tính năng nâng cao

### 1. Real-time notifications
- Webhook từ server về Odoo
- Email notifications cho status changes
- In-app notifications

### 2. Dashboard tích hợp
- Thống kê từ cả Odoo và Server
- Biểu đồ xu hướng
- Real-time updates

### 3. Backup và recovery
- Database backup cho cả Odoo và Server
- Point-in-time recovery
- Data consistency checks

## Development

### 1. Thêm tính năng mới
1. Tạo model trong Odoo
2. Thêm API endpoint trong Server
3. Cập nhật integration logic
4. Test end-to-end

### 2. Customization
- Extend existing models
- Add new API endpoints
- Customize workflows
- Modify UI/UX

### 3. Testing
- Unit tests cho models
- Integration tests cho API
- End-to-end workflow testing
- Performance testing

## Deployment

### 1. Production checklist
- [ ] SSL certificates
- [ ] Database backup
- [ ] Monitoring setup
- [ ] Error handling
- [ ] Performance optimization
- [ ] Security audit

### 2. Environment variables
```bash
# Odoo
ODOO_SERVER_API_URL=http://your-server.com
ODOO_SERVER_API_KEY=your-api-key

# Server
ODOO_WEBHOOK_URL=http://your-odoo.com/webhook
ODOO_API_KEY=your-odoo-api-key
```

## Support

### 1. Documentation
- Module documentation trong Odoo
- API documentation
- User guides

### 2. Troubleshooting
- Common issues và solutions
- Debug procedures
- Performance optimization

### 3. Contact
- Development team
- Technical support
- Community forum

## License

LGPL-3 License - See LICENSE file for details.
