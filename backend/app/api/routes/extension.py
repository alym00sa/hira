"""
Browser Extension API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.services.llm_service import LLMService
from app.rag.rag_engine import RAGEngine

router = APIRouter()
llm_service = LLMService()
rag_engine = RAGEngine()

class TextAnalysisRequest(BaseModel):
    text: str
    user_id: Optional[str] = "default_user"  # For MVP, use default user

class Citation(BaseModel):
    source: str
    excerpt: str

class TextAnalysisResponse(BaseModel):
    rights_issues: List[str]
    suggestions: List[str]
    rewrites: List[str]
    risk_prompts: List[str]
    citations: List[Citation]

@router.post("/analyze-text", response_model=TextAnalysisResponse)
async def analyze_text(request: TextAnalysisRequest):
    """
    Analyze text against HRBA principles using RAG knowledge base

    Returns suggestions, rights issues, rewrites, and citations
    """
    try:
        # Get relevant context from RAG
        context_prompt = rag_engine.build_context_prompt(
            query=f"human rights issues and HRBA principles related to: {request.text[:200]}",
            user_id=request.user_id
        )

        # Build analysis prompt
        analysis_prompt = f"""You are HiRA, a Human Rights Assistant. Analyze the following text for alignment with human rights-based approaches (HRBA).

Text to analyze:
\"\"\"{request.text}\"\"\"

Relevant knowledge from documents:
{context_prompt}

Provide your analysis in the following format:

RIGHTS ISSUES:
- [List any potential rights violations, discriminatory language, or problematic framing]
- [If none, write "None identified"]

SUGGESTIONS:
- [Specific improvements to make the text more rights-aligned]
- [Focus on participation, accountability, non-discrimination, empowerment]
- [If none needed, write "Text aligns well with HRBA principles"]

REWRITES:
- [Provide 1-2 alternative phrasings that better reflect HRBA]
- [Only if significant improvements are possible]

RISK PROMPTS:
- [Questions to help the writer think about potential risks]
- [e.g., "Have you considered how this affects marginalized groups?"]

CITATIONS:
- [Reference specific documents from the knowledge base that support your suggestions]
- Format: "Document Name: relevant excerpt or principle"

Be concise and actionable. Focus on the most important issues."""

        # Get LLM response
        response = llm_service.generate(analysis_prompt)

        # Parse response
        parsed = parse_analysis_response(response)

        return parsed

    except Exception as e:
        print(f"❌ Extension analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def parse_analysis_response(response: str) -> TextAnalysisResponse:
    """
    Parse LLM response into structured format
    """
    lines = response.split('\n')

    rights_issues = []
    suggestions = []
    rewrites = []
    risk_prompts = []
    citations = []

    current_section = None

    for line in lines:
        line = line.strip()

        # Detect section headers
        if 'RIGHTS ISSUES:' in line.upper():
            current_section = 'rights_issues'
            continue
        elif 'SUGGESTIONS:' in line.upper():
            current_section = 'suggestions'
            continue
        elif 'REWRITES:' in line.upper() or 'REWRITE OPTIONS:' in line.upper():
            current_section = 'rewrites'
            continue
        elif 'RISK PROMPTS:' in line.upper() or 'RISK PROMPTING:' in line.upper():
            current_section = 'risk_prompts'
            continue
        elif 'CITATIONS:' in line.upper():
            current_section = 'citations'
            continue

        # Skip empty lines
        if not line:
            continue

        # Skip "None identified" type responses
        if any(phrase in line.lower() for phrase in ['none identified', 'no issues', 'aligns well', 'none needed']):
            continue

        # Add to appropriate section
        if current_section == 'rights_issues' and line.startswith('-'):
            rights_issues.append(line[1:].strip())
        elif current_section == 'suggestions' and line.startswith('-'):
            suggestions.append(line[1:].strip())
        elif current_section == 'rewrites' and line.startswith('-'):
            rewrites.append(line[1:].strip())
        elif current_section == 'risk_prompts' and line.startswith('-'):
            risk_prompts.append(line[1:].strip())
        elif current_section == 'citations' and line.startswith('-'):
            # Parse citation format "Document Name: excerpt"
            if ':' in line:
                parts = line[1:].split(':', 1)
                citations.append(Citation(
                    source=parts[0].strip(),
                    excerpt=parts[1].strip() if len(parts) > 1 else ""
                ))

    return TextAnalysisResponse(
        rights_issues=rights_issues,
        suggestions=suggestions,
        rewrites=rewrites,
        risk_prompts=risk_prompts,
        citations=citations
    )
