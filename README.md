# StrataAI

[![Production Ready](https://img.shields.io/badge/status-production%20ready-green.svg)]
[![Backend](https://img.shields.io/badge/backend-FastAPI-009688.svg)]
[![Frontend](https://img.shields.io/badge/frontend-React%2018-61dafb.svg)]
[![Database](https://img.shields.io/badge/database-Supabase-3ecf8e.svg)]
[![API](https://img.shields.io/badge/API-OpenAI%20Compatible-412991.svg)]

A production-ready unified API gateway platform that provides developers with a single interface to access multiple AI providers (OpenAI, Anthropic, etc.) while offering comprehensive observability, usage monitoring, cost tracking, and an interactive playground for testing and development.

## Features

### Core Platform
- **Unified API Gateway**: OpenAI-compatible single endpoint for multiple AI providers
- **Personal Access Tokens (PAT)**: Secure API authentication with organization scoping
- **Multi-tenant Organizations**: Complete organization management with role-based access control
- **Encrypted API Key Storage**: Fernet-encrypted provider API keys with validation
- **Real-time Usage Tracking**: Token consumption, cost calculation, and analytics

### Interactive Playground
- **Advanced Model Configuration**: Temperature, max tokens, streaming with user preferences
- **Session Management**: Automatic session creation with provider-based separation
- **Regenerate Functionality**: Parameter override system with 5-tier precedence
- **Usage Analytics**: Session-level cost tracking and breakdown by provider/model
- **Provider Preflight**: Key validation with user-friendly error messages

### Management & Observability
- **Provider Management**: API key configuration with model enablement controls
- **User Management**: Complete CRUD operations with invite system and role management
- **Real-time Dashboard**: Usage patterns, cost analytics, and performance metrics
- **OpenAI-Compatible Errors**: Consistent error handling across all endpoints
- **Request Correlation**: X-Client-Request-ID headers for observability

## Tech Stack

### Backend
- **Framework**: FastAPI with Python 3.11+
- **Database**: Supabase (PostgreSQL with Row Level Security)
- **Authentication**: Supabase Auth with JWT tokens + PAT system
- **AI Providers**: Direct OpenAI and Anthropic API integration
- **Security**: Fernet encryption for API keys, comprehensive RLS policies
- **Observability**: Structured logging, request tracking, error management

### Frontend
- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS with shadcn/ui components
- **State Management**: React Context + React Query for server state
- **HTTP Client**: Axios with automatic auth and organization headers
- **Architecture**: F1 frontend architecture with OpenAI-compatible client
- **Error Handling**: OpenAI-style error normalization across all services

## Project Structure

```
strataAI/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API route modules
│   │   │   ├── playground/ # Playground-specific endpoints
│   │   │   ├── v1/         # Unified API v1 endpoints
│   │   │   └── *.py        # Core API routes
│   │   ├── core/           # Configuration and dependencies
│   │   ├── models/         # Pydantic data models
│   │   ├── services/       # Business logic services
│   │   ├── utils/          # Utility functions and helpers
│   │   ├── errors/         # Error handling and OpenAI envelope
│   │   └── middleware/     # Custom middleware
│   ├── migrations/         # Database migration files
│   ├── .env.example        # Environment template
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # Reusable React components
│   │   ├── pages/          # Page-level components
│   │   ├── contexts/       # React context providers
│   │   ├── hooks/          # Custom React hooks
│   │   ├── services/       # API client services
│   │   ├── utils/          # Frontend utilities
│   │   └── types/          # TypeScript type definitions
│   ├── .env.local          # Frontend environment variables
│   └── package.json        # Node.js dependencies
├── render.yaml             # Render deployment configuration
├── *.md                    # Documentation files
└── README.md
```

## Quick Start

### Prerequisites

- **Python 3.11+** (for backend development)
- **Node.js 18+** (for frontend development)
- **Supabase Account** (database and authentication)
- **AI Provider API Keys** (OpenAI and/or Anthropic)
- **Git** (for version control)

### Environment Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-org/strataAI.git
   cd strataAI
   ```

2. **Backend Environment Setup**

   ```bash
   cd backend
   cp .env.example .env
   ```

   Edit `backend/.env` with your configuration:
   ```bash
   # Supabase Configuration
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_ANON_KEY=your_supabase_anon_key
   SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
   SUPABASE_JWT_SECRET=your_supabase_jwt_secret
   
   # Security
   ENCRYPTION_KEY=your_32_character_fernet_encryption_key
   
   # CORS Configuration
   ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:5174
   
   # Optional: Redis for caching (if available)
   REDIS_URL=redis://localhost:6379
   ```

3. **Frontend Environment Setup**

   ```bash
   cd frontend
   cp .env.example .env.local
   ```

   Edit `frontend/.env.local`:
   ```bash
   VITE_SUPABASE_URL=your_supabase_project_url
   VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
   VITE_API_BASE_URL=http://localhost:8000
   ```

### Development Setup

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations (if needed)
# Apply migrations in Supabase dashboard or via SQL

# Start development server
uvicorn app.main:app --reload --port 8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
# or
npm start
```

#### Optional: Redis Setup (for caching)

```bash
# Using Docker (recommended)
docker run -d -p 6379:6379 --name strataai-redis redis:7-alpine

# Or install locally
# macOS
brew install redis && redis-server

# Ubuntu/Debian
sudo apt install redis-server && redis-server
```

### Access the Application

- **Frontend Application**: http://localhost:5173 (Vite) or http://localhost:3000 (Create React App)
- **Backend API**: http://localhost:8000
- **Interactive API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Alternative API Docs**: http://localhost:8000/redoc (ReDoc)
- **Health Check**: http://localhost:8000/health

### First-Time Setup

1. **Create Account**: Visit the frontend and register a new account
2. **Create Organization**: Set up your first organization
3. **Configure Providers**: Add your OpenAI/Anthropic API keys in the Providers page
4. **Test in Playground**: Use the interactive playground to test AI models
5. **Generate PAT**: Create Personal Access Tokens for external API access

## Development

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run development server with auto-reload
uvicorn app.main:app --reload --port 8000

# Run tests (when available)
pytest

# Code formatting
black app/
isort app/

# Type checking
mypy app/

# Linting
flake8 app/
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev  # Vite development server

# Run tests
npm test

# Build for production
npm run build

# Preview production build
npm run preview

# Linting and formatting
npm run lint
npm run lint:fix
npm run format

# Type checking
npm run type-check
```

### Database Development

```bash
# Database migrations are managed through Supabase
# Apply migrations in the Supabase dashboard or via SQL files in migrations/

# View current schema
# Check DATABASE_SCHEMA.md for complete schema documentation

# Test database connection
# Use the /health endpoint to verify database connectivity
```

## API Documentation

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs - Interactive API testing
- **ReDoc**: http://localhost:8000/redoc - Clean API documentation

### API Endpoints Overview

#### Unified API (External Access)
- `POST /v1/chat/completions` - OpenAI-compatible chat completions
- `GET /v1/models` - List available models
- Authentication: Bearer token (Personal Access Token)

#### Playground API (Internal Use)
- `POST /api/v1/playground/chat/completions` - Direct provider chat completions
- `GET /api/v1/playground/sessions` - List chat sessions
- `POST /api/v1/playground/sessions/{id}/regenerate` - Regenerate responses
- `GET /api/v1/playground/sessions/{id}/usage` - Session usage analytics
- Authentication: Supabase JWT token

#### Management API
- `GET /api/v1/providers` - List AI providers
- `POST /api/v1/api-keys` - Configure provider API keys
- `GET /api/v1/user-management/tokens` - Manage Personal Access Tokens
- `GET /api/v1/user-management/users` - Organization user management

For complete API documentation, see `UNIFIED_API_GUIDE.md`.

## Architecture Overview

### Two-Tier API Architecture

1. **Playground (Simple)**: User → Supabase Auth → Direct Provider APIs
   - Optimized for interactive playground use
   - Direct provider API calls for better performance
   - Session management and usage tracking

2. **External Apps (Unified)**: User → PAT → Unified API → Provider APIs
   - OpenAI-compatible unified interface
   - Personal Access Token authentication
   - Organization-scoped access control

### Key Design Principles

- **OpenAI Compatibility**: All external APIs follow OpenAI response formats
- **Multi-tenant Security**: Row Level Security (RLS) for data isolation
- **Provider Agnostic**: Unified interface across OpenAI, Anthropic, and future providers
- **Zero Secret Leakage**: API keys never exposed to frontend clients
- **Comprehensive Observability**: Request tracking, usage analytics, and error monitoring

## Deployment

### Production Deployment (Render)

The application is configured for deployment on Render using `render.yaml`:

```bash
# Deploy to Render
git push origin main  # Triggers automatic deployment

# Manual deployment
# Use Render dashboard to deploy from GitHub repository
```

### Environment Variables (Production)

Ensure all production environment variables are configured in your deployment platform:
- Supabase credentials
- Encryption keys
- CORS origins (include production URLs)
- AI provider API keys (configured through the application UI)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Update documentation if needed
5. Add tests for new functionality
6. Ensure all tests pass
7. Submit a pull request

### Development Guidelines

- Follow OpenAI-compatible error formats for all APIs
- Maintain comprehensive documentation
- Use TypeScript for type safety
- Follow the established project structure
- Add proper error handling and logging

## Documentation

- `BACKEND_DESIGN.md` - Complete backend architecture
- `FRONTEND_DESIGN.md` - Frontend component architecture
- `DATABASE_SCHEMA.md` - Database schema and relationships
- `UNIFIED_API_GUIDE.md` - Complete API reference
- `BUSINESS_OVERVIEW.md` - Business context and features
- `PROJECT_STATUS.md` - Implementation status and roadmap

## License

This project is licensed under the MIT License - see the LICENSE file for details.
