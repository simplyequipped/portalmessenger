# Portal Messenger Tech Stack Documentation

## Overview

Portal Messenger v2 uses a modern, cross-platform web application architecture that maintains simple installation while leveraging contemporary development tools. The application serves a Svelte frontend from a Python backend, with direct WebSocket connections to pyjs8call for real-time radio messaging.

## Architecture

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Svelte Frontend   │◄──►│ Starlette Backend   │◄──►│    pyjs8call API    │
│   (Tailwind CSS)    │    │ (TinyDB + uvicorn)  │    │   (WebSocket)       │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

## Technology Stack

### Backend
- **uvicorn** - ASGI server (cross-platform, production-ready)
- **Starlette** - Lightweight async web framework
- **TinyDB** - File-based JSON document database
- **Python 3.7+** - Runtime environment

### Frontend
- **Svelte** - Modern reactive framework (simpler than React)
- **Tailwind CSS** - Utility-first CSS framework
- **SvelteKit** - Build tool and dev server (development only)

### Development Tools
- **SvelteKit** - Frontend build system, bundling, and hot reload
- **npm/Node.js** - Frontend package management (development only)

## Key Benefits

- **Cross-platform** - All technologies work identically on Windows, Linux, macOS
- **Simple installation** - End users: `pip install portalmessenger`
- **Modern development** - Component-based UI, reactive state, utility CSS
- **Human-readable data** - TinyDB stores data as JSON files
- **No runtime dependencies** - Frontend compiled to static assets
- **Local network friendly** - Direct WebSocket connections, no external services

## Development Workflow

### Project Structure
```
portalmessenger/
├── setup.py                    # Python package configuration
├── build.sh                    # Build script
├── portalmessenger/
│   ├── __init__.py
│   ├── server.py              # Starlette server + TinyDB
│   └── static/                # Pre-built frontend assets (git ignored)
│       ├── index.html
│       └── assets/
├── frontend/                   # Frontend source (not in Python package)
│   ├── src/
│   │   ├── App.svelte
│   │   └── components/
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
└── .gitignore
```

### Development Setup
```bash
# Backend development
pip install -e .
python -m portalmessenger

# Frontend development (separate terminal)
cd frontend
npm install
npm run dev
```

### Build Process
```bash
# 1. Build frontend assets
cd frontend
npm run build                   # Creates dist/ with compiled Svelte + Tailwind

# 2. Copy assets to Python package
cp -r dist/* ../portalmessenger/static/

# 3. Build Python package
cd ..
python setup.py sdist bdist_wheel
```

## Distribution Strategy

### For Developers
- Source code includes both frontend source and Python backend
- Requires Node.js for frontend development
- Uses SvelteKit/Vite for hot reload and modern development experience

### For End Users
- **Installation**: `pip install portalmessenger`
- **No Node.js required** - gets pre-compiled frontend assets
- **No build tools needed** - just Python dependencies
- **Same familiar experience** as current Portal Messenger

### Package Contents (End User)
```
portalmessenger-2.0.0/
├── portalmessenger/
│   ├── server.py              # Starlette + TinyDB backend
│   └── static/                # Compiled Svelte app
│       ├── index.html         # Single page application
│       └── assets/
│           ├── index.js       # Bundled Svelte components
│           └── index.css      # Compiled Tailwind styles
└── setup.py
```

## Runtime Behavior

### Application Startup
1. User runs `python -m portalmessenger`
2. Starlette server starts on configurable port (default: 8080)
3. TinyDB initializes `portalmessenger.json` database
4. Static file server serves Svelte app at `/`
5. API endpoints available at `/api/*`
6. Browser opens to `http://localhost:8080`

### Data Flow
1. **Settings**: Loaded from TinyDB on startup, configures pyjs8call
2. **Messages**: Stored in TinyDB for persistence across devices
3. **Real-time updates**: Direct WebSocket to pyjs8call API
4. **Cross-device sync**: All devices on network access same TinyDB

## Comparison to Current Stack

| Aspect | Current (v1) | Proposed (v2) |
|--------|-------------|---------------|
| Backend | Flask + Flask-SocketIO | Starlette + uvicorn |
| Frontend | jQuery + vanilla JS | Svelte + Tailwind |
| Database | SQLite | TinyDB (JSON) |
| Build | None | SvelteKit (dev only) |
| Installation | `pip install` | `pip install` (same) |
| Dependencies | Runtime JS dependencies | Pre-compiled assets |

## Benefits for Ham Radio Operators

- **Familiar installation** - Same `pip install` experience
- **Cross-platform** - Works on any OS with Python
- **Local network only** - No internet dependencies
- **Readable data** - JSON database files can be inspected/backed up
- **Modern UI** - Responsive design, better mobile support
- **Maintainable** - Modern development tools for future features
