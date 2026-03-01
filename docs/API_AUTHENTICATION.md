# API Authentication Documentation

## Overview

The RANGEN API implements a secure authentication system using API keys and JWT tokens to protect access to sensitive endpoints.

## Authentication Methods

### 1. API Key Authentication

API keys are the primary method for authenticating with the RANGEN API.

#### Format
```
Authorization: Bearer rang_<random_string>
```

#### Example
```bash
curl -H "Authorization: Bearer rang_abc123def456..." \
     -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -d '{"query": "test query"}'
```

### 2. JWT Token Authentication

JWT tokens can be used for session-based authentication.

#### Format
```
Authorization: Bearer <jwt_token>
```

## Environment Variables

Configure authentication using these environment variables:

```bash
# Secret key for signing JWT tokens (auto-generated if not set)
RANGEN_SECRET_KEY=your-secret-key-here

# Default API key for initial access
RANGEN_API_KEY=rang_your-default-api-key
```

## Endpoint Protection Levels

### Public Endpoints (No Authentication)
- `GET /health` - Basic health check

### Read Permission Required
- `GET /health/auth` - Authenticated health check
- `GET /auth/info` - Get current authentication info

### Write Permission Required
- `POST /chat` - Submit queries to the agent system

### Admin Permission Required
- `GET /diag` - System diagnostic information
- `POST /auth/api-key` - Create new API keys

## Creating API Keys

### Using Environment Variable

Set a default API key via environment:
```bash
export RANGEN_API_KEY=rang_$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
```

### Using API Endpoint

Create new API keys using the admin endpoint:

```bash
curl -X POST http://localhost:8000/auth/api-key \
     -H "Authorization: Bearer rang_admin_key" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "my-app",
       "permissions": "read,write"
     }'
```

Response:
```json
{
  "api_key": "rang_new_generated_key",
  "name": "my-app",
  "permissions": ["read", "write"],
  "message": "API key created successfully"
}
```

## Permission Levels

- **read**: Access to read-only endpoints and health checks
- **write**: Access to chat and other modifying endpoints  
- **admin**: Full system access including key management and diagnostics

## Security Features

### API Key Security
- API keys are hashed using SHA-256 for storage
- Keys should be treated like passwords
- Regular key rotation is recommended

### HTTP Security Headers
All responses include security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`

### Error Handling
- 401 Unauthorized: Missing or invalid authentication
- 403 Forbidden: Insufficient permissions
- 500 Internal Server Error: Server-side authentication errors

## Testing Authentication

The test suite includes comprehensive authentication tests:

```bash
# Run authentication tests
pytest tests/test_api_auth.py -v
```

## Migration from Insecure Version

If upgrading from an insecure version:

1. Set `RANGEN_API_KEY` environment variable
2. Update client applications to include Authorization header
3. Test all API calls with authentication
4. Remove or disable any unprotected diagnostic endpoints

## Troubleshooting

### Common Issues

1. **401 Unauthorized**
   - Check API key format (must start with `rang_`)
   - Verify `RANGEN_API_KEY` is set correctly
   - Ensure Authorization header is properly formatted

2. **403 Forbidden**
   - Check API key permissions
   - Verify endpoint permission requirements

3. **500 Internal Server Error**
   - Check server logs for authentication errors
   - Verify `RANGEN_SECRET_KEY` is not empty

### Debug Mode

For debugging, you can temporarily disable authentication (NOT RECOMMENDED FOR PRODUCTION):

```python
# In src/api/server.py, comment out auth dependencies:
# auth_data: dict = Depends(require_write)
# Replace with:
# auth_data = {"name": "debug", "permissions": ["read", "write"]}
```

Remember to re-enable authentication before deploying to production.