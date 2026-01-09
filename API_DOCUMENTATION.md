# License Verification API - Hướng dẫn sử dụng

## Base URL
```
https://verify-api-ru8s.onrender.com
```

---

## 1. Activate License

Kích hoạt license lần đầu và bind với machine_id.

**Endpoint:** `POST /activate`

**Request:**
```json
{
    "license_key": "LIC-8F3A9C2D-7B41-4E9A-A1C7-92F6D3A5B8E1",
    "machine_id": "machine-hash-12345"
}
```

**Response (Success):**
```json
{
    "status": "activated"
}
```

**Response (Error - 400):**
```json
{
    "detail": "Invalid license"
}
```

**Các lỗi có thể gặp:**
- `Invalid license` - License không tồn tại
- `License revoked` - License đã bị revoke
- `License expired` - License đã hết hạn
- `License already activated` - License đã bind với machine khác

**Example cURL:**
```bash
curl -X POST https://verify-api-ru8s.onrender.com/activate \
  -H "Content-Type: application/json" \
  -d '{"license_key": "LIC-XXX", "machine_id": "machine-123"}'
```

---

## 2. Verify License

Xác thực license định kỳ.

**Endpoint:** `POST /verify`

**Request:**
```json
{
    "license_key": "LIC-8F3A9C2D-7B41-4E9A-A1C7-92F6D3A5B8E1",
    "machine_id": "machine-hash-12345"
}
```

**Response:**
```json
{
    "valid": true
}
```

Hoặc nếu không hợp lệ:
```json
{
    "valid": false
}
```

**Example cURL:**
```bash
curl -X POST https://verify-api-ru8s.onrender.com/verify \
  -H "Content-Type: application/json" \
  -d '{"license_key": "LIC-XXX", "machine_id": "machine-123"}'
```

---

## Code Examples

### Python
```python
import requests

BASE_URL = "https://verify-api-ru8s.onrender.com"

# Activate
response = requests.post(
    f"{BASE_URL}/activate",
    json={"license_key": "LIC-XXX", "machine_id": "machine-123"}
)
print(response.json())  # {"status": "activated"}

# Verify
response = requests.post(
    f"{BASE_URL}/verify",
    json={"license_key": "LIC-XXX", "machine_id": "machine-123"}
)
result = response.json()
print(result["valid"])  # True hoặc False
```

### JavaScript
```javascript
const BASE_URL = "https://verify-api-ru8s.onrender.com";

// Activate
const activateResponse = await fetch(`${BASE_URL}/activate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        license_key: "LIC-XXX",
        machine_id: "machine-123"
    })
});
const activateData = await activateResponse.json();
console.log(activateData); // {status: "activated"}

// Verify
const verifyResponse = await fetch(`${BASE_URL}/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        license_key: "LIC-XXX",
        machine_id: "machine-123"
    })
});
const verifyData = await verifyResponse.json();
console.log(verifyData.valid); // true hoặc false
```

---

## Lưu ý

1. **Machine ID**: Tạo unique ID cho mỗi máy (có thể dùng MAC address, CPU ID, hoặc hash hardware info)

2. **Activate**: Chỉ gọi 1 lần khi user nhập license lần đầu

3. **Verify**: Gọi định kỳ (mỗi lần mở app, hoặc mỗi 24h)

4. **Cold Start**: API có thể mất ~50s để wake up nếu đã sleep (Render free tier). Nên retry nếu request đầu tiên fail.

---

## Test API

- Swagger UI: https://verify-api-ru8s.onrender.com/docs
- Health Check: https://verify-api-ru8s.onrender.com/health
