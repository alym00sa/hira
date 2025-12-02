# HiRA - Human Rights Assistant

HiRA is an AI-powered assistant that helps teams apply human rights-based approaches (HRBA) to their work. Currently implementing Phases 1, 3, and 4 of the MVP roadmap.

## Current Features

### Phase 1: RAG Foundation ✅
- **RAG-Powered Knowledge Base**: Two-tier document system (core + user documents)
- **Interactive Chat**: Ask HiRA questions and get responses grounded in your knowledge base
- **Document Upload**: Add organization-specific policies and guidelines
- **Source Citations**: HiRA cites sources naturally in responses
- **Warm & Professional Persona**: Designed to be helpful, inclusive, and human

### Phase 3: Meeting Archive ✅
- **Meeting Library**: View all past meetings with summaries
- **Structured Summaries**: Auto-generated summaries with action items, rights issues, risk flags
- **Shareable Links**: Share meeting summaries via public link
- **Transcript View**: Full transcript with searchable text
- **Manual Upload**: Upload transcripts and get AI-generated summaries

### Phase 4: Browser Extension ⏳
- Planned for future release
- See "Future Directions" below

## Phase 2: Zoom Bot (Current Focus 🚧)

**Goal**: HiRA joins Zoom meetings, transcribes in real-time, and generates structured summaries

**Approach**: Using **Recall.ai** as middleware service
- Recall.ai handles Zoom API complexity (no special approval needed)
- Provides real-time audio streaming via WebSocket
- Reference: [zoom-sidekick implementation](https://github.com/nsaigal/zoom-sidekick)

**Architecture**:
```
Zoom Meeting → Recall.ai Bot → WebSocket → HiRA Backend
                                              ↓
                                          Deepgram (STT)
                                              ↓
                                      Transcript Storage
                                              ↓
                                      LLM Summary Generation
```

**Implementation Steps**:
1. ✅ Research Recall.ai approach
2. ⏳ Sign up for Recall.ai account
3. ⏳ Build WebSocket endpoint for audio streaming
4. ⏳ Integrate Deepgram for real-time transcription
5. ⏳ Store transcripts in Meeting database
6. ⏳ Auto-generate summaries using existing LLM service
7. ⏳ Test full meeting flow end-to-end

**Requirements**:
- Recall.ai account + API key
- Deepgram API key (already in .env)
- Zoom Pro account (you have this)
- No special Zoom app approval needed!

## Architecture

### Backend (Python + FastAPI)
- FastAPI web framework
- ChromaDB vector database
- Anthropic Claude or OpenAI for LLM
- PDF/DOCX/TXT document processing
- RAG pipeline with embeddings and retrieval

### Frontend (React + Vite)
- React 18 with hooks
- React Router for navigation
- Axios for API communication
- Clean, responsive UI

## Project Structure

```
hrba-agent/
├── agent-rag-docs/          # Core knowledge base documents (human rights PDFs)
├── backend/
│   ├── app/
│   │   ├── api/routes/      # API endpoints
│   │   ├── core/            # Configuration
│   │   ├── models/          # Data schemas
│   │   ├── rag/             # RAG engine, vector store, document processor
│   │   ├── services/        # Business logic (chat, documents, LLM)
│   │   └── main.py          # FastAPI application
│   ├── data/                # Generated: uploads & vector database
│   ├── load_core_docs.py    # Utility to load core documents
│   ├── requirements.txt     # Python dependencies
│   └── .env                 # Configuration (create from .env.example)
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Chat and Documents pages
│   │   ├── services/        # API client
│   │   └── styles/          # CSS files
│   ├── package.json         # Node dependencies
│   └── vite.config.js       # Vite configuration
└── README.md                # This file
```

## Setup Instructions

### Prerequisites

- Python 3.9+
- Node.js 18+
- Anthropic API key OR OpenAI API key

### Step 1: Clone and Navigate

```bash
cd hrba-agent
```

### Step 2: Backend Setup

#### 2.1 Create Virtual Environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

#### 2.2 Install Dependencies

```bash
pip install -r requirements.txt
```

#### 2.3 Configure Environment

```bash
# Copy the example env file
copy .env.example .env    # Windows
cp .env.example .env      # Mac/Linux
```

Edit `.env` and add your API keys:

```env
# Required: Choose one
ANTHROPIC_API_KEY=your_anthropic_api_key_here
# OR
OPENAI_API_KEY=your_openai_api_key_here

# LLM Configuration
LLM_PROVIDER=anthropic  # or "openai"
LLM_MODEL=claude-3-5-sonnet-20241022  # or "gpt-4-turbo"
```

#### 2.4 Load Core Knowledge Base

This loads all PDFs from `agent-rag-docs` as core documents:

```bash
python load_core_docs.py
```

You should see output confirming documents were processed and chunked.

### Step 3: Frontend Setup

Open a **new terminal** (keep backend terminal open):

```bash
cd frontend
npm install
```

### Step 4: Run the Application

#### Terminal 1: Start Backend

```bash
cd backend
# Activate venv if not already activated
venv\Scripts\activate   # Windows
source venv/bin/activate  # Mac/Linux

# Run FastAPI
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`

#### Terminal 2: Start Frontend

```bash
cd frontend
npm run dev
```

Frontend will be available at: `http://localhost:3000`

### Step 5: Open the App

Navigate to `http://localhost:3000` in your browser.

## Usage Guide

### Chat with HiRA

1. Go to the **Chat** page (default)
2. Type your question in the input box
3. Press Enter or click Send
4. HiRA will respond with information from the knowledge base
5. View source citations below each response

**Example questions:**
- "What are the key principles of HRBA?"
- "How do I ensure participation in program design?"
- "What does the UNESCO report say about AI and human rights?"

### Upload Documents

1. Go to the **Documents** page
2. Click "Select File" in the upload section
3. Choose a PDF, DOCX, TXT, or MD file (max 50MB)
4. Wait for processing (you'll see chunk count when done)
5. The document is now part of HiRA's knowledge base
6. Ask questions about your uploaded documents in Chat

### Manage Documents

- **View**: See all uploaded documents with metadata
- **Delete**: Click the trash icon to remove your documents
- **Core docs** (from agent-rag-docs) are protected and cannot be deleted by users

## Two-Tier Document System

HiRA uses a two-tier knowledge base:

### Core Documents (Developer-Managed)
- Located in `agent-rag-docs/`
- Loaded via `load_core_docs.py`
- Available to ALL users
- Cannot be deleted by users
- Contains foundational human rights knowledge

### User Documents (User-Managed)
- Uploaded via the web interface
- Private to each user/organization
- Can be added, viewed, and deleted by users
- Augments core knowledge with specific policies

When answering questions, HiRA searches **both** core and user documents.

## API Endpoints

### Chat
- `POST /api/v1/chat` - Send a message to HiRA
- `GET /api/v1/chat/history/{conversation_id}` - Get conversation history

### Documents
- `POST /api/v1/documents/upload` - Upload a document
- `GET /api/v1/documents` - List all documents
- `GET /api/v1/documents/{document_id}` - Get document details
- `DELETE /api/v1/documents/{document_id}` - Delete a document

### Health
- `GET /api/v1/health` - Check API status

Full API documentation: `http://localhost:8000/docs` (when backend is running)

## Development

### Adding Core Documents

1. Add PDF/TXT/MD files to `agent-rag-docs/`
2. Run the loader script:
   ```bash
   cd backend
   python load_core_docs.py
   ```

### Resetting the Knowledge Base

To clear all documents and start fresh:

```bash
cd backend
python load_core_docs.py --reset
```

Then reload core documents with `python load_core_docs.py`

### Configuration Options

Edit `backend/app/core/config.py` or `.env` to customize:

- **Chunk size and overlap**: Control how documents are split
- **Retrieval settings**: Number of chunks to retrieve (TOP_K_RETRIEVAL)
- **Similarity threshold**: Minimum relevance score for chunks
- **LLM temperature**: Control response creativity
- **File size limits**: Maximum upload size

## Troubleshooting

### Backend won't start
- Ensure virtual environment is activated
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Verify API keys are set in `.env`

### No documents found
- Run `python load_core_docs.py` to load core documents
- Check that `agent-rag-docs/` contains PDF files

### Frontend can't connect to backend
- Ensure backend is running on port 8000
- Check browser console for CORS errors
- Verify proxy configuration in `frontend/vite.config.js`

### Upload fails
- Check file size (max 50MB)
- Verify file type is supported (.pdf, .docx, .txt, .md)
- Check backend logs for processing errors

## Technology Stack

### Backend
- **FastAPI**: Web framework
- **ChromaDB**: Vector database for embeddings
- **Anthropic Claude** or **OpenAI GPT**: LLM for responses
- **PyPDF2**: PDF text extraction
- **Pydantic**: Data validation

### Frontend
- **React 18**: UI framework
- **Vite**: Build tool
- **React Router**: Navigation
- **Axios**: HTTP client
- **Lucide React**: Icons

## Development Status

- ✅ **Phase 1**: RAG foundation, chat, documents - **COMPLETE**
- 🚧 **Phase 2**: Zoom bot integration - **IN PROGRESS** (Recall.ai approach)
- ✅ **Phase 3**: Meeting archive and summaries - **COMPLETE**
- ⏳ **Phase 4**: Browser extension - **PLANNED**
- ⏳ **Phase 5**: Polish and refinement - **PLANNED**

See `PRD.MD` for full roadmap and detailed requirements.

## Future Directions

### Browser Extension (Grammarly-Style)
**Vision**: Real-time HRBA suggestions as you type on any website

**Features** (designed but not yet implemented):
- Monitors text inputs across all webpages (Gmail, Google Docs, Notion, etc.)
- Automatic analysis against RAG knowledge base
- Inline suggestions with visual indicators (like Grammarly underlines)
- One-click rewrites based on HRBA principles
- Rights issue detection with citations from your documents

**Status**: Initial implementation in `extension/` folder
- Manifest V3 Chrome extension
- Content script for text monitoring
- Backend endpoint for RAG-based analysis
- Grammarly-style floating overlay UI

**Next Steps**: Complete after Zoom bot is fully functional

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

[Your License Here]

## Support

For issues or questions, please open a GitHub issue.

---

**Built with care for human rights work 🌍**
