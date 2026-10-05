"""
eSpeak TTS引擎

基于eSpeak开源语音合成器的TTS引擎。
轻量级、跨平台，支持多种语言，适合Linux和嵌入式系统。
"""

from .tts import EspeakTTS

__all__ = ["EspeakTTS"]
