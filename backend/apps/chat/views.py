"""
Views for chat app.
ChatSessionViewSet and ChatMessageViewSet for managing chat sessions and messages.
Includes endpoints for audio transcription, file processing, and bot response generation.
"""
from rest_framework import viewsets, views, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404

from apps.chat.models import ChatSession, ChatMessage
from apps.bots.models import Bot
from apps.chat.serializers import ChatMessageSerializer, ChatSessionSerializer
from core.permissions import IsOwnerOrReadOnly
from services.transcription import transcribe_audio
from services.file_processing import extract_text_from_file
from services.gemini import get_gemini_service
from apps.knowledge.models import DocumentChunk, TextSnippet
from pgvector.django import L2Distance
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings


class ChatSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing chat sessions.
    
    list: GET /api/v1/bots/{bot_id}/sessions/ - List chat sessions for a bot
    retrieve: GET /api/v1/sessions/{id}/ - Get session details
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ChatSessionSerializer
    
    def get_queryset(self):
        """Filter sessions by bot and ensure user owns the bot."""
        bot_id = self.kwargs.get('bot_id')
        if bot_id:
            bot = get_object_or_404(Bot, id=bot_id, owner=self.request.user)
            return ChatSession.objects.filter(bot=bot).select_related('user', 'bot')
        return ChatSession.objects.none()
    
    def list(self, request, bot_id=None):
        """List chat sessions for a bot."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ChatMessageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing chat messages.
    
    list: GET /api/v1/sessions/{session_id}/messages/ - List messages for a session
    retrieve: GET /api/v1/messages/{id}/ - Get message details
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ChatMessageSerializer
    
    def get_queryset(self):
        """Filter messages by session and ensure user owns the bot."""
        session_id = self.kwargs.get('session_id')
        if session_id:
            session = get_object_or_404(
                ChatSession,
                id=session_id,
                bot__owner=self.request.user
            )
            return ChatMessage.objects.filter(session=session).select_related('session')
        return ChatMessage.objects.none()
    
    def list(self, request, session_id=None):
        """List messages for a session."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ChatGenerationView(views.APIView):
    """
    API View for generating bot responses.
    
    POST /api/v1/chat/generate/ - Generate bot response using Gemini API
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]
    
    def post(self, request):
        """
        Generate bot response using Gemini API.
        
        Request:
            {
                "bot_id": "uuid",
                "prompt": "User message",
                "history": [
                    {"role": "user", "content": "..."},
                    {"role": "model", "content": "..."}
                ],
                "system_instruction": "...",
                "thinking_budget": 32768,  // optional
                "temperature": 0.7  // optional
            }
        
        Response:
            {
                "text": "Bot response",
                "groundingChunks": [...]  // optional
            }
        """
        bot_id = request.data.get('bot_id')
        prompt = request.data.get('prompt')
        history = request.data.get('history', [])
        system_instruction = request.data.get('system_instruction', 'You are a helpful AI assistant.')
        thinking_budget = request.data.get('thinking_budget', None)
        temperature = request.data.get('temperature', 0.7)
        
        # Validate required fields
        if not bot_id:
            return Response(
                {'error': 'bot_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not prompt:
            return Response(
                {'error': 'prompt is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get bot and verify ownership
        try:
            bot = get_object_or_404(Bot, id=bot_id, owner=request.user)
        except Exception:
            return Response(
                {'error': 'Bot not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Use bot settings if not provided
        model_name = bot.model or 'gemini-2.5-flash'
        final_system_instruction = system_instruction or bot.system_instruction or 'You are a helpful AI assistant.'
        final_temperature = temperature if temperature is not None else (bot.temperature or 0.7)
        final_thinking_budget = thinking_budget if thinking_budget is not None else bot.thinking_budget
        
        # RAG: Get relevant context from knowledge base
        rag_context = None
        try:
            # Embed the prompt
            embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
            prompt_embedding = embeddings.embed_query(prompt)
            
            # Get relevant document chunks
            doc_chunks = DocumentChunk.objects.filter(
                document__bot=bot
            ).order_by(
                L2Distance('embedding', prompt_embedding)
            )[:3]  # Top 3 most relevant chunks
            
            # Get relevant text snippets
            snippet_chunks = TextSnippet.objects.filter(
                bot=bot,
                embedding__isnull=False
            ).order_by(
                L2Distance('embedding', prompt_embedding)
            )[:3]  # Top 3 most relevant snippets
            
            # Combine context
            context_parts = []
            if doc_chunks.exists():
                context_parts.append("## Relevant Document Content:")
                for chunk in doc_chunks:
                    context_parts.append(f"- {chunk.text[:500]}...")  # Limit chunk size
            
            if snippet_chunks.exists():
                context_parts.append("\n## Relevant Knowledge Base Snippets:")
                for snippet in snippet_chunks:
                    context_parts.append(f"- {snippet.title}: {snippet.content[:500]}...")
            
            if context_parts:
                rag_context = "\n".join(context_parts)
                final_system_instruction = f"{final_system_instruction}\n\n{rag_context}"
        except Exception as e:
            # Log error but continue without RAG context
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to retrieve RAG context: {str(e)}")
        
        # Generate response using Gemini service
        try:
            gemini_service = get_gemini_service()
            result = gemini_service.generate_response(
                model_name=model_name,
                prompt=prompt,
                system_instruction=final_system_instruction,
                history=history,
                thinking_budget=final_thinking_budget,
                temperature=final_temperature
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            error_detail = str(e)
            traceback.print_exc()
            
            return Response(
                {
                    'error': f'Failed to generate response: {error_detail}',
                    'details': traceback.format_exc()
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TranscriptionViewSet(viewsets.ViewSet):
    """
    ViewSet for audio transcription.
    
    transcribe: POST /api/v1/chat/transcribe/ - Transcribe audio file
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def transcribe(self, request):
        """
        Transcribe audio file.
        
        Request:
            - audio_file: Audio file (required)
            - language_code: Language code (optional, auto-detected if not provided)
                - 'uz-UZ' for Uzbek
                - 'ru-RU' for Russian
                - 'en-US' for English
            - audio_format: Audio format (optional, auto-detected from file)
        
        Response:
            {
                "text": "Transcribed text",
                "confidence": 0.95,
                "language_code": "uz-UZ",
                "alternatives": [...]
            }
        """
        if 'audio_file' not in request.FILES:
            return Response(
                {'error': 'audio_file is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        audio_file = request.FILES['audio_file']
        language_code = request.data.get('language_code', None)
        audio_format = request.data.get('audio_format', None)
        
        # Read audio file content
        audio_content = audio_file.read()
        
        # Detect audio format from file extension if not provided
        if not audio_format:
            filename = audio_file.name.lower()
            if filename.endswith('.wav'):
                audio_format = 'wav'
            elif filename.endswith('.mp3'):
                audio_format = 'mp3'
            elif filename.endswith('.flac'):
                audio_format = 'flac'
            elif filename.endswith('.webm'):
                audio_format = 'webm'
            elif filename.endswith('.ogg'):
                audio_format = 'ogg'
            else:
                audio_format = 'wav'  # Default
        
        # Perform transcription
        try:
            # Log audio file info for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f'Transcribing audio: format={audio_format}, size={len(audio_content)} bytes, language={language_code}')
            
            result = transcribe_audio(
                audio_file=audio_content,
                audio_format=audio_format,
                language_code=language_code,  # If None, will auto-detect
                enable_automatic_punctuation=True,
                auto_detect_language=True  # Enable auto-detection if language not specified
            )

            # Check for errors in result
            if result.get('error'):
                logger.error(f'Transcription error: {result["error"]}')
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Check if text is empty but no error
            if not result.get('text'):
                logger.warning('Transcription returned empty text')
                return Response(
                    {
                        'error': 'Transcription returned empty result. Audio may be too short, too quiet, or in unsupported language.',
                        'text': '',
                        'confidence': result.get('confidence', 0.0),
                        'language_code': result.get('language_code', language_code or 'unknown')
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            logger.info(f'Transcription successful: text_length={len(result.get("text", ""))}, confidence={result.get("confidence", 0.0)}')
            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f'Transcription exception: {str(e)}\n{traceback.format_exc()}')
            return Response(
                {'error': f'Transcription failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FileProcessingViewSet(viewsets.ViewSet):
    """
    ViewSet for file processing (text extraction).
    
    process: POST /api/v1/chat/process-file/ - Process file and extract text
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def process_file(self, request):
        """
        Process file and extract text.
        
        Request:
            - file: File to process (required)
                - Supported: PDF, DOCX, TXT, MD, Images (JPG, PNG, etc.)
            - file_type: File type (optional, auto-detected)
            - ocr_languages: OCR languages for images (optional, default: ['uzb', 'rus', 'eng'])
        
        Response:
            {
                "text": "Extracted text",
                "pages": 3,
                "file_type": "pdf",
                "file_name": "document.pdf"
            }
        """
        if 'file' not in request.FILES:
            return Response(
                {'error': 'file is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        file = request.FILES['file']
        file_type = request.data.get('file_type', None)
        ocr_languages = request.data.get('ocr_languages', None)
        
        # Parse OCR languages if provided as string
        if ocr_languages and isinstance(ocr_languages, str):
            ocr_languages = [lang.strip() for lang in ocr_languages.split(',')]
        
        # Read file content
        file_content = file.read()
        
        # Process file
        try:
            result = extract_text_from_file(
                file_content=file_content,
                file_name=file.name,
                file_type=file_type,
                ocr_languages=ocr_languages
            )
            
            # Add file name to result
            result['file_name'] = file.name
            
            if 'error' in result:
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'File processing failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
