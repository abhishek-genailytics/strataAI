# Development Rules and Guidelines

## Directory Organization

### Mandatory Directory Structure

All code must be organized according to the following structure:

- **Frontend Code**: All frontend-related code (React, TypeScript, CSS, etc.) must be placed in the `frontend/` directory
- **Backend Code**: All backend-related code (Python, API endpoints, services, etc.) must be placed in the `backend/` directory
- **Root Directory**: Should only contain project-level configuration files such as:
  - `docker-compose.yml`
  - `README.md`
  - `DEVELOPMENT_RULES.md`
  - Other project documentation

### Code Placement Rules

1. **Frontend Code** (`frontend/` directory):

   - React components
   - TypeScript/JavaScript files
   - CSS/SCSS files
   - Frontend configuration files (package.json, tsconfig.json, etc.)
   - Frontend tests
   - Frontend build artifacts

2. **Backend Code** (`backend/` directory):

   - Python application code
   - API endpoints and routes
   - Services and business logic
   - Database models and migrations
   - Backend configuration files
   - Backend tests
   - Backend documentation

3. **Root Directory** (project level only):
   - Docker Compose configuration
   - Project documentation
   - CI/CD configuration files
   - Environment configuration templates

### Enforcement

- No frontend code should be placed in the root directory
- No backend code should be placed in the root directory
- All new code must follow this directory structure
- When refactoring or moving code, ensure it follows these rules

### Benefits

- Clear separation of concerns
- Easier deployment and containerization
- Better maintainability
- Consistent project structure
- Simplified CI/CD pipeline setup
