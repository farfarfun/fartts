"""
Tortoise TTS引擎

高质量的语音克隆TTS模型，能够生成极其逼真的语音。
虽然合成速度较慢，但音质接近真人水平，特别适合高质量语音克隆应用。
"""

from .tts import TortoiseTTS

__all__ = ["TortoiseTTS"]
