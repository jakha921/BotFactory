"""
Gemini client for generating bot responses.
Uses backend Django service for Gemini API integration.
"""
from typing import List, Dict, Optional, Any
import os
import sys
from asgiref.sync import sync_to_async
import logging

logger = logging.getLogger(__name__)

# Add backend to path for imports
backend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from services.gemini import GeminiService
from bot.integrations.django_orm import get_bot_knowledge_base
from apps.knowledge.models import DocumentChunk
from pgvector.django import L2Distance
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings


_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Get global Gemini service instance."""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service


async def generate_bot_response(
    bot,
    prompt: str,
    history: List[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Generate bot response using Gemini API.
    
    Args:
        bot: Bot model instance
        prompt: User prompt
        history: Chat history as list of {role, content} dicts
        
    Returns:
        Dict with 'text' and optional 'groundingChunks'
    """
    try:
        @sync_to_async
        def _get_rag_context(prompt):
            try:
                # 1. Embed the user's prompt
                embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
                prompt_embedding = embeddings.embed_query(prompt)

                # 2. Query the vector database for relevant document chunks
                doc_chunks = list(
                    DocumentChunk.objects.filter(document__bot=bot).order_by(
                        L2Distance('embedding', prompt_embedding)
                    )[:3]  # Top 3 most relevant chunks
                )

                # 3. Query text snippets
                from apps.knowledge.models import TextSnippet
                snippet_chunks = list(
                    TextSnippet.objects.filter(
                        bot=bot,
                        embedding__isnull=False
                    ).order_by(
                        L2Distance('embedding', prompt_embedding)
                    )[:3]  # Top 3 most relevant snippets
                )

                # 4. Combine context
                context_parts = []
                if doc_chunks:
                    context_parts.append("## Relevant Document Content:")
                    for chunk in doc_chunks:
                        context_parts.append(f"- {chunk.text[:500]}...")  # Limit chunk size
                
                if snippet_chunks:
                    context_parts.append("\n## Relevant Knowledge Base Snippets:")
                    for snippet in snippet_chunks:
                        context_parts.append(f"- {snippet.title}: {snippet.content[:500]}...")
                
                if context_parts:
                    return "\n".join(context_parts)
                return None
            except Exception as e:
                logger.warning(f"Failed to retrieve RAG context: {str(e)}")
                return None

        rag_context = await _get_rag_context(prompt)
        
        system_instruction = bot.system_instruction or "You are a helpful AI assistant."
        
        if rag_context:
            system_instruction = f"{system_instruction}\n\n{rag_context}"
        
        # Use sync_to_async for Django service
        @sync_to_async
        def _generate_response():
            gemini_service = get_gemini_service()
            return gemini_service.generate_response(
                model_name=bot.model or 'gemini-2.5-flash',
                prompt=prompt,
                system_instruction=system_instruction,
                history=history or [],
                thinking_budget=bot.thinking_budget if bot.thinking_budget else None,
                temperature=bot.temperature or 0.7
            )
        
        result = await _generate_response()
        return result
    except Exception as e:
        logger.error(f"Error generating bot response: {str(e)}", exc_info=True)
        return {
            'text': 'Извините, произошла ошибка при генерации ответа. Попробуйте позже.',
            'groundingChunks': []
        }

