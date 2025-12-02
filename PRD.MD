# Product Requirements Document (PRD)
# **HiRA — Human Rights Assistant (MVP)**  
**Version:** 1.0  
**Date:** 2025  

---

# 1. Product Overview

## 1.1 Vision
HiRA is a real-time **Human Rights Assistant** that joins Zoom meetings, takes notes, answers questions when addressed, and helps teams frame their work through a human-rights-based approach (HRBA). It also provides post-meeting summaries, a chat interface for deeper inquiry, and a browser extension that offers rights-focused improvements to written text.

HiRA is designed to be:
- warm  
- human  
- professional  
- inclusive  
- grounded strictly in her provided knowledge base  

## 1.2 Goal of MVP
Deliver an end-to-end functional system that:
- attends Zoom meetings as a bot participant  
- takes structured notes  
- responds when addressed  
- uses a RAG pipeline based on user-supplied documents  
- provides a web interface for chat + meeting archive  
- offers a browser extension for rights-framing suggestions  

---

# 2. Core User Personas

### 1. Program Officer / NGO Staff
Needs help applying HRBA principles during planning or meetings.

### 2. Policy Writer
Needs help ensuring their documents reflect non-discrimination, participation, accountability, and inclusion.

### 3. Meeting Facilitator
Wants real-time support & structured output after meetings.

---

# 3. User Stories

### Meeting Interaction
- “As a meeting participant, I want HiRA to join automatically and take notes.”
- “As a participant, I want to say ‘Hey HiRA…’ and get an accurate, concise answer.”
- “As a participant, I want to tag @HiRA in chat and get a quick response.”

### Post-Meeting
- “As a user, I want transcript and summary views of every meeting.”
- “As a user, I want action items clearly extracted.”
- “As a user, I want risk and rights flags surfaced in the summary.”

### Ongoing Support
- “As a user, I want to chat with HiRA using my documents as the knowledge base.”
- “As a user, I want to upload my organization’s policies so HiRA can use them.”

### Browser Extension
- “As a policy writer, I want HiRA to offer rights-framing suggestions in a sidebar while writing text online.”

---

# 4. Scope (MVP)

## 4.1 In-Scope
- Zoom meeting bot  
- Real-time transcription (no recording stored)  
- Trigger detection via speech and chat  
- RAG pipeline built from user-supplied documents  
- Web app with Google login  
- Meeting library (transcripts & summaries)  
- Chat with HiRA  
- Document uploads  
- Browser extension sidebar  
- Cloud-based model processing  

## 4.2 Out of Scope (MVP)
- Audio/video recording storage  
- Organization-level admin dashboards  
- Fine-grained role permissions  
- Offline mode  
- Custom avatars & branding  
- Advanced analytics  

---

# 5. Functional Requirements

## 5.1 Zoom Bot

### FR-1: Bot Participation  
HiRA joins all scheduled Zoom meetings automatically (MVP logic can assume all meetings).

### FR-2: Privacy Announcement  
Upon joining:
- Sends a one-time chat message introducing itself  
- Notes that it is taking notes  
- States that it will respond when prompted  

### FR-3: Real-Time Audio Processing  
The system must:
- Capture audio from the meeting  
- Convert to text in real-time  
- Feed into trigger detection + note-taking  

### FR-4: Trigger Detection  
HiRA activates when:
- Speech contains “Hey HiRA” + natural variants  
- Chat includes “@HiRA” or equivalent  

### FR-5: Response Behavior  
- Wait 0.5–1 second before responding  
- Speak via Zoom audio (TTS)  
- Provide relevant, concise answers  
- Use citations from RAG documents where appropriate  
- Tone: warm, human, inclusive, professional  

### FR-6: Safety & Hallucination Control  
- HiRA only cites documents that exist in the RAG database.  
- If unsure, HiRA says:  
  “Based on the documents I have, I don’t have information on this.”  

---

## 5.2 Meeting Notes System

### FR-7: Transcript  
Full transcript with:
- Speaker labels  
- Timestamps  

### FR-8: Structured Summary  
Automatically generate:
- Key topics  
- Action items  
- Rights issues  
- Risk flags  
- Obligations  
- Key stakeholders  
- Next steps  

### FR-9: Storage & Access  
- Stored in the web app  
- Accessible via link without login  

---

## 5.3 RAG Knowledge Base

### FR-10: User-Supplied Documents  
The RAG corpus consists *only* of documents uploaded by the owner/user.

### FR-11: Document Ingestion  
- Chunking  
- Embedding  
- Versioning  
- Optional auto-update toggle  

### FR-12: Citation Behavior  
When HiRA answers questions, references must be:
- natural language  
- sourced from provided documents  

Examples:
- “According to your Equity Policy…”  
- “In the HRBA Guide uploaded to your workspace…”  

---

## 5.4 Web App

### FR-13: Authentication  
Google login (OAuth).

### FR-14: Meeting Library  
Each entry includes:
- Transcript  
- Summary  
- Action items  
- Rights flags  

### FR-15: Chat with HiRA  
- Persistent chat interface  
- Private chat threads per user  
- Optional org-shared threads  

### FR-16: Document Upload  
Users can upload:
- policies  
- guidelines  
- frameworks  
- manuals  

Documents become part of the RAG DB.

---

## 5.5 Browser Extension

### FR-17: Sidebar UI  
Users click extension → opens a sidebar.

### FR-18: Text Processing  
HiRA should:
- Read selected text or auto-detect text  
- Offer rights-based suggestions  
- Provide risk prompting questions  
- Give rewrite options  
- Include contextual citations  

### FR-19: Cloud-Based Model  
All inference is done server-side for MVP.

---

# 6. Non-Functional Requirements

### NFR-1: Latency  
HiRA must respond in meetings within 1–3 seconds.

### NFR-2: Data Privacy  
- No audio/video stored  
- Meeting notes stored only as text  
- Only user-uploaded documents are used for RAG  

### NFR-3: Scalability  
Must support multiple concurrent meetings (future).

### NFR-4: Tone Consistency  
All outputs must match HiRA’s persona (warm, human, inclusive, professional).

### NFR-5: Error Handling  
If HiRA cannot answer, it states this politely.

---

# 7. Success Metrics

### Primary
- HiRA correctly responds to “Hey HiRA” > 85% of the time  
- Summaries produced for 100% of meetings  
- Browser extension suggestions accepted by users > 30%  
- Chat users return weekly  

### Secondary
- Number of uploaded documents  
- Accuracy of citations  
- Reduction in revision cycles for policy language  

---

# 8. Architecture Overview

### Components
1. **Zoom Meeting Bot Service**
   - WebSocket to Zoom  
   - STT engine  
   - Trigger detection  
   - Real-time response generation  
   - Note-taking pipeline  

2. **RAG Engine**
   - Vector database  
   - Embedding API  
   - Chunk store  
   - Citation mapping  

3. **HiRA Brain (LLM Orchestration Layer)**
   - Prompting  
   - Context injection  
   - Response synthesis  
   - Safety rails  

4. **Web App**
   - Front-end (React/Vue)  
   - Backend (Node/Python/Go)  
   - Meeting repository  
   - Chat interface  
   - Document upload  

5. **Browser Extension**
   - Manifest v3  
   - Sidebar UI  
   - Backend API communication  

---

# 9. Roadmap

## Phase 1 — Foundations
- RAG pipeline  
- Chat interface  
- Document upload  

## Phase 2 — Zoom Bot
- Live transcription  
- Trigger detection  
- Chat + voice responses  
- Meeting notes generation  

## Phase 3 — Web App Expansion
- Meeting archive  
- Sharing by link  
- Summaries with labels  

## Phase 4 — Browser Extension
- Sidebar  
- Rewrite suggestions  
- Rights flags  
- Citations  

## Phase 5 — Polish
- Tone refinement  
- Model tuning  
- UI/UX improvements  

---

# End of Document