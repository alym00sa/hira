import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Calendar, Users, Clock, AlertCircle, Loader2, FileText, Trash2, Search, ChevronDown, ChevronUp } from 'lucide-react'
import { meetingsAPI } from '../services/api'
import '../styles/MeetingsPage.css'

function MeetingsPage() {
  const [meetings, setMeetings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedActionItems, setExpandedActionItems] = useState({})
  const navigate = useNavigate()

  useEffect(() => {
    loadMeetings()
  }, [])

  const loadMeetings = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await meetingsAPI.list()
      setMeetings(response.meetings || [])
    } catch (err) {
      console.error('Error loading meetings:', err)
      setError('Failed to load meetings. Please ensure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatDuration = (minutes) => {
    if (!minutes) return 'Duration unknown'
    if (minutes < 60) return `${minutes}m`
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`
  }

  const handleMeetingClick = (meetingId) => {
    navigate(`/meetings/${meetingId}`)
  }

  const handleDelete = async (meetingId, e) => {
    e.stopPropagation()
    if (confirm('Delete this meeting? This cannot be undone.')) {
      try {
        await meetingsAPI.delete(meetingId)
        setMeetings(prev => prev.filter(m => m.id !== meetingId))
      } catch (err) {
        console.error('Error deleting meeting:', err)
        alert('Failed to delete meeting')
      }
    }
  }

  const toggleActionItems = (meetingId, e) => {
    e.stopPropagation()
    setExpandedActionItems(prev => ({
      ...prev,
      [meetingId]: !prev[meetingId]
    }))
  }

  const filteredMeetings = meetings.filter(meeting => {
    if (!searchQuery) return true
    const query = searchQuery.toLowerCase()
    return (
      meeting.title?.toLowerCase().includes(query) ||
      meeting.summary?.toLowerCase().includes(query) ||
      meeting.key_topics?.some(topic => topic.toLowerCase().includes(query))
    )
  })

  return (
    <div className="meetings-page">
      <div className="meetings-container">
        <div className="meetings-header">
          <div>
            <h1>Meeting Archive</h1>
            <p>Review past meetings, transcripts, and structured summaries</p>
          </div>
        </div>

        <div className="meetings-controls">
          <div className="search-bar">
            <Search size={18} />
            <input
              type="text"
              placeholder="Search meetings by title, summary, or topics..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        {loading ? (
          <div className="loading-state">
            <Loader2 size={32} className="spinner" />
            <p>Loading meetings...</p>
          </div>
        ) : error ? (
          <div className="error-state">
            <AlertCircle size={32} />
            <p>{error}</p>
            <button onClick={loadMeetings} className="retry-button">
              Try Again
            </button>
          </div>
        ) : meetings.length === 0 ? (
          <div className="empty-state">
            <FileText size={48} />
            <p>No meetings yet</p>
            <p className="empty-subtitle">
              Meetings will appear here once created
            </p>
          </div>
        ) : (
          <div className="meetings-list">
              {filteredMeetings.map((meeting) => (
                <div
                  key={meeting.id}
                  className="meeting-card"
                  onClick={() => handleMeetingClick(meeting.id)}
                >
                  <div className="meeting-card-header">
                    <h3 className="meeting-title">{meeting.title}</h3>
                    <div className="meeting-card-actions">
                      {meeting.processed && (
                        <span className="badge badge-success">Processed</span>
                      )}
                      <button
                        className="meeting-delete-btn"
                        onClick={(e) => handleDelete(meeting.id, e)}
                        title="Delete meeting"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>

                  <div className="meeting-meta">
                    <div className="meta-item">
                      <Calendar size={16} />
                      <span>{formatDate(meeting.date)}</span>
                    </div>
                    {meeting.duration_minutes && (
                      <div className="meta-item">
                        <Clock size={16} />
                        <span>{formatDuration(meeting.duration_minutes)}</span>
                      </div>
                    )}
                    {meeting.participants && meeting.participants.length > 0 && (
                      <div className="meta-item">
                        <Users size={16} />
                        <span>{meeting.participants.length} participants</span>
                      </div>
                    )}
                  </div>

                  {meeting.summary && (
                    <p className="meeting-summary">{meeting.summary}</p>
                  )}

                  {meeting.key_topics && meeting.key_topics.length > 0 && (
                    <div className="meeting-topics">
                      {meeting.key_topics.slice(0, 3).map((topic, idx) => (
                        <span key={idx} className="topic-badge">{topic}</span>
                      ))}
                      {meeting.key_topics.length > 3 && (
                        <span className="topic-badge">+{meeting.key_topics.length - 3} more</span>
                      )}
                    </div>
                  )}

                  {meeting.action_items && meeting.action_items.length > 0 && (
                    <div className="meeting-card-action-items">
                      <button
                        className="action-items-toggle-btn"
                        onClick={(e) => toggleActionItems(meeting.id, e)}
                      >
                        {expandedActionItems[meeting.id] ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                        <span>Action Items ({meeting.action_items.length})</span>
                      </button>
                      {expandedActionItems[meeting.id] && (
                        <div className="action-items-list-card">
                          {meeting.action_items.map((item, idx) => (
                            <div key={idx} className="action-item-inline">
                              <span className="action-item-bullet">•</span>
                              <span>{typeof item === 'string' ? item : item.item || item}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
        )}
      </div>
    </div>
  )
}

export default MeetingsPage
