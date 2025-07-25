import speech_recognition as sr
import io
import os
from gtts import gTTS
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import tempfile
import uuid


def speech_to_text(audio_file, language='en'):
    """
    Convert audio file to text using speech recognition
    """
    try:
        # Initialize recognizer
        recognizer = sr.Recognizer()
        
        # Read audio file
        with sr.AudioFile(audio_file) as source:
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            # Record the audio
            audio_data = recognizer.record(source)
        
        # Use Google Speech Recognition
        try:
            # Convert language code format
            lang_code = 'it-IT' if language == 'it' else 'en-US'
            text = recognizer.recognize_google(audio_data, language=lang_code)
            return {
                'success': True,
                'text': text,
                'language': language
            }
        except sr.UnknownValueError:
            return {
                'success': False,
                'error': 'Could not understand audio',
                'text': ''
            }
        except sr.RequestError as e:
            return {
                'success': False,
                'error': f'Speech recognition service error: {e}',
                'text': ''
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'Audio processing error: {e}',
            'text': ''
        }


def text_to_speech(text, language='en'):
    """
    Convert text to speech and return audio file path
    """
    try:
        # Convert language code
        lang_code = 'it' if language == 'it' else 'en'
        
        # Create TTS object
        tts = gTTS(text=text, lang=lang_code, slow=False)
        
        # Generate unique filename
        filename = f"tts_{uuid.uuid4().hex}.mp3"
        
        # Save to temporary file first
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            tts.save(tmp_file.name)
            
            # Read the file content
            with open(tmp_file.name, 'rb') as audio_file:
                audio_content = audio_file.read()
            
            # Clean up temporary file
            os.unlink(tmp_file.name)
        
        # Save to Django storage
        audio_file_path = default_storage.save(
            f'audio/{filename}',
            ContentFile(audio_content)
        )
        
        return {
            'success': True,
            'audio_url': default_storage.url(audio_file_path),
            'file_path': audio_file_path
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Text-to-speech error: {e}',
            'audio_url': None
        }


def convert_audio_format(input_file, output_format='wav'):
    """
    Convert audio file to specified format using pydub
    """
    try:
        from pydub import AudioSegment
        
        # Load audio file
        audio = AudioSegment.from_file(input_file)
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{output_format}') as tmp_file:
            # Export to specified format
            audio.export(tmp_file.name, format=output_format)
            return tmp_file.name
            
    except Exception as e:
        print(f"Audio conversion error: {e}")
        return None


def cleanup_audio_file(file_path):
    """
    Clean up temporary audio files
    """
    try:
        if file_path and os.path.exists(file_path):
            os.unlink(file_path)
    except Exception as e:
        print(f"Error cleaning up audio file {file_path}: {e}")
