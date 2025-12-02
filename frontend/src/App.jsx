import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import { MessageSquare, Upload, FileText, Calendar, Bot } from 'lucide-react'
import ChatPage from './pages/ChatPage'
import DocumentsPage from './pages/DocumentsPage'
import MeetingsPage from './pages/MeetingsPage'
import MeetingDetailPage from './pages/MeetingDetailPage'
import BotPage from './pages/BotPage'
import './styles/App.css'

function App() {
  return (
    <Router>
      <div className="app">
        <nav className="navbar">
          <div className="nav-content">
            <Link to="/" className="nav-brand">
              <h1>HiRA</h1>
            </Link>
            <div className="nav-links">
              <Link to="/" className="nav-link">
                <MessageSquare size={20} />
                <span>Chat</span>
              </Link>
              <Link to="/documents" className="nav-link">
                <FileText size={20} />
                <span>Documents</span>
              </Link>
              <Link to="/meetings" className="nav-link">
                <Calendar size={20} />
                <span>Meetings</span>
              </Link>
              <Link to="/bot" className="nav-link">
                <Bot size={20} />
                <span>Bot</span>
              </Link>
            </div>
          </div>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<ChatPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/meetings" element={<MeetingsPage />} />
            <Route path="/meetings/:meetingId" element={<MeetingDetailPage />} />
            <Route path="/bot" element={<BotPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
