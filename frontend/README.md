# NeuraBuddy Frontend

A modern, professional React frontend for the NeuraBuddy neuroanatomy learning platform.

## Features

- **Query Interface**: Ask questions and get detailed answers from the knowledge base
- **Socratic Teaching**: Learn through guided questions and discovery
- **Interactive Quizzes**: Test your knowledge with MCQ, short-answer, and clinical vignette questions
- **Document Upload**: Add PDF, HTML, or text files to the knowledge base
- **Progress Tracking**: Monitor your learning progress and performance

## Setup

1. **Install dependencies**:
```bash
cd frontend
npm install
```

2. **Development mode**:
```bash
npm run dev
```

The frontend will run on `http://localhost:3000` with hot-reload enabled.

3. **Build for production**:
```bash
npm run build
```

The built files will be in the `dist/` directory and will be served by the FastAPI backend.

## Development

The frontend uses:
- **React 18** with functional components and hooks
- **React Router** for navigation
- **Framer Motion** for smooth animations
- **Lucide React** for icons
- **Axios** for API calls
- **Vite** as the build tool

## Project Structure

```
frontend/
├── src/
│   ├── components/      # React components
│   │   ├── Query.jsx    # Query/chat interface
│   │   ├── Teaching.jsx # Socratic teaching
│   │   ├── Quiz.jsx     # Quiz interface
│   │   ├── Upload.jsx   # Document upload
│   │   └── Progress.jsx # Progress dashboard
│   ├── api/
│   │   └── client.js    # API client
│   ├── App.jsx          # Main app component
│   ├── App.css          # App styles
│   ├── main.jsx         # Entry point
│   └── index.css        # Global styles
├── index.html           # HTML template
├── vite.config.js       # Vite configuration
└── package.json         # Dependencies
```

## API Integration

The frontend communicates with the backend API at `/api/v1`. Make sure the backend is running on `http://localhost:8000` (or update the proxy in `vite.config.js`).

## Styling

The UI uses CSS custom properties (CSS variables) for theming. Colors, spacing, and other design tokens are defined in `src/index.css`.

