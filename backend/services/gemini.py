"""
Google Gemini API integration service.
"""
import os
from typing import Optional, List, Dict, Any
import google.generativeai as genai
from django.conf import settings


class GeminiService:
    """Service for interacting with Google Gemini API."""
    
    def __init__(self):
        """Initialize Gemini service with API key."""
        api_key = os.environ.get('GEMINI_API_KEY') or settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set")
        
        genai.configure(api_key=api_key)
        self.client = genai
    
    def create_client(self):
        """Create Gemini client instance."""
        return self.client
    
    def generate_response(
        self,
        model_name: str,
        prompt: str,
        system_instruction: str = "You are a helpful AI assistant.",
        history: Optional[List[Dict[str, str]]] = None,
        thinking_budget: Optional[int] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate a response using Gemini API.
        
        Args:
            model_name: Model name (e.g., 'gemini-2.5-flash')
            prompt: User prompt
            system_instruction: System instruction for the model
            history: Chat history as list of {role, content} dicts
            thinking_budget: Thinking budget in ms (for thinking models)
            temperature: Temperature parameter (0-2)
        
        Returns:
            Dict with 'text' and optional 'groundingChunks'
        """
        try:
            # Create model instance
            model = self.client.GenerativeModel(
                model_name=model_name,
                system_instruction=system_instruction
            )
            
            # Prepare generation config
            generation_config = {
                'temperature': temperature,
            }
            
            # Apply thinking config if budget is provided
            # CRITICAL: maxOutputTokens must NOT be set when using thinkingConfig
            if thinking_budget:
                generation_config['thinkingConfig'] = {
                    'thinkingBudget': thinking_budget
                }
                # Ensure maxOutputTokens is undefined
                generation_config.pop('maxOutputTokens', None)
            
            # Start chat if history exists
            if history and len(history) > 0:
                # Convert history format for Gemini
                chat_history = []
                for msg in history:
                    role = 'user' if msg['role'] == 'user' else 'model'
                    chat_history.append({
                        'role': role,
                        'parts': [msg['content']]
                    })
                
                chat = model.start_chat(history=chat_history)
                response = chat.send_message(
                    prompt,
                    generation_config=generation_config
                )
            else:
                # Simple generation without history
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
            
            # Extract response text
            text = response.text if hasattr(response, 'text') else str(response)
            
            # Clean markdown formatting from response
            # Remove common markdown symbols
            import re
            # Remove bold/italic markers
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **text**
            text = re.sub(r'\*([^*]+)\*', r'\1', text)  # *text*
            text = re.sub(r'__([^_]+)__', r'\1', text)  # __text__
            text = re.sub(r'_([^_]+)_', r'\1', text)  # _text_
            # Remove code blocks
            text = re.sub(r'```[\s\S]*?```', '', text)  # ```code```
            text = re.sub(r'`([^`]+)`', r'\1', text)  # `code`
            # Remove headers
            text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)  # # Header
            # Remove links but keep text
            text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # [text](url)
            # Clean up extra spaces
            text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 newlines
            text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to one
            text = text.strip()
            
            # Extract grounding chunks if available
            # Convert protobuf objects to serializable dicts
            grounding_chunks = []
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata'):
                    grounding_metadata = candidate.grounding_metadata
                    if hasattr(grounding_metadata, 'grounding_chunks'):
                        # Convert protobuf RepeatedComposite to list of dicts
                        for chunk in grounding_metadata.grounding_chunks:
                            chunk_dict = {}
                            # Extract common fields from grounding chunk
                            if hasattr(chunk, 'web'):
                                chunk_dict['web'] = {
                                    'uri': str(chunk.web.uri) if hasattr(chunk.web, 'uri') else None,
                                    'title': str(chunk.web.title) if hasattr(chunk.web, 'title') else None,
                                }
                            if hasattr(chunk, 'retrieved_context'):
                                chunk_dict['retrieved_context'] = {
                                    'uri': str(chunk.retrieved_context.uri) if hasattr(chunk.retrieved_context, 'uri') else None,
                                    'title': str(chunk.retrieved_context.title) if hasattr(chunk.retrieved_context, 'title') else None,
                                }
                            if chunk_dict:  # Only add if we extracted something
                                grounding_chunks.append(chunk_dict)
            
            return {
                'text': text,
                'groundingChunks': grounding_chunks
            }
        
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")


# Global service instance
_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Get or create Gemini service instance."""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service

