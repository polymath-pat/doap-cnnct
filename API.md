# CNNCT API Reference

Base URL: `https://cnnct.metaciety.net/api` (production) or `http://localhost:8081` (local)

All endpoints return JSON. The frontend proxies requests through `/api/*` which strips the prefix before reaching the backend.

## Rate Limits

| Scope | Limit |
|-------|-------|
| Global default | 100/hour, 20/minute |
| `/dns/<domain>` | 10/minute |
| `/diag` | 5/minute |
| `/status` | 5/minute |
| `/healthz` | Exempt |

Rate limit state is stored in Valkey (production) or in-memory (local dev). Exceeding limits returns `429 Too Many Requests`.

---

## `GET /healthz`

Health check endpoint.

**Rate limit:** Exempt

**Response `200`**
```json
{
  "status": "healthy"
}
```

---

## `GET /cnnct`

Tests TCP connectivity to a host on port 443.

**Query parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `target` | string | Yes | IP address or domain to probe |

**Response `200`** (port open)
```json
{
  "target": "8.8.8.8",
  "tcp_443": true,
  "latency_ms": 12.34
}
```

**Response `200`** (port closed/unreachable)
```json
{
  "target": "192.168.1.1",
  "tcp_443": false,
  "latency_ms": null
}
```

**Response `400`** (missing target)
```json
{
  "error": "No target specified"
}
```

---

## `GET /dns/<domain>`

Resolves DNS A records for a domain.

**Path parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `domain` | string | Yes | Domain name to resolve |

**Response `200`**
```json
{
  "target": "example.com",
  "records": ["93.184.216.34"],
  "timestamp": 1706745600.123
}
```

**Response `400`**
```json
{
  "error": "The DNS query name does not exist: example.invalid."
}
```

---

## `GET /diag`

Performs an HTTP diagnostic on a URL — measures response time, download speed, status code, redirects, and content type.

**Query parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | string | Yes | URL to diagnose (auto-prepends `https://` if no scheme) |

**Response `200`**
```json
{
  "url": "https://example.com/",
  "http_code": 200,
  "method": "GET",
  "remote_ip": "93.184.216.34",
  "total_time_ms": 245.67,
  "speed_download_bps": 5324.12,
  "content_type": "text/html; charset=UTF-8",
  "redirects": 0
}
```

**Response `400`**
```json
{
  "error": "ConnectionError: ..."
}
```

---

## `GET /status`

Returns the health and stats of the backend rate-limiting store (Valkey/Redis).

**Response `200`** (Redis connected)
```json
{
  "backend": "redis",
  "connected": true,
  "latency_ms": 1.23,
  "version": "7.2.0",
  "uptime_seconds": 86400,
  "connected_clients": 3,
  "used_memory_human": "1.5M"
}
```

**Response `200`** (in-memory fallback, no Redis configured)
```json
{
  "backend": "memory",
  "connected": false,
  "message": "Using in-memory rate limiting (no Redis configured)"
}
```

**Response `503`** (Redis configured but unreachable)
```json
{
  "backend": "redis",
  "connected": false,
  "error": "Connection refused"
}
```
