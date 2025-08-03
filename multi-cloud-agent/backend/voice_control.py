import speech_recognition as sr
from gtts import gTTS
import os

def voice_to_text(audio_data: bytes) -> str:
    """Converts voice input to text using speech recognition."""
    r = sr.Recognizer()
    audio = sr.AudioData(audio_data, sample_rate=16000, sample_width=2)
    try:
        return r.recognize_google(audio)
    except sr.UnknownValueError:
        return "Could not understand audio."
    except sr.RequestError as e:
        return f"Could not request results; {e}"

def text_to_voice(text: str) -> bytes:
    """Converts text to voice audio."""
    tts = gTTS(text)
    audio_file = 'output.mp3'
    tts.save(audio_file)
    with open(audio_file, 'rb') as f:
        audio_bytes = f.read()
    os.remove(audio_file)
    return audio_bytes