# 🩺 DiAsure — Diabetic Foot Ulcer Assessment Platform

DiAsure is an AI-powered web application that helps users assess diabetic foot ulcers (DFU) through image analysis, severity prediction, and an intelligent chat assistant. It also helps users find nearby hospitals and doctors.

---

## 🧰 Tech Stack

| Layer      | Technology                                      |
| ---------- | ----------------------------------------------- |
| Frontend   | React 19, Vite, React Router                    |
| Backend    | Python, FastAPI, SQLAlchemy                      |
| Database   | PostgreSQL                                       |
| AI/ML      | TensorFlow (MobileNetV2 + ResNet50)              |
| Chat AI    | Groq API (LLaMA 3.1)                            |
| Maps       | Google Places API, Distance Matrix API           |

---

## 📋 Prerequisites

Make sure you have the following installed before proceeding:

- [**Git**](https://git-scm.com/downloads)
- [**Node.js**](https://nodejs.org/) (v18 or higher) — includes `npm`
- [**Python 3.10.11**](https://www.python.org/downloads/release/python-31011/)
- [**PostgreSQL**](https://www.postgresql.org/download/) (v14 or higher)

You will also need API keys for:
- [Groq](https://console.groq.com/) — for AI chat
- [Google Cloud](https://console.cloud.google.com/) — for Places API (requires billing enabled)
- [Resend](https://resend.com/) — for email verification

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/TauheedCodez/DiAsure.git
cd DiAsure
```

---

### 2. Backend Setup

#### 2.1 Create a virtual environment

```bash
cd backend
python -m venv venv
```

#### 2.2 Activate the virtual environment

- **Windows (PowerShell):**
  ```powershell
  .\venv\Scripts\activate
  ```
- **macOS / Linux:**
  ```bash
  source venv/bin/activate
  ```

#### 2.3 Install Python dependencies

```bash
pip install -r requirements.txt
```

#### 2.4 Download ML Model Files

The model files are too large for GitHub and must be downloaded separately.
Download both files from **[Hugging Face](https://huggingface.co/TauheedDev/dfu_classification_model/tree/main)** and place them inside `backend/models/`:

| File                                  | Description                   |
| ------------------------------------- | ----------------------------- |
| `dfu_filter_mobilenetv2.h5`          | Foot vs. random image filter  |
| `resnet50_3class_phase2_best.h5`     | DFU severity classifier       |

Your `backend/models/` directory should look like:

```
backend/
└── models/
    ├── dfu_filter_mobilenetv2.h5
    └── resnet50_3class_phase2_best.h5
```

#### 2.5 Set up PostgreSQL

1. Open **pgAdmin** or your PostgreSQL client.
2. Create a new database (e.g., `diasure_db`).
3. Note your PostgreSQL credentials (username, password, host, port, database name).

#### 2.6 Configure environment variables

Create a `.env` file inside `backend/`:

```env
# Database
DATABASE_URL=postgresql://USERNAME:PASSWORD@localhost:5432/diasure_db

# JWT Authentication
JWT_SECRET_KEY=your_secret_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Groq AI Chat
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant

# Google Places API
GOOGLE_PLACES_API_KEY=your_google_api_key_here

# Resend (for email verification)
RESEND_API_KEY=your_resend_api_key_here

# Frontend URL (used in email verification links)
FRONTEND_URL=http://localhost:5173
```

> **Tip:** To generate a secure `JWT_SECRET_KEY`, run this in your terminal:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```
> Copy the output and use it as your secret key.

#### 2.7 Start the backend server

```bash
uvicorn main:app --reload
```

The API will be running at **http://localhost:8000**.

You can verify by visiting:
- Health check: [http://localhost:8000/health](http://localhost:8000/health)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 3. Frontend Setup

Open a **new terminal** and navigate to the frontend directory:

#### 3.1 Install dependencies

```bash
cd frontend
npm install
```

#### 3.2 Start the development server

```bash
npm run dev
```

The app will be running at **http://localhost:5173**.
