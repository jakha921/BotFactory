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
        # Get knowledge base for bot
        knowledge_base = await get_bot_knowledge_base(str(bot.id))
        
        # Build system instruction with knowledge base
        system_instruction = bot.system_instruction or "You are a helpful AI assistant."
        
        # Add knowledge base context
        if knowledge_base.get('snippets') or knowledge_base.get('documents'):
            knowledge_context = []
            
            # Add snippets
            if knowledge_base.get('snippets'):
                knowledge_context.append("\n\n## Knowledge Base:")
                for snippet in knowledge_base['snippets']:
                    knowledge_context.append(f"\n### {snippet.get('title', 'Untitled')}")
                    knowledge_context.append(snippet.get('content', ''))
                    if snippet.get('tags'):
                        knowledge_context.append(f"\nTags: {', '.join(snippet['tags'])}")
            
            # Add document summaries
            if knowledge_base.get('documents'):
                knowledge_context.append("\n\n## Available Documents:")
                for doc in knowledge_base['documents']:
                    knowledge_context.append(f"- {doc.get('name', 'Unknown')} ({doc.get('type', 'unknown')})")
            
            if knowledge_context:
                system_instruction = f"{system_instruction}\n{''.join(knowledge_context)}"
        
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

