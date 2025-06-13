# Authentication Service - Technical Specification

## Overview

The Authentication Service is a comprehensive microservice providing user authentication, session management, and audit logging capabilities for the RAG Model Control Panel (MCP) system. Built with FastAPI and PostgreSQL, it implements JWT-based authentication with role-based access control (RBAC) and comprehensive audit trails.

## Architecture

### System Design
- **Architecture Pattern**: Repository pattern with service layer
- **Framework**: FastAPI 0.104.1 with Uvicorn ASGI server
- **Database**: PostgreSQL with AsyncPG and SQLAlchemy 2.0 async ORM
- **Authentication**: JWT tokens with refresh token rotation
- **Security**: bcrypt password hashing, CORS protection, rate limiting
- **Logging**: Structured logging with audit trails

### Directory Structure
```
backend/auth_service/
├── Dockerfile                 # Container configuration
├── alembic.ini               # Database migration configuration
├── requirements.txt          # Python dependencies
├── scripts/
│   └── run_migrations.py     # Migration runner script
└── src/
    ├── config.py             # Application configuration
    ├── database.py           # Database connection and setup
    ├── dependencies.py       # FastAPI dependency injection
    ├── main.py              # FastAPI application entry point
    ├── schemas.py           # Pydantic data models
    ├── security.py          # Authentication and cryptography
    ├── migrations/          # Alembic database migrations
    ├── models/              # SQLAlchemy ORM models
    ├── repositories/        # Data access layer
    ├── routers/            # API route handlers
    └── services/           # Business logic layer
```

## Database Schema

### Core Tables

#### users
Primary user entity with authentication and profile data:
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,           -- User email (unique identifier)
    hashed_password VARCHAR NOT NULL,        -- bcrypt hashed password
    full_name VARCHAR,                       -- User display name
    role VARCHAR,                           -- User role (user, admin, superuser)
    is_active BOOLEAN DEFAULT TRUE,         -- Account status
    is_superuser BOOLEAN DEFAULT FALSE,     -- Superuser privileges
    last_login TIMESTAMP WITH TIME ZONE,    -- Last successful login
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX ix_users_email ON users(email);
CREATE INDEX ix_users_id ON users(id);
```

#### user_sessions
JWT refresh token session management:
```sql
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    token_hash VARCHAR UNIQUE NOT NULL,      -- SHA256 hash of refresh token
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX ix_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX ix_user_sessions_token_hash ON user_sessions(token_hash);
```

#### audit_logs
Comprehensive audit trail for all system actions:
```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR NOT NULL,            -- Type of entity (user, session, etc.)
    entity_id INTEGER NOT NULL,              -- ID of the affected entity
    action VARCHAR NOT NULL,                 -- Action performed (login, register, etc.)
    user_id INTEGER,                        -- User who performed the action
    user_role VARCHAR,                      -- Role of the user at time of action
    ip_address VARCHAR,                     -- Client IP address
    details JSON,                           -- Additional action details
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX ix_audit_logs_entity_type ON audit_logs(entity_type);
CREATE INDEX ix_audit_logs_entity_id ON audit_logs(entity_id);
CREATE INDEX ix_audit_logs_action ON audit_logs(action);
CREATE INDEX ix_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX ix_audit_logs_created_at ON audit_logs(created_at);
```

## API Endpoints

### Authentication Routes (`/auth`)

#### POST /auth/register
Register a new user account.
- **Input**: `UserCreate` (email, password, full_name, role)
- **Output**: `UserResponse`
- **Status**: 201 Created
- **Validation**: Password complexity requirements (8+ chars, uppercase, lowercase, digit)
- **Audit**: Logs user registration with IP address

#### POST /auth/login
Authenticate user and return JWT tokens.
- **Input**: `UserLogin` (email, password)
- **Output**: `Token` (access_token, refresh_token, expires_in)
- **Security**: Rate limited, failed attempts logged
- **Session**: Creates database session with refresh token hash
- **Audit**: Logs successful/failed login attempts

#### POST /auth/refresh
Refresh access token using refresh token.
- **Input**: `RefreshToken`
- **Output**: `Token` (new access_token, same refresh_token)
- **Validation**: Verifies refresh token in database and expiration
- **Cleanup**: Automatically removes expired sessions
- **Audit**: Logs token refresh events

#### POST /auth/logout
Invalidate all user sessions.
- **Authentication**: Requires valid JWT token
- **Action**: Deletes all user sessions from database
- **Output**: Success message
- **Audit**: Logs logout with session count

#### GET /auth/me
Get current user profile information.
- **Authentication**: Requires valid JWT token
- **Output**: `UserResponse` (current user data)

#### POST /auth/cleanup-sessions
Clean up expired sessions (internal endpoint).
- **Action**: Removes all expired sessions
- **Output**: Count of cleaned sessions

### User Management Routes (`/users`)

#### GET /users/
List all users (superuser only).
- **Authentication**: Requires superuser privileges
- **Output**: `List[UserResponse]`

#### GET /users/{user_id}
Get user by ID.
- **Authorization**: Users can view own profile, superusers can view any
- **Output**: `UserResponse`
- **Error**: 404 if user not found, 403 if insufficient permissions

#### PUT /users/{user_id}
Update user information.
- **Input**: `UserUpdate` (email, full_name, role, is_active)
- **Authorization**: Users can update own profile, superusers can update any
- **Audit**: Logs all profile changes

#### POST /users/{user_id}/change-password
Change user password.
- **Input**: `PasswordChange` (current_password, new_password)
- **Validation**: Verifies current password, enforces complexity rules
- **Security**: Invalidates all user sessions after password change
- **Audit**: Logs password changes

#### POST /users/{user_id}/deactivate
Deactivate user account (superuser only).
- **Authentication**: Requires superuser privileges
- **Action**: Sets `is_active = false`
- **Audit**: Logs account deactivation

#### POST /users/{user_id}/activate
Activate user account (superuser only).
- **Authentication**: Requires superuser privileges
- **Action**: Sets `is_active = true`
- **Audit**: Logs account activation

#### GET /users/role/{role}
Get users by role (superuser only).
- **Authentication**: Requires superuser privileges
- **Output**: `List[dict]` with user summaries

#### GET /users/{user_id}/audit-logs
Get audit logs for user.
- **Authorization**: Users can view own logs, superusers can view any
- **Parameters**: `limit` (default 100)
- **Output**: `List[AuditLogResponse]`

### System Routes

#### GET /health
Health check endpoint.
- **Output**: Service status, version, timestamp
- **Usage**: Load balancer health checks

#### GET /
Root endpoint with API information.
- **Output**: Service metadata and documentation links

## Data Models

### Core Entities

#### User Model
```python
class User(Base):
    id: int                              # Primary key
    email: str                           # Unique email address
    hashed_password: str                 # bcrypt hash
    full_name: Optional[str]             # Display name
    role: Optional[str]                  # User role
    is_active: bool = True               # Account status
    is_superuser: bool = False           # Admin privileges
    last_login: Optional[DateTime]       # Last login timestamp
    created_at: DateTime                 # Account creation
    updated_at: Optional[DateTime]       # Last profile update
    
    # Relationships
    sessions: List[UserSession]          # Active sessions
```

#### UserSession Model
```python
class UserSession(Base):
    id: int                              # Primary key
    user_id: int                         # Foreign key to users
    token_hash: str                      # SHA256 hash of refresh token
    expires_at: DateTime                 # Session expiration
    created_at: DateTime                 # Session creation
    
    # Relationships
    user: User                           # Session owner
```

#### AuditLog Model
```python
class AuditLog(Base):
    id: int                              # Primary key
    entity_type: str                     # Type of entity affected
    entity_id: int                       # ID of affected entity
    action: str                          # Action performed
    user_id: Optional[int]               # User who performed action
    user_role: Optional[str]             # User role at time of action
    ip_address: Optional[str]            # Client IP address
    details: Optional[dict]              # Additional JSON details
    created_at: DateTime                 # Timestamp of action
```

### API Schemas

#### Request Schemas
- **UserCreate**: Registration data with password validation
- **UserLogin**: Email and password for authentication
- **UserUpdate**: Partial user data for profile updates
- **PasswordChange**: Current and new password for changes
- **RefreshToken**: Refresh token for token renewal

#### Response Schemas
- **UserResponse**: User data without sensitive information
- **Token**: JWT tokens with expiration and type
- **AuditLogResponse**: Audit log entry with metadata

## Security Implementation

### Password Security
- **Hashing**: bcrypt with automatic salt generation
- **Complexity**: Minimum 8 characters, uppercase, lowercase, digit required
- **Validation**: Server-side validation with detailed error messages

### JWT Token Management
- **Access Tokens**: Short-lived (60 minutes default), contain user ID, email, role
- **Refresh Tokens**: Long-lived (7 days default), stored as hashes in database
- **Algorithm**: HS256 (HMAC SHA-256)
- **Claims**: Standard JWT claims plus custom user data

### Session Security
- **Token Storage**: Only hashed refresh tokens stored in database
- **Expiration**: Automatic cleanup of expired sessions
- **Rotation**: New access tokens generated on refresh
- **Invalidation**: All sessions cleared on logout/password change

### Access Control
- **Authentication**: Bearer token validation for protected endpoints
- **Authorization**: Role-based access control (user, admin, superuser)
- **Permissions**: Users can access own data, superusers can access all

## Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db

# JWT Configuration
JWT_SECRET=<secure-random-string>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS Settings
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Rate Limiting
RATE_LIMIT_REQUESTS=30
RATE_LIMIT_PERIOD=60

# Logging
LOG_LEVEL=INFO
```

### Application Settings
Managed through `Settings` class with environment variable support:
- Database connection configuration
- JWT secret and algorithm settings
- Token expiration periods
- CORS allowed origins
- Rate limiting parameters
- Logging configuration

## Repository Pattern

### UserRepository
Data access layer for user operations:
- **CRUD Operations**: Create, read, update, delete users
- **Authentication**: Email lookup and password verification
- **Session Management**: Create, validate, and cleanup sessions
- **Query Methods**: Find by email, role, activity status
- **Transaction Management**: Proper rollback on errors

### AuditRepository
Comprehensive audit logging:
- **Log Actions**: Record all significant user actions
- **Query Methods**: Get logs by entity, user, or time period
- **Performance**: Optimized with database indexes
- **Retention**: Configurable log retention policies

## Service Layer

### AuthService
Core authentication business logic:
- **Registration**: User creation with validation and audit logging
- **Authentication**: Login verification with session management
- **Token Management**: Access and refresh token lifecycle
- **Session Control**: Login, logout, and session cleanup
- **Audit Integration**: Comprehensive action logging

### UserService
User management operations:
- **Profile Management**: User data updates and validation
- **Account Control**: Activation, deactivation, role changes
- **Password Management**: Secure password changes with session invalidation
- **Query Operations**: User searches and filtering

## Middleware and Error Handling

### Request Middleware
- **CORS**: Cross-origin request handling
- **Logging**: Structured request/response logging
- **Security**: Trusted host validation in production
- **Performance**: Request timing and metrics

### Exception Handling
- **HTTP Exceptions**: Structured error responses with appropriate status codes
- **General Exceptions**: Safe error handling with detailed logging
- **Validation Errors**: Clear field-level validation messages
- **Database Errors**: Transaction rollback and error recovery

## Deployment

### Docker Configuration
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8003"]
```

### Database Migrations
Managed with Alembic:
- **Versioning**: Sequential migration versioning
- **Rollback**: Safe downgrade procedures
- **Indexes**: Performance optimization migrations
- **Data Migration**: Safe data transformation procedures

### Health Monitoring
- **Health Endpoint**: `/health` for load balancer checks
- **Metrics**: Request timing and error rates
- **Logging**: Structured JSON logs for aggregation
- **Monitoring**: Database connection and performance metrics

## Testing Strategy

### Unit Tests
- **Repositories**: Database operation testing
- **Services**: Business logic validation
- **Security**: Password hashing and JWT validation
- **Schemas**: Data validation and serialization

### Integration Tests
- **API Endpoints**: Full request/response testing
- **Authentication**: Token-based access control
- **Database**: Transaction and rollback testing
- **Error Handling**: Exception and edge case testing

## Performance Considerations

### Database Optimization
- **Indexes**: Strategic indexing for query performance
- **Connection Pooling**: Async connection management
- **Query Optimization**: Efficient data access patterns
- **Session Management**: Cleanup of expired sessions

### Caching Strategy
- **Token Validation**: In-memory JWT verification
- **User Data**: Repository-level caching potential
- **Session Data**: Redis integration for session storage

### Scalability
- **Stateless Design**: JWT tokens enable horizontal scaling
- **Database Separation**: Dedicated auth database
- **Microservice Architecture**: Independent scaling capability
- **Load Balancing**: Health check endpoint support

## Security Audit

### Authentication Security
- ✅ Password complexity requirements
- ✅ bcrypt hashing with automatic salts
- ✅ JWT token expiration and rotation
- ✅ Refresh token database validation
- ✅ Session invalidation on logout

### Authorization Security
- ✅ Role-based access control
- ✅ Token-based authentication
- ✅ User isolation (own data access)
- ✅ Superuser privilege separation
- ✅ IP address logging

### Data Security
- ✅ No plaintext password storage
- ✅ Token hashing in database
- ✅ Comprehensive audit trails
- ✅ Input validation and sanitization
- ✅ SQL injection prevention (ORM)

## Integration Points

### Internal Services
- **MCP Server**: User authentication validation
- **ADK Host**: API access token verification
- **Common Library**: Shared utilities and interfaces

### External Dependencies
- **PostgreSQL**: Primary data storage
- **Redis**: Session caching (future)
- **Load Balancer**: Health check integration
- **Monitoring System**: Structured log ingestion

## Version History

### v1.0.0 (Current)
- Complete authentication and user management
- JWT token implementation
- Comprehensive audit logging
- Role-based access control
- Database migration system
- Docker containerization
- Structured logging
- Health monitoring

### Planned Features
- OAuth2 integration
- Multi-factor authentication
- Advanced rate limiting
- Session analytics
- User activity dashboards