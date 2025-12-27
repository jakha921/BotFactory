"""
AI-powered views for bots app.
Provides endpoints for AI-assisted instruction improvement and content generation.
"""
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from services.gemini import get_gemini_service


class ImproveInstructionView(views.APIView):
    """
    POST /api/v1/bots/improve-instruction/ - Improve system instruction with AI.
    
    Request Body:
    {
        "instruction": "current instruction text",
        "bot_id": "optional-bot-id"
    }
    
    Response:
    {
        "text": "improved instruction",
        "success": true
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        instruction = request.data.get('instruction', '')
        bot_id = request.data.get('bot_id')
        
        if not instruction:
            return Response(
                {'error': 'instruction is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            gemini = get_gemini_service()
            
            prompt = f"""Rewrite the following system instructions for an AI bot to be more professional, concise, and robust. Keep the core intent and behavior, but improve clarity and effectiveness:

{instruction}

Return ONLY the improved instruction text, nothing else."""
            
            result = gemini.generate_response(
                model_name='gemini-2.0-flash-exp',
                prompt=prompt,
                system_instruction='You are an expert prompt engineer.',
                temperature=0.7
            )
            
            return Response({
                'text': result.get('text', ''),
                'success': True
            })
            
        except Exception as e:
            return Response(
                {'error': str(e), 'success': False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GenerateContentView(views.APIView):
    """
    POST /api/v1/bots/generate-content/ - Generate content for knowledge base.
    
    Request Body:
    {
        "title": "topic title",
        "bot_id": "optional-bot-id"
    }
    
    Response:
    {
        "text": "generated content",
        "success": true
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        title = request.data.get('title', '')
        bot_id = request.data.get('bot_id')
        
        if not title:
            return Response(
                {'error': 'title is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            gemini = get_gemini_service()
            
            prompt = f"""Generate comprehensive content about: {title}

Make it informative, well-structured, suitable for a knowledge base, 200-400 words.

Return ONLY the content text."""
            
            result = gemini.generate_response(
                model_name='gemini-2.0-flash-exp',
                prompt=prompt,
                system_instruction='You are a helpful content generator.',
                temperature=0.7
            )
            
            return Response({
                'text': result.get('text', ''),
                'success': True
            })
            
        except Exception as e:
            return Response(
                {'error': str(e), 'success': False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
