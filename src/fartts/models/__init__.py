"""
FarTTS数据模型模块
统一的数据结构定义
"""

# 导入所有数据模型
from .audio_segment import AudioSegment
from .request_response import TTSRequest, TTSResponse
from .subtitle_maker import SubtitleMaker
from .voice_info import VoiceInfo

# 公开的API
__all__ = ["AudioSegment", "SubtitleMaker", "VoiceInfo", "TTSRequest", "TTSResponse"]
