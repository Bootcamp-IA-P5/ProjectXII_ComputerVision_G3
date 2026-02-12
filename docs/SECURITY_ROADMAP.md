# 🔐 API Security Implementation Roadmap

This document outlines the security gaps identified in the current API implementation and provides a roadmap for addressing them before production deployment.

## Current Security Status

| Area | Status | Risk Level |
|------|--------|------------|
| Authentication | ❌ None | 🔴 High |
| Authorization | ❌ None | 🔴 High |
| Rate Limiting | ❌ None | 🟡 Medium |
| CORS | ⚠️ Permissive | 🟡 Medium |
| Input Validation | ✅ Basic (Pydantic) | 🟢 Low |
| HTTPS | ⚠️ Depends on deployment | 🟡 Medium |

---

## 1. Authentication (Priority: High)

### Current State
The API has no authentication - anyone can upload videos and access results.

### Recommended Implementation
Use **JWT (JSON Web Tokens)** for stateless authentication:

```python
# Example implementation with python-jose
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=["HS256"]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

# Apply to routes
@app.post("/upload")
async def upload_video(
    file: UploadFile,
    user: dict = Depends(verify_token)
):
    ...
```

### Dependencies to Add
```
# requirements.txt
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

### Environment Variables
```env
JWT_SECRET_KEY=your-super-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60
```

---

## 2. Authorization (Priority: High)

### Current State
No role-based access control. All users have equal access.

### Recommended Implementation
Implement role-based access control (RBAC):

```python
from enum import Enum

class UserRole(str, Enum):
    VIEWER = "viewer"      # Can view results
    UPLOADER = "uploader"  # Can upload and view
    ADMIN = "admin"        # Full access

def require_role(allowed_roles: list[UserRole]):
    async def role_checker(user: dict = Depends(verify_token)):
        if user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return user
    return role_checker

# Apply to routes
@app.delete("/videos/{video_id}")
async def delete_video(
    video_id: int,
    user: dict = Depends(require_role([UserRole.ADMIN]))
):
    ...
```

---

## 3. Rate Limiting (Priority: Medium)

### Current State
No rate limiting - API is vulnerable to abuse and DoS attacks.

### Recommended Implementation
Use **slowapi** for rate limiting:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/upload")
@limiter.limit("5/minute")  # 5 uploads per minute per IP
async def upload_video(request: Request, file: UploadFile):
    ...

@app.get("/videos")
@limiter.limit("100/minute")  # 100 requests per minute per IP
async def list_videos(request: Request):
    ...
```

### Dependencies to Add
```
# requirements.txt
slowapi==0.1.9
```

---

## 4. CORS Configuration (Priority: Medium)

### Current State
```python
# Current permissive configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # Too permissive
    allow_headers=["*"],  # Too permissive
)
```

### Recommended Fix
Restrict to specific methods and headers:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Keep configurable via env
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],  # Only what's needed
    allow_headers=["Authorization", "Content-Type"],  # Only what's needed
)
```

---

## 5. File Upload Security (Priority: Medium)

### Current State
Basic file validation, but missing:
- File size limits
- Content type verification
- Virus scanning

### Recommended Implementation

```python
from fastapi import UploadFile, HTTPException
import magic  # python-magic for content type detection

MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB

async def validate_video_file(file: UploadFile):
    # Check file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)} MB"
        )
    
    # Verify content type using magic bytes
    mime = magic.from_buffer(contents[:2048], mime=True)
    allowed_mimes = ["video/mp4", "video/avi", "video/quicktime"]
    if mime not in allowed_mimes:
        raise HTTPException(
            status_code=415,
            detail=f"Invalid file type: {mime}"
        )
    
    # Reset file position
    await file.seek(0)
    return contents
```

### Dependencies to Add
```
# requirements.txt
python-magic==0.4.27
```

---

## 6. HTTPS (Priority: High for Production)

### Recommendation
Always use HTTPS in production. Options:

1. **Reverse Proxy (Recommended)**: Use nginx or Traefik in front of FastAPI
2. **Cloud Load Balancer**: AWS ALB, GCP Load Balancer handle SSL termination
3. **Direct SSL**: Configure uvicorn with SSL certificates

```yaml
# docker-compose.production.yml
services:
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
    ports:
      - "443:443"
      - "80:80"
    depends_on:
      - api
```

---

## Implementation Timeline

| Phase | Items | Estimated Effort |
|-------|-------|-----------------|
| **Phase 1** | JWT Authentication, CORS Hardening | 1-2 days |
| **Phase 2** | Rate Limiting, File Validation | 1 day |
| **Phase 3** | Authorization (RBAC) | 1-2 days |
| **Phase 4** | HTTPS + Security Headers | 1 day |

---

## Security Headers Checklist

Add these headers via middleware for production:

```python
from fastapi import Request

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

---

## References

- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [OWASP API Security Top 10](https://owasp.org/API-Security/)
- [JWT Best Practices](https://auth0.com/blog/jwt-security-best-practices/)
