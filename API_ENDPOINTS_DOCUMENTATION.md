# Tài liệu API Endpoints - Hệ thống Quản lý Quỹ Đầu tư Odoo

Base URL: `http://localhost:10018`

## 1. Authentication & Custom Auth

### 1.1 Signup với OTP
- **URL**: `/web/signup/otp`
- **Method**: POST (JSON)
- **Auth**: public
- **Mô tả**: Gửi OTP cho đăng ký tài khoản

### 1.2 Xác thực OTP
- **URL**: `/web/signup/verify-otp`
- **Method**: POST (JSON)
- **Auth**: public
- **Mô tả**: Xác thực mã OTP

## 2. Fund Management APIs

### 2.1 Lấy danh sách quỹ
- **URL**: `/data_fund`
- **Method**: GET
- **Auth**: public
- **Response**: JSON array các quỹ đầu tư
```json
[
  {
    "id": 1,
    "ticker": "VFM-VN30",
    "name": "Vietnam 30 Fund",
    "description": "Quỹ đầu tư VN30",
    "current_ytd": 12.5,
    "current_nav": 25000,
    "investment_type": "equity"
  }
]
```

### 2.2 Trang widget quỹ
- **URL**: `/fund_widget`
- **Method**: GET
- **Auth**: public
- **Mô tả**: Hiển thị trang danh sách quỹ

### 2.3 So sánh quỹ
- **URL**: `/fund_compare`
- **Method**: GET
- **Auth**: public
- **Mô tả**: Trang so sánh các quỹ

### 2.4 Mua quỹ
- **URL**: `/fund_buy`
- **Method**: GET
- **Auth**: public
- **Mô tả**: Trang mua quỹ

### 2.5 Xác nhận mua quỹ
- **URL**: `/fund_confirm`
- **Method**: GET
- **Auth**: public
- **Mô tả**: Trang xác nhận giao dịch mua

### 2.6 Kết quả giao dịch
- **URL**: `/fund_result`
- **Method**: GET
- **Auth**: public
- **Mô tả**: Trang hiển thị kết quả giao dịch

### 2.7 Bán quỹ
- **URL**: `/fund_sell`
- **Method**: GET
- **Auth**: public
- **Mô tả**: Trang bán quỹ

### 2.8 Xác nhận bán quỹ
- **URL**: `/fund_sell_confirm`
- **Method**: GET
- **Auth**: public
- **Mô tả**: Trang xác nhận giao dịch bán

## 3. Investment Management APIs

### 3.1 Tạo đầu tư mới
- **URL**: `/create_investment`
- **Method**: POST
- **Auth**: user
- **Parameters**:
  - `fund_id`: ID của quỹ
  - `amount`: Số tiền đầu tư
  - `units`: Số lượng chứng chỉ quỹ
- **Response**: JSON
```json
{
  "success": true,
  "message": "Da tao investment thanh cong",
  "id": 123
}
```

### 3.2 Lấy danh sách đầu tư của user
- **URL**: `/data_investment`
- **Method**: GET
- **Auth**: user
- **Response**: JSON array các khoản đầu tư
```json
[
  {
    "id": 1,
    "fund_id": 5,
    "fund_name": "Vietnam Growth Fund",
    "fund_ticker": "VGF",
    "units": 100.5,
    "amount": 2500000,
    "current_nav": 25000,
    "investment_type": "equity"
  }
]
```

### 3.3 Bán quỹ
- **URL**: `/submit_fund_sell`
- **Method**: POST
- **Auth**: user
- **Parameters**:
  - `investment_id`: ID khoản đầu tư
  - `quantity`: Số lượng bán
  - `estimated_value`: Giá trị ước tính
- **Response**: JSON
```json
{
  "success": true,
  "message": "Cập nhật investment thành công."
}
```

## 4. Portfolio Management APIs

### 4.1 Widget danh mục đầu tư
- **URL**: `/portfolio_widget`
- **Method**: GET
- **Auth**: public
- **Mô tả**: Hiển thị trang danh mục đầu tư

## 5. Account Balance APIs

### 5.1 Số dư tài khoản
- **URL**: `/account_balance`
- **Method**: GET
- **Auth**: public
- **Mô tả**: Trang hiển thị số dư tài khoản

## 6. Investor Profile Management APIs

### 6.1 Trang thông tin cá nhân
- **URL**: `/personal_profile`
- **Method**: GET
- **Auth**: user
- **Mô tả**: Trang quản lý thông tin cá nhân

### 6.2 Trang thông tin ngân hàng
- **URL**: `/bank_info`
- **Method**: GET
- **Auth**: user
- **Mô tả**: Trang quản lý thông tin ngân hàng

### 6.3 Trang địa chỉ
- **URL**: `/address_info`
- **Method**: GET
- **Auth**: user
- **Mô tả**: Trang quản lý địa chỉ

### 6.4 Trang xác minh
- **URL**: `/verification`
- **Method**: GET
- **Auth**: user
- **Mô tả**: Trang xác minh hồ sơ

### 6.5 Lấy danh sách quốc gia
- **URL**: `/get_countries`
- **Method**: GET
- **Auth**: user
- **Response**: JSON array
```json
[
  {
    "id": 1,
    "name": "Vietnam"
  }
]
```

### 6.6 Lấy danh sách tiền tệ
- **URL**: `/get_currencies`
- **Method**: GET
- **Auth**: user
- **Response**: JSON array
```json
[
  {
    "id": 1,
    "name": "VND",
    "symbol": "₫"
  }
]
```

### 6.7 Lấy thông tin trạng thái
- **URL**: `/get_status_info`
- **Method**: GET
- **Auth**: user
- **Response**: JSON array thông tin trạng thái tài khoản

### 6.8 Lấy thông tin cá nhân
- **URL**: `/data_personal_profile`
- **Method**: GET
- **Auth**: user
- **Response**: JSON array thông tin profile
```json
[
  {
    "id": 1,
    "name": "Nguyen Van A",
    "email": "a@example.com",
    "phone": "0123456789",
    "birth_date": "1990-01-01",
    "gender": "male",
    "nationality": 1,
    "id_type": "citizen_id",
    "id_number": "123456789",
    "id_issue_date": "2010-01-01",
    "id_issue_place": "Hanoi",
    "id_front": "/web/image?model=investor.profile&field=id_front&id=1",
    "id_back": "/web/image?model=investor.profile&field=id_back&id=1"
  }
]
```

### 6.9 Lưu thông tin cá nhân
- **URL**: `/save_personal_profile`
- **Method**: POST (JSON)
- **Auth**: user
- **Body**: JSON object với thông tin profile
- **Response**: JSON success/error

### 6.10 Upload ảnh CMND/CCCD
- **URL**: `/upload_id_image`
- **Method**: POST
- **Auth**: user
- **Parameters**: File upload
- **Response**: JSON success/error

### 6.11 Lấy thông tin ngân hàng
- **URL**: `/data_bank_info`
- **Method**: GET
- **Auth**: user
- **Response**: JSON array thông tin ngân hàng

### 6.12 Lưu thông tin ngân hàng
- **URL**: `/save_bank_info`
- **Method**: POST (JSON)
- **Auth**: user
- **Body**: JSON object với thông tin ngân hàng
- **Response**: JSON success/error

### 6.13 Lấy thông tin địa chỉ
- **URL**: `/data_address_info`
- **Method**: GET
- **Auth**: user
- **Response**: JSON array thông tin địa chỉ

### 6.14 Lưu thông tin địa chỉ
- **URL**: `/save_address_info`
- **Method**: POST (JSON)
- **Auth**: user
- **Body**: JSON object với thông tin địa chỉ
- **Response**: JSON success/error

### 6.15 Lấy dữ liệu xác minh
- **URL**: `/data_verification`
- **Method**: GET
- **Auth**: user
- **Response**: JSON data xác minh

### 6.16 Lưu tất cả dữ liệu profile
- **URL**: `/save_all_profile_data`
- **Method**: POST (JSON)
- **Auth**: user
- **Body**: JSON object với tất cả thông tin profile
- **Response**: JSON success/error

## 7. Transaction Management APIs

### 7.1 Giao dịch định kỳ
- **URL**: `/transaction_management/periodic`
- **Method**: GET
- **Auth**: user
- **Mô tả**: Trang quản lý giao dịch định kỳ

### 7.2 Lệnh giao dịch
- **URL**: `/transaction_management/order`
- **Method**: GET
- **Auth**: user
- **Mô tả**: Trang quản lý lệnh giao dịch

### 7.3 Giao dịch chờ xử lý
- **URL**: `/transaction_management/pending`
- **Method**: GET
- **Auth**: user
- **Mô tả**: Trang giao dịch chờ xử lý

## 8. Overview & Dashboard APIs

### 8.1 Dashboard tổng quan đầu tư
- **URL**: `/investment_dashboard`
- **Method**: GET
- **Auth**: user
- **Mô tả**: Trang dashboard tổng quan

## 9. Asset Management APIs

### 9.1 Quản lý tài sản
- **URL**: `/asset-management`
- **Method**: GET
- **Auth**: user
- **Mô tả**: Trang quản lý tài sản

## Ghi chú quan trọng:

1. **Authentication**: 
   - `public`: Không cần đăng nhập
   - `user`: Cần đăng nhập
   
2. **CORS**: Một số API có hỗ trợ CORS với `cors='*'`

3. **CSRF**: Các API POST có `csrf=False` để dễ dàng gọi từ frontend

4. **Content-Type**: 
   - `type='http'`: HTTP request thông thường
   - `type='json'`: JSON request

5. **Error Handling**: Tất cả API đều có xử lý exception và trả về JSON error

## Cách sử dụng:

1. Để test API, truy cập: `http://localhost:10018/[endpoint]`
2. Sử dụng Postman collection đã tạo để test các API
3. Đối với các API cần auth, cần login trước qua web interface 