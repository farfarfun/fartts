"""
eSpeak TTS引擎实现
支持开源的多语言语音合成器
"""

import subprocess
import time

from farlog import getLogger

from ...base import BaseTTS
from ...models import TTSRequest, TTSResponse, VoiceInfo

logger = getLogger("funtts.tts.espeak")


class EspeakTTS(BaseTTS):
    """
    eSpeak开源TTS引擎

    特性:
    - 完全免费开源
    - 支持100+种语言
    - 轻量级，资源占用少
    - 支持SSML部分功能
    - 跨平台支持
    - 可调节语音参数

    依赖:
    - eSpeak系统程序
    """

    def __init__(self, voice_name: str = "zh", **kwargs):
        """
        初始化eSpeak TTS引擎

        Args:
            voice_name: 默认语音名称（语言代码）
            **kwargs: 其他配置参数，包括:
                - espeak_path: eSpeak可执行文件路径
        """
        super().__init__(voice_name, **kwargs)
        self.espeak_path = kwargs.get("espeak_path", "espeak")

        # 检查eSpeak是否可用
        if self._check_espeak_available():
            logger.info(f"eSpeak TTS引擎初始化完成，默认语音: {voice_name}")
        else:
            logger.warning("eSpeak程序不可用，请确保已正确安装")

    def _pre_synthesize_check(self, request: TTSRequest) -> TTSResponse | None:
        """eSpeak 引擎的合成前检查

        不要改回重写 `synthesize()`：那样会跳过基类的字幕落盘与输出文件处理。
        """
        # 参数验证
        if not self._validate_request(request):
            return TTSResponse(
                success=False,
                request=request,
                error_message="请求参数验证失败",
                error_code="INVALID_REQUEST",
            )

        # 检查eSpeak可用性
        if not self._check_espeak_available():
            return TTSResponse(
                success=False,
                request=request,
                error_message="eSpeak程序不可用，请安装eSpeak",
                error_code="MISSING_DEPENDENCY",
            )

        return None

    def _synthesize(self, request: TTSRequest) -> TTSResponse:
        """eSpeak TTS语音合成核心方法"""
        start_time = time.time()

        try:
            voice_name = request.voice_name or self.get_default_voice()

            # 构建eSpeak命令
            cmd = [
                self.espeak_path,
                "-v",
                voice_name,  # 语音/语言
                "-s",
                str(int(150 * request.voice_rate)),  # 语音速度 (words per minute)
                "-w",
                request.output_file,  # 输出文件
                request.text,  # 要合成的文本
            ]

            # 如果需要调整音调
            if hasattr(request, "voice_pitch") and request.voice_pitch != 1.0:
                pitch = int(50 * request.voice_pitch)  # eSpeak音调范围0-99
                pitch = max(0, min(99, pitch))
                cmd.extend(["-p", str(pitch)])

            # 如果需要调整音量
            if hasattr(request, "voice_volume") and request.voice_volume != 1.0:
                volume = int(100 * request.voice_volume)  # eSpeak音量范围0-200
                volume = max(0, min(200, volume))
                cmd.extend(["-a", str(volume)])

            logger.info(
                f"开始eSpeak合成: voice={voice_name}, rate={request.voice_rate}"
            )
            logger.debug(f"eSpeak命令: {' '.join(cmd)}")

            # 执行eSpeak命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,  # 30秒超时
            )

            if result.returncode == 0:
                # 获取音频时长
                duration = self._get_audio_duration(request.output_file)

                logger.success(
                    f"eSpeak合成完成: {request.output_file}, 时长: {duration:.2f}s"
                )

                return TTSResponse(
                    success=True,
                    request=request,
                    audio_file=request.output_file,
                    duration=duration,
                    voice_used=voice_name,
                    processing_time=time.time() - start_time,
                    engine_info=self._get_engine_info(),
                )
            else:
                error_msg = f"eSpeak执行失败: {result.stderr.strip()}"
                logger.error(error_msg)
                return TTSResponse(
                    success=False,
                    request=request,
                    error_message=error_msg,
                    error_code="ESPEAK_ERROR",
                    processing_time=time.time() - start_time,
                )

        except subprocess.TimeoutExpired:
            error_msg = "eSpeak执行超时"
            logger.error(error_msg)
            return TTSResponse(
                success=False,
                request=request,
                error_message=error_msg,
                error_code="TIMEOUT_ERROR",
                processing_time=time.time() - start_time,
            )
        except Exception as e:
            logger.error(f"eSpeak处理失败: {str(e)}")
            return TTSResponse(
                success=False,
                request=request,
                error_message=str(e),
                error_code="ESPEAK_ERROR",
                processing_time=time.time() - start_time,
            )

    def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        """
        获取可用语音列表

        Args:
            language: 语言代码过滤（如 'zh', 'en'）

        Returns:
            List[VoiceInfo]: 语音信息列表
        """
        try:
            if not self._check_espeak_available():
                logger.warning("eSpeak不可用，返回预定义语音列表")
                return self._get_predefined_voices(language)

            # 获取eSpeak语音列表
            result = subprocess.run(
                [self.espeak_path, "--voices"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                voices = []
                lines = result.stdout.strip().split("\n")[1:]  # 跳过标题行

                for line in lines:
                    if not line.strip():
                        continue

                    parts = line.split()
                    if len(parts) >= 4:
                        lang_code = parts[1]
                        voice_name = parts[3]

                        # 语言过滤
                        if language and not lang_code.startswith(language):
                            continue

                        voice_info = self._create_voice_info(
                            lang_code, voice_name, parts
                        )
                        voices.append(voice_info)

                logger.info(f"获取到 {len(voices)} 个eSpeak语音")
                return voices
            else:
                logger.warning("获取eSpeak语音列表失败，返回预定义列表")
                return self._get_predefined_voices(language)

        except Exception as e:
            logger.error(f"获取eSpeak语音列表失败: {e}")
            return self._get_predefined_voices(language)

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
        except Exception:
            # 如果无法获取语音列表，假设语音可用
            return True

    def _validate_request(self, request: TTSRequest) -> bool:
        """验证请求参数"""
        if not request.text or not request.text.strip():
            logger.error("文本内容为空")
            return False

        if len(request.text) > 10000:  # eSpeak建议限制
            logger.error(f"文本长度超出建议限制: {len(request.text)} > 10000")
            return False

        return True

    def _check_espeak_available(self) -> bool:
        """检查eSpeak是否可用"""
        try:
            result = subprocess.run(
                [self.espeak_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _create_voice_info(
        self, lang_code: str, voice_name: str, parts: list[str]
    ) -> VoiceInfo:
        """创建VoiceInfo对象"""
        # eSpeak语音信息格式：Pty Language Age/Gender VoiceName File Other
        age_gender = parts[2] if len(parts) > 2 else ""
        gender = "unknown"
        age = "adult"

        if "M" in age_gender:
            gender = "male"
        elif "F" in age_gender:
            gender = "female"

        if "child" in age_gender.lower():
            age = "child"

        return VoiceInfo(
            name=lang_code,  # eSpeak使用语言代码作为语音名称
            display_name=voice_name,
            language=lang_code.split("-")[0] if "-" in lang_code else lang_code,
            locale=lang_code,
            gender=gender,
            age=age,
            engine="espeak",
            sample_rate=22050,  # eSpeak默认采样率
            quality="standard",
            is_neural=False,
            supports_ssml=True,  # 部分支持
            supported_formats=["wav"],
            engine_specific={
                "age_gender": age_gender,
                "voice_file": parts[4] if len(parts) > 4 else "",
            },
        )

    def _get_predefined_voices(self, language: str | None = None) -> list[VoiceInfo]:
        """获取预定义的语音列表（当无法获取eSpeak语音时使用）"""
        predefined_voices = [
            # 主要语言
            ("zh", "中文", "zh", "female"),
            ("en", "English", "en", "male"),
            ("es", "Español", "es", "female"),
            ("fr", "Français", "fr", "female"),
            ("de", "Deutsch", "de", "male"),
            ("it", "Italiano", "it", "female"),
            ("pt", "Português", "pt", "male"),
            ("ru", "Русский", "ru", "female"),
            ("ja", "日本語", "ja", "female"),
            ("ko", "한국어", "ko", "female"),
        ]

        result = []
        for lang_code, display_name, language_code, gender in predefined_voices:
            if language and not lang_code.startswith(language):
                continue

            voice_info = VoiceInfo(
                name=lang_code,
                display_name=display_name,
                language=language_code,
                locale=lang_code,
                gender=gender,
                engine="espeak",
                sample_rate=22050,
                quality="standard",
                is_neural=False,
                supports_ssml=True,
                supported_formats=["wav"],
            )
            result.append(voice_info)

        return result

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
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            logger.debug(
                f"无法通过 ffprobe 获取 eSpeak 音频时长，改用文件大小估算: {exc}"
            )

        # 估算时长
        try:
            import os

            file_size = os.path.getsize(audio_file)
            # WAV文件大约44KB/s (22kHz 16-bit)
            return file_size / 44100
        except Exception:
            return 0.0

    def _get_engine_info(self) -> dict:
        """获取引擎信息"""
        version = "unknown"
        try:
            result = subprocess.run(
                [self.espeak_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                version = result.stdout.strip().split("\n")[0]
        except (OSError, subprocess.SubprocessError) as exc:
            logger.debug(f"无法获取 eSpeak 版本: {exc}")

        return {
            "engine": "espeak",
            "version": version,
            "default_voice": self.get_default_voice(),
            "supported_formats": ["wav"],
            "max_text_length": 10000,
            "supports_ssml": True,
            "supports_subtitles": False,
            "free_tier": True,
            "open_source": True,
        }
