# 🔥 Development Environment with Hot Reloading

Your Docker Compose setup now supports **live file watching** and **hot reloading** for both backend and frontend development!

## 🚀 Quick Start

### Option 1: Use the Development Script (Recommended)
```bash
./dev-start.sh
```

### Option 2: Manual Docker Compose
```bash
# Standard development mode
docker-compose up --build

# Advanced development mode with extra features
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

## 🔧 What's Enabled

### Backend Hot Reloading
- **Uvicorn with --reload**: Automatically restarts when Python files change
- **Volume mounting**: Your local code is mounted into the container
- **Reload directories**: Watches `/app/src` and `/app` for changes
- **Cache exclusion**: Python `__pycache__` directories are excluded

### Frontend Hot Reloading  
- **React Fast Refresh**: Instant updates for React components
- **File polling**: Enabled for reliable change detection in containers
- **Source mapping**: Preserves debugging capabilities

### Database Persistence
- **Named volumes**: Database data persists between container restarts
- **Development overrides**: Separate dev database for easy reset

## 📁 File Structure for Hot Reloading

```
werewolf/
├── docker-compose.yml          # Base configuration
├── docker-compose.dev.yml      # Development overrides
├── dev-start.sh               # Convenient startup script
├── app.py                     # Backend entry point
├── src/                       # Backend source (watched)
│   ├── api/
│   ├── services/
│   └── models/
└── frontend/                  # Frontend source (watched)
    ├── src/
    ├── public/
    └── Dockerfile.dev
```

## 🎯 Development Workflow

1. **Start the environment**: `./dev-start.sh`
2. **Edit backend code**: Changes in `src/` trigger automatic reload
3. **Edit frontend code**: React components update instantly
4. **View changes**: 
   - Backend: http://localhost:8000
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/docs

## 🔧 Configuration Details

### Docker Compose Volumes
```yaml
volumes:
  - ./:/app                    # Full source code mount
  - /app/__pycache__          # Exclude Python cache
  - /app/src/__pycache__      # Exclude nested cache
  - /app/.git                 # Exclude git directory
```

### Uvicorn Configuration
```bash
uvicorn app:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload \
  --reload-dir /app/src \
  --reload-dir /app
```

### Environment Variables
```bash
PYTHONUNBUFFERED=1          # Real-time output
PYTHONDONTWRITEBYTECODE=1   # Don't create .pyc files
CHOKIDAR_USEPOLLING=true    # Reliable file watching
```

## 🛠️ Troubleshooting

### Hot Reload Not Working?
1. **Check volume mounts**: Ensure your code directory is properly mounted
2. **File permissions**: Make sure Docker can read your source files
3. **Restart containers**: `docker-compose restart`

### Database Issues?
1. **Reset database**: `docker-compose down -v && docker-compose up`
2. **Check logs**: `docker-compose logs postgres`
3. **Connection**: Verify `DATABASE_URL` in `.env`

### Performance Issues?
1. **Use .dockerignore**: Exclude unnecessary files
2. **Delegated volumes**: Already configured for macOS optimization
3. **Resource limits**: Increase Docker memory if needed

## 🎮 Ready to Develop!

Your development environment now features:
- ⚡ **Instant backend reloads** when you change Python code
- 🔥 **Hot React updates** for frontend changes  
- 🗄️ **Persistent database** across restarts
- 📊 **Real-time logs** from all services
- 🐛 **Debug-ready setup** with proper source mapping

Start coding and see your changes instantly! 🚀
