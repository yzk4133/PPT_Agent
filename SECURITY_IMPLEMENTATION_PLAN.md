# Authentication & Security Implementation Plan
## MultiAgentPPT Project

**Status**: Implementation Plan
**Created**: 2026-02-02
**Priority**: CRITICAL - System has no authentication and critical security vulnerabilities

---

## 📋 Executive Summary

The MultiAgentPPT system currently has **no authentication mechanism** and **critical security vulnerabilities**. All endpoints are publicly accessible, API keys are stored in plain text, and there is no input validation or rate limiting.

This plan implements enterprise-grade authentication and security in **4 phases** over 8-12 weeks.

### Risk Assessment
- **Current Risk Level**: 🔴 **CRITICAL**
- **Main Vulnerabilities**: No authentication, plain-text secrets, open endpoints
- **Potential Impact**: Unauthorized access, data breaches, API key theft, resource abuse

---

## 🎯 Implementation Phases

### Phase 1: Critical Security Foundation (Weeks 1-2)
**Goal**: Implement basic authentication and secure API key storage
**Impact**: Prevents unauthorized access to endpoints

### Phase 2: Input Security & Rate Limiting (Weeks 3-4)
**Goal**: Protect against injection attacks and abuse
**Impact**: Prevents DoS, injection attacks, resource exhaustion

### Phase 3: Advanced Security Features (Weeks 5-7)
**Goal**: JWT authentication, RBAC, audit logging
**Impact**: Enterprise-grade access control and compliance

### Phase 4: Security Hardening & Monitoring (Weeks 8-10)
**Goal**: Comprehensive security posture
**Impact**: Production-ready security with monitoring

---

## 📝 Phase 1: Critical Security Foundation

### Task 1.1: Implement API Key Authentication Middleware
**Priority**: 🔴 CRITICAL
**Estimated Time**: 3 days
**Dependencies**: None

**Description**:
Create a FastAPI dependency that validates API keys for all endpoints.

**Implementation Steps**:

1. **Create authentication module**
   - File: `backend/common/auth.py`
   - Implement `APIKeyHeader` security scheme
   - Create `get_api_key_dependency()` function

2. **Define API key storage structure**
   ```python
   # In database or config
   VALID_API_KEYS = {
       "admin": {"key": "sk-admin-...", "role": "admin", "scopes": ["all"]},
       "user": {"key": "sk-user-...", "role": "user", "scopes": ["ppt:read", "ppt:write"]}
   }
   ```

3. **Create authentication decorator**
   ```python
   from fastapi import Security, HTTPException, status
   from fastapi.security import APIKeyHeader

   api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

   async def verify_api_key(api_key: str = Security(api_key_header)):
       if not api_key or not validate_api_key(api_key):
           raise HTTPException(
               status_code=status.HTTP_401_UNAUTHORIZED,
               detail="Invalid or missing API key"
           )
       return api_key
   ```

4. **Apply to all endpoints**
   - Add `dependencies=[Depends(verify_api_key)]` to all routes
   - Update files:
     - `ppt_api/main_api.py`
     - `save_ppt/main_api.py`
     - `host_agent_api.py`
     - All other API files

**Acceptance Criteria**:
- [ ] All endpoints return 401 without valid API key
- [ ] Valid API key grants access
- [ ] API key format is validated (starts with `sk-`)
- [ ] Unit tests for authentication logic
- [ ] Integration tests for protected endpoints

**Files to Create**:
- `backend/common/auth.py` (new)
- `backend/common/__init__.py` (update exports)

**Files to Modify**:
- `backend/ppt_api/main_api.py`
- `backend/save_ppt/main_api.py`
- `backend/host_agent_api.py`
- All other `main_api.py` files

---

### Task 1.2: Secure API Key Storage with Encryption
**Priority**: 🔴 CRITICAL
**Estimated Time**: 4 days
**Dependencies**: None

**Description**:
Implement encrypted storage for LLM provider API keys using cryptography library.

**Implementation Steps**:

1. **Install dependencies**
   ```bash
   pip install cryptography python-dotencv
   ```

2. **Create encryption utility**
   - File: `backend/common/encryption.py`
   - Implement Fernet encryption for secrets
   - Use environment-derived encryption key

3. **Update config.py**
   ```python
   from common.encryption import decrypt_secret

   class Settings(BaseSettings):
       # Encrypted keys stored in .env
       DEEPSEEK_API_KEY_ENCRYPTED: str
       OPENAI_API_KEY_ENCRYPTED: str

       @property
       def DEEPSEEK_API_KEY(self):
           return decrypt_secret(self.DEEPSEEK_API_KEY_ENCRYPTED)
   ```

4. **Create secrets migration script**
   - Encrypt existing API keys
   - Update .env files with encrypted values
   - Add `.env.encrypted` to `.gitignore`

5. **Add encryption key management**
   - Use `ENCRYPTION_KEY` environment variable
   - Provide fallback to key file for development
   - Document key generation process

**Acceptance Criteria**:
- [ ] API keys are stored encrypted in .env files
- [ ] Decryption happens at runtime only
- [ ] Encryption key is separate from .env files
- [ ] Migration script successfully encrypts existing keys
- [ ] Documentation for key generation and rotation

**Files to Create**:
- `backend/common/encryption.py` (new)
- `scripts/migrate_secrets.py` (new)
- `docs/SECURITY_SETUP.md` (new)

**Files to Modify**:
- `backend/common/config.py`

---

### Task 1.3: Implement Environment-Specific Configuration
**Priority**: 🟡 HIGH
**Estimated Time**: 2 days
**Dependencies**: Task 1.2

**Description**:
Support different configuration profiles (development, staging, production).

**Implementation Steps**:

1. **Update config.py structure**
   ```python
   class Settings(BaseSettings):
       ENVIRONMENT: str = "development"  # development | staging | production

       class Config:
           env_file = f".env.{ENVIRONMENT}"
           env_file_encoding = "utf-8"
   ```

2. **Create environment files**
   - `.env.development` (local development)
   - `.env.staging` (staging environment)
   - `.env.production` (production - encrypted only)

3. **Add validation rules**
   - Production requires encrypted keys
   - Development can use plain text with warning
   - Staging requires SSL/TLS for databases

4. **Create environment detection**
   ```python
   def is_production() -> bool:
       return settings.ENVIRONMENT == "production"
   ```

**Acceptance Criteria**:
- [ ] Different configs for different environments
- [ ] Production rejects plain-text secrets
- [ ] Environment variables are clearly documented
- [ ] Configuration validation on startup

**Files to Create**:
- `.env.development` (template)
- `.env.staging` (template)
- `.env.production` (template)
- `docs/CONFIGURATION.md` (new)

**Files to Modify**:
- `backend/common/config.py`

---

### Task 1.4: Add Security Headers Middleware
**Priority**: 🟡 HIGH
**Estimated Time**: 1 day
**Dependencies**: None

**Description**:
Add security headers to all HTTP responses.

**Implementation Steps**:

1. **Create security middleware**
   - File: `backend/common/middleware.py`
   - Add headers: X-Content-Type-Options, X-Frame-Options, etc.

2. **Apply to all FastAPI apps**
   ```python
   from common.middleware import SecurityHeadersMiddleware

   app.add_middleware(SecurityHeadersMiddleware)
   ```

**Acceptance Criteria**:
- [ ] All responses include security headers
- [ ] Headers are configurable per environment
- [ ] Tests verify header presence

**Files to Create**:
- `backend/common/middleware.py` (new)

**Files to Modify**:
- All `main_api.py` files

---

## 📝 Phase 2: Input Security & Rate Limiting

### Task 2.1: Implement Input Validation for All Endpoints
**Priority**: 🔴 CRITICAL
**Estimated Time**: 5 days
**Dependencies**: None

**Description**:
Create Pydantic models for all request payloads and add validation.

**Implementation Steps**:

1. **Create shared validation models**
   - File: `backend/common/models.py`
   - Define base models with validation

2. **Create endpoint-specific models**
   ```python
   class OutlineRequest(BaseModel):
       topic: str = Field(..., min_length=1, max_length=500)
       slide_count: int = Field(..., ge=1, le=100)
       language: str = Field("en", regex="^(en|zh|es|fr|de)$")

       class Config:
           schema_extra = {
               "example": {
                   "topic": "Introduction to Machine Learning",
                   "slide_count": 10,
                   "language": "en"
               }
           }
   ```

3. **Add sanitization helpers**
   - HTML escape for user input
   - SQL injection prevention
   - XSS protection

4. **Update all endpoints**
   - Replace `request: dict` with Pydantic models
   - Add validation error handling

**Acceptance Criteria**:
- [ ] All endpoints use Pydantic models
- [ ] Input size limits enforced
- [ ] Invalid input returns 422 with clear errors
- [ ] Tests for validation logic
- [ ] Sanitization prevents XSS and SQL injection

**Files to Create**:
- `backend/common/models.py` (new)
- `backend/common/validators.py` (new)

**Files to Modify**:
- All API files with endpoints

---

### Task 2.2: Implement Rate Limiting
**Priority**: 🔴 CRITICAL
**Estimated Time**: 3 days
**Dependencies**: Task 1.1

**Description**:
Add rate limiting to prevent abuse and DoS attacks.

**Implementation Steps**:

1. **Create rate limiter**
   - File: `backend/common/rate_limit.py`
   - Use Redis for distributed rate limiting
   - Implement sliding window algorithm

2. **Configure rate limits**
   ```python
   RATE_LIMITS = {
       "default": "100/minute",
       "ppt:generate": "10/hour",
       "search": "30/minute",
   }
   ```

3. **Add rate limit middleware**
   ```python
   @app.post("/outline", dependencies=[Depends(rate_limit("ppt:generate"))])
   async def generate_outline(...):
       ...
   ```

4. **Add rate limit headers**
   - `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

**Acceptance Criteria**:
- [ ] Rate limits enforced per API key
- [ ] Rate limit headers in responses
- [ ] Tests for rate limiting
- [ ] Configuration per endpoint type

**Files to Create**:
- `backend/common/rate_limit.py` (new)

**Files to Modify**:
- All API files

---

### Task 2.3: Restrict CORS Configuration
**Priority**: 🟡 HIGH
**Estimated Time**: 1 day
**Dependencies**: Task 1.3

**Description**:
Restrict CORS to specific origins instead of wildcard.

**Implementation Steps**:

1. **Update CORS configuration**
   ```python
   ALLOWED_ORIGINS = {
       "development": ["http://localhost:3000", "http://localhost:8000"],
       "staging": ["https://staging.example.com"],
       "production": ["https://app.example.com"]
   }
   ```

2. **Apply to all apps**
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=settings.ALLOWED_ORIGINS,
       allow_credentials=True,
       allow_methods=["GET", "POST"],
       allow_headers=["Content-Type", "X-API-Key"],
   )
   ```

**Acceptance Criteria**:
- [ ] CORS restricted to specific origins
- [ ] Different origins per environment
- [ ] Credentials allowed for authenticated requests
- [ ] Tests verify CORS behavior

**Files to Modify**:
- All `main_api.py` files
- `backend/common/config.py`

---

### Task 2.4: Add Request Size Limits
**Priority**: 🟡 HIGH
**Estimated Time**: 1 day
**Dependencies**: None

**Description**:
Add middleware to limit request size and prevent DoS.

**Implementation Steps**:

1. **Create size limit middleware**
   ```python
   class RequestSizeMiddleware:
       def __init__(self, app, max_size: int = 10_000_000):  # 10MB
           self.app = app
           self.max_size = max_size
   ```

2. **Apply to all FastAPI apps**

**Acceptance Criteria**:
- [ ] Requests over limit rejected with 413
- [ ] Size limit configurable per environment
- [ ] Tests for size limits

**Files to Create**:
- `backend/common/middleware.py` (extend)

---

## 📝 Phase 3: Advanced Security Features

### Task 3.1: Implement JWT Authentication
**Priority**: 🟢 MEDIUM
**Estimated Time**: 5 days
**Dependencies**: Phase 1 complete

**Description**:
Add JWT-based authentication alongside API key authentication.

**Implementation Steps**:

1. **Install dependencies**
   ```bash
   pip install python-jose[cryptography] passlib[bcrypt]
   ```

2. **Create JWT auth module**
   - File: `backend/common/jwt_auth.py`
   - Implement token generation and validation
   - Add refresh token support

3. **Create user model**
   ```python
   class User(BaseModel):
       user_id: str
       email: EmailStr
       role: str
       scopes: List[str]
   ```

4. **Add authentication endpoints**
   - POST /auth/login
   - POST /auth/refresh
   - POST /auth/logout

5. **Create JWT dependency**
   ```python
   async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
       ...
   ```

**Acceptance Criteria**:
- [ ] JWT tokens generated on login
- [ ] Tokens validated on protected endpoints
- [ ] Refresh token flow works
- [ ] Tokens expire after configurable time
- [ ] Tests for JWT authentication

**Files to Create**:
- `backend/common/jwt_auth.py` (new)
- `backend/auth_api/main_api.py` (new)
- `backend/common/models.py` (extend)

**Files to Modify**:
- All API files (add JWT option)

---

### Task 3.2: Implement Role-Based Access Control (RBAC)
**Priority**: 🟢 MEDIUM
**Estimated Time**: 4 days
**Dependencies**: Task 3.1

**Description**:
Add role-based permissions for fine-grained access control.

**Implementation Steps**:

1. **Define roles and permissions**
   ```python
   ROLE_PERMISSIONS = {
       "admin": ["*"],
       "user": ["ppt:read", "ppt:write", "search:execute"],
       "viewer": ["ppt:read"]
   }
   ```

2. **Create authorization decorator**
   ```python
   def require_scope(*scopes):
       def dependency(user: User = Depends(get_current_user)):
           if not has_scope(user, scopes):
               raise HTTPException(status_code=403, detail="Insufficient permissions")
           return user
       return dependency
   ```

3. **Apply to endpoints**
   ```python
   @app.delete("/ppt/{id}", dependencies=[Depends(require_scope("ppt:delete"))])
   async def delete_ppt(id: str):
       ...
   ```

**Acceptance Criteria**:
- [ ] Roles have defined permissions
- [ ] Endpoints enforce required scopes
- [ ] Tests for authorization logic
- [ ] Admin role has full access

**Files to Create**:
- `backend/common/rbac.py` (new)

**Files to Modify**:
- All API files

---

### Task 3.3: Implement Audit Logging
**Priority**: 🟢 MEDIUM
**Estimated Time**: 3 days
**Dependencies**: Task 1.1

**Description**:
Log all security-relevant events for compliance and monitoring.

**Implementation Steps**:

1. **Create audit logger**
   - File: `backend/common/audit.py`
   - Structured logging format (JSON)

2. **Define audit events**
   ```python
   AUDIT_EVENTS = {
       "auth:success": "User authenticated successfully",
       "auth:failure": "Authentication failed",
       "ppt:created": "Presentation created",
       "ppt:deleted": "Presentation deleted",
   }
   ```

3. **Add audit middleware**
   ```python
   @app.post("/outline")
   async def generate_outline(...):
       audit_log("ppt:create", user_id=user.id, topic=topic)
       ...
   ```

4. **Store audit logs**
   - Write to separate audit log table
   - Include timestamp, user, action, result

**Acceptance Criteria**:
- [ ] All auth events logged
- [ ] All resource modifications logged
- [ ] Logs include user, action, timestamp
- [ ] Logs stored in database
- [ ] Query interface for logs

**Files to Create**:
- `backend/common/audit.py` (new)
- `backend/database/migrations/xxx_audit_logs.py` (new)

**Files to Modify**:
- All API files

---

### Task 3.4: Add Database Connection Encryption
**Priority**: 🟡 HIGH
**Estimated Time**: 2 days
**Dependencies**: Task 1.3

**Description**:
Enable SSL/TLS for database and Redis connections.

**Implementation Steps**:

1. **Update database URLs**
   ```python
   # Add ?sslmode=require to PostgreSQL URL
   DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{db}?sslmode=require"
   ```

2. **Update Redis connection**
   ```python
   redis_client = redis.Redis(
       host=settings.REDIS_HOST,
       password=settings.REDIS_PASSWORD,
       ssl=True,
       ssl_cert_reqs="required"
   )
   ```

3. **Add certificate validation**
   - Configure CA certificates
   - Validate certificates in production

4. **Add connection security tests**
   ```python
   def test_database_uses_ssl():
       assert "sslmode=require" in settings.DATABASE_URL
   ```

**Acceptance Criteria**:
- [ ] PostgreSQL uses SSL in production
- [ ] Redis uses SSL in production
- [ ] Certificates validated
- [ ] Fallback for development
- [ ] Tests verify SSL configuration

**Files to Modify**:
- `backend/common/config.py`
- `backend/database/database.py`
- `backend/common/redis_client.py`

---

## 📝 Phase 4: Security Hardening & Monitoring

### Task 4.1: Implement Secrets Rotation
**Priority**: 🟢 MEDIUM
**Estimated Time**: 3 days
**Dependencies**: Task 1.2

**Description**:
Add mechanism to rotate API keys and secrets.

**Implementation Steps**:

1. **Create key rotation utility**
   - File: `backend/common/rotation.py`
   - Support manual rotation triggers
   - Schedule automatic rotation

2. **Add versioned keys**
   ```python
   API_KEY_VERSIONS = {
       "openai": {"current": 2, "keys": {1: "...", 2: "..."}}
   }
   ```

3. **Implement grace period**
   - Old keys work for 24 hours after rotation
   - Monitor usage of old keys

4. **Create rotation endpoint**
   - POST /admin/rotate-keys (admin only)

**Acceptance Criteria**:
- [ ] Keys can be rotated without downtime
- [ ] Old keys work during grace period
- [ ] Rotation logged
- [ ] Tests for rotation logic

**Files to Create**:
- `backend/common/rotation.py` (new)

**Files to Modify**:
- `backend/common/config.py`

---

### Task 4.2: Add Security Monitoring and Alerting
**Priority**: 🟢 MEDIUM
**Estimated Time**: 4 days
**Dependencies**: Task 3.3

**Description**:
Monitor security events and send alerts for suspicious activity.

**Implementation Steps**:

1. **Define security alerts**
   ```python
   ALERT_RULES = {
       "brute_force": {"condition": "5 failed auth in 5 minutes"},
       "rate_limit": {"condition": "Rate limit exceeded 10 times"},
       "unusual_access": {"condition": "Access from new location"},
   }
   ```

2. **Create alert handler**
   - File: `backend/common/alerts.py`
   - Send alerts via email, Slack, PagerDuty

3. **Add metrics**
   - Failed auth attempts
   - Rate limit hits
   - Unusual patterns

4. **Create monitoring dashboard**
   - Security metrics overview
   - Recent alerts

**Acceptance Criteria**:
- [ ] Suspicious activity triggers alerts
- [ ] Alerts delivered to configured channels
- [ ] Dashboard shows security metrics
- [ ] Tests for alert logic

**Files to Create**:
- `backend/common/alerts.py` (new)
- `backend/monitoring/main_api.py` (new)

---

### Task 4.3: Implement API Key Scopes and Quotas
**Priority**: 🟢 MEDIUM
**Estimated Time**: 3 days
**Dependencies**: Task 3.2

**Description**:
Add fine-grained API key permissions and usage quotas.

**Implementation Steps**:

1. **Extend API key model**
   ```python
   class APIKey(BaseModel):
       key_id: str
       scopes: List[str]
       quota_limit: int  # requests per day
       quota_used: int
       quota_reset: datetime
   ```

2. **Implement quota tracking**
   - Track usage in Redis
   - Reset quotas daily

3. **Add quota exceeded handling**
   ```python
   if api_key.quota_used >= api_key.quota_limit:
       raise HTTPException(status_code=429, detail="Quota exceeded")
   ```

**Acceptance Criteria**:
- [ ] API keys have defined scopes
- [ ] Quotas enforced per key
- [ ] Quotas reset daily
- [ ] Tests for quota enforcement

**Files to Create**:
- `backend/common/quota.py` (new)

**Files to Modify**:
- `backend/common/auth.py`

---

### Task 4.4: Security Testing Suite
**Priority**: 🟡 HIGH
**Estimated Time**: 5 days
**Dependencies**: All previous tasks

**Description**:
Create comprehensive security tests.

**Implementation Steps**:

1. **Install security testing tools**
   ```bash
   pip install bandit pytest-security
   ```

2. **Create security test suite**
   - Authentication bypass tests
   - Authorization tests
   - Input validation tests
   - Rate limiting tests
   - SQL injection tests
   - XSS tests

3. **Add dependency scanning**
   ```bash
   pip safety check
   ```

4. **Run security tests in CI**
   - Add to GitHub Actions
   - Fail build on critical vulnerabilities

**Acceptance Criteria**:
- [ ] Comprehensive security test suite
- [ ] Tests run automatically in CI
- [ ] Vulnerabilities detected and reported
- [ ] Code coverage for security code

**Files to Create**:
- `tests/security/` (new directory)
- `.github/workflows/security-tests.yml` (new)

---

## 📊 Summary Table

| Phase | Tasks | Duration | Priority | Status |
|-------|-------|----------|----------|--------|
| Phase 1: Critical Foundation | 4 tasks | 2 weeks | CRITICAL | 🔴 Not Started |
| Phase 2: Input Security | 4 tasks | 2 weeks | HIGH | 🔴 Not Started |
| Phase 3: Advanced Features | 4 tasks | 3 weeks | MEDIUM | 🔴 Not Started |
| Phase 4: Hardening | 4 tasks | 3 weeks | MEDIUM-HIGH | 🔴 Not Started |

**Total Duration**: 10 weeks

---

## 🚀 Quick Start (Immediate Actions)

### Week 1: Critical Fixes
1. **Monday-Tuesday**: Implement Task 1.1 (API Key Auth)
2. **Wednesday-Friday**: Implement Task 1.2 (Encrypt Secrets)

### Week 2: Basic Security
1. **Monday-Tuesday**: Implement Task 1.3 (Environment Config)
2. **Wednesday**: Implement Task 1.4 (Security Headers)
3. **Thursday-Friday**: Implement Task 2.1 (Input Validation)

### Week 3: Protection
1. **Monday-Wednesday**: Implement Task 2.2 (Rate Limiting)
2. **Thursday**: Implement Task 2.3 (Restrict CORS)
3. **Friday**: Implement Task 2.4 (Request Size Limits)

---

## 📚 Documentation Requirements

### New Documentation Files
1. `docs/SECURITY_SETUP.md` - Setup and configuration
2. `docs/AUTHENTICATION.md` - Authentication guide
3. `docs/AUTHORIZATION.md` - Authorization and RBAC
4. `docs/API_SECURITY.md` - API security best practices
5. `docs/SECRETS_MANAGEMENT.md` - Secrets and encryption

### Code Documentation
- All security modules need docstrings
- Type hints for all security functions
- Examples in docstrings

---

## ✅ Success Metrics

### Phase 1 Success Criteria
- [ ] All endpoints require authentication
- [ ] No plain-text API keys in code
- [ ] Security headers present
- [ ] Environment-specific configs

### Phase 2 Success Criteria
- [ ] All input validated
- [ ] Rate limiting active
- [ ] CORS restricted
- [ ] Request size limited

### Phase 3 Success Criteria
- [ ] JWT authentication working
- [ ] RBAC enforced
- [ ] Audit logging active
- [ ] Database SSL enabled

### Phase 4 Success Criteria
- [ ] Secrets rotate automatically
- [ ] Security monitoring active
- [ ] API quotas enforced
- [ ] Security tests passing

---

## 🔐 Security Checklist

Before going to production, ensure:

- [ ] All endpoints have authentication
- [ ] All secrets encrypted
- [ ] Rate limiting enabled
- [ ] Input validation complete
- [ ] Security headers configured
- [ ] CORS restricted
- [ ] Database using SSL
- [ ] Audit logging enabled
- [ ] Security tests passing
- [ ] Monitoring configured
- [ ] Incident response plan documented
- [ ] Security review completed

---

## 📞 Support and Questions

For questions about this implementation plan, contact:
- **Security Lead**: [Assigned]
- **Engineering Team**: [team@company.com]

---

## 📄 Appendix

### A. File Structure After Implementation

```
backend/
├── common/
│   ├── auth.py              # Authentication logic
│   ├── jwt_auth.py          # JWT authentication
│   ├── rbac.py              # Role-based access control
│   ├── encryption.py        # Secret encryption
│   ├── rate_limit.py        # Rate limiting
│   ├── audit.py             # Audit logging
│   ├── alerts.py            # Security alerts
│   ├── quota.py             # API quotas
│   ├── rotation.py          # Secrets rotation
│   ├── middleware.py        # Security middleware
│   ├── models.py            # Shared models
│   └── validators.py        # Input validators
├── auth_api/
│   └── main_api.py          # Authentication endpoints
├── monitoring/
│   └── main_api.py          # Monitoring endpoints
├── database/
│   └── migrations/
│       └── xxx_audit_logs.py
└── tests/
    └── security/            # Security tests
```

### B. Environment Variables

```bash
# .env.production example
ENVIRONMENT=production
ENCRYPTION_KEY=<generate with python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">

# Encrypted API keys
DEEPSEEK_API_KEY_ENCRYPTED=<encrypted>
OPENAI_API_KEY_ENCRYPTED=<encrypted>

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require

# Redis
REDIS_HOST=redis.example.com
REDIS_PASSWORD=<encrypted>
REDIS_SSL=true

# JWT
JWT_SECRET_KEY=<generate strong secret>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# CORS
ALLOWED_ORIGINS=["https://app.example.com"]

# Rate limiting
REDIS_RATE_LIMIT_URL=redis://redis.example.com:6379
```

### C. Migration Script Example

```python
# scripts/migrate_secrets.py
from cryptography.fernet import Fernet
from common.encryption import encrypt_secret
import os

def migrate_env_file():
    with open('.env', 'r') as f:
        lines = f.readlines()

    encrypted_lines = []
    for line in lines:
        if line.startswith('API_KEY=') or '_API_KEY=' in line:
            key, value = line.split('=', 1)
            encrypted = encrypt_secret(value.strip())
            encrypted_lines.append(f'{key}_ENCRYPTED={encrypted}\n')
        else:
            encrypted_lines.append(line)

    with open('.env.encrypted', 'w') as f:
        f.writelines(encrypted_lines)

if __name__ == '__main__':
    migrate_env_file()
    print('Secrets migrated. Update your .env file to use .env.encrypted')
```

---

**End of Implementation Plan**
