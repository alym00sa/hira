# HiRA - Quick Start Guide

Get HiRA running in 5 minutes!

## Prerequisites
- Python 3.9+
- Node.js 18+
- Anthropic API key (get one at https://console.anthropic.com/)

## 1. Backend Setup (Terminal 1)

```bash
# Navigate to backend
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env   # Windows
# cp .env.example .env   # Mac/Linux

# Edit .env and add your API key:
# ANTHROPIC_API_KEY=your_key_here

# Load core documents
python load_core_docs.py

# Start backend
uvicorn app.main:app --reload --port 8000
```

Backend running at: http://localhost:8000

## 2. Frontend Setup (Terminal 2)

```bash
# Navigate to frontend (new terminal!)
cd frontend

# Install dependencies
npm install

# Start frontend
npm run dev
```

Frontend running at: http://localhost:3000

## 3. Open the App

Visit http://localhost:3000 in your browser and start chatting with HiRA!

## First Steps

1. **Try the Chat**: Ask HiRA "What are the key principles of HRBA?"
2. **Upload a Document**: Go to Documents tab, upload a PDF
3. **Ask About Your Document**: Return to Chat and ask questions about it

## Troubleshooting

**"No module named 'app'"**
- Make sure you're in the `backend` directory
- Activate virtual environment first

**"Cannot find module"**
- Make sure you're in the `frontend` directory
- Run `npm install` first

**"Authentication error"**
- Check your API key in `backend/.env`
- Make sure it starts with `sk-ant-` (Anthropic) or `sk-` (OpenAI)

**"No documents found"**
- Run `python load_core_docs.py` from backend directory
- Check that `agent-rag-docs/` folder has PDF files

## Need More Help?

See the full README.md for detailed documentation!
