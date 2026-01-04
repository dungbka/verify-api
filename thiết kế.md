# Thiết kế Backend License API (FastAPI)

## 1. Mục tiêu

Thiết kế **backend FastAPI** phục vụ việc xác thực license cho tool desktop với các yêu cầu:

* Verify license online **nhẹ**
* 1 license chỉ bind được **1 machine**
* Có activate lần đầu
* Có verify định kỳ
* Chạy được trên **free tier (Render / Railway / tương đương)**
* Code đơn giản, dễ maintain, dễ mở rộng

---

## 2. Phạm vi backend

Backend **chỉ chịu trách nhiệm**:

* Lưu trữ license key
* Bind license với machine_id
* Kiểm tra trạng thái license
* Trả kết quả verify cho client

❌ Backend KHÔNG xử lý:

* Tạo machine_id
* Obfuscation / chống crack
* UI / GUI

---

## 3. Kiến trúc backend

```
Client App
   |
   | HTTPS (JSON)
   v
FastAPI App
   |
   v
Database (SQLite / PostgreSQL)
```

---

## 4. Công nghệ

* Language: Python 3.10+
* Framework: FastAPI
* ASGI Server: Uvicorn
* ORM: sqlite3 (phase 1) / SQLAlchemy (optional)
* Hosting: Render Free Tier

---

## 5. Database Design

### 5.1 Bảng: licenses

| Field          | Type       | Nullable | Mô tả               |
| -------------- | ---------- | -------- | ------------------- |
| license_key    | TEXT (PK)  | ❌        | License key         |
| machine_id     | TEXT       | ✅        | Machine ID đã bind  |
| status         | TEXT       | ❌        | active / revoked    |
| expired_at     | TEXT (ISO) | ✅        | Ngày hết hạn        |
| activated_at   | TEXT (ISO) | ✅        | Thời điểm activate  |
| last_verify_at | TEXT (ISO) | ✅        | Lần verify gần nhất |

---

## 6. API Design

### 6.1 POST /activate

#### Mục đích

* Kích hoạt license lần đầu
* Bind license với machine_id

#### Request

```json
{
  "license_key": "XXXX-XXXX",
  "machine_id": "HASH"
}
```

#### Logic xử lý

1. Tìm license theo license_key
2. Nếu không tồn tại → error
3. Nếu status != active → error
4. Nếu expired_at < now → error
5. Nếu machine_id NULL → bind machine_id
6. Nếu machine_id khác → error (đã dùng máy khác)
7. Lưu activated_at nếu chưa có

#### Response (success)

```json
{ "status": "activated" }
```

---

### 6.2 POST /verify

#### Mục đích

* Xác thực license định kỳ

#### Request

```json
{
  "license_key": "XXXX-XXXX",
  "machine_id": "HASH"
}
```

#### Logic xử lý

1. Tìm license
2. Nếu không tồn tại → valid = false
3. Nếu status != active → valid = false
4. Nếu expired_at < now → valid = false
5. Nếu machine_id không khớp → valid = false
6. Update last_verify_at

#### Response

```json
{ "valid": true }
```

---

## 7. Error Handling

| Trường hợp               | HTTP Code | Message                   |
| ------------------------ | --------- | ------------------------- |
| License không tồn tại    | 400       | Invalid license           |
| License đã dùng máy khác | 400       | License already activated |
| License hết hạn          | 400       | License expired           |
| License bị revoke        | 400       | License revoked           |

---

## 8. Security cơ bản

* Bắt buộc HTTPS
* Validate input (Pydantic)
* Không trả chi tiết thừa trong response
* Có thể thêm API-KEY nội bộ sau này

---

## 9. Seed & Quản lý license

### 9.1 Seed license thủ công

* Insert license_key trước vào DB
* machine_id = NULL
* status = active
* expired_at set theo gói

### 9.2 Re-issue license (thủ công)

* Reset machine_id = NULL
* Giữ nguyên license_key hoặc tạo key mới

---

## 10. Non-functional

* Timeout API: ≤ 5s
* Không yêu cầu high throughput
* Ưu tiên stability > performance

---

## 11. Extension (future)

* Thêm bảng `license_events`
* Thêm endpoint `/revoke`
* Thêm PostgreSQL
* Thêm admin API

---

## 12. Deliverable cho Cursor

Cursor cần sinh:

1. main.py (FastAPI app)
2. DB init script
3. Pydantic models
4. README deploy Render

---

## 13. Kết luận

Thiết kế backend này:

* Đủ đơn giản để chạy free
* Đủ chặt để kiểm soát license nội bộ
* Dễ mở rộng khi cần

Phù hợp cho hệ thống license verify online nhẹ.
