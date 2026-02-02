# NeuraBuddy Frontend Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Development Mode

Run the frontend in development mode (with hot-reload):

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

**Important:** Make sure the backend is running on `http://localhost:8000` for the frontend to work properly.

### 3. Build for Production

Build the frontend for production:

```bash
npm run build
```

The built files will be in `frontend/dist/` and will be automatically served by the FastAPI backend when you run the main application.

## Running Both Frontend and Backend

### Option 1: Separate Terminals (Development)

**Terminal 1 - Backend:**
```bash
# From project root
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
# From frontend directory
cd frontend
npm run dev
```

Access:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

### Option 2: Production Mode (Single Server)

1. Build the frontend:
```bash
cd frontend
npm run build
```

2. Run the backend (it will serve the frontend):
```bash
# From project root
uvicorn main:app --host 0.0.0.0 --port 8000
```

Access everything at `http://localhost:8000`

## Troubleshooting

### Connection Issues

If you see "Backend disconnected" in the UI:

1. **Check if backend is running:**
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

2. **Check CORS settings** in `main.py` - should allow all origins in development

3. **Check API base URL** in `frontend/src/api/client.js` - should be `/api/v1`

### Build Issues

If `npm install` fails:

1. Make sure you have Node.js 16+ installed
2. Try deleting `node_modules` and `package-lock.json`, then run `npm install` again
3. Check for any version conflicts

### Port Conflicts

If port 3000 is already in use:

1. Edit `frontend/vite.config.js` and change the port:
   ```js
   server: {
     port: 3001, // or any other available port
   }
   ```

## Features

- ✅ Query Interface with filters
- ✅ Socratic Teaching Sessions
- ✅ Interactive Quizzes
- ✅ Document Upload
- ✅ Progress Tracking
- ✅ Connection Status Indicator
- ✅ Error Handling
- ✅ Responsive Design

## Development Tips

- The frontend uses React Router for navigation
- All API calls go through `/api/v1` endpoints
- User ID is stored in localStorage
- Components use Framer Motion for animations
- Styling uses CSS custom properties for theming
