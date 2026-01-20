# AES Key Caching Implementation

## Overview
Successfully implemented AES key caching with automatic expiration and refresh for the EFRIS API client. This prevents unnecessary calls to T104 key exchange endpoint and improves efficiency.

## Changes Made

### 1. Added Expiration Tracking
**File:** `efris_client.py`

Added instance variables to track key expiration:
```python
self.aes_key = None  # The 16-byte AES key from T104
self.server_sign = None  # Server signature from T104
self.aes_key_expires_at = None  # Timestamp when key expires
self.key_expiry_hours = 24  # Configurable expiration (default: 24 hours)
```

### 2. Updated _key_exchange() Method
Modified to set expiration timestamp after successful key retrieval:
```python
# After obtaining AES key
self.aes_key_expires_at = datetime.now() + timedelta(hours=self.key_expiry_hours)
print(f"       - Key expires at: {self.aes_key_expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
```

### 3. Added is_key_valid() Helper Method
New method to check if cached key is still valid:
```python
def is_key_valid(self):
    """Check if the current AES key is still valid (exists and not expired)"""
    if not hasattr(self, 'aes_key') or not self.aes_key:
        return False
    if not hasattr(self, 'aes_key_expires_at') or not self.aes_key_expires_at:
        return False
    return datetime.now() < self.aes_key_expires_at
```

### 4. Updated ensure_authenticated() Method
Modified to check key validity and auto-refresh if expired:
```python
def ensure_authenticated(self):
    """Ensure a valid AES key is available, refreshing if necessary
    
    Checks if we have a valid (non-expired) AES key.
    If not, performs the full handshake (T101 -> T104 -> T103).
    """
    if not self.is_key_valid():
        self._perform_handshake()
    else:
        time_remaining = self.aes_key_expires_at - datetime.now()
        print(f"[AUTH] Using cached AES key (expires in {time_remaining.total_seconds()/3600:.1f} hours)")
```

### 5. Integrated with API Methods
Added `ensure_authenticated()` call in:
- `_build_request_payload()` - Called before building any API request
- `_encrypt_aes()` - Ensures key is valid before encryption

## How It Works

### First API Call:
1. Client calls `get_registration_details()` or any API method
2. `_build_request_payload()` calls `ensure_authenticated()`
3. `is_key_valid()` returns `False` (no key yet)
4. Performs full handshake: T101 (time sync) → T104 (key exchange) → T103 (get parameters)
5. T104 returns 16-byte AES key
6. Sets `aes_key_expires_at` to 24 hours from now
7. API request proceeds with encrypted data

### Subsequent API Calls (within 24 hours):
1. Client calls any API method
2. `_build_request_payload()` calls `ensure_authenticated()`
3. `is_key_valid()` returns `True` (key exists and not expired)
4. Skips handshake - uses cached key
5. Logs: `[AUTH] Using cached AES key (expires in XX hours)`
6. API request proceeds immediately

### After Expiration:
1. Client calls API method
2. `ensure_authenticated()` checks `is_key_valid()`
3. Returns `False` because current time > expiration time
4. Automatically performs new handshake
5. Gets fresh AES key with new 24-hour expiration
6. Continues with API request

## Benefits

1. **Efficiency**: Avoids redundant T104 calls (which involve RSA encryption/decryption)
2. **Performance**: Faster API calls after initial handshake
3. **Best Practice**: Aligns with EFRIS specification (call T104 once, cache key)
4. **Auto-Refresh**: Transparently handles expired keys
5. **Configurable**: Can adjust expiration time via `key_expiry_hours`

## Testing

Created `test_caching_demo.py` to verify:
- First call performs handshake
- Subsequent calls use cached key
- Key expiration triggers automatic refresh
- Short expiry test (3 seconds) works correctly

## Configuration

To change key expiry time:
```python
client = EfrisManager(tin='1015264035', test_mode=True)
client.key_expiry_hours = 12  # Expire after 12 hours instead of 24
```

To force key refresh:
```python
client.aes_key = None
client.aes_key_expires_at = None
client.ensure_authenticated()  # Will get fresh key
```

## Production Recommendations

1. Keep default 24-hour expiration (EFRIS best practice)
2. Monitor key refresh frequency in logs
3. Consider persisting key to disk for process restarts (advanced)
4. Add alerting if handshake fails repeatedly

## API Endpoints Using Cached Key

All API methods now benefit from caching:
- `get_registration_details()` (T103)
- `get_goods_and_services()` (T123)
- `query_taxpayer_by_tin()` (T119)
- `generate_invoice()` and other methods
- Any method using `_build_request_payload()`

## Notes

- Key is stored in memory only (lost on restart)
- First call after restart will always perform handshake
- Each EfrisManager instance has its own cache
- Thread-safe for single-threaded applications (add locking for multi-threaded use)
