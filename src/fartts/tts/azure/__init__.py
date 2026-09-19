"""
Azure TTS引擎

基于Microsoft Azure认知服务的高质量文本转语音引擎。
支持多种语言和语音，提供SSML支持和高质量音频输出。
"""

from .tts import AzureTTS

__all__ = ["AzureTTS"]
