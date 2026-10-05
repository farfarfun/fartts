"""
Edge TTS引擎实现
支持微软Edge浏览器的免费高质量语音合成和字幕生成
"""

import asyncio
import time

from edge_tts import Communicate, list_voices
from edge_tts import SubMaker as EdgeSubMaker
from farlog import getLogger
from funutil import deep_get
from funutil.util.retrying import retry

from funtts.base import BaseTTS
from funtts.models import SubtitleMaker, TTSRequest, TTSResponse, VoiceInfo

logger = getLogger("funtts")


def convert_rate_to_percent(rate: float) -> str:
    """将语音速率转换为Edge TTS支持的百分比格式"""
    if rate == 1.0:
        return "+0%"
    percent = round((rate - 1.0) * 100)
    if percent > 0:
        return f"+{percent}%"
    else:
        return f"{percent}%"


class EdgeTTS(BaseTTS):
    """
    Microsoft Edge TTS引擎

    特性:
    - 免费使用，无需API密钥
    - 高质量神经网络语音
    - 支持多种语言和语音
    - 支持SSML标记
    - 自动生成时间同步字幕
    - 支持语音速率调节

    依赖:
    - edge-tts: >=6.1.0
    """

    def __init__(self, voice_name: str = "zh-CN-XiaoxiaoNeural", **kwargs):
        """
        初始化Edge TTS引擎

        Args:
            voice_name: 默认语音名称
            **kwargs: 其他配置参数
        """
        super().__init__(voice_name, **kwargs)
        logger.info(f"Edge TTS引擎初始化完成，默认语音: {voice_name}")

    def synthesize(self, request: TTSRequest) -> TTSResponse:
        """
        语音合成实现

        Args:
            request: TTS请求对象

        Returns:
            TTSResponse: TTS响应对象
        """
        try:
            # 参数验证
            if not self._validate_request(request):
                return TTSResponse(
                    success=False,
                    request=request,
                    error_message="请求参数验证失败",
                    error_code="INVALID_REQUEST",
                )

            # 语音检查
            voice_name = request.voice_name or self.get_default_voice()
            if not self.is_voice_available(voice_name):
                logger.warning(f"语音可能不可用: {voice_name}，尝试继续合成")

            return self._synthesize(request)

        except ImportError as e:
            logger.error(f"Edge TTS依赖包未安装: {e}")
            return TTSResponse(
                success=False,
                request=request,
                error_message="缺少依赖包: pip install edge-tts",
                error_code="MISSING_DEPENDENCY",
            )

        except Exception as e:
            logger.error(f"Edge TTS语音合成失败: {e}")
            return TTSResponse(
                success=False,
                request=request,
                error_message=str(e),
                error_code="SYNTHESIS_ERROR",
            )

    @retry(4)
    def _synthesize(self, request: TTSRequest) -> TTSResponse:
        """Edge TTS语音合成核心方法"""
        start_time = time.time()
        text = request.text.strip()
        voice_file = request.output_file

        if not voice_file:
            import tempfile

            voice_file = tempfile.mktemp(suffix=f".{request.output_format}")

        try:
            rate_str = convert_rate_to_percent(request.voice_rate)
            voice_name = request.voice_name or self.get_default_voice()
            communicate = Communicate(text, voice_name, rate=rate_str)
            edge_sub_maker = EdgeSubMaker()

            # 创建我们自己的字幕制作器
            subtitle_maker = SubtitleMaker() if request.generate_subtitles else None

            logger.info(f"开始Edge TTS合成: voice={voice_name}, rate={rate_str}")

            with open(voice_file, "wb") as file:
                for chunk in communicate.stream_sync():
                    if chunk["type"] == "audio":
                        file.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary" and subtitle_maker:
                        edge_sub_maker.create_sub(
                            (chunk["offset"], chunk["duration"]), chunk["text"]
                        )
                        # 同时添加到我们的字幕制作器
                        subtitle_maker.add_segment_from_offset(
                            (chunk["offset"], chunk["duration"]), chunk["text"]
                        )

            # 获取音频时长
            duration = (
                subtitle_maker.get_total_duration()
                if subtitle_maker
                else self._get_audio_duration(voice_file)
            )

            logger.success(
                f"Edge TTS合成完成: voice={voice_name}, file={voice_file}, duration={duration:.2f}s"
            )

            return TTSResponse(
                success=True,
                request=request,
                audio_file=voice_file,
                subtitle_maker=subtitle_maker,
                duration=duration,
                voice_used=voice_name,
                processing_time=time.time() - start_time,
                engine_info=self._get_engine_info(),
            )

        except Exception as e:
            logger.error(f"Edge TTS处理失败: {str(e)}")
            return TTSResponse(
                success=False,
                request=request,
                error_message=str(e),
                error_code="EDGE_ERROR",
                processing_time=time.time() - start_time,
            )

    def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        """
        获取可用语音列表

        Args:
            language: 语言代码过滤（如 'zh-CN'）

        Returns:
            List[VoiceInfo]: 语音信息列表
        """
        try:
            voice_list = asyncio.run(list_voices())
            result = []
            if voice_list is None:
                logger.error("获取voice为空")
                return []
            for voice in voice_list:
                voice_info = self._create_voice_info(voice)
                result.append(voice_info)
            logger.info(f"获取到 {len(result)} 个Edge TTS语音")
            return result
        except ImportError:
            logger.error("edge-tts包未安装，无法获取语音列表")
            return []
        except Exception as e:
            logger.error(f"获取Edge TTS语音列表失败: {str(e)}")
            return []

    def is_voice_available(self, voice_name: str) -> bool:
        """
        检查语音是否可用

        Args:
            voice_name: 语音名称

        Returns:
            bool: 是否可用
        """
        try:
            voices = self.list_voices()
            return any(voice.name == voice_name for voice in voices)
        except Exception as e:
            logger.error("无法获取语音列表，假设语音可用", e)
            # 如果无法获取语音列表，假设语音可用
            return True

    def _validate_request(self, request: TTSRequest) -> bool:
        """验证请求参数"""
        if not request.text or not request.text.strip():
            logger.error("文本内容为空")
            return False

        if len(request.text) > 10000:
            logger.error(f"文本长度超出限制: {len(request.text)} > 10000")
            return False

        return True

    def _create_voice_info(self, voice_data: dict) -> VoiceInfo:
        """创建VoiceInfo对象"""
        locale = deep_get(voice_data, "Locale", "") or ""
        gender = deep_get(voice_data, "Gender", "") or ""  # 确保不为None
        return VoiceInfo(
            name=deep_get(voice_data, "Name", ""),
            display_name=deep_get(voice_data, "DisplayName", ""),
            language=deep_get(voice_data, "Language", ""),
            locale=locale,
            gender=gender.lower(),
            region=locale.split("-")[1] if "-" in locale else "unknown",
            engine="edge",
            sample_rate=24000,
            quality="high",
            is_neural=True,
            supports_ssml=True,
            supported_formats=["wav", "mp3"],
            engine_specific={
                "locale": locale,
                "local_name": deep_get(voice_data, "LocalName", ""),
                "short_name": deep_get(voice_data, "ShortName", ""),
                "voice_tag": deep_get(voice_data, "VoiceTag", {}),
            },
        )

    def _get_audio_duration(self, audio_file: str) -> float:
        """获取音频文件时长"""
        try:
            import subprocess

            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "quiet",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "csv=p=0",
                    audio_file,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                return float(result.stdout.strip())
        except Exception:
            pass

        # 估算时长
        try:
            import os

            file_size = os.path.getsize(audio_file)
            # MP3文件大约16KB/s (24kHz)
            return file_size / 16000
        except Exception:
            return 0.0

    def _get_engine_info(self) -> dict:
        """获取引擎信息"""
        return {
            "engine": "edge",
            "version": "1.0.0",
            "default_voice": self.get_default_voice(),
            "supported_formats": ["wav", "mp3"],
            "max_text_length": 10000,
            "supports_ssml": True,
            "supports_subtitles": True,
            "free_tier": True,
            "neural_voices": True,
        }
