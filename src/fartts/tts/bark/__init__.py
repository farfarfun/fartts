"""
Bark TTS引擎

基于Transformer的文本转语音模型，支持生成高度逼真的语音。
除了语音合成外，还支持非语言声音（如笑声、叹息）和背景音乐生成。
"""

from .tts import BarkTTS

__all__ = ["BarkTTS"]
