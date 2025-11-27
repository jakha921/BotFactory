"""
Message processor for handling different message types (text, audio, files).
"""
from aiogram.types import Message
from typing import Optional
import aiohttp
import os
import logging

from bot.config import settings

logger = logging.getLogger(__name__)

DJANGO_API_URL = settings.DJANGO_API_BASE_URL


async def process_message(message: Message, bot) -> Optional[str]:
    """
    Process incoming message and extract text content.
    
    Handles:
    - Text messages: return text directly
    - Audio/Voice: transcribe using backend API
    - Files/Documents: extract text using backend API
    - Photos: extract text using OCR (if needed)
    
    Args:
        message: Telegram message object
        bot: Bot model instance
        
    Returns:
        Processed text content or None if error
    """
    try:
        # Handle text messages
        if message.text:
            return message.text
        
        # Handle voice/audio messages
        if message.voice or message.audio:
            return await process_audio_message(message)
        
        # Handle document messages
        if message.document:
            return await process_document_message(message)
        
        # Handle photo messages
        if message.photo:
            # For photos, return caption or placeholder
            return message.caption or "[Изображение]"
        
        return None
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        return None


async def process_audio_message(message: Message) -> Optional[str]:
    """Process audio/voice message and transcribe it."""
    try:
        file = message.voice or message.audio
        file_info = await message.bot.get_file(file.file_id)
        
        # Download file content
        file_bytes = await message.bot.download_file(file_info.file_path)
        
        # Determine audio format
        audio_format = 'ogg' if message.voice else (file_info.file_path.split('.')[-1] or 'wav')
        
        # Send to backend for transcription
        async with aiohttp.ClientSession() as session:
            form_data = aiohttp.FormData()
            form_data.add_field('audio_file', file_bytes.read(), filename=f'audio.{audio_format}')
            form_data.add_field('audio_format', audio_format)
            
            async with session.post(
                f'{DJANGO_API_URL}/chat/transcribe/',
                data=form_data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('text', '')
                else:
                    error_data = await response.json()
                    error_msg = error_data.get('error', 'Unknown error')
                    logger.error(f"Transcription failed: {error_msg}")
                    return None
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}", exc_info=True)
        return None


async def process_document_message(message: Message) -> Optional[str]:
    """Process document message and extract text."""
    try:
        file_info = await message.bot.get_file(message.document.file_id)
        file_bytes = await message.bot.download_file(file_info.file_path)
        
        # Send to backend for processing
        async with aiohttp.ClientSession() as session:
            form_data = aiohttp.FormData()
            form_data.add_field(
                'file',
                file_bytes.read(),
                filename=message.document.file_name or 'document'
            )
            
            async with session.post(
                f'{DJANGO_API_URL}/chat/process-file/',
                data=form_data,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('text', '')
                else:
                    error_data = await response.json()
                    error_msg = error_data.get('error', 'Unknown error')
                    logger.error(f"File processing failed: {error_msg}")
                    return None
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}", exc_info=True)
        return None

