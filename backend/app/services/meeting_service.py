"""
Meeting Service - Business logic for meeting management and summary generation
"""
from sqlalchemy.orm import Session
from typing import List, Tuple, Optional
from app.models.meeting import Meeting
from app.models.schemas import MeetingCreate, MeetingUpdate
from app.services.llm_service import LLMService
from sqlalchemy import or_, func
import uuid
import json

class MeetingService:
    """Service for managing meetings and generating summaries"""

    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()

    async def create_meeting(self, meeting_data: MeetingCreate) -> Meeting:
        """Create a new meeting"""
        meeting = Meeting(
            title=meeting_data.title,
            date=meeting_data.date,
            duration_minutes=meeting_data.duration_minutes,
            platform=meeting_data.platform,
            meeting_link=meeting_data.meeting_link,
            participants=meeting_data.participants or [],
            transcript=meeting_data.transcript,
        )

        self.db.add(meeting)
        self.db.commit()
        self.db.refresh(meeting)

        # If transcript provided, auto-generate summary
        if meeting_data.transcript:
            await self.generate_summary(meeting.id)
            self.db.refresh(meeting)

        return meeting

    async def list_meetings(
        self,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Meeting], int]:
        """List meetings with pagination"""
        query = self.db.query(Meeting)

        if user_id:
            query = query.filter(Meeting.user_id == user_id)

        total = query.count()

        meetings = query.order_by(Meeting.date.desc()).offset(offset).limit(limit).all()

        return meetings, total

    async def get_meeting(self, meeting_id: str) -> Optional[Meeting]:
        """Get a meeting by ID"""
        return self.db.query(Meeting).filter(Meeting.id == meeting_id).first()

    async def get_meeting_by_share_token(self, share_token: str) -> Optional[Meeting]:
        """Get a public meeting by share token"""
        return self.db.query(Meeting).filter(
            Meeting.share_token == share_token,
            Meeting.is_public == True
        ).first()

    async def update_meeting(self, meeting_id: str, meeting_data: MeetingUpdate) -> Optional[Meeting]:
        """Update a meeting"""
        meeting = await self.get_meeting(meeting_id)
        if not meeting:
            return None

        # Update fields
        if meeting_data.title is not None:
            meeting.title = meeting_data.title
        if meeting_data.transcript is not None:
            meeting.transcript = meeting_data.transcript
        if meeting_data.summary is not None:
            meeting.summary = meeting_data.summary
        if meeting_data.key_stakeholders is not None:
            meeting.key_stakeholders = meeting_data.key_stakeholders
        if meeting_data.structured_notes is not None:
            meeting.structured_notes = meeting_data.structured_notes
        if meeting_data.next_steps is not None:
            meeting.next_steps = meeting_data.next_steps
        if meeting_data.action_items is not None:
            meeting.action_items = meeting_data.action_items
        if meeting_data.is_public is not None:
            meeting.is_public = meeting_data.is_public

        self.db.commit()
        self.db.refresh(meeting)

        return meeting

    async def delete_meeting(self, meeting_id: str) -> bool:
        """Delete a meeting"""
        meeting = await self.get_meeting(meeting_id)
        if not meeting:
            return False

        self.db.delete(meeting)
        self.db.commit()

        return True

    async def create_share_token(self, meeting_id: str) -> Optional[str]:
        """Create a public share token for a meeting"""
        meeting = await self.get_meeting(meeting_id)
        if not meeting:
            return None

        # Generate unique token
        share_token = str(uuid.uuid4())[:12]
        meeting.share_token = share_token
        meeting.is_public = True

        self.db.commit()

        return share_token

    async def generate_summary(self, meeting_id: str) -> Optional[Meeting]:
        """
        Generate structured summary for a meeting using HiRA's LLM

        Extracts:
        - Overall summary
        - Key topics
        - Action items
        - Rights issues
        - Risk flags
        - Obligations
        - Key stakeholders
        - Next steps
        """
        meeting = await self.get_meeting(meeting_id)
        if not meeting or not meeting.transcript:
            return None

        # Build prompt for LLM
        prompt = self._build_summary_prompt(meeting.transcript)

        # Generate summary using LLM
        response = await self.llm_service.generate_response(
            user_message=prompt,
            context="",  # No RAG context needed for summary generation
            conversation_history=None
        )

        # Parse structured response
        summary_data = self._parse_summary_response(response["message"])

        # Update meeting with summary data
        meeting.summary = summary_data.get("summary", "")
        meeting.key_stakeholders = summary_data.get("key_stakeholders", [])
        meeting.structured_notes = summary_data.get("structured_notes", {})
        meeting.next_steps = summary_data.get("next_steps", [])

        # Keep these for backward compatibility but deprioritize
        meeting.key_topics = list(summary_data.get("structured_notes", {}).keys()) if summary_data.get("structured_notes") else []
        meeting.action_items = []
        meeting.rights_issues = []
        meeting.risk_flags = []
        meeting.obligations = []
        meeting.processed = True

        self.db.commit()
        self.db.refresh(meeting)

        return meeting

    def _build_summary_prompt(self, transcript: str) -> str:
        """Build prompt for meeting summary generation"""
        return f"""Analyze this meeting transcript and provide a structured summary in JSON format.

Meeting Transcript:
{transcript}

Please provide a JSON response with the following structure:
{{
    "summary": "3 sentence maximum overall summary of the meeting",
    "key_stakeholders": ["participant 1", "participant 2", "participant 3"],
    "structured_notes": {{
        "Topic 1 Name": [
            "Specific point or decision that was made about this topic",
            "Key concern or question raised by [person name] about X",
            "Proposed solution or approach discussed: [specific details]",
            "HiRA: [Specific explanation or guidance HiRA provided] (only if HiRA spoke)"
        ],
        "Topic 2 Name": [
            "Point 1 with actual substance from the discussion",
            "Point 2 with specific details mentioned"
        ]
    }},
    "next_steps": ["Specific action item 1", "Specific action item 2"]
}}

CRITICAL REQUIREMENTS:
- Summary must be EXACTLY 3 sentences or less
- Meeting notes MUST contain ACTUAL SUBSTANCE from the conversation - what was specifically said, decided, or discussed
- Do NOT write vague notes like "discussed X" - extract the ACTUAL points made
- Include WHO said important things when relevant
- If HiRA appears in the transcript, prefix her contributions with "HiRA: " and include what she specifically said
- Each note should be specific and informative, not generic
- Only include fields that have content"""

    def _parse_summary_response(self, response: str) -> dict:
        """Parse LLM response into structured summary data"""
        try:
            # Try to extract JSON from response
            # LLM might wrap it in markdown code blocks
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()

            summary_data = json.loads(json_str)
            return summary_data

        except Exception as e:
            print(f"Failed to parse summary JSON: {e}")
            # Fallback: return basic structure with raw response
            return {
                "summary": response[:500],  # First 500 chars
                "key_topics": [],
                "action_items": [],
                "rights_issues": [],
                "risk_flags": [],
                "obligations": [],
                "key_stakeholders": [],
                "next_steps": []
            }

    async def search_relevant_meetings(self, query: str, limit: int = 3, exclude_meeting_id: Optional[str] = None) -> List[dict]:
        """
        Search for relevant previous meetings based on a query

        Returns meeting summaries that are semantically relevant to the query.
        This gives HiRA institutional memory across meetings.

        Args:
            query: The search query (usually the current question)
            limit: Max number of meetings to return
            exclude_meeting_id: Optional meeting ID to exclude (current meeting)

        Returns:
            List of meeting summaries with metadata
        """
        try:
            # Get all processed meetings with summaries
            query_builder = self.db.query(Meeting).filter(
                Meeting.processed == True,
                Meeting.summary.isnot(None),
                Meeting.summary != ""
            )

            # Exclude current meeting if specified
            if exclude_meeting_id:
                query_builder = query_builder.filter(Meeting.id != exclude_meeting_id)

            # Get recent meetings (last 50)
            meetings = query_builder.order_by(Meeting.date.desc()).limit(50).all()

            if not meetings:
                return []

            # Simple keyword-based relevance scoring
            # TODO: Could upgrade to embeddings-based semantic search
            query_lower = query.lower()
            query_keywords = set(query_lower.split())

            scored_meetings = []
            for meeting in meetings:
                # Create searchable text from meeting
                searchable_text = " ".join([
                    meeting.title or "",
                    meeting.summary or "",
                    " ".join(meeting.key_topics or []),
                    " ".join([str(item) for item in (meeting.rights_issues or [])]),
                    " ".join([str(item) for item in (meeting.risk_flags or [])])
                ]).lower()

                # Calculate relevance score (simple keyword matching)
                score = sum(1 for keyword in query_keywords if keyword in searchable_text)

                if score > 0:
                    scored_meetings.append((score, meeting))

            # Sort by relevance score and take top N
            scored_meetings.sort(key=lambda x: x[0], reverse=True)
            relevant_meetings = [m for _, m in scored_meetings[:limit]]

            # Format for context
            result = []
            for meeting in relevant_meetings:
                result.append({
                    "title": meeting.title,
                    "date": meeting.date,
                    "summary": meeting.summary,
                    "key_topics": meeting.key_topics,
                    "action_items": meeting.action_items[:3] if meeting.action_items else [],  # Top 3
                    "rights_issues": meeting.rights_issues[:2] if meeting.rights_issues else []  # Top 2
                })

            print(f"📚 Found {len(result)} relevant past meetings")
            return result

        except Exception as e:
            print(f"❌ Error searching meetings: {str(e)}")
            return []
