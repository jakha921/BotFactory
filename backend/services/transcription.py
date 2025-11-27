"""
Audio transcription service using Google Speech-to-Text API.
Supports multiple languages: Uzbek (Cyrillic), Uzbek (Latin), Russian, English.

Fallback to speech_recognition library if Google Cloud Speech is not available.
Uses pure Python libraries for audio processing when possible (avoids FFmpeg dependency).
"""
import os
import io
import wave
from typing import Optional
from django.conf import settings

# Try to import Google Cloud Speech
try:
    from google.cloud import speech
    from google.cloud.speech import enums
    GOOGLE_SPEECH_AVAILABLE = True
except ImportError:
    GOOGLE_SPEECH_AVAILABLE = False

# Try to import speech_recognition as fallback
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

# Try to import pydub for audio conversion (requires FFmpeg for most formats)
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

# Check if FFmpeg is available (optional, for format conversion)
def _check_ffmpeg_available() -> bool:
    """Check if FFmpeg is available in system."""
    import shutil
    return shutil.which('ffmpeg') is not None or shutil.which('ffprobe') is not None

FFMPEG_AVAILABLE = _check_ffmpeg_available()

# Language codes for supported languages
LANGUAGE_CODES = {
    'uz_cyrl': 'uz-UZ',  # Uzbek (Cyrillic)
    'uz_latn': 'uz-UZ',  # Uzbek (Latin) - same code, auto-detected
    'ru': 'ru-RU',  # Russian
    'en': 'en-US',  # English
}

# Alternative languages list for auto-detection
ALTERNATIVE_LANGUAGES = ['uz-UZ', 'ru-RU', 'en-US']


def detect_language(audio_file: bytes, audio_format: str = 'wav') -> Optional[str]:
    """
    Auto-detect language of audio file.
    Tries Google Speech API with multiple languages to detect the best match.
    
    Returns:
        Language code (uz-UZ, ru-RU, en-US) or None if detection failed
    """
    # Try each supported language and see which gives the best result
    languages_to_try = ['uz-UZ', 'ru-RU', 'en-US']
    best_result = None
    best_confidence = 0.0
    
    # Use speech_recognition for quick language detection
    if SPEECH_RECOGNITION_AVAILABLE:
        try:
            recognizer = sr.Recognizer()
            
            # Convert to WAV if needed
            if audio_format.lower() == 'wav':
                wav_io = io.BytesIO(audio_file)
            else:
                # Skip conversion for now, just use WAV
                return None  # Will be detected during transcription
            
            try:
                with sr.AudioFile(wav_io) as source:
                    audio = recognizer.record(source)
                
                # Try each language and see which one works
                for lang in languages_to_try:
                    try:
                        text = recognizer.recognize_google(audio, language=lang, show_all=True)
                        if text and isinstance(text, dict) and 'alternative' in text:
                            # Get confidence from first alternative
                            alt = text['alternative'][0] if text['alternative'] else {}
                            confidence = alt.get('confidence', 0.5)
                            if confidence > best_confidence:
                                best_confidence = confidence
                                best_result = lang
                    except:
                        continue
                
                return best_result if best_confidence > 0.3 else None
            except:
                return None
        except:
            return None
    
    return None


def transcribe_audio(
    audio_file: bytes,
    audio_format: str = 'wav',
    language_code: Optional[str] = None,
    sample_rate: int = 16000,
    enable_automatic_punctuation: bool = True,
    enable_word_time_offsets: bool = False,
    auto_detect_language: bool = True
) -> dict:
    """
    Transcribe audio file using Google Speech-to-Text API.
    
    Args:
        audio_file: Audio file content as bytes
        audio_format: Audio format ('wav', 'mp3', 'flac', 'webm', etc.)
        language_code: Language code (uz-UZ, ru-RU, en-US). If None, uses auto-detection.
        sample_rate: Sample rate in Hz (default: 16000)
        enable_automatic_punctuation: Enable automatic punctuation
        enable_word_time_offsets: Enable word-level timestamps
        auto_detect_language: Auto-detect language if language_code is None
        
    Returns:
        dict with keys:
            - text: Transcribed text
            - confidence: Confidence score (0-1)
            - language_code: Detected language code
            - alternatives: List of alternative transcriptions
    """
    # Auto-detect language FIRST if not provided
    detected_language = language_code
    if not detected_language and auto_detect_language:
        detected_language = detect_language(audio_file, audio_format)
        if detected_language:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f'Language auto-detected: {detected_language}')
        else:
            # Default to Uzbek if detection fails
            detected_language = 'uz-UZ'
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f'Language auto-detection failed, using default: {detected_language}')
    
    # Use detected or requested language
    final_language_code = detected_language or language_code or 'uz-UZ'
    
    # First try Google Cloud Speech-to-Text if available
    if GOOGLE_SPEECH_AVAILABLE:
        try:
            # Initialize Speech-to-Text client
            # Try multiple authentication methods
            client = None
            credentials_path = getattr(settings, 'GOOGLE_APPLICATION_CREDENTIALS', None)
            
            # Method 1: Service account file
            if credentials_path and os.path.exists(credentials_path):
                client = speech.SpeechClient.from_service_account_file(credentials_path)
            else:
                # Method 2: Try default credentials
                try:
                    client = speech.SpeechClient()
                except Exception as cred_error:
                    # If default credentials fail, log and skip Google Cloud Speech
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f'Google Cloud Speech API credentials not found: {str(cred_error)}. Will use fallback method.')
                    raise cred_error
            
            if client is None:
                raise ValueError("Could not initialize Google Cloud Speech client")
            
            # Configure audio encoding based on format
            encoding_map = {
                'wav': enums.RecognitionConfig.AudioEncoding.LINEAR16,
                'mp3': enums.RecognitionConfig.AudioEncoding.MP3,
                'flac': enums.RecognitionConfig.AudioEncoding.FLAC,
                'webm': enums.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                'ogg': enums.RecognitionConfig.AudioEncoding.OGG_OPUS,
                'amr': enums.RecognitionConfig.AudioEncoding.AMR,
                'amr_wb': enums.RecognitionConfig.AudioEncoding.AMR_WB_ODS,
            }
            
            encoding = encoding_map.get(audio_format.lower(), enums.RecognitionConfig.AudioEncoding.LINEAR16)
            
            # For MP3 and other formats, we might need to detect encoding
            if audio_format.lower() in ['mp3', 'webm', 'ogg']:
                encoding = enums.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED
            
            # Build recognition config
            config = speech.RecognitionConfig(
                encoding=encoding,
                sample_rate_hertz=sample_rate,
                language_code=final_language_code,
                alternative_language_codes=[lang for lang in ALTERNATIVE_LANGUAGES if lang != final_language_code],
                enable_automatic_punctuation=enable_automatic_punctuation,
                enable_word_time_offsets=enable_word_time_offsets,
                model='latest_long',
                use_enhanced=True,
            )
            
            # Create audio object
            audio_obj = speech.RecognitionAudio(content=audio_file)
            
            # Perform transcription
            response = client.recognize(config=config, audio=audio_obj)
            
            # Process results
            if not response.results:
                # If Google Cloud fails, fall back to speech_recognition
                if SPEECH_RECOGNITION_AVAILABLE:
                    return _transcribe_with_speech_recognition(audio_file, audio_format, final_language_code)
                return {
                    'text': '',
                    'confidence': 0.0,
                    'language_code': final_language_code,
                    'alternatives': [],
                    'error': 'No transcription results'
                }
            
            # Get the best result
            best_result = response.results[0]
            best_alternative = best_result.alternatives[0]
            
            # Get alternatives
            alternatives = []
            for result in response.results:
                for alternative in result.alternatives:
                    if alternative != best_alternative:
                        alternatives.append({
                            'text': alternative.transcript,
                            'confidence': alternative.confidence
                        })
            
            return {
                'text': best_alternative.transcript,
                'confidence': best_alternative.confidence,
                'language_code': final_language_code,
                'alternatives': alternatives,
            }
            
        except Exception as e:
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Google Cloud Speech API failed: {str(e)}. Audio format: {audio_format}')
            
            # If Google Cloud fails, try fallback only if FFmpeg is available or format is WAV
            # For webm format, Google Cloud Speech should work, so this is likely a configuration issue
            if SPEECH_RECOGNITION_AVAILABLE and audio_format.lower() == 'wav':
                # Only try fallback for WAV format (doesn't require FFmpeg)
                try:
                    return _transcribe_with_speech_recognition(audio_file, audio_format, final_language_code)
                except Exception as fallback_error:
                    return {
                        'text': '',
                        'confidence': 0.0,
                        'language_code': final_language_code,
                        'alternatives': [],
                        'error': f'Google Cloud Speech API error: {str(e)}. Fallback also failed: {str(fallback_error)}'
                    }
            
            # Return error with helpful message
            error_msg = f'Google Speech API error: {str(e)}'
            if audio_format.lower() != 'wav':
                error_msg += f'. Note: Audio format {audio_format} requires Google Cloud Speech API (not available) or FFmpeg for conversion (not installed).'
            
            return {
                'text': '',
                'confidence': 0.0,
                'language_code': language_code or 'unknown',
                'alternatives': [],
                'error': error_msg
            }
    
    # Fallback to speech_recognition if Google Cloud Speech is not available
    # But only for WAV format (other formats require FFmpeg or Google Cloud Speech API)
    if SPEECH_RECOGNITION_AVAILABLE:
        if audio_format.lower() == 'wav':
            # Only try fallback for WAV format (doesn't require FFmpeg)
            return _transcribe_with_speech_recognition(audio_file, audio_format, language_code)
        else:
            # For non-WAV formats (webm, mp3, ogg), we need either:
            # 1. Google Cloud Speech API (supports these formats directly, no FFmpeg needed)
            # 2. FFmpeg for conversion to WAV
            error_msg = (
                f'Google Cloud Speech API недоступен (требуются service account credentials). '
                f'Формат {audio_format} можно обработать двумя способами:\n'
                f'1. Настроить Google Cloud Speech API credentials (рекомендуется, не требует FFmpeg)\n'
                f'2. Использовать формат WAV на frontend (работает без FFmpeg и credentials)\n'
                f'3. Установить FFmpeg для конвертации: brew install ffmpeg (macOS)'
            )
            return {
                'text': '',
                'confidence': 0.0,
                'language_code': language_code or 'unknown',
                'alternatives': [],
                'error': error_msg
            }
    
    # No transcription libraries available
    return {
        'text': '',
        'confidence': 0.0,
        'language_code': language_code or 'unknown',
        'alternatives': [],
        'error': 'No transcription libraries available. Please install google-cloud-speech (recommended) or SpeechRecognition with FFmpeg for audio conversion.'
    }


def _transcribe_with_speech_recognition(
    audio_file: bytes,
    audio_format: str,
    language_code: Optional[str] = None
) -> dict:
    """
    Fallback transcription using speech_recognition library.
    This is less accurate but doesn't require Google Cloud credentials.
    Note: For formats other than WAV, requires FFmpeg for conversion.
    """
    if not SPEECH_RECOGNITION_AVAILABLE:
        return {
            'text': '',
            'confidence': 0.0,
            'language_code': language_code or 'unknown',
            'alternatives': [],
            'error': 'speech_recognition library not installed'
        }
    
    try:
        recognizer = sr.Recognizer()
        
        # If format is already WAV, validate and use it directly without conversion
        if audio_format.lower() == 'wav':
            # Validate WAV format before using
            try:
                # Check if it's a valid WAV file by reading header
                wav_file = io.BytesIO(audio_file)
                header = wav_file.read(12)
                if len(header) < 12 or header[0:4] != b'RIFF' or header[8:12] != b'WAVE':
                    return {
                        'text': '',
                        'confidence': 0.0,
                        'language_code': final_language_code,
                        'alternatives': [],
                        'error': 'Invalid WAV file format. Audio file may be corrupted or not properly converted.'
                    }
                wav_file.seek(0)
                wav_io = wav_file
            except Exception as wav_error:
                return {
                    'text': '',
                    'confidence': 0.0,
                    'language_code': final_language_code,
                    'alternatives': [],
                    'error': f'Error reading WAV file: {str(wav_error)}'
                }
        else:
            # Try to convert to WAV using pydub (requires FFmpeg)
            # Only attempt conversion if FFmpeg is available
            if not PYDUB_AVAILABLE or not FFMPEG_AVAILABLE:
                return {
                    'text': '',
                    'confidence': 0.0,
                    'language_code': final_language_code,
                    'alternatives': [],
                    'error': f'Формат {audio_format} требует конвертацию в WAV, но FFmpeg не установлен. Рекомендации: 1) Используйте формат WAV на frontend (не требует конвертации), 2) Установите FFmpeg: brew install ffmpeg (macOS), 3) Используйте Google Cloud Speech API (поддерживает {audio_format} напрямую, но требует credentials).'
                }
            
            try:
                audio_data = AudioSegment.from_file(io.BytesIO(audio_file), format=audio_format.lower())
                # Convert to WAV
                wav_io = io.BytesIO()
                audio_data.export(wav_io, format='wav')
                wav_io.seek(0)
            except Exception as conv_error:
                # If conversion fails (e.g., FFmpeg not available), return error
                return {
                    'text': '',
                    'confidence': 0.0,
                    'language_code': final_language_code,
                    'alternatives': [],
                    'error': f'Ошибка конвертации аудио (требуется FFmpeg для формата {audio_format}): {str(conv_error)}. Установите FFmpeg или используйте WAV формат.'
                }
        
        # Use Google Web Speech API (free but limited)
        try:
            with sr.AudioFile(wav_io) as source:
                audio = recognizer.record(source)
        except Exception as audio_error:
            return {
                'text': '',
                'confidence': 0.0,
                'language_code': language_code or 'unknown',
                'alternatives': [],
                'error': f'Failed to load audio file: {str(audio_error)}'
            }
        
        # Map language codes for Google Web Speech API
        language_map = {
            'uz-UZ': 'uz-UZ',  # speech_recognition might not support Uzbek, will try
            'ru-RU': 'ru-RU',
            'en-US': 'en-US',
        }
        
        lang = language_map.get(language_code or 'uz-UZ', 'uz-UZ')
        
        # Try recognition with different language options
        # Google Web Speech API may not support Uzbek, so try Russian/English as fallback
        recognition_errors = []
        
        # Priority order: requested language, then alternatives
        languages_to_try = [lang]
        if lang == 'uz-UZ':
            # Uzbek might not be supported, try Russian and English
            languages_to_try.extend(['ru-RU', 'en-US'])
        elif lang == 'ru-RU':
            languages_to_try.append('en-US')
        elif lang == 'en-US':
            languages_to_try.append('ru-RU')
        
        for try_lang in languages_to_try:
            try:
                text = recognizer.recognize_google(audio, language=try_lang)
                return {
                    'text': text,
                    'confidence': 0.8,  # Approximate confidence for Web Speech API
                    'language_code': try_lang,
                    'alternatives': [],
                }
            except sr.UnknownValueError:
                recognition_errors.append(f'{try_lang}: Could not understand audio')
                continue  # Try next language
            except sr.RequestError as e:
                recognition_errors.append(f'{try_lang}: {str(e)}')
                continue  # Try next language
        
        # If all languages failed, return error with details
        error_details = '; '.join(recognition_errors)
        return {
            'text': '',
            'confidence': 0.0,
            'language_code': language_code or 'unknown',
            'alternatives': [],
            'error': f'Could not understand audio. Tried languages: {", ".join(languages_to_try)}. Details: {error_details}. Возможные причины: 1) Аудио слишком тихое или неразборчивое, 2) Язык не поддерживается Google Web Speech API (для узбекского может потребоваться Google Cloud Speech API), 3) Аудио слишком короткое.'
        }
    except Exception as e:
        return {
            'text': '',
            'confidence': 0.0,
            'language_code': language_code or 'unknown',
            'alternatives': [],
            'error': f'speech_recognition error: {str(e)}'
        }
