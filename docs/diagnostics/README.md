# System Diagnostics and Configuration

## System Overview

This is a microservices-based backend system with the following components:

### Core Services
1. **Auth Service** (`backend/auth_service/`)
   - Handles user authentication and session management
   - Uses SQLAlchemy for database operations
   - Implements Alembic for database migrations

2. **MCP Server** (`backend/mcp_server/`)
   - Main Control Panel server
   - Handles core business logic

3. **ADK Host** (`backend/adk_host/`)
   - API Development Kit host service
   - Provides API endpoints for client applications

4. **Common Library** (`backend/common/`)
   - Shared utilities and components
   - Vector store implementations
   - Document processing utilities

### Database Components
- **ChromaDB** (`chroma_db/`)
  - Vector database for document storage and retrieval
  - Currently in development state

## Working Components

### Authentication System
- ✅ User session management
- ✅ Database migrations setup
- ✅ Basic authentication flow
- ✅ Audit logging system

### Common Library
- ✅ Vector store interface
- ✅ Document processing utilities
- ✅ Configuration management

### Development Environment
- ✅ Python virtual environment setup
- ✅ Git repository configuration
- ✅ Basic project structure

## Known Issues and Limitations

### Authentication Service
- ⚠️ Session management needs testing
- ⚠️ Audit logging implementation incomplete
- ⚠️ Missing comprehensive error handling

### MCP Server
- ❌ Core functionality not implemented
- ❌ Missing API endpoints
- ❌ No integration tests

### ADK Host
- ❌ API endpoints not implemented
- ❌ Missing authentication middleware
- ❌ No documentation

### Common Library
- ⚠️ Vector store implementation incomplete
- ⚠️ Missing comprehensive error handling
- ⚠️ Limited test coverage

### Database
- ⚠️ ChromaDB integration needs testing
- ⚠️ Migration scripts need validation
- ⚠️ Backup strategy not implemented

## System Configuration

### Environment Requirements
- Python 3.11+
- PostgreSQL (for auth service)
- ChromaDB
- Docker (for containerization)

### Dependencies
- FastAPI
- SQLAlchemy
- Alembic
- ChromaDB
- Pydantic
- Uvicorn

## Development Status

### Completed Tasks
1. Basic project structure
2. Authentication service setup
3. Database migration framework
4. Common library foundation
5. Development environment configuration

### In Progress
1. Vector store implementation
2. Document processing system
3. API endpoint development
4. Testing framework

### Pending Tasks
1. Complete MCP server implementation
2. Implement ADK host endpoints
3. Add comprehensive testing
4. Documentation
5. Deployment configuration

## Code Map

```
backend/
├── auth_service/           # Authentication service
│   ├── src/
│   │   ├── models/        # Database models
│   │   ├── migrations/    # Database migrations
│   │   └── repositories/  # Data access layer
│   └── scripts/           # Utility scripts
├── common/                # Shared library
│   └── src/
│       ├── config/        # Configuration
│       ├── vector_store/  # Vector database interface
│       └── document_processor.py
├── mcp_server/           # Main Control Panel
│   └── src/
│       └── main.py
├── adk_host/            # API Development Kit
│   └── src/
│       └── main.py
└── tests/               # Test suite
    └── auth_service/    # Auth service tests
```

## Code Relationships and Dependencies

### Service Dependencies
1. **Auth Service Dependencies**
   - Depends on `common` library for:
     - Configuration management
     - Database connection utilities
     - Logging utilities
   - External dependencies:
     - SQLAlchemy for ORM
     - Alembic for migrations
     - FastAPI for API endpoints
     - Pydantic for data validation

2. **MCP Server Dependencies**
   - Depends on `common` library for:
     - Vector store interface
     - Document processing
     - Configuration management
   - Depends on `auth_service` for:
     - User authentication
     - Session management
   - External dependencies:
     - FastAPI for API endpoints
     - ChromaDB for vector storage
     - Pydantic for data validation

3. **ADK Host Dependencies**
   - Depends on `common` library for:
     - Configuration management
     - Vector store interface
   - Depends on `auth_service` for:
     - Authentication middleware
     - User session validation
   - External dependencies:
     - FastAPI for API endpoints
     - Pydantic for data validation

### Data Flow Patterns

1. **Authentication Flow**
   ```
   Client Request → ADK Host → Auth Service → Database
   Response ← Auth Service ← ADK Host ← Client
   ```

2. **Document Processing Flow**
   ```
   Document → MCP Server → Document Processor → Vector Store
   Query → MCP Server → Vector Store → Response
   ```

3. **API Request Flow**
   ```
   Client → ADK Host → Auth Middleware → Service Layer → Database/Vector Store
   Response ← Service Layer ← ADK Host ← Client
   ```

### Key Interfaces

1. **Vector Store Interface** (`common/src/vector_store/`)
   ```python
   class VectorStore:
       async def add_documents(self, documents: List[Document]) -> None
       async def search(self, query: str, limit: int) -> List[Document]
       async def delete_documents(self, document_ids: List[str]) -> None
   ```

2. **Document Processor Interface** (`common/src/document_processor.py`)
   ```python
   class DocumentProcessor:
       async def process_document(self, document: Document) -> ProcessedDocument
       async def extract_metadata(self, document: Document) -> Dict[str, Any]
   ```

3. **Auth Service Interface** (`auth_service/src/`)
   ```python
   class AuthService:
       async def authenticate_user(self, credentials: UserCredentials) -> UserSession
       async def validate_session(self, session_id: str) -> bool
       async def create_audit_log(self, event: AuditEvent) -> None
   ```

### Database Schema Relationships

1. **User Management**
   ```
   User
   ├── id: UUID (PK)
   ├── email: String
   ├── password_hash: String
   └── sessions: UserSession[]
   ```

2. **Session Management**
   ```
   UserSession
   ├── id: UUID (PK)
   ├── user_id: UUID (FK)
   ├── token: String
   └── expires_at: DateTime
   ```

3. **Audit Logging**
   ```
   AuditLog
   ├── id: UUID (PK)
   ├── user_id: UUID (FK)
   ├── event_type: String
   └── timestamp: DateTime
   ```

### Configuration Management

1. **Environment Variables**
   ```
   AUTH_DB_URL=postgresql://user:pass@localhost:5432/auth_db
   CHROMA_DB_PATH=./chroma_db
   JWT_SECRET=your-secret-key
   ```

2. **Service Configuration**
   ```python
   class ServiceConfig:
       database_url: str
       vector_store_path: str
       jwt_secret: str
       log_level: str
   ```

### Error Handling Patterns

1. **Service Layer Errors**
   ```python
   class ServiceError(Exception):
       def __init__(self, message: str, error_code: str):
           self.message = message
           self.error_code = error_code
   ```

2. **API Error Responses**
   ```python
   class APIError(BaseModel):
       error_code: str
       message: str
       details: Optional[Dict[str, Any]]
   ```

### Testing Strategy

1. **Unit Tests**
   - Test individual components in isolation
   - Mock external dependencies
   - Focus on business logic

2. **Integration Tests**
   - Test service interactions
   - Use test databases
   - Verify data flow

3. **End-to-End Tests**
   - Test complete user flows
   - Use test environment
   - Verify system behavior

## Next Steps

1. **Immediate Priorities**
   - Complete authentication service implementation
   - Implement basic MCP server functionality
   - Add comprehensive testing

2. **Short-term Goals**
   - Complete vector store implementation
   - Implement ADK host endpoints
   - Add API documentation

3. **Long-term Goals**
   - Implement full document processing pipeline
   - Add monitoring and logging
   - Set up CI/CD pipeline

## Notes

- The system is currently in early development
- Focus is on core functionality and stability
- Documentation and testing need improvement
- Deployment strategy needs to be defined 