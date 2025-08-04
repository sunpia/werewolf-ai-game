# 🐺 AI Werewolf Game - Docker Setup

A modern full-stack application featuring AI-powered Werewolf gameplay with user authentication, game limits, and persistent storage.

## 🏗️ Architecture

- **Backend**: FastAPI with PostgreSQL database
- **Frontend**: React with TypeScript
- **Authentication**: Google OAuth 2.0 with JWT tokens
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Containerization**: Docker Compose

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Google OAuth 2.0 credentials (for authentication)
- OpenAI API key (for AI players)

### 1. Environment Setup

Update the `.env` file with your credentials:

```bash
# Required: OpenAI API key for AI players
OPENAI_API_KEY=your_openai_api_key_here

# Required: Google OAuth credentials
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# Required: JWT secret (generate a long random string)
JWT_SECRET_KEY=your_jwt_secret_key_here_should_be_very_long_and_random

# Database settings (already configured for Docker)
DATABASE_URL=postgresql://werewolf_user:werewolf_password@db:5432/werewolf_db
POSTGRES_DB=werewolf_db
POSTGRES_USER=werewolf_user
POSTGRES_PASSWORD=werewolf_password
```

### 2. Launch the Application

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🎮 Features

### User Management
- **Google OAuth 2.0** authentication
- **JWT token** based sessions
- **User profiles** with persistent data

### Game System
- **3 free games** per user limit
- **Game history** tracking
- **Real-time gameplay** with WebSocket events
- **AI-powered players** using OpenAI GPT models

### Database Features
- **Persistent user data** across sessions
- **Game state preservation** 
- **Complete game history** logging
- **PostgreSQL** with advanced JSON support

## 🏗️ Development

### Local Development Setup

1. **Database only** (for local backend development):
```bash
docker-compose up db -d
```

2. **Backend development** (with local Python environment):
```bash
# Install dependencies
pip install -r requirements.txt

# Run backend locally
python app.py
```

3. **Frontend development**:
```bash
cd frontend
npm install
npm start
```

### Docker Services

| Service | Port | Description |
|---------|------|-------------|
| `frontend` | 3000 | React development server |
| `backend` | 8000 | FastAPI application |
| `db` | 5432 | PostgreSQL database |

### Database Management

#### View database logs:
```bash
docker-compose logs db
```

#### Connect to database:
```bash
docker-compose exec db psql -U werewolf_user -d werewolf_db
```

#### Reset database:
```bash
docker-compose down -v
docker-compose up --build
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://werewolf_user:werewolf_password@db:5432/werewolf_db` |
| `OPENAI_API_KEY` | OpenAI API key for AI players | Required |
| `JWT_SECRET_KEY` | JWT token signing secret | Required |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | Required |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | Required |
| `MIN_PLAYERS` | Minimum players per game | `6` |
| `MAX_PLAYERS` | Maximum players per game | `15` |

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized origins:
   - `http://localhost:3000` (development)
   - Your production domain

## 📊 Database Schema

### Users Table
- User profiles with OAuth data
- Game limits and play counts
- Session management

### Games Table
- Game configurations and states
- User ownership tracking
- Status and completion data

### Game History Table
- Detailed game event logging
- Player actions and outcomes
- Timeline reconstruction

## 🔍 Monitoring & Debugging

### View logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

### Database queries:
```sql
-- View user game statistics
SELECT u.name, u.total_games_played, u.free_games_remaining 
FROM users u;

-- View recent games
SELECT g.id, u.name as player, g.status, g.created_at 
FROM games g 
JOIN users u ON g.user_id = u.id 
ORDER BY g.created_at DESC;
```

### Health checks:
- Backend health: http://localhost:8000/api/health
- Database connection: Check backend logs

## 🚢 Production Deployment

### Security Considerations
1. **Change default passwords** in `.env`
2. **Use strong JWT secrets** (64+ characters)
3. **Enable HTTPS** for production
4. **Set secure CORS origins**
5. **Use production PostgreSQL** instance

### Environment Updates
```bash
# Production environment variables
DATABASE_URL=postgresql://user:pass@prod-db:5432/werewolf_prod
ALLOWED_ORIGINS=https://yourdomain.com
JWT_SECRET_KEY=super_long_production_secret_key_here
```

## 🔄 Backup & Recovery

### Database backup:
```bash
docker-compose exec db pg_dump -U werewolf_user werewolf_db > backup.sql
```

### Database restore:
```bash
docker-compose exec -T db psql -U werewolf_user werewolf_db < backup.sql
```

## 🆘 Troubleshooting

### Common Issues

1. **Database connection failed**
   - Check if PostgreSQL container is running
   - Verify DATABASE_URL in .env file

2. **Authentication not working**
   - Verify Google OAuth credentials
   - Check JWT_SECRET_KEY is set
   - Ensure frontend can reach backend

3. **Game creation fails**
   - Check OpenAI API key
   - Verify user has free games remaining
   - Check backend logs for detailed errors

### Reset Everything
```bash
# Stop and remove all containers, networks, volumes
docker-compose down -v --remove-orphans

# Rebuild and restart
docker-compose up --build
```

## 📚 API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation with:
- Authentication endpoints
- Game management
- User profile management
- Game history access

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Test with Docker Compose
4. Submit pull request

## 📝 License

MIT License - see LICENSE file for details.
