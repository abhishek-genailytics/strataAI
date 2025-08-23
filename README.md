# StrataAI

A unified API gateway platform that provides developers with a single interface to access multiple AI providers (OpenAI, Anthropic, etc.) while offering comprehensive observability, usage monitoring, and cost tracking.

## Features

- **Unified API Gateway**: Single endpoint for multiple AI providers
- **Authentication & Security**: Secure user management with Supabase Auth
- **API Key Management**: Encrypted storage and management of provider API keys
- **Interactive Playground**: Test different AI models through a web interface
- **Usage Monitoring**: Track API usage, costs, and performance metrics
- **Observability Dashboard**: Visualize usage patterns and cost analytics
- **Rate Limiting & Caching**: Redis-based performance optimization

## Tech Stack

- **Backend**: FastAPI with Python
- **Frontend**: React with TypeScript and Tailwind CSS
- **Database**: Supabase (PostgreSQL with built-in auth)
- **Cache/Rate Limiting**: Redis
- **AI Integration**: LangChain for provider abstractions
- **Authentication**: Supabase Auth with JWT tokens

## Project Structure

```
strataAI/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Configuration and settings
│   │   ├── models/         # Pydantic models
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utility functions
│   ├── tests/              # Backend tests
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── services/       # API services
│   │   └── utils/          # Utility functions
│   └── package.json        # Node.js dependencies
├── docker-compose.yml      # Local development setup
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- Supabase account

### Environment Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd strataAI
   ```

2. **Copy environment file**
   ```bash
   cp .env.example .env
   ```

3. **Configure environment variables**
   Edit `.env` file with your Supabase credentials:
   ```
   SUPABASE_URL=your_supabase_url_here
   SUPABASE_KEY=your_supabase_anon_key_here
   SUPABASE_JWT_SECRET=your_supabase_jwt_secret_here
   ENCRYPTION_KEY=your_32_character_encryption_key_here
   ```

### Development Setup

#### Option 1: Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Option 2: Manual Setup

**Backend Setup:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend Setup:**
```bash
cd frontend
npm install
npm start
```

**Redis Setup:**
```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or install locally (macOS)
brew install redis
redis-server
```

### Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Redis**: localhost:6379

## Development

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Code formatting
black app/
isort app/

# Linting
flake8 app/
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm start

# Run tests
npm test

# Build for production
npm run build

# Linting
npm run lint
npm run lint:fix
```

## API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive API documentation.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License.