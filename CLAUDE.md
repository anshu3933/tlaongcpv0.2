# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
This is a **Retrieval-Augmented Generation (RAG) Model Control Panel (MCP) Backend** - a microservices-based system for document processing, vector storage, and AI-powered querying. The system uses FastAPI, PostgreSQL, ChromaDB, and Google Cloud AI services.

## Architecture
- **Microservices design** with service-oriented architecture
- **Repository pattern** for data access layer
- **Async/await** throughout for high performance
- **Database-per-service** pattern (PostgreSQL + ChromaDB)

## Core Services
- **auth_service/**: User authentication, sessions, audit logging (90% complete)
- **mcp_server/**: Main RAG control panel server (not implemented)
- **adk_host/**: API Development Kit host service (not implemented)
- **common/**: Shared utilities and vector store interfaces (structure only)

## Technology Stack
- **FastAPI** (0.104.1+) with Uvicorn ASGI server
- **PostgreSQL** with AsyncPG and SQLAlchemy 2.0 async ORM
- **ChromaDB** for vector embeddings storage
- **Alembic** for database migrations
- **Google Cloud AI Platform** with VertexAI and Gemini models
- **Redis** for caching and sessions
- **Docker** for containerization

## Development Commands

### Environment Setup
```bash
# Activate virtual environment
source backend/venv/bin/activate

# Install dependencies (when requirements.txt exists)
pip install -r backend/auth_service/requirements.txt
```

### Database Operations
```bash
# Run migrations for auth service
cd backend/auth_service
python scripts/run_migrations.py

# Generate new migration
alembic revision --autogenerate -m "migration_name"

# Apply migrations
alembic upgrade head
```

### Service Operations
```bash
# Services run on different ports (configured in .env):
# MCP_SERVER_PORT=8001
# ADK_HOST_PORT=8002  
# AUTH_SERVICE_PORT=8003

# Start auth service (when main.py exists)
cd backend/auth_service
uvicorn src.main:app --host 0.0.0.0 --port 8003 --reload
```

### Docker Operations
```bash
# Build auth service
docker build -f backend/auth_service/Dockerfile -t auth-service .

# Run with docker-compose (when compose file exists)
docker-compose up --build
```

## Database Schema Patterns

### Authentication Service (PostgreSQL)
- **users**: Core user management with role-based access
- **user_sessions**: JWT session management with expiration
- **audit_logs**: Comprehensive audit trail for all actions

All database operations use async patterns with proper transaction management and error handling.

## Configuration Management
- Environment variables configured in `.env` file
- Service ports, database URLs, AI model settings, and security keys
- Google Cloud AI configuration for Gemini 2.5 Flash and text-embedding-005 models

## Code Patterns

### Repository Pattern
```python
# All data access through repository classes
class UserRepository:
    async def create_user(self, user_data: UserCreate) -> User:
        # Async database operations with proper error handling
```

### Service Layer
```python
# Business logic in service classes with dependency injection
class AuthService:
    def __init__(self, user_repo: UserRepository, audit_repo: AuditRepository):
        # Services receive dependencies
```

### Migration Strategy
- Use Alembic for all schema changes
- Include both upgrade and downgrade methods
- Add proper indexes for performance (see 002_add_audit_log_indexes.py)

## Current Development Status
- **Authentication service**: Models, repositories, migrations complete; FastAPI app needed
- **Core services**: MCP server and ADK host require full implementation
- **Common library**: Package structure exists; vector store interface needed
- **Integration**: Service-to-service communication not implemented

## ChromaDB Integration
- Vector database located in `/chroma_db/`
- Used for document embeddings and similarity search
- Integration with common library vector store interface pending

## Security Considerations
- JWT-based authentication with secure session management
- Comprehensive audit logging for all user actions
- Password hashing with bcrypt
- Rate limiting configured (30 requests/60 seconds)
- No sensitive data in repository (configured via environment variables)