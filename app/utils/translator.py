"""
Translation utility for handling Khmer and other languages
"""
from googletrans import Translator
import re

translator = Translator()

def detect_language(text):
    """Detect if text contains Khmer characters"""
    khmer_pattern = re.compile(r'[\u1780-\u17FF]')
    return 'km' if khmer_pattern.search(text) else 'en'

def translate_to_english(text):
    """Translate text to English"""
    try:
        if not text:
            return text
            
        # Check if already in English
        lang = detect_language(text)
        if lang == 'en':
            return text
            
        # Translate to English
        result = translator.translate(text, src='km', dest='en')
        return result.text
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # Return original if translation fails

def translate_job_title(title):
    """
    Translate job title to English for matching
    Returns both original and translated title
    """
    try:
        translated = translate_to_english(title)
        return {
            'original': title,
            'english': translated,
            'is_khmer': detect_language(title) == 'km'
        }
    except Exception as e:
        print(f"Job title translation error: {e}")
        return {
            'original': title,
            'english': title,
            'is_khmer': False
        }

def translate_keywords(keywords):
    """
    Translate a list of keywords to English
    """
    translated = []
    for keyword in keywords:
        try:
            trans = translate_to_english(keyword)
            translated.append(trans)
        except Exception as e:
            print(f"Keyword translation error: {e}")
            translated.append(keyword)
    return translated
