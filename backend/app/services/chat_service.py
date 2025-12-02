"""
Chat Service - Orchestrates RAG and LLM for conversations
"""
from typing import Dict, List, Optional
from app.rag.rag_engine import RAGEngine
from app.services.llm_service import LLMService
import json
from pathlib import Path

class ChatService:
    """Manages chat interactions with HiRA"""

    def __init__(self):
        self.rag_engine = RAGEngine()
        self.llm_service = LLMService()
        self.conversation_store = {}  # In-memory for MVP (use DB in production)

    async def process_message(
        self,
        message: str,
        conversation_id: str,
        user_id: Optional[str] = None
    ) -> Dict:
        """
        Process a user message and generate HiRA's response

        Args:
            message: User's message
            conversation_id: Conversation ID
            user_id: User ID (for accessing user-specific documents)

        Returns:
            Dict with response and sources
        """
        # Retrieve relevant context from RAG
        context_data = self.rag_engine.build_context_prompt(
            query=message,
            user_id=user_id
        )

        # Get conversation history
        history = self._get_conversation_history(conversation_id)

        # Generate response using LLM
        response_data = await self.llm_service.generate_response(
            user_message=message,
            context=context_data["context"],
            conversation_history=history
        )

        # Update conversation history
        self._add_to_history(
            conversation_id=conversation_id,
            user_message=message,
            assistant_message=response_data["message"]
        )

        return {
            "message": response_data["message"],
            "sources": context_data["sources"],
            "has_context": context_data["has_context"],
            "model": response_data["model"],
            "provider": response_data["provider"]
        }

    async def get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """Get full conversation history"""
        return self.conversation_store.get(conversation_id, [])

    def _get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """Get conversation history formatted for LLM"""
        return self.conversation_store.get(conversation_id, [])

    def _add_to_history(
        self,
        conversation_id: str,
        user_message: str,
        assistant_message: str
    ):
        """Add messages to conversation history"""
        if conversation_id not in self.conversation_store:
            self.conversation_store[conversation_id] = []

        self.conversation_store[conversation_id].extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_message}
        ])

        # Keep only last 10 exchanges (20 messages) to manage context length
        if len(self.conversation_store[conversation_id]) > 20:
            self.conversation_store[conversation_id] = \
                self.conversation_store[conversation_id][-20:]

    def clear_conversation(self, conversation_id: str):
        """Clear a conversation history"""
        if conversation_id in self.conversation_store:
            del self.conversation_store[conversation_id]
