"""
Pyttsx3 TTS引擎实现

Pyttsx3是一个跨平台的Python文本转语音库，支持多种TTS引擎：
- Windows: SAPI5
- macOS: NSSpeechSynthesizer
- Linux: espeak

本模块提供了统一的接口来使用pyttsx3进行语音合成。
"""

import os
import tempfile
import time

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

from farlog import getLogger

from funtts.base import BaseTTS
from funtts.models import (
    AudioSegment,
    SubtitleMaker,
    TTSRequest,
    TTSResponse,
    VoiceInfo,
)

logger = getLogger("funtts")


class Pyttsx3TTS(BaseTTS):
    """Pyttsx3 TTS引擎实现

    基于pyttsx3库的跨平台TTS引擎，支持Windows SAPI5、macOS NSSpeechSynthesizer和Linux espeak。
    """

    def __init__(self, voice_name: str = "default", **kwargs):
        """初始化Pyttsx3 TTS引擎

        Args:
            voice_name: 语音名称、ID或索引（数字字符串）
            **kwargs: 其他配置参数
                - rate: 语音速率倍数，默认1.0
                - volume: 音量，默认1.0
        """
        super().__init__(voice_name, **kwargs)

        if pyttsx3 is None:
            raise ImportError("pyttsx3库未安装，请运行: pip install pyttsx3")

        self.engine = None
        self.rate_multiplier = kwargs.get("rate", 1.0)
        self.volume = kwargs.get("volume", 1.0)

        self._init_engine()

    def _init_engine(self):
        """初始化pyttsx3引擎"""
        try:
            self.engine = pyttsx3.init()

            # 设置语音
            voices = self.engine.getProperty("voices")
            if voices:
                selected_voice = self._select_voice(voices)
                if selected_voice:
                    self.engine.setProperty("voice", selected_voice.id)
                    logger.info(
                        f"选择语音: {selected_voice.name} ({selected_voice.id})"
                    )
                else:
                    logger.warning(f"未找到指定语音: {self.voice_name}，使用默认语音")

            # 设置基础参数
            self.engine.setProperty("volume", self.volume)

            logger.info("Pyttsx3引擎初始化成功")

        except Exception as e:
            logger.error(f"Pyttsx3引擎初始化失败: {str(e)}")
            raise

    def _select_voice(self, voices):
        """选择合适的语音

        Args:
            voices: 可用语音列表

        Returns:
            选中的语音对象或None
        """
        if self.voice_name == "default" and voices:
            return voices[0]

        # 如果voice_name是数字，按索引选择
        if self.voice_name.isdigit():
            voice_index = int(self.voice_name)
            if 0 <= voice_index < len(voices):
                return voices[voice_index]

        # 按名称或ID匹配
        for voice in voices:
            if (
                self.voice_name in voice.name
                or self.voice_name == voice.id
                or self.voice_name.lower() in voice.name.lower()
            ):
                return voice

        return None

    def _synthesize(self, request: TTSRequest) -> TTSResponse:
        """执行语音合成

        Args:
            request: TTS请求对象

        Returns:
            TTS响应对象
        """
        start_time = time.time()

        try:
            if not self.engine:
                self._init_engine()

            # 验证文本长度
            if len(request.text) > 10000:
                return TTSResponse(
                    success=False,
                    request=request,
                    error_message="文本长度超过限制（最大10000字符）",
                    error_code="TEXT_TOO_LONG",
                    processing_time=time.time() - start_time,
                )

            # 准备输出文件
            output_file = request.output_file
            if not output_file:
                output_file = tempfile.mktemp(suffix=".wav")

            # 确保输出目录存在（相对文件名时 dirname 为空串，不能直接 makedirs）
            output_dir = os.path.dirname(os.path.abspath(output_file))
            os.makedirs(output_dir, exist_ok=True)

            # 设置语音参数
            self._configure_voice_parameters(request)

            # 执行合成
            logger.info(f"开始合成语音: {len(request.text)}字符")
            self.engine.save_to_file(request.text, output_file)
            self.engine.runAndWait()

            # 验证输出文件
            if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
                return TTSResponse(
                    success=False,
                    request=request,
                    error_message=f"音频文件生成失败: {output_file}",
                    error_code="FILE_GENERATION_ERROR",
                    processing_time=time.time() - start_time,
                )

            # 获取音频时长
            duration = self._estimate_audio_duration(output_file, request.text)

            # 生成字幕（如果需要）
            subtitle_file = None
            frt_subtitle_file = None
            if request.generate_subtitles:
                subtitle_file, frt_subtitle_file = self._generate_subtitles(
                    request, output_file, duration
                )

            logger.success(f"Pyttsx3合成完成: {output_file} ({duration:.2f}s)")

            return TTSResponse(
                success=True,
                request=request,
                audio_file=output_file,
                subtitle_file=subtitle_file,
                frt_subtitle_file=frt_subtitle_file,
                duration=duration,
                voice_used=self._get_current_voice_name(),
                processing_time=time.time() - start_time,
                engine_info=self.get_engine_info(),
            )

        except Exception as e:
            logger.error(f"Pyttsx3语音合成失败: {str(e)}")
            return TTSResponse(
                success=False,
                request=request,
                error_message=str(e),
                error_code="SYNTHESIS_ERROR",
                processing_time=time.time() - start_time,
            )

    def _configure_voice_parameters(self, request: TTSRequest):
        """配置语音参数

        Args:
            request: TTS请求对象
        """
        # 设置语音速率 (pyttsx3默认速率约200 words/min)
        base_rate = 200
        rate = int(base_rate * request.voice_rate * self.rate_multiplier)
        rate = max(50, min(400, rate))  # 限制在合理范围内
        self.engine.setProperty("rate", rate)

        # 设置音量：引擎级 volume 与请求级 voice_volume 相乘
        volume = min(1.0, max(0.0, self.volume * request.voice_volume))
        self.engine.setProperty("volume", volume)

    def _get_current_voice_name(self) -> str:
        """获取当前使用的语音名称"""
        try:
            if self.engine:
                current_voice = self.engine.getProperty("voice")
                voices = self.engine.getProperty("voices")
                for voice in voices:
                    if voice.id == current_voice:
                        return voice.name
        except Exception:
            pass
        return self.voice_name

    def _generate_subtitles(
        self, request: TTSRequest, audio_file: str, duration: float
    ):
        """生成字幕文件

        Args:
            request: TTS请求对象
            audio_file: 音频文件路径
            duration: 音频时长

        Returns:
            (subtitle_file, frt_subtitle_file) 字幕文件路径元组
        """
        try:
            subtitle_maker = SubtitleMaker()

            # 创建音频段
            segment = AudioSegment(
                start_time=0.0,
                end_time=duration,
                text=request.text,
                voice_name=self._get_current_voice_name(),
                speaker=getattr(request, "speaker", None),
            )
            subtitle_maker.add_segment(segment)

            # 生成字幕文件
            base_name = os.path.splitext(audio_file)[0]
            subtitle_file = f"{base_name}.srt"
            frt_subtitle_file = f"{base_name}.frt"

            # 保存字幕
            subtitle_maker.save_srt(subtitle_file)
            subtitle_maker.save_frt(frt_subtitle_file)

            return subtitle_file, frt_subtitle_file

        except Exception as e:
            logger.error(f"生成字幕失败: {str(e)}")
            return None, None

    def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        """获取可用的语音列表

        Args:
            language: 语言代码过滤（如 'en', 'zh' 等）

        Returns:
            语音信息列表
        """
        try:
            if not self.engine:
                self._init_engine()

            voices = self.engine.getProperty("voices")
            if not voices:
                logger.warning("未找到可用语音")
                return []

            result = []
            for i, voice in enumerate(voices):
                # 获取语音语言信息
                voice_languages = getattr(voice, "languages", [])
                if not voice_languages:
                    # 尝试从名称推断语言
                    voice_languages = self._infer_language_from_name(voice.name)

                # 语言过滤
                if language:
                    if not any(
                        lang.lower().startswith(language.lower())
                        for lang in voice_languages
                    ):
                        continue

                # 解析语音信息
                primary_language = voice_languages[0] if voice_languages else "unknown"
                gender = self._infer_gender_from_name(voice.name)

                voice_info = VoiceInfo(
                    name=voice.id,
                    display_name=voice.name,
                    language=primary_language,
                    gender=gender,
                    region="system",
                    engine="pyttsx3",
                    sample_rate=22050,  # pyttsx3默认采样率
                    quality="medium",
                    metadata={
                        "index": i,
                        "languages": voice_languages,
                        "age": getattr(voice, "age", "unknown"),
                        "platform_specific": True,
                    },
                )
                result.append(voice_info)

            logger.info(f"找到 {len(result)} 个可用语音")
            return result

        except Exception as e:
            logger.error(f"获取语音列表失败: {str(e)}")
            return []

    def _infer_language_from_name(self, voice_name: str) -> list[str]:
        """从语音名称推断语言"""
        name_lower = voice_name.lower()

        # 常见语言标识
        language_indicators = {
            "english": ["en-US"],
            "chinese": ["zh-CN"],
            "mandarin": ["zh-CN"],
            "cantonese": ["zh-HK"],
            "japanese": ["ja-JP"],
            "korean": ["ko-KR"],
            "french": ["fr-FR"],
            "german": ["de-DE"],
            "spanish": ["es-ES"],
            "italian": ["it-IT"],
            "russian": ["ru-RU"],
        }

        for indicator, languages in language_indicators.items():
            if indicator in name_lower:
                return languages

        # 默认假设为英语
        return ["en-US"]

    def _infer_gender_from_name(self, voice_name: str) -> str:
        """从语音名称推断性别"""
        name_lower = voice_name.lower()

        # 常见的性别标识
        if any(
            indicator in name_lower for indicator in ["female", "woman", "girl", "she"]
        ):
            return "female"
        elif any(indicator in name_lower for indicator in ["male", "man", "boy", "he"]):
            return "male"

        # 一些常见的名字性别推断
        female_names = ["anna", "mary", "susan", "linda", "karen", "helen", "sarah"]
        male_names = [
            "david",
            "michael",
            "john",
            "robert",
            "william",
            "james",
            "richard",
        ]

        for name in female_names:
            if name in name_lower:
                return "female"

        for name in male_names:
            if name in name_lower:
                return "male"

        return "unknown"

    def is_voice_available(self, voice_name: str) -> bool:
        """检查指定语音是否可用

        Args:
            voice_name: 语音名称或ID

        Returns:
            是否可用
        """
        try:
            voices = self.list_voices()
            return any(
                voice.name == voice_name or voice.display_name == voice_name
                for voice in voices
            )
        except Exception:
            return False

    def _estimate_audio_duration(self, audio_file: str, text: str) -> float:
        """估算音频时长

        Args:
            audio_file: 音频文件路径
            text: 原始文本

        Returns:
            估算的时长（秒）
        """
        try:
            # 尝试使用ffprobe获取精确时长
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

            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())

        except Exception:
            pass

        try:
            # 基于文件大小估算（WAV文件）
            file_size = os.path.getsize(audio_file)
            # WAV文件大约44KB/s (22kHz, 16bit, mono)
            return max(0.1, file_size / 44000)
        except Exception:
            pass

        # 基于文本长度估算（每分钟约200词）
        word_count = len(text.split())
        return max(0.1, word_count / 200 * 60)

    def get_engine_info(self) -> dict:
        """获取引擎信息

        Returns:
            引擎信息字典
        """
        return {
            "engine_name": "Pyttsx3TTS",
            "version": "1.0.0",
            "description": "跨平台Python TTS引擎",
            "supported_formats": ["wav"],
            "max_text_length": 10000,
            "supports_ssml": False,
            "supports_subtitles": True,
            "platform_dependent": True,
            "default_voice": self.voice_name,
            "current_rate_multiplier": self.rate_multiplier,
            "current_volume": self.volume,
        }

    def __del__(self):
        """析构函数，清理资源"""
        if hasattr(self, "engine") and self.engine:
            try:
                self.engine.stop()
            except Exception:
                pass
