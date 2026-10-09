"""
Azure TTS引擎实现
支持微软Azure认知服务的高质量语音合成和字幕生成
"""

import os
import time
from xml.sax.saxutils import escape as xml_escape

from farlog import getLogger

from ...base import BaseTTS
from ...models import SubtitleMaker, TTSRequest, TTSResponse, VoiceInfo

logger = getLogger("funtts.tts.azure")


class AzureTTS(BaseTTS):
    """
    Microsoft Azure认知服务TTS引擎

    特性:
    - 企业级高质量语音合成
    - 支持SSML和自定义语音
    - 丰富的语音选择和语言支持
    - 支持语音情感和风格调节
    - 支持批量处理和流式合成
    - 可自定义语音模型

    依赖:
    - azure-cognitiveservices-speech: >=1.30.0
    """

    def __init__(self, voice_name: str = "zh-CN-XiaoxiaoNeural", **kwargs):
        """
        初始化Azure TTS引擎

        Args:
            voice_name: 默认语音名称
            **kwargs: 其他非敏感配置参数，例如 service_region。Azure 密钥只能
                通过 AZURE_SPEECH_KEY 环境变量提供。
        """
        if {"speech_key", "subscription_key"}.intersection(kwargs):
            raise ValueError(
                "Azure 密钥不能作为构造参数传入，请使用 AZURE_SPEECH_KEY 环境变量"
            )
        super().__init__(voice_name, **kwargs)
        self.speech_key = os.getenv("AZURE_SPEECH_KEY", "")
        self.service_region = kwargs.get("service_region") or os.getenv(
            "AZURE_SPEECH_REGION", ""
        )

        if not self.speech_key or not self.service_region:
            logger.warning(
                "Azure语音服务密钥或区域未配置，请设置AZURE_SPEECH_KEY和AZURE_SPEECH_REGION环境变量"
            )
        else:
            logger.info(f"Azure TTS引擎初始化完成，区域: {self.service_region}")

    def _pre_synthesize_check(self, request: TTSRequest) -> TTSResponse | None:
        """Azure 引擎的合成前检查

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

        # 检查Azure配置
        if not self.speech_key or not self.service_region:
            return TTSResponse(
                success=False,
                request=request,
                error_message="Azure语音服务未配置，请设置 AZURE_SPEECH_KEY 和 AZURE_SPEECH_REGION 环境变量",
                error_code="MISSING_CREDENTIALS",
            )

        # 检查SDK是否安装
        try:
            import azure.cognitiveservices.speech  # noqa: F401
        except ImportError as e:
            logger.error(f"Azure SDK未安装: {e}")
            return TTSResponse(
                success=False,
                request=request,
                error_message="缺少依赖包: pip install azure-cognitiveservices-speech",
                error_code="MISSING_DEPENDENCY",
            )

        return None

    def _synthesize(self, request: TTSRequest) -> TTSResponse:
        """Azure TTS语音合成核心方法"""
        start_time = time.time()

        try:
            import azure.cognitiveservices.speech as speechsdk

            # 配置语音服务
            speech_config = speechsdk.SpeechConfig(
                subscription=self.speech_key, region=self.service_region
            )

            voice_name = request.voice_name or self.get_default_voice()
            speech_config.speech_synthesis_voice_name = voice_name

            # 设置输出格式
            if request.output_format.lower() == "wav":
                speech_config.set_speech_synthesis_output_format(
                    speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm
                )

            # 配置音频输出
            audio_config = speechsdk.audio.AudioOutputConfig(
                filename=request.output_file
            )

            # 创建合成器
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config, audio_config=audio_config
            )

            # 构建SSML（速率/音调/音量任一偏离默认值时都需要走SSML）
            prosody_attrs = []
            if request.voice_rate != 1.0:
                # 用 round 而不是 int：int 对负数是朝零截断，且浮点误差会让
                # 0.7 这类取值算出 -29% 而不是 -30%
                prosody_attrs.append(
                    f'rate="{round((request.voice_rate - 1.0) * 100):+d}%"'
                )
            if request.voice_pitch != 1.0:
                prosody_attrs.append(
                    f'pitch="{round((request.voice_pitch - 1.0) * 100):+d}%"'
                )
            if request.voice_volume != 1.0:
                # SSML volume 取 0-100 的绝对值，voice_volume 定义域是 0.0-1.0
                prosody_attrs.append(
                    f'volume="{max(0, min(100, round(request.voice_volume * 100)))}"'
                )

            if prosody_attrs:
                escaped_text = xml_escape(request.text)
                text_to_speak = f"""
                <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-CN">
                    <voice name="{voice_name}">
                        <prosody {" ".join(prosody_attrs)}>
                            {escaped_text}
                        </prosody>
                    </voice>
                </speak>
                """
                is_ssml = True
            else:
                text_to_speak = request.text
                is_ssml = False

            logger.info(
                f"开始Azure TTS合成: voice={voice_name}, rate={request.voice_rate}"
            )

            # 执行合成
            if is_ssml:
                result = synthesizer.speak_ssml_async(text_to_speak).get()
            else:
                result = synthesizer.speak_text_async(text_to_speak).get()

            # 检查结果
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # 获取音频时长
                duration = self._get_audio_duration(request.output_file)

                # 创建字幕（Azure TTS不直接提供时间戳，需要估算）
                subtitle_maker = None
                if request.generate_subtitles:
                    subtitle_maker = self._create_subtitle_from_text(
                        request.text, duration
                    )

                logger.success(
                    f"Azure TTS合成完成: {request.output_file}, 时长: {duration:.2f}s"
                )

                return TTSResponse(
                    success=True,
                    request=request,
                    audio_file=request.output_file,
                    subtitle_maker=subtitle_maker,
                    duration=duration,
                    voice_used=voice_name,
                    processing_time=time.time() - start_time,
                    engine_info=self._get_engine_info(),
                )

            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = speechsdk.CancellationDetails(result)
                error_msg = f"Azure TTS取消: {cancellation_details.reason}"
                if cancellation_details.error_details:
                    error_msg += f", 详情: {cancellation_details.error_details}"

                logger.error(error_msg)
                return TTSResponse(
                    success=False,
                    request=request,
                    error_message=error_msg,
                    error_code="AZURE_CANCELLED",
                    processing_time=time.time() - start_time,
                )
            else:
                error_msg = f"Azure TTS合成失败: {result.reason}"
                logger.error(error_msg)
                return TTSResponse(
                    success=False,
                    request=request,
                    error_message=error_msg,
                    error_code="AZURE_ERROR",
                    processing_time=time.time() - start_time,
                )

        except Exception as e:
            logger.error(f"Azure TTS处理失败: {str(e)}")
            return TTSResponse(
                success=False,
                request=request,
                error_message=str(e),
                error_code="AZURE_ERROR",
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
            import azure.cognitiveservices.speech as speechsdk

            if not self.speech_key or not self.service_region:
                logger.warning("Azure配置不完整，返回预定义语音列表")
                return self._get_predefined_voices(language)

            # 配置语音服务
            speech_config = speechsdk.SpeechConfig(
                subscription=self.speech_key, region=self.service_region
            )

            # 创建合成器
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)

            # 获取语音列表
            voices_result = synthesizer.get_voices_async().get()

            if voices_result.reason == speechsdk.ResultReason.VoicesListRetrieved:
                result = []
                for voice in voices_result.voices:
                    if language and not voice.locale.startswith(language):
                        continue

                    voice_info = self._create_voice_info_from_azure(voice)
                    result.append(voice_info)

                logger.info(f"获取到 {len(result)} 个Azure语音")
                return result
            else:
                logger.warning("获取Azure语音列表失败，返回预定义列表")
                return self._get_predefined_voices(language)

        except ImportError:
            logger.error("Azure SDK未安装，返回预定义语音列表")
            return self._get_predefined_voices(language)
        except Exception as e:
            logger.error(f"获取Azure语音列表失败: {e}")
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

        if len(request.text) > 50000:  # Azure限制更高
            logger.error(f"文本长度超出限制: {len(request.text)} > 50000")
            return False

        return True

    def _create_voice_info_from_azure(self, azure_voice) -> VoiceInfo:
        """从Azure语音对象创建VoiceInfo"""
        return VoiceInfo(
            name=azure_voice.short_name,
            display_name=azure_voice.local_name,
            language=azure_voice.locale.split("-")[0],
            locale=azure_voice.locale,
            gender=azure_voice.gender.name.lower() if azure_voice.gender else "unknown",
            region=azure_voice.locale.split("-")[1]
            if "-" in azure_voice.locale
            else "unknown",
            engine="azure",
            sample_rate=24000,
            quality="premium",
            is_neural=True,
            supports_ssml=True,
            supported_formats=["wav", "mp3"],
            engine_specific={
                "voice_type": azure_voice.voice_type.name
                if azure_voice.voice_type
                else "Standard",
                "style_list": getattr(azure_voice, "style_list", []),
                "role_play_list": getattr(azure_voice, "role_play_list", []),
            },
        )

    def _get_predefined_voices(self, language: str | None = None) -> list[VoiceInfo]:
        """获取预定义的语音列表（当无法连接Azure时使用）"""
        predefined_voices = [
            # 中文语音
            ("zh-CN-XiaoxiaoNeural", "晓晓", "zh-CN", "female"),
            ("zh-CN-YunxiNeural", "云希", "zh-CN", "male"),
            ("zh-CN-YunyangNeural", "云扬", "zh-CN", "male"),
            ("zh-CN-XiaoyiNeural", "晓伊", "zh-CN", "female"),
            ("zh-CN-YunjianNeural", "云健", "zh-CN", "male"),
            # 英文语音
            ("en-US-AriaNeural", "Aria", "en-US", "female"),
            ("en-US-JennyNeural", "Jenny", "en-US", "female"),
            ("en-US-GuyNeural", "Guy", "en-US", "male"),
            ("en-GB-SoniaNeural", "Sonia", "en-GB", "female"),
            ("en-AU-NatashaNeural", "Natasha", "en-AU", "female"),
        ]

        result = []
        for name, display_name, locale, gender in predefined_voices:
            if language and not locale.startswith(language):
                continue

            voice_info = VoiceInfo(
                name=name,
                display_name=display_name,
                language=locale.split("-")[0],
                locale=locale,
                gender=gender,
                region=locale.split("-")[1] if "-" in locale else "unknown",
                engine="azure",
                sample_rate=24000,
                quality="premium",
                is_neural=True,
                supports_ssml=True,
                supported_formats=["wav", "mp3"],
            )
            result.append(voice_info)

        return result

    def _create_subtitle_from_text(self, text: str, duration: float) -> SubtitleMaker:
        """从文本创建简单字幕（估算时间）"""
        subtitle_maker = SubtitleMaker()

        # 简单的时间估算：假设平均语速
        words = text.split()
        if words:
            word_duration = duration / len(words)
            current_time = 0.0

            for word in words:
                start_time = current_time
                end_time = current_time + word_duration
                subtitle_maker.add_segment(start_time, end_time, word)
                current_time = end_time
        else:
            # 如果没有词，整个文本作为一个片段
            subtitle_maker.add_segment(0.0, duration, text)

        return subtitle_maker

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
                f"无法通过 ffprobe 获取 Azure 音频时长，改用文件大小估算: {exc}"
            )

        # 估算时长
        try:
            import os

            file_size = os.path.getsize(audio_file)
            # WAV文件大约48KB/s (24kHz 16-bit)
            return file_size / 48000
        except Exception:
            return 0.0

    def _get_engine_info(self) -> dict:
        """获取引擎信息"""
        return {
            "engine": "azure",
            "version": "1.0.0",
            "default_voice": self.get_default_voice(),
            "supported_formats": ["wav", "mp3"],
            "max_text_length": 50000,
            "supports_ssml": True,
            "supports_subtitles": True,
            "neural_voices": True,
            "custom_voices": True,
            "region": self.service_region,
        }
