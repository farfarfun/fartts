"""
Coqui TTS引擎实现

Coqui TTS是一个功能强大的深度学习文本转语音工具包，支持多种先进的TTS模型。
包括VITS、Tacotron、GlowTTS等多种架构，提供高质量的语音合成和语音克隆功能。
"""

import tempfile
import time
from pathlib import Path
from typing import Any

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


class CoquiTTS(BaseTTS):
    """Coqui TTS引擎实现类"""

    def __init__(self, model_name: str | None = None, device: str = "auto", **kwargs):
        """
        初始化Coqui TTS引擎

        Args:
            model_name: 模型名称，如 'tts_models/en/ljspeech/tacotron2-DDC'
            device: 计算设备 ('cpu', 'cuda', 'auto')
            **kwargs: 其他配置参数
        """
        super().__init__(**kwargs)

        self.model_name = model_name or "tts_models/en/ljspeech/tacotron2-DDC"
        self.device = self._setup_device(device)
        self.tts_model = None

        # 配置参数
        self.config = {
            "sample_rate": kwargs.get("sample_rate", 22050),
            "vocoder_name": kwargs.get("vocoder_name", None),
            "speaker_wav": kwargs.get("speaker_wav", None),  # 用于语音克隆
            "language": kwargs.get("language", "en"),
            "emotion": kwargs.get("emotion", "neutral"),
            "speed": kwargs.get("speed", 1.0),
        }

        logger.info(
            f"Coqui TTS引擎初始化完成，模型: {self.model_name}, 设备: {self.device}"
        )

    def _setup_device(self, device: str) -> str:
        """设置计算设备"""
        if device == "auto":
            try:
                import torch

                if torch.cuda.is_available():
                    return "cuda"
                elif (
                    hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
                ):
                    return "mps"
                else:
                    return "cpu"
            except ImportError:
                return "cpu"
        return device

    def _load_model(self):
        """延迟加载模型"""
        if self.tts_model is not None:
            return

        try:
            from TTS.api import TTS

            logger.info(f"正在加载Coqui TTS模型: {self.model_name}")

            # 初始化TTS模型
            self.tts_model = TTS(
                model_name=self.model_name, gpu=(self.device == "cuda")
            )

            logger.success("Coqui TTS模型加载成功")

        except ImportError:
            logger.error("Coqui TTS未安装，请运行: pip install TTS")
            raise RuntimeError("Coqui TTS未安装，请先安装依赖")
        except Exception as e:
            logger.error(f"Coqui TTS模型加载失败: {e}")
            raise RuntimeError(f"无法加载Coqui TTS模型: {e}")

    def _synthesize(self, request: TTSRequest) -> TTSResponse:
        """
        执行语音合成

        Args:
            request: TTS请求对象

        Returns:
            TTSResponse: 包含音频文件路径和字幕信息的响应对象
        """
        try:
            # 延迟加载模型
            self._load_model()

            logger.info(f"开始Coqui TTS语音合成: {request.text[:50]}...")
            start_time = time.time()

            # 准备输出文件路径
            timestamp = int(time.time() * 1000)
            base_name = f"coqui_output_{timestamp}"

            if request.output_dir:
                output_dir = Path(request.output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
            else:
                output_dir = Path(tempfile.gettempdir()) / "funtts"
                output_dir.mkdir(parents=True, exist_ok=True)

            audio_file = output_dir / f"{base_name}.wav"

            # 准备合成参数
            synthesis_params = self._prepare_synthesis_params(request)

            # 执行语音合成
            if self._is_multispeaker_model():
                # 多说话人模型
                self.tts_model.tts_to_file(
                    text=request.text,
                    file_path=str(audio_file),
                    speaker=synthesis_params.get("speaker", None),
                    language=synthesis_params.get("language", None),
                    emotion=synthesis_params.get("emotion", None),
                )
            elif synthesis_params.get("speaker_wav"):
                # 语音克隆
                self.tts_model.tts_to_file(
                    text=request.text,
                    file_path=str(audio_file),
                    speaker_wav=synthesis_params["speaker_wav"],
                    language=synthesis_params.get("language", None),
                )
            else:
                # 单说话人模型
                self.tts_model.tts_to_file(text=request.text, file_path=str(audio_file))

            # 获取音频时长
            duration = self._get_audio_duration(audio_file)

            # 生成字幕：只产出 SubtitleMaker，落盘统一交给 BaseTTS.synthesize()。
            # 原实现拿 request.subtitle_format 本身当开关，而该字段默认是
            # "srt"（恒为真），既忽略了 generate_subtitles 开关，又只认
            # "srt"/"frt" 两个子串——subtitle_format="vtt" 时什么都不会写。
            subtitle_maker = None
            if request.generate_subtitles:
                subtitle_maker = SubtitleMaker(
                    [
                        AudioSegment(
                            text=request.text,
                            start_time=0.0,
                            end_time=duration,
                            voice_name=request.voice_name or "default",
                        )
                    ]
                )

            synthesis_time = time.time() - start_time
            logger.success(f"Coqui TTS语音合成完成，耗时: {synthesis_time:.2f}秒")

            return TTSResponse(
                success=True,
                audio_file=str(audio_file),
                subtitle_maker=subtitle_maker,
                duration=duration,
                voice_used=request.voice_name or "default",
                engine_info={
                    "engine_name": "Coqui TTS",
                    "sample_rate": self.config["sample_rate"],
                },
            )

        except Exception as e:
            logger.error(f"Coqui TTS语音合成失败: {e}")
            raise RuntimeError(f"Coqui TTS语音合成错误: {e}")

    def _prepare_synthesis_params(self, request: TTSRequest) -> dict[str, Any]:
        """准备合成参数"""
        params = {}

        # 语言设置
        if hasattr(request, "language") and request.language:
            params["language"] = request.language
        elif self.config["language"]:
            params["language"] = self.config["language"]

        # 说话人设置
        if request.voice_name:
            params["speaker"] = request.voice_name

        # 情感设置
        if hasattr(request, "emotion") and request.emotion:
            params["emotion"] = request.emotion
        elif self.config["emotion"]:
            params["emotion"] = self.config["emotion"]

        # 语音克隆
        if hasattr(request, "speaker_wav") and request.speaker_wav:
            params["speaker_wav"] = request.speaker_wav
        elif self.config["speaker_wav"]:
            params["speaker_wav"] = self.config["speaker_wav"]

        return params

    def _is_multispeaker_model(self) -> bool:
        """检查是否为多说话人模型"""
        return len(getattr(self.tts_model, "speakers", None) or []) > 1

    def _get_audio_duration(self, audio_file: Path) -> float:
        """获取音频文件时长"""
        try:
            import librosa

            y, sr = librosa.load(str(audio_file))
            return len(y) / sr
        except ImportError:
            # 如果没有librosa，使用估算
            return len(str(audio_file)) * 0.1
        except Exception as e:
            logger.warning(f"获取音频时长失败: {e}")
            return 0.0

    def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        """
        获取可用语音列表

        Args:
            language: 语言代码过滤，如 'en', 'zh'

        Returns:
            List[VoiceInfo]: 语音信息列表
        """
        try:
            logger.info("获取Coqui TTS可用语音列表")

            # 延迟加载模型
            self._load_model()

            voices = []

            # 获取模型支持的说话人
            if hasattr(self.tts_model, "speakers") and self.tts_model.speakers:
                for speaker in self.tts_model.speakers:
                    voice_info = VoiceInfo(
                        name=speaker,
                        display_name=speaker,
                        language=self._get_model_language(),
                        gender="Unknown",
                        locale=self._get_model_language(),
                        sample_rate=self.config["sample_rate"],
                        description=f"Coqui TTS speaker: {speaker}",
                    )
                    voices.append(voice_info)
            else:
                # 单说话人模型
                voice_info = VoiceInfo(
                    name="default",
                    display_name="Default Voice",
                    language=self._get_model_language(),
                    gender="Unknown",
                    locale=self._get_model_language(),
                    sample_rate=self.config["sample_rate"],
                    description="Coqui TTS default voice",
                )
                voices.append(voice_info)

            # 根据语言过滤
            if language:
                voices = [v for v in voices if v.language.startswith(language)]

            logger.success(f"获取到 {len(voices)} 个Coqui TTS语音")
            return voices

        except Exception as e:
            logger.error(f"获取Coqui TTS语音列表失败: {e}")
            return []

    def _get_model_language(self) -> str:
        """获取模型语言"""
        # 从模型名称推断语言
        if "/en/" in self.model_name:
            return "en"
        elif "/zh/" in self.model_name:
            return "zh"
        elif "/es/" in self.model_name:
            return "es"
        elif "/fr/" in self.model_name:
            return "fr"
        elif "/de/" in self.model_name:
            return "de"
        elif "/ja/" in self.model_name:
            return "ja"
        else:
            return "en"  # 默认英语

    def list_available_models(self) -> list[str]:
        """获取可用模型列表"""
        try:
            from TTS.api import TTS

            # 获取预训练模型列表
            models = TTS.list_models()
            return models

        except ImportError:
            logger.error("Coqui TTS未安装")
            return []
        except Exception as e:
            logger.error(f"获取模型列表失败: {e}")
            return []

    def clone_voice(
        self, text: str, speaker_wav: str, output_path: str, language: str = "en"
    ) -> str:
        """
        语音克隆功能

        Args:
            text: 要合成的文本
            speaker_wav: 参考语音文件路径
            output_path: 输出文件路径
            language: 语言代码

        Returns:
            str: 生成的音频文件路径
        """
        try:
            # 延迟加载模型
            self._load_model()

            logger.info(f"开始语音克隆: {text[:50]}...")

            # 执行语音克隆
            self.tts_model.tts_to_file(
                text=text,
                file_path=output_path,
                speaker_wav=speaker_wav,
                language=language,
            )

            logger.success(f"语音克隆完成: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"语音克隆失败: {e}")
            raise RuntimeError(f"语音克隆错误: {e}")

    def get_engine_info(self) -> dict[str, Any]:
        """获取引擎信息"""
        return {
            "name": "Coqui TTS",
            "version": "0.22.0",
            "description": "功能强大的深度学习TTS工具包，支持多种模型和语音克隆",
            "supported_formats": ["wav"],
            "supported_languages": [
                "en",
                "es",
                "fr",
                "de",
                "it",
                "pt",
                "pl",
                "tr",
                "ru",
                "nl",
                "cs",
                "ar",
                "zh",
                "ja",
                "hu",
                "ko",
            ],
            "features": [
                "多种TTS模型支持",
                "语音克隆",
                "多语言支持",
                "高质量语音合成",
                "可训练自定义模型",
            ],
            "model_name": self.model_name,
            "device": self.device,
            "sample_rate": self.config["sample_rate"],
        }
