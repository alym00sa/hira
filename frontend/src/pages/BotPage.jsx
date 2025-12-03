import { useState } from 'react';
import { Bot, Lock, Loader, Play, Square, CheckCircle, AlertCircle, MessageCircle, Mic } from 'lucide-react';
import { botAPI } from '../services/api';
import '../styles/BotPage.css';

export default function BotPage() {
  const [meetingUrl, setMeetingUrl] = useState('');
  const [meetingTitle, setMeetingTitle] = useState('');
  const [botName, setBotName] = useState('HiRA');
  const [isLoading, setIsLoading] = useState(false);
  const [activeBot, setActiveBot] = useState(null);
  const [error, setError] = useState(null);

  const handleStart = async () => {
    if (!meetingUrl.trim()) {
      setError('Please enter a Zoom meeting URL');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Build voice interface URL (will be bot's video feed)
      // Use deployed Vercel URL for public access (required by Recall.ai)
      const frontendUrl = 'https://hira-frontend.vercel.app';
      const voiceInterfaceUrl = `${frontendUrl}/voice`;

      const response = await botAPI.start({
        meeting_url: meetingUrl,
        meeting_title: meetingTitle || undefined,
        bot_name: botName,
        output_media: voiceInterfaceUrl  // Voice interface as bot's video
      });

      setActiveBot(response.data);
      console.log('Bot started with voice interface:', voiceInterfaceUrl);
    } catch (err) {
      console.error('Failed to start bot:', err);
      setError(err.response?.data?.detail || 'Failed to start bot. Make sure backend is running.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStop = async () => {
    if (!activeBot) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await botAPI.stop(activeBot.bot_id);
      console.log('Bot stopped:', response.data);

      // Reset form
      setActiveBot(null);
      setMeetingUrl('');
      setMeetingTitle('');
    } catch (err) {
      console.error('Failed to stop bot:', err);
      setError(err.response?.data?.detail || 'Failed to stop bot');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bot-page">
      <div className="bot-container">
        <header className="bot-header">
          <div className="header-icon">
            <Bot size={40} />
          </div>
          <div>
            <h1>Zoom Meeting Bot</h1>
            <p className="subtitle">Send HiRA to join your Zoom meetings</p>
          </div>
        </header>

        {!activeBot ? (
          <div className="bot-form">
            <div className="form-section">
              <label htmlFor="meetingUrl">Zoom Meeting URL *</label>
              <input
                id="meetingUrl"
                type="text"
                placeholder="https://zoom.us/j/123456789..."
                value={meetingUrl}
                onChange={(e) => setMeetingUrl(e.target.value)}
                disabled={isLoading}
              />
            </div>

            <div className="form-section">
              <label htmlFor="meetingTitle">Meeting Title (optional)</label>
              <input
                id="meetingTitle"
                type="text"
                placeholder="e.g., Project Planning Meeting"
                value={meetingTitle}
                onChange={(e) => setMeetingTitle(e.target.value)}
                disabled={isLoading}
              />
            </div>

            <div className="form-section">
              <label htmlFor="botName">Bot Name</label>
              <input
                id="botName"
                type="text"
                value={botName}
                onChange={(e) => setBotName(e.target.value)}
                disabled={isLoading}
              />
              <small>This is how the bot will appear in the meeting</small>
            </div>

            {error && (
              <div className="error-message">
                <AlertCircle size={20} />
                <span>{error}</span>
              </div>
            )}

            <div className="bot-features">
              <h3>What HiRA will do:</h3>
              <div className="features-grid">
                <div className="feature-item">
                  <Mic className="feature-icon" />
                  <div>
                    <strong>Voice Responses</strong>
                    <p>Say "Hey HiRA" + your question</p>
                    <small className="feature-note">Uses OpenAI Realtime API with RAG</small>
                  </div>
                </div>
                <div className="feature-item">
                  <MessageCircle className="feature-icon" />
                  <div>
                    <strong>Public Chat</strong>
                    <p>Type @HiRA in meeting chat</p>
                    <small className="feature-note">Text responses via webhook</small>
                  </div>
                </div>
                <div className="feature-item">
                  <Lock className="feature-icon private" />
                  <div>
                    <strong>Private DMs</strong>
                    <p>Message HiRA privately for discreet help</p>
                    <small className="feature-note">Both voice & text supported</small>
                  </div>
                </div>
              </div>
              <div className="bot-architecture-note">
                <p><strong>How it works:</strong> HiRA joins with a voice interface displayed as video feed. Participants see HiRA's status (listening, thinking, speaking) and can interact via voice or chat.</p>
              </div>
            </div>

            <button
              className="start-button"
              onClick={handleStart}
              disabled={isLoading || !meetingUrl}
            >
              {isLoading ? (
                <>
                  <Loader className="spinner" size={20} />
                  Starting Bot...
                </>
              ) : (
                <>
                  <Play size={20} />
                  Start HiRA Bot
                </>
              )}
            </button>
          </div>
        ) : (
          <div className="bot-active">
            <div className="status-card">
              <CheckCircle className="success-icon" size={48} />
              <h2>HiRA is active!</h2>
              <p>Bot ID: <code>{activeBot.bot_id}</code></p>
              <p className="status-text">{activeBot.message}</p>
            </div>

            <div className="instructions">
              <h3>How to interact with HiRA:</h3>

              <div className="instruction-item">
                <div className="instruction-number">1</div>
                <div>
                  <strong>Admit from waiting room</strong>
                  <p>Let HiRA join if prompted by Zoom</p>
                </div>
              </div>

              <div className="instruction-item">
                <div className="instruction-number">2</div>
                <div>
                  <strong>Voice: "Hey HiRA, [question]"</strong>
                  <p>HiRA will speak the answer to everyone</p>
                </div>
              </div>

              <div className="instruction-item">
                <div className="instruction-number">3</div>
                <div>
                  <strong>Public chat: @HiRA [question]</strong>
                  <p>HiRA responds in chat + with voice</p>
                </div>
              </div>

              <div className="instruction-item">
                <div className="instruction-number">4</div>
                <div>
                  <strong>Private DM: Message HiRA directly</strong>
                  <p>Get private answers without interrupting</p>
                </div>
              </div>
            </div>

            <button
              className="stop-button"
              onClick={handleStop}
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader className="spinner" size={20} />
                  Stopping...
                </>
              ) : (
                <>
                  <Square size={20} />
                  Stop Bot & Save Transcript
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
