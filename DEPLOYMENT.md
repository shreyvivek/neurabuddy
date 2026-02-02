# Deploy NeuraBuddy

Deploy [NeuraBuddy](https://github.com/shreyvivek/neurabuddy) to production. You'll deploy the **backend** (Railway or Render) and **frontend** (Vercel) separately.

## Prerequisites

- GitHub account (repo: https://github.com/shreyvivek/neurabuddy)
- [OpenAI API key](https://platform.openai.com/api-keys)
- Accounts: [Vercel](https://vercel.com), [Railway](https://railway.app) or [Render](https://render.com)

---

## Step 1: Deploy Backend (Railway)

1. Go to [railway.app](https://railway.app) → **Login** → **New Project**
2. **Deploy from GitHub** → Select `shreyvivek/neurabuddy`
3. Railway will detect the Python app. If prompted, set:
   - **Root Directory:** leave empty (uses repo root)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. **Variables** → Add:
   - `OPENAI_API_KEY` = your OpenAI API key
5. **Settings** → **Generate Domain** to get a public URL (e.g. `neurabuddy-production-xxxx.up.railway.app`)
6. Copy your backend URL (e.g. `https://neurabuddy-production-xxxx.up.railway.app`)

### Alternative: Deploy Backend on Render

1. Go to [render.com](https://render.com) → **New** → **Web Service**
2. Connect `shreyvivek/neurabuddy`
3. Settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. **Environment** → Add `OPENAI_API_KEY`
5. **Deploy** → Copy the URL (e.g. `https://neurabuddy-api.onrender.com`)

---

## Step 2: Deploy Frontend (Vercel)

1. Go to [vercel.com](https://vercel.com) → **Add New** → **Project**
2. Import `shreyvivek/neurabuddy`
3. **Configure:**
   - **Root Directory:** `frontend`
   - **Framework Preset:** Vite
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
4. **Environment Variables** → Add:
   - **Name:** `VITE_API_URL`
   - **Value:** `https://YOUR-BACKEND-URL/api/v1` (replace with your Railway URL from Step 1)
   - **Environments:** Select all (Production, Preview, Development)
   
   Example (Railway): `https://neurabuddy-production-xxxx.up.railway.app/api/v1`  
   Example (Render): `https://neurabuddy-api.onrender.com/api/v1`
5. **Deploy** (Vercel will build and deploy)

---

## Step 3: Connect Frontend to Backend

After both deployments complete, you need to link them:

### 3.1 Get Your Backend URL

**For Railway:**
- Go to Railway Dashboard → Your Project
- Click **Settings** tab → **Networking** section
- Copy the **Public Domain** (e.g., `neurabuddy-production-xxxx.up.railway.app`)

**For Render:**
- The URL is shown at the top of your service dashboard (e.g., `neurabuddy-api.onrender.com`)

### 3.2 Configure Frontend Environment Variable

1. Go to **Vercel Dashboard** → Your Project → **Settings** → **Environment Variables**
2. Find `VITE_API_URL` (if you already added it in Step 2)
3. **Edit** the value to: `https://your-railway-or-render-url.com/api/v1`
   - Example: `https://neurabuddy-production-xxxx.up.railway.app/api/v1`
4. Click **Save**

### 3.3 Redeploy Frontend

After updating the environment variable:

1. Go to Vercel → **Deployments** tab
2. Click the **⋯** menu on the latest deployment
3. Select **Redeploy** → **Use existing Build Cache**
4. Or simply push any commit to trigger auto-deploy

---

## Step 4: Verify Connection

1. Open your Vercel URL (e.g., `https://neurabuddy.vercel.app`)
2. Open browser DevTools (F12) → **Console** tab
3. Test features:
   - Upload a PDF in chat
   - Ask a question
   - Try generating flashcards
4. Check for errors:
   - If you see "Network Error" or CORS issues, verify:
     - Backend is running (visit `https://your-backend-url.com/` - should show "Welcome to NeuraBuddy API")
     - `VITE_API_URL` in Vercel matches your backend URL exactly
     - Backend URL includes `/api/v1` at the end

---

## ChromaDB Note

ChromaDB stores data on the local filesystem. On Railway/Render:

- Data is lost when the service restarts
- Upload documents again after deploy or restart

For long-term persistence, you’d need a hosted vector DB or Railway volumes.

---

## Quick Reference

| Component | Platform | URL env / setting |
|-----------|----------|-------------------|
| Backend   | Railway or Render | `OPENAI_API_KEY` |
| Frontend  | Vercel | `VITE_API_URL` = `https://backend-url/api/v1` |
