"""
LLM Service - Handles interactions with Claude/OpenAI
"""
from typing import Dict, Optional
from app.core.config import settings
import anthropic
import openai

class LLMService:
    """Service for LLM interactions with HiRA's persona"""

    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS

        # Initialize clients
        if self.provider == "anthropic" and settings.ANTHROPIC_API_KEY:
            self.anthropic_client = anthropic.Anthropic(
                api_key=settings.ANTHROPIC_API_KEY
            )
        elif self.provider == "openai" and settings.OPENAI_API_KEY:
            self.openai_client = openai.OpenAI(
                api_key=settings.OPENAI_API_KEY
            )
        else:
            print(f"⚠️  Warning: No API key configured for {self.provider}")

    def get_hira_system_prompt(self) -> str:
        """Get HiRA's system prompt defining her persona"""
        return """You are HiRA (Human Rights Assistant), an AI assistant specializing in human rights-based approaches (HRBA).

Your personality:
- Warm and human in your interactions
- Professional and knowledgeable
- Inclusive and respectful of all people and perspectives
- Grounded strictly in the provided knowledge base
- Honest about limitations

Your role:
- Help teams apply human rights principles to their work
- Answer questions using ONLY the provided context from your knowledge base
- Cite sources naturally when referencing documents
- Flag potential rights issues or risks when relevant

Critical rules:
1. ONLY use information from the provided context - never make up facts
2. Use basic markdown formatting for emphasis: **bold** for key terms, *italic* for subtle emphasis. Keep it minimal and professional.
3. When citing, use natural language like "According to your Equity Policy..." or "In the HRBA@Tech Guide..."
4. Keep responses concise but thorough (2-4 paragraphs typically)
5. Maintain your warm, professional tone even when discussing difficult topics
6. If specific information isn't in your knowledge base, still provide helpful guidance from general HRBA principles without over-apologizing

Remember: Your goal is to help people apply human rights principles effectively, always grounded in accurate, sourced information."""

    async def generate_response(
        self,
        user_message: str,
        context: str,
        conversation_history: Optional[list] = None
    ) -> Dict:
        """
        Generate a response using the LLM

        Args:
            user_message: The user's question
            context: Retrieved context from RAG
            conversation_history: Previous messages in conversation

        Returns:
            Dict with response and metadata
        """
        # Build the prompt
        if context and context != "No relevant information found in the knowledge base.":
            user_prompt = f"""Context from knowledge base:

{context}

---

User question: {user_message}

Please answer the user's question using the context provided above. Cite sources naturally."""
        else:
            user_prompt = f"""User question: {user_message}

Note: No relevant information was found in the knowledge base for this question."""

        try:
            if self.provider == "anthropic":
                response = await self._generate_with_anthropic(
                    user_prompt, conversation_history
                )
            elif self.provider == "openai":
                response = await self._generate_with_openai(
                    user_prompt, conversation_history
                )
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")

            return {
                "message": response,
                "provider": self.provider,
                "model": self.model
            }

        except Exception as e:
            raise Exception(f"LLM generation failed: {str(e)}")

    async def _generate_with_anthropic(
        self,
        user_prompt: str,
        conversation_history: Optional[list] = None
    ) -> str:
        """Generate response using Claude"""
        messages = []

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)

        # Add current message
        messages.append({
            "role": "user",
            "content": user_prompt
        })

        response = self.anthropic_client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=self.get_hira_system_prompt(),
            messages=messages
        )

        return response.content[0].text

    async def _generate_with_openai(
        self,
        user_prompt: str,
        conversation_history: Optional[list] = None
    ) -> str:
        """Generate response using OpenAI"""
        messages = [
            {"role": "system", "content": self.get_hira_system_prompt()}
        ]

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)

        # Add current message
        messages.append({
            "role": "user",
            "content": user_prompt
        })

        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        return response.choices[0].message.content
