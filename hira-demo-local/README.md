# HiRA Demo - Local Version for Screenshots

This is a standalone demo version of the HiRA frontend with mock data. Perfect for taking screenshots and demos without needing the backend running.

## 📸 What's Included

- **5 Fully-Filled Meeting Cards** with realistic data:
  - AI Policy Strategy Workshop
  - AI Wearables: Privacy and Ethics Discussion
  - Strategic Partnerships for AI Development
  - Building AI Agents for Healthcare Applications
  - AI Agents for Education: Equity and Access

- **Empty Documents Page** - Clean state for screenshots

## 🚀 Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Run the Demo
```bash
npm run dev
```

The app will open at `http://localhost:5173`

## 📷 Taking Screenshots

### Meetings Page
1. Navigate to `/meetings` (or click "Meetings" in the sidebar)
2. You'll see 5 meeting cards with:
   - Meeting titles and dates
   - Participant counts
   - Duration
   - Summaries
   - Key topics
   - Action items

3. Click on any meeting to see the full details page with:
   - Complete transcript
   - Detailed action items
   - Participant list
   - Full summary

### Documents Page
1. Navigate to `/documents`
2. Shows empty state - clean and ready for screenshots

### Chat Page
- Chat interface is available but requires backend
- For demo purposes, focus on Meetings and Documents pages

## 🎨 Best Screenshot Settings

- **Window Size**: 1920x1080 or 1440x900
- **Zoom Level**: 100% (or 90% if cards look too large)
- **Browser**: Chrome or Firefox in normal mode (not incognito)

## 📝 Notes

- This is a **demo-only** version - no data is saved
- No backend connection required
- Mock data is hardcoded in `src/data/mockMeetings.js`
- DO NOT push this folder to GitHub (it's for local screenshots only)

## 🛠️ Customizing Mock Data

If you need to adjust the meeting data, edit:
```
src/data/mockMeetings.js
```

Then restart the dev server.

## 🎯 Purpose

This demo version is specifically designed for:
- Taking clean screenshots for presentations
- Showing UI/UX without live data
- Demos where internet connectivity is unreliable
- Quick previews of the interface

Enjoy your screenshots! 📸
