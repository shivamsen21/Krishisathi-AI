# 🌱 KrishiSathi AI (AgroVision AI)

<p align="center">
  <b>Smart Crop Protection & Disease Detection Powered by Deep Learning & Supabase</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python" alt="Python Version" />
  <img src="https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C?logo=pytorch" alt="PyTorch" />
  <img src="https://img.shields.io/badge/Supabase-Database%20%26%20Auth-3ECF8E?logo=supabase" alt="Supabase" />
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License" />
</p>

---

## 📖 Overview

**KrishiSathi AI** (also known as **AgroVision AI**) is a comprehensive smart agriculture web platform designed to empower farmers, agronomists, and researchers. By combining computer vision powered by transfer-learned **MobileNetV2** and modern cloud infrastructure powered by **FastAPI** and **Supabase**, the system delivers instant, reliable plant disease diagnosis, actionable treatment recommendations, and an intelligent agronomy chatbot.

The platform is designed to operate with resilience: it connects directly to a live Supabase backend for cloud authentication and history synchronization, while also providing built-in in-memory fallback mechanisms for local development and offline environments.

---

## ✨ Key Features

- 🌿 **Real-time Crop Disease Detection**:
  - Fine-tuned MobileNetV2 architecture trained on crop leaf imagery.
  - Multi-crop support (Tomato, Potato, Corn, Apple, Grape, Pepper, and more).
  - Multi-class classification with top-3 confidence rankings and low-confidence validation safeguards.
  - Instant disease insights: symptoms, biological cause, preventive actions, and chemical/organic treatments.

- 🤖 **AI Agronomy Assistant**:
  - Interactive chatbot for farmers and growers.
  - Answers queries on crop health, soil management, seasonal pest cycles, fertilizer application, and irrigation.

- 📊 **Farmer Dashboard & Historical Records**:
  - Complete history log of leaf scans with disease status, confidence score, and timestamp.
  - Search, filter, and modal drill-down into historical analyses.
  - Visual summary cards showing total scans, healthy vs. infected ratios, and prevalent pathogens.

- 🛡️ **Role-Based Access Control (RBAC)**:
  - Separate portals for **Farmers** and **Administrators**.
  - Secure authentication via Supabase Auth with fallback JWT token support.
  - Admin dashboard displaying platform-wide analytics, surveillance stats, and system diagnostics.

- ⚡ **Developer-Friendly Dual Mode**:
  - Fully functional with a live Supabase project.
  - Automatically falls back to local dev mock services when remote credentials are not configured, enabling immediate zero-configuration onboarding.

- 🧪 **End-to-End ML Pipeline**:
  - Complete dataset downloader and processor (`ml/prepare_dataset.py`, `prepare_dataset.py`).
  - Two-stage training workflow (frozen classifier head followed by backbone fine-tuning).
  - Evaluation tool generating normalized and raw confusion matrices and precision/recall metrics.

---

## 🏗️ Architecture & Technology Stack

```
KrishiSathi AI
├── Backend (FastAPI, PyTorch, Uvicorn, Pydantic v2)
├── Frontend (HTML5, Modern CSS Glassmorphism, Vanilla JS ES6+)
├── Machine Learning (MobileNetV2, Torchvision, Scikit-learn)
└── Database & Auth (Supabase PostgreSQL, Row-Level Security, JWT)
```

| Component | Technologies |
| :--- | :--- |
| **Backend API** | FastAPI, Uvicorn, Pydantic v2, Python-Multipart |
| **Deep Learning** | PyTorch, Torchvision, Pillow, NumPy, Scikit-Learn |
| **Database & Auth** | Supabase (PostgreSQL), PyJWT |
| **Frontend UI** | Semantic HTML5, Vanilla CSS3 (Custom Design System), Vanilla JavaScript |
| **Icons & Fonts** | FontAwesome 6, Google Fonts |
| **Testing** | Pytest, Pytest-asyncio, HTTPX |

---

## 📂 Project Directory Structure

```plaintext
krishisathi-ai/
├── backend/                  # FastAPI Application Source Code
│   ├── config.py             # App settings & pydantic-settings environment loading
│   ├── dependencies.py       # Authentication & security dependency injection
│   ├── main.py               # Application entrypoint & CORS middleware
│   ├── requirements.txt      # Backend-specific package requirements
│   ├── routes/               # API Routers
│   │   ├── admin.py          # Admin metrics and management endpoints
│   │   ├── auth.py           # Login, registration, token verification
│   │   ├── chatbot.py        # Agronomy AI assistant conversation endpoints
│   │   ├── history.py        # Farmer prediction history & filtering
│   │   └── prediction.py     # Leaf image upload & ML inference endpoint
│   ├── schemas/              # Pydantic data validation models
│   │   ├── auth.py
│   │   ├── chatbot.py
│   │   └── prediction.py
│   ├── services/             # Core business logic
│   │   ├── model_service.py  # Image preprocessing, model inference & fallback
│   │   └── supabase_service.py # Supabase client & in-memory dev fallback
│   ├── tests/                # Automated API test suite
│   │   └── test_api.py
│   └── uploads/              # Local storage for uploaded scan images (.gitkeep)
├── frontend/                 # Client-side Web Application
│   ├── index.html            # Landing page
│   ├── detection.html        # Leaf upload & disease diagnostic page
│   ├── dashboard.html        # Farmer overview & statistics
│   ├── history.html          # Scan history & detailed record viewer
│   ├── assistant.html        # Agronomy chatbot interface
│   ├── login.html            # Farmer sign in
│   ├── register.html         # Farmer registration
│   ├── profile.html          # Farmer user profile settings
│   ├── admin-login.html      # Administrator portal login
│   ├── admin-dashboard.html  # Administrator analytics dashboard
│   ├── css/                  # Styling & themes
│   └── js/                   # API clients and UI interactivity
├── ml/                       # Machine Learning Pipeline
│   ├── train.py              # Two-phase transfer learning training script
│   ├── evaluate.py           # Model evaluation and confusion matrix generator
│   ├── predict.py            # Standalone CLI prediction utility
│   ├── preprocessing.py      # Image transforms & augmentations
│   ├── model.py              # MobileNetV2 architecture definition
│   ├── prepare_dataset.py    # Dataset processing & train/val/test splitter
│   ├── dataset/              # Dataset storage folder (.gitkeep)
│   ├── models/               # Saved model checkpoints (.gitkeep)
│   └── results/              # Evaluation plots & reports (.gitkeep)
├── supabase/                 # Supabase Infrastructure
│   ├── schema.sql            # PostgreSQL schema, triggers & RLS policies
│   └── complete_schema.sql   # Standalone SQL migration script with seed diseases
├── .env.example              # Sample environment configuration file
├── .gitignore                # Production-grade git ignore configuration
├── conftest.py               # Pytest test fixtures
├── prepare_dataset.py        # HuggingFace PlantVillage dataset downloader
├── requirements.txt          # Unified dependencies file
├── run.py                    # Root server startup utility
└── README.md                 # Project documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites

- **Python**: Version `3.10` or higher
- **Git**: Installed on your system
- **Pip**: Latest version

### 2. Clone the Repository

```bash
git clone https://github.com/shivamsen21/Krishisathi-AI.git
cd Krishisathi-AI
```

### 3. Create and Activate a Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

Install all necessary packages via the unified `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## ⚙️ Environment Configuration

1. Create your local environment file by copying `.env.example`:

   ```bash
   cp .env.example .env
   ```

2. Open `.env` and configure your settings:

   ```ini
   # Supabase Configuration (Optional for local testing)
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_ANON_KEY=your-anon-key-here
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

   # Authentication Secret
   JWT_SECRET=your-secure-jwt-secret-here

   # Application Mode
   APP_ENV=development
   HOST=0.0.0.0
   PORT=8000
   ```

> **Note**: If `SUPABASE_URL` is omitted or empty, the backend automatically activates **In-Memory Local Dev Mode**. In this mode, user registration, login, scan history, and chatbot operations function in-memory without needing an active Supabase project.

---

## 🗄️ Supabase Database Setup (Optional for Cloud Mode)

To enable persistent cloud storage, real-time sync, and Supabase Auth:

1. Create a new project on [Supabase](https://supabase.com).
2. Open the **SQL Editor** in your Supabase dashboard.
3. Open [`supabase/complete_schema.sql`](supabase/complete_schema.sql), copy its entire content, and execute it.
4. The script creates:
   - `profiles` table with row-level security and trigger on user registration.
   - `predictions` table storing diagnosis records, confidence, symptoms, and image URLs.
   - `diseases` knowledgebase table pre-populated with disease descriptions and treatments.
   - `chat_messages` table storing farmer assistant dialogues.
5. Copy your project's **Project URL**, **Anon Key**, and **Service Role Key** into your `.env` file.

---

## 💻 Running the Application

### Step 1: Start the Backend API

You can start the server using either the convenient startup runner or Uvicorn directly:

```bash
# Using run.py
python run.py

# Or directly with uvicorn
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

The backend will start at:
- **API Endpoint**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`

### Step 2: Open the Frontend

You can serve the frontend using any static file server or your browser:

**Using Python's built-in HTTP server:**
```bash
cd frontend
python -m http.server 3000
```
Then visit: `http://localhost:3000`

**Or using VS Code Live Server:**
Right-click on `frontend/index.html` and choose **"Open with Live Server"**.

---

## 🧪 Running Automated Tests

A comprehensive Pytest test suite verifies authentication, health check endpoints, mock fallback modes, and prediction payloads:

```bash
pytest -v
```

All tests execute against local mock fixtures and do not require external cloud connectivity.

---

## 🧠 Machine Learning Workflow

The `ml/` directory contains tools to prepare data and train custom models:

### 1. Prepare Dataset
```bash
python ml/prepare_dataset.py --source /path/to/raw_images --output ml/dataset
```

### 2. Train MobileNetV2
```bash
python ml/train.py --data ml/dataset --epochs 30 --batch-size 32
```
Trained weights will be saved to `ml/models/crop_disease_mobilenetv2.pth`.

### 3. Evaluate Model
```bash
python ml/evaluate.py --model ml/models/crop_disease_mobilenetv2.pth
```
Evaluation metrics and confusion matrix plots are saved to `ml/results/`.

---

## 🔒 Security & Data Hygiene

- `.env` and any credential files are strictly ignored via `.gitignore`.
- Image uploads are restricted to supported MIME types (`image/jpeg`, `image/png`, `image/webp`) with a 10MB size limit.
- Model weights, raw datasets, and temporary extraction artifacts are excluded from git tracking to keep the repository lightweight and portable.

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch: `git checkout -b feature/your-feature-name`.
3. Commit your changes: `git commit -m "Add new feature"`.
4. Push to your branch: `git push origin feature/your-feature-name`.
5. Open a Pull Request.

---

## 📄 License

This project is licensed under the MIT License — feel free to use and modify for educational, research, and commercial purposes.
