# Frontend-Backend Connection Guide

## ✅ Current Status

### Servers Running
- **Frontend**: http://localhost:5173 (Vite dev server)
- **Backend**: http://localhost:8000 (FastAPI with uvicorn)

Both servers are now running and ready for testing!

---

## 🔧 How to Start Servers

### Backend Server
```powershell
cd c:\Users\TAUHEED\Desktop\diassure\backend
.\venv\Scripts\activate
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Server
```powershell
cd c:\Users\TAUHEED\Desktop\diassure\frontend
npm run dev
```

---

## 🧪 Testing the Connection

### 1. Test Backend Health Endpoint
Open your browser or use curl:
```
http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "filter_model_loaded": true,
  "severity_model_loaded": true,
  "foot_accept_threshold": 0.95,
  "severity_classes": ["high", "low", "medium"],
  "filter_classes": ["foot", "random"]
}
```

### 2. Test Frontend Connection

**Open in Browser**: http://localhost:5173

**Expected Flow**:
1. Landing page loads with DiAsure branding
2. Click "Get Started" → Guest chat mode (no backend required)
3. Click "Sign In" → Auth page
4. Register a new account:
   - Name: Test User
   - Email: test@example.com
   - Password: password123
5. Should auto-redirect to chat page after registration

### 3. Test API Integration

Once logged in:

#### A. Create Chat
1. Click "New Chat" button
2. Check browser DevTools → Network tab
3. Should see `POST http://localhost:8000/chat/create`
4. Response: `{ chat_id: 1, title: "New Chat", created_at: "..." }`

#### B. Send Message
1. Type: "What is diabetic foot ulcer?"
2. Press Send
3. Check Network tab: `POST http://localhost:8000/chat/1/ai-message`
4. Bot should respond with educational info

#### C. Upload Image
1. Click "📷 Upload Ulcer Image"
2. Select a foot image (JPG/PNG)
3. Click "Upload & Analyze"
4. Check Network tab: `POST http://localhost:8000/chat/1/upload-image`
5. Should see severity prediction (low/medium/high)

#### D. Generate Summary
1. Complete the Q&A flow
2. Click "📋 Generate Summary"
3. Check Network tab: `GET http://localhost:8000/chat/1/summary`
4. Modal should display patient summary

---

## 🔍 Common Issues & Solutions

### Issue 1: CORS Errors
**Symptom**: Console error: `Access to fetch at 'http://localhost:8000' has been blocked by CORS policy`

**Solution**: Backend already configured with CORS in `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue 2: Backend Not Running
**Symptom**: Network error, ERR_CONNECTION_REFUSED

**Solution**: 
1. Check backend terminal for errors
2. Ensure virtual environment is activated
3. Restart backend server

### Issue 3: Token Errors
**Symptom**: 401 Unauthorized errors

**Solution**:
1. Check localStorage has token: DevTools → Application → Local Storage → token
2. If expired, logout and login again
3. Backend JWT expires after 60 minutes (configured in .env)

### Issue 4: Database Errors
**Symptom**: `OperationalError: connection to server failed`

**Solution**:
1. Ensure PostgreSQL is running
2. Check connection string in `backend/.env`:
   ```
   DATABASE_URL=postgresql://postgres:admin48@localhost:5432/dfu_db
   ```
3. Verify database exists: `psql -U postgres -l`

---

## 🎯 Quick Integration Test

### Full Flow Test (5 minutes)

1. **Register**: http://localhost:5173/auth
   - Create account with email/password
   - Should redirect to `/chat`

2. **Create Chat**: 
   - Click "New Chat"
   - Verify chat appears in sidebar

3. **Send Message**:
   - Type: "What causes diabetic foot ulcers?"
   - Verify AI response appears

4. **Upload Image**:
   - Click "📷 Upload Ulcer Image"
   - Upload foot ulcer image
   - Verify severity prediction

5. **Q&A Flow**:
   - Answer questions from chatbot
   - Complete all questions
   - Verify final risk assessment (🔴/🟠/🟢)

6. **Summary**:
   - Click "📋 Generate Summary"
   - Verify summary modal displays
   - Click "Copy to Clipboard"

7. **Chat Management**:
   - Create another chat
   - Switch between chats
   - Delete a chat

8. **Logout & Re-login**:
   - Logout
   - Login again
   - Verify chats persist

---

## 📊 API Endpoints Reference

### Authentication
```
POST /auth/register       → { name, email, password }
POST /auth/login          → FormData { username: email, password }
GET  /auth/me             → User info
```

### Chat
```
POST   /chat/create           → Create new chat
GET    /chat/history          → List all chats
GET    /chat/{chat_id}        → Get chat with messages
DELETE /chat/{chat_id}        → Delete chat
```

### AI Interaction
```
POST /chat/{chat_id}/ai-message    → { content }
POST /chat/{chat_id}/upload-image  → FormData { file }
GET  /chat/{chat_id}/summary       → Summary data
```

---

## 🚦 Connection Status Check

Run this in PowerShell to check both servers:

```powershell
# Check backend
curl http://localhost:8000/health -UseBasicParsing

# Check frontend
curl http://localhost:5173 -UseBasicParsing
```

Both should return Status 200 OK.

---

## 🎉 Ready to Test!

Both servers are running. Open your browser to:

**http://localhost:5173**

Follow the test scenarios above to verify the full integration!
