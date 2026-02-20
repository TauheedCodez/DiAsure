# Guest Mode Image Upload - Complete ✅

## Overview
Successfully added image upload functionality for guest mode chat. Guest users can now upload ulcer images, get CNN-based severity predictions, and receive personalized Q&A flow - all without authentication!

---

## Backend Implementation

### New Endpoint: POST /guest/{session_id}/upload-image

**Location**: `backend/guest_chat_routes.py`

**What It Does**:
1. Validates guest session exists
2. Validates image file (JPG/PNG only)
3. Loads and preprocesses image
4. Uses CNN models to predict severity (low/medium/high)
5. Activates Q&A mode in session state
6. Returns severity and first Q&A question

**Response**:
```json
{
  "status": "success",
  "prediction": "medium",
  "assistant_message": "✅ **Image Analysis Complete**\n\n**Predicted Severity:** 🟠 MEDIUM\n\nI will now ask you some questions...",
  "patient_state": { "severity": "medium", "qa_active": true, ... }
}
```

### Model Integration

**Updated**: `backend/main.py`
```python
from guest_chat_routes import set_guest_models

# After loading models
set_models(foot_random_model, severity_model)
set_guest_models(foot_random_model, severity_model)  # NEW
```

Both authenticated and guest routes now share the same CNN models.

---

## Frontend Implementation

### 1. API Function: uploadGuestImage

**Location**: `frontend/src/api/guestApi.js`

```javascript
export const uploadGuestImage = async (sessionId, file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post(
    `/guest/${sessionId}/upload-image`, 
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  );
  return response.data;
};
```

### 2. ChatPage Updates

**Import**:
```javascript
import { startGuestChat, sendGuestMessage, uploadGuestImage } from '../api/guestApi';
```

**Image Upload Click Handler**:
```javascript
const handleImageUploadClick = () => {
    if (!isAuthenticated) {
        // Guest mode - check session
        if (!guestSessionId) {
            alert('Initializing guest session, please try again...');
            return;
        }
        setShowImageUploader(true);
        return;
    }
    
    // Authenticated mode
    if (!activeChatId) {
        alert('Please create a chat first');
        return;
    }
    setShowImageUploader(true);
};
```

**Image Upload Handler**:
```javascript
const handleImageUpload = async (file) => {
    setLoading(true);
    
    try {
        // GUEST MODE
        if (!isAuthenticated) {
            if (!guestSessionId) {
                throw new Error('No guest session available');
            }
            
            const response = await uploadGuestImage(guestSessionId, file);
            
            const aiMessage = {
                role: 'assistant',
                content: response.assistant_message,
                timestamp: new Date(),
            };
            setGuestMessages((prev) => [...prev, aiMessage]);
            setShowImageUploader(false);
            return;
        }
        
        // AUTHENTICATED MODE
        if (!activeChatId) return;
        
        const response = await uploadImage(activeChatId, file);
        // ... handle authenticated upload
    } catch (error) {
        console.error('Failed to upload image:', error);
        throw new Error(error.response?.data?.detail || 'Upload failed');
    } finally {
        setLoading(false);
    }
};
```

**Show Image Upload Button**:
```javascript
<ChatWindow
    showImageUpload={
        isAuthenticated 
            ? (activeChatId !== null) 
            : (guestSessionId !== null)  // NEW: Enable for guests
    }
    onImageUpload={handleImageUploadClick}
/>
```

---

## User Flow

### Guest Image Upload Flow

1. **User Opens Chat (Not Logged In)**
   - Guest session created automatically
   - Chat interface loads
   - "📷 Upload Ulcer Image" button visible

2. **User Clicks Upload Button**
   - Image uploader modal opens
   - Shows DOs and DON'Ts
   - User selects image file

3. **User Uploads Image**
   - Frontend sends to `/guest/{session_id}/upload-image`
   - Backend processes with CNN models
   - Returns severity prediction

4. **Prediction Displayed**
   ```
   ✅ Image Analysis Complete

   Predicted Severity: 🟠 MEDIUM

   I will now ask you some questions to provide personalized recommendations.

   **Doctor Question:** How long have you had this ulcer?
   Answers can be like: "2 days", "1 week", "3 months"
   ```

5. **Q&A Begins**
   - Backend activates Q&A mode in session
   - User answers questions
   - AI guides through assessment
   - Final risk classification provided

---

## Feature Comparison

| Feature | Guest Mode | Authenticated Mode |
|---------|-----------|-------------------|
| Chat with AI | ✅ Yes | ✅ Yes |
| Image Upload | ✅ Yes (NEW!) | ✅ Yes |
| Severity Prediction | ✅ Yes (NEW!) | ✅ Yes |
| Q&A Flow | ✅ Yes (NEW!) | ✅ Yes |
| Save Chat History | ❌ No | ✅ Yes |
| Generate Summary | ❌ No | ✅ Yes |
| Session Persistence | ⚠️ Until refresh | ✅ Permanent |

---

## Testing

### Test Scenario: Guest Image Upload

1. **Open Chat as Guest**
   - Navigate to http://localhost:5173/chat (not logged in)
   - Guest banner appears
   - Session created automatically

2. **Click Upload Image**
   - "📷 Upload Ulcer Image" button visible
   - Click button
   - Modal opens

3. **Upload Foot Ulcer Image**
   - Select JPG/PNG image
   - Preview shows
   - Click "Upload & Analyze"

4. **Verify Results**
   - Modal closes
   - Severity prediction displays:
     - 🟢 LOW severity
     - 🟠 MEDIUM severity
     - 🔴 HIGH severity
   - First Q&A question appears

5. **Answer Questions**
   - Type answer (e.g., "5 days")
   - Next question appears
   - Continue until complete

6. **Final Recommendation**
   - Risk classification displays
   - Care recommendations provided
   - All without login! ✨

---

## Technical Details

### CNN Models Used
- **Filter Model**: MobileNetV2 (foot/random classification)
- **Severity Model**: ResNet50 (low/medium/high classification)

### Model Sharing
Both authenticated and guest routes share the same model instances loaded in `main.py`:
```python
foot_random_model = tf.keras.models.load_model(FILTER_MODEL_PATH)
severity_model = tf.keras.models.load_model(SEVERITY_MODEL_PATH)

set_models(foot_random_model, severity_model)          # For authenticated
set_guest_models(foot_random_model, severity_model)    # For guests
```

### Session State
After image upload, guest session state includes:
```python
{
    "state": {
        "severity": "medium",
        "qa_active": True,
        "current_question_key": "ulcer_duration",
        # ... other Q&A fields
    },
    "messages": [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "Image Analysis Complete..."},
    ]
}
```

---

## Benefits

### For Users
✅ Try full DFU assessment without creating account  
✅ Get real CNN-based predictions  
✅ Experience complete Q&A flow  
✅ Understand value before signing up  

### For Product
✅ Lower barrier to entry  
✅ Better user conversion  
✅ Showcase AI capabilities  
✅ Build trust before commitment  

---

## Files Modified

**Backend**:
- `backend/guest_chat_routes.py` - Added upload endpoint
- `backend/main.py` - Injected models into guest routes

**Frontend**:
- `frontend/src/api/guestApi.js` - Added uploadGuestImage
- `frontend/src/pages/ChatPage.jsx` - Enabled guest image upload

---

## Success! 🎉

Guest mode now has **full feature parity** with authenticated mode for image analysis and Q&A, with the only difference being chat persistence!

All changes are live - refresh your browser to test!
