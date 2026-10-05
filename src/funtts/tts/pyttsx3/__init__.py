"""
Pyttsx3 TTS引擎

跨平台的Python文本转语音引擎，基于pyttsx3库。
支持Windows SAPI5、macOS NSSpeechSynthesizer和Linux espeak。
"""

from .tts import Pyttsx3TTS

__all__ = ["Pyttsx3TTS"]
