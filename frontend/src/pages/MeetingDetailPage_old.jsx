import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Calendar, Users, Clock, AlertTriangle, CheckCircle, Flag, User, ArrowRight, Loader2, Share2, Trash2, Edit2, Save, X, Plus, Minus } from 'lucide-react'
import { meetingsAPI } from '../services/api'
import '../styles/MeetingDetailPage.css'

function MeetingDetailPage() {
  const { meetingId } = useParams()
  const navigate = useNavigate()
  const [meeting, setMeeting] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('summary')
  const [shareLink, setShareLink] = useState(null)
  const [copying, setCopying] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editedText, setEditedText] = useState('')

  useEffect(() => {
    loadMeeting()
  }, [meetingId])

  const loadMeeting = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await meetingsAPI.get(meetingId)
      setMeeting(data)
    } catch (err) {
      console.error('Error loading meeting:', err)
      setError('Failed to load meeting details')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateShareLink = async () => {
    try {
      const result = await meetingsAPI.createShareLink(meetingId)
      const fullUrl = `${window.location.origin}/meetings/share/${result.share_token}`
      setShareLink(fullUrl)
    } catch (err) {
      console.error('Error creating share link:', err)
      alert('Failed to create share link')
    }
  }

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(shareLink)
      setCopying(true)
      setTimeout(() => setCopying(false), 2000)
    } catch (err) {
      alert('Failed to copy link')
    }
  }

  const handleDelete = async () => {
    if (confirm('Delete this meeting? This cannot be undone.')) {
      try {
        await meetingsAPI.delete(meetingId)
        navigate('/meetings')
      } catch (err) {
        console.error('Error deleting meeting:', err)
        alert('Failed to delete meeting')
      }
    }
  }

  const formatMeetingAsText = (meeting) => {
    let text = ''

    if (meeting.summary) {
      text += `SUMMARY:\n${meeting.summary}\n\n`
    }

    const participants = meeting.key_stakeholders || meeting.participants || []
    if (participants.length > 0) {
      text += `PARTICIPANTS:\n${participants.map(p => `- ${p}`).join('\n')}\n\n`
    }

    if (meeting.structured_notes && Object.keys(meeting.structured_notes).length > 0) {
      text += `MEETING NOTES:\n`
      Object.entries(meeting.structured_notes).forEach(([topic, notes]) => {
        text += `\n## ${topic}\n`
        if (Array.isArray(notes)) {
          notes.forEach(note => {
            text += `- ${note}\n`
          })
        }
      })
      text += '\n'
    }

    if (meeting.next_steps && meeting.next_steps.length > 0) {
      text += `NEXT STEPS:\n${meeting.next_steps.map(s => `- ${s}`).join('\n')}\n`
    }

    return text
  }

  const parseMeetingText = (text) => {
    const lines = text.split('\n')
    let summary = ''
    const participants = []
    const structured_notes = {}
    const next_steps = []

    let currentSection = ''
    let currentTopic = ''

    for (let line of lines) {
      line = line.trim()

      if (line === 'SUMMARY:') {
        currentSection = 'summary'
        continue
      } else if (line === 'PARTICIPANTS:') {
        currentSection = 'participants'
        continue
      } else if (line === 'MEETING NOTES:') {
        currentSection = 'notes'
        continue
      } else if (line === 'NEXT STEPS:') {
        currentSection = 'next_steps'
        continue
      }

      if (currentSection === 'summary' && line && !line.startsWith('##') && !line.startsWith('-')) {
        summary += (summary ? ' ' : '') + line
      } else if (currentSection === 'participants' && line.startsWith('-')) {
        participants.push(line.substring(1).trim())
      } else if (currentSection === 'notes') {
        if (line.startsWith('##')) {
          currentTopic = line.substring(2).trim()
          structured_notes[currentTopic] = []
        } else if (line.startsWith('-') && currentTopic) {
          structured_notes[currentTopic].push(line.substring(1).trim())
        }
      } else if (currentSection === 'next_steps' && line.startsWith('-')) {
        next_steps.push(line.substring(1).trim())
      }
    }

    return { summary, key_stakeholders: participants, structured_notes, next_steps }
  }

  const handleEdit = () => {
    setEditedText(formatMeetingAsText(meeting))
    setIsEditing(true)
  }

  const handleSave = async () => {
    try {
      const updateData = parseMeetingText(editedText)
      await meetingsAPI.update(meetingId, updateData)

      setMeeting({
        ...meeting,
        ...updateData
      })

      setIsEditing(false)
    } catch (err) {
      console.error('Error updating meeting:', err)
      alert('Failed to update meeting')
    }
  }

  const handleCancelEdit = () => {
    setIsEditing(false)
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (loading) {
    return (
      <div className="meeting-detail-page">
        <div className="loading-container">
          <Loader2 size={48} className="spinner" />
          <p>Loading meeting...</p>
        </div>
      </div>
    )
  }

  if (error || !meeting) {
    return (
      <div className="meeting-detail-page">
        <div className="error-container">
          <AlertTriangle size={48} />
          <p>{error || 'Meeting not found'}</p>
          <button onClick={() => navigate('/meetings')} className="back-button">
            Back to Meetings
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="meeting-detail-page">
      <div className="meeting-detail-container">
        {/* Header */}
        <div className="meeting-detail-header">
          <button onClick={() => navigate('/meetings')} className="back-link">
            <ArrowLeft size={20} />
            <span>Back to Meetings</span>
          </button>

          <h1>{meeting.title}</h1>

          <div className="meeting-info">
            <div className="info-item">
              <Calendar size={18} />
              <span>{formatDate(meeting.date)}</span>
            </div>
            {meeting.duration_minutes && (
              <div className="info-item">
                <Clock size={18} />
                <span>{meeting.duration_minutes} minutes</span>
              </div>
            )}
            {meeting.participants && meeting.participants.length > 0 && (
              <div className="info-item">
                <Users size={18} />
                <span>{meeting.participants.join(', ')}</span>
              </div>
            )}
          </div>

          <div className="header-actions">
            {!meeting.is_public && (
              <button onClick={handleCreateShareLink} className="share-button">
                <Share2 size={18} />
                <span>Create Share Link</span>
              </button>
            )}
            {shareLink && (
              <div className="share-link-container">
                <input type="text" value={shareLink} readOnly className="share-link-input" />
                <button onClick={handleCopyLink} className="copy-button">
                  {copying ? 'Copied!' : 'Copy'}
                </button>
              </div>
            )}
            <button onClick={handleDelete} className="delete-button" title="Delete meeting">
              <Trash2 size={18} />
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="tabs">
          <button
            className={`tab ${activeTab === 'summary' ? 'active' : ''}`}
            onClick={() => setActiveTab('summary')}
          >
            Summary
          </button>
          <button
            className={`tab ${activeTab === 'transcript' ? 'active' : ''}`}
            onClick={() => setActiveTab('transcript')}
          >
            Transcript
          </button>
        </div>

        {/* Content */}
        <div className="meeting-content">
          {activeTab === 'summary' ? (
            <div className="summary-view-single">
              <div className="single-blurb">
                {/* Edit Controls at Top */}
                <div className="blurb-header">
                  {!isEditing ? (
                    <button onClick={handleEdit} className="edit-blurb-btn">
                      <Edit2 size={18} />
                      <span>Edit Meeting</span>
                    </button>
                  ) : (
                    <div className="edit-actions">
                      <button onClick={handleSave} className="save-btn">
                        <Save size={18} />
                        <span>Save</span>
                      </button>
                      <button onClick={handleCancelEdit} className="cancel-btn">
                        <X size={18} />
                        <span>Cancel</span>
                      </button>
                    </div>
                  )}
                </div>

                {/* Summary */}
                {(meeting.summary || isEditing) && (
                  <div className="blurb-section">
                    <h2>Summary</h2>
                    {isEditing ? (
                      <textarea
                        value={editedData.summary}
                        onChange={(e) => updateEditedSummary(e.target.value)}
                        className="summary-editor"
                        rows={4}
                        placeholder="Enter summary (3 sentences max)"
                      />
                    ) : (
                      <p>{meeting.summary}</p>
                    )}
                  </div>
                )}

                {/* Participants */}
                {((meeting.key_stakeholders?.length > 0 || meeting.participants?.length > 0) || isEditing) && (
                  <div className="blurb-section">
                    <h2>Participants</h2>
                    {isEditing ? (
                      <div className="editable-list">
                        {editedData.key_stakeholders.map((participant, idx) => (
                          <div key={idx} className="editable-item">
                            <input
                              type="text"
                              value={participant}
                              onChange={(e) => updateEditedStakeholder(idx, e.target.value)}
                              className="item-input"
                              placeholder="Participant name"
                            />
                            <button onClick={() => removeStakeholder(idx)} className="remove-btn">
                              <Minus size={16} />
                            </button>
                          </div>
                        ))}
                        <button onClick={addStakeholder} className="add-btn">
                          <Plus size={16} />
                          <span>Add Participant</span>
                        </button>
                      </div>
                    ) : (
                      <ul>
                        {(meeting.key_stakeholders || meeting.participants).map((participant, idx) => (
                          <li key={idx}>{participant}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}

                {/* Meeting Notes by Topic */}
                {((meeting.structured_notes && Object.keys(meeting.structured_notes).length > 0) || isEditing) && (
                  <div className="blurb-section">
                    <h2>Meeting Notes</h2>
                    {isEditing ? (
                      <div className="editable-notes">
                        {Object.entries(editedData.structured_notes).map(([topic, notes], topicIdx) => (
                          <div key={topicIdx} className="topic-edit-section">
                            <h3>{topic}</h3>
                            <div className="editable-list">
                              {Array.isArray(notes) && notes.map((note, noteIdx) => (
                                <div key={noteIdx} className="editable-item">
                                  <input
                                    type="text"
                                    value={note}
                                    onChange={(e) => updateEditedNote(topic, noteIdx, e.target.value)}
                                    className="item-input"
                                    placeholder="Note point"
                                  />
                                  <button onClick={() => removeNote(topic, noteIdx)} className="remove-btn">
                                    <Minus size={16} />
                                  </button>
                                </div>
                              ))}
                              <button onClick={() => addNote(topic)} className="add-btn-small">
                                <Plus size={14} />
                                <span>Add Note</span>
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <>
                        {Object.entries(meeting.structured_notes).map(([topic, notes], topicIdx) => (
                          <div key={topicIdx} className="topic-notes">
                            <h3>{topic}</h3>
                            <ul>
                              {Array.isArray(notes) ? (
                                notes.map((note, noteIdx) => (
                                  <li key={noteIdx} className={note.startsWith('HiRA:') ? 'hira-note' : ''}>
                                    {note}
                                  </li>
                                ))
                              ) : (
                                <li>{notes}</li>
                              )}
                            </ul>
                          </div>
                        ))}
                      </>
                    )}
                  </div>
                )}

                {/* Next Steps */}
                {((meeting.next_steps && meeting.next_steps.length > 0) || isEditing) && (
                  <div className="blurb-section">
                    <h2>Next Steps</h2>
                    {isEditing ? (
                      <div className="editable-list">
                        {editedData.next_steps.map((step, idx) => (
                          <div key={idx} className="editable-item">
                            <input
                              type="text"
                              value={step}
                              onChange={(e) => updateNextStep(idx, e.target.value)}
                              className="item-input"
                              placeholder="Next step"
                            />
                            <button onClick={() => removeNextStep(idx)} className="remove-btn">
                              <Minus size={16} />
                            </button>
                          </div>
                        ))}
                        <button onClick={addNextStep} className="add-btn">
                          <Plus size={16} />
                          <span>Add Next Step</span>
                        </button>
                      </div>
                    ) : (
                      <ul>
                        {meeting.next_steps.map((step, idx) => (
                          <li key={idx}>{step}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="transcript-view">
              <section className="summary-section">
                <h2>Full Transcript</h2>
                {meeting.transcript ? (
                  <div className="transcript-text">{meeting.transcript}</div>
                ) : (
                  <p className="no-transcript">No transcript available</p>
                )}
              </section>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default MeetingDetailPage
