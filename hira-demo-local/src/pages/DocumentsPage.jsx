import { useState, useEffect } from 'react'
import { Upload, FileText, Trash2, Loader2, Check, AlertCircle } from 'lucide-react'
import { documentsAPI } from '../services/api'
import '../styles/DocumentsPage.css'

function DocumentsPage() {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadStatus, setUploadStatus] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      setLoading(true)
      setError(null)
      // Demo mode: showing empty documents page
      await new Promise(resolve => setTimeout(resolve, 300))
      setDocuments([])
    } catch (err) {
      console.error('Error loading documents:', err)
      setError('Failed to load documents.')
    } finally {
      setLoading(false)
    }
  }

  const handleFileSelect = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    // Validate file type
    const allowedTypes = ['.pdf', '.docx', '.txt', '.md']
    const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()

    if (!allowedTypes.includes(fileExt)) {
      setUploadStatus({
        type: 'error',
        message: `File type not supported. Allowed: ${allowedTypes.join(', ')}`
      })
      return
    }

    // Validate file size (50MB)
    if (file.size > 50 * 1024 * 1024) {
      setUploadStatus({
        type: 'error',
        message: 'File size exceeds 50MB limit'
      })
      return
    }

    try {
      setUploading(true)
      setUploadProgress(0)
      setUploadStatus(null)
      setError(null)

      await documentsAPI.upload(file, (progress) => {
        setUploadProgress(progress)
      })

      setUploadStatus({
        type: 'success',
        message: `Successfully uploaded ${file.name}`
      })

      // Reload documents list
      await loadDocuments()

      // Clear file input
      event.target.value = ''

      // Clear success message after 3 seconds
      setTimeout(() => {
        setUploadStatus(null)
      }, 3000)

    } catch (err) {
      console.error('Error uploading document:', err)
      setUploadStatus({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to upload document'
      })
    } finally {
      setUploading(false)
      setUploadProgress(0)
    }
  }

  const handleDelete = async (documentId, filename) => {
    if (!confirm(`Are you sure you want to delete "${filename}"?`)) {
      return
    }

    try {
      await documentsAPI.delete(documentId)
      setDocuments(prev => prev.filter(doc => doc.document_id !== documentId))
    } catch (err) {
      console.error('Error deleting document:', err)
      alert('Failed to delete document: ' + (err.response?.data?.detail || err.message))
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString()
  }

  return (
    <div className="documents-page">
      <div className="documents-container">
        <div className="documents-header">
          <div>
            <h1>Document Library</h1>
            <p>Upload your organization's policies, guidelines, and frameworks to enhance HiRA's knowledge.</p>
          </div>
        </div>

        {/* Upload Section */}
        <div className="upload-section">
          <div className="upload-card">
            <Upload size={36} />
            <h3>Upload Document</h3>
            <p>Supported formats: PDF, DOCX, TXT, MD (max 50MB)</p>

            <label className="upload-button">
              <input
                type="file"
                accept=".pdf,.docx,.txt,.md"
                onChange={handleFileSelect}
                disabled={uploading}
                style={{ display: 'none' }}
              />
              {uploading ? (
                <span>
                  <Loader2 size={20} className="spinner" />
                  Uploading... {uploadProgress}%
                </span>
              ) : (
                <span>Select File</span>
              )}
            </label>

            {uploadStatus && (
              <div className={`upload-status ${uploadStatus.type}`}>
                {uploadStatus.type === 'success' ? (
                  <Check size={18} />
                ) : (
                  <AlertCircle size={18} />
                )}
                <span>{uploadStatus.message}</span>
              </div>
            )}
          </div>

          <div className="stats-card">
            <h3>Library Statistics</h3>
            <div className="stats-grid">
              <div className="stat-item">
                <div className="stat-value">{documents.length}</div>
                <div className="stat-label">Total Documents</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">
                  {documents.reduce((acc, doc) => acc + (doc.chunk_count || 0), 0)}
                </div>
                <div className="stat-label">Total Chunks</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">
                  {documents.filter(doc => doc.scope === 'core').length}
                </div>
                <div className="stat-label">Core Knowledge</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">
                  {documents.filter(doc => doc.scope === 'user').length}
                </div>
                <div className="stat-label">Your Documents</div>
              </div>
            </div>
          </div>
        </div>

        {/* Documents List */}
        <div className="documents-list-section">
          <h2>Your Documents</h2>

          {loading ? (
            <div className="loading-state">
              <Loader2 size={32} className="spinner" />
              <p>Loading documents...</p>
            </div>
          ) : error ? (
            <div className="error-state">
              <AlertCircle size={32} />
              <p>{error}</p>
              <button onClick={loadDocuments} className="retry-button">
                Try Again
              </button>
            </div>
          ) : documents.length === 0 ? (
            <div className="empty-state">
              <FileText size={48} />
              <p>No documents uploaded yet</p>
              <p className="empty-subtitle">
                Upload your first document to get started
              </p>
            </div>
          ) : (
            <div className="documents-list">
              {documents.map((doc) => (
                <div key={doc.document_id} className="document-card">
                  <div className="document-icon">
                    <FileText size={24} />
                  </div>

                  <div className="document-info">
                    <h3 className="document-title">{doc.filename}</h3>

                    <div className="document-meta">
                      <span>{formatFileSize(doc.file_size)}</span>
                      <span>•</span>
                      <span>{doc.chunk_count} chunks</span>
                      <span>•</span>
                      <span>{formatDate(doc.upload_date)}</span>
                    </div>

                    {doc.scope && (
                      <div className="document-badges">
                        <span className={`badge badge-${doc.scope}`}>
                          {doc.scope === 'core' ? 'Core Knowledge' : 'Your Document'}
                        </span>
                        {doc.processed && (
                          <span className="badge badge-success">Processed</span>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="document-actions">
                    {doc.scope !== 'core' && (
                      <button
                        onClick={() => handleDelete(doc.document_id, doc.filename)}
                        className="delete-button"
                        title="Delete document"
                      >
                        <Trash2 size={18} />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default DocumentsPage
