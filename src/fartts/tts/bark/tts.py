"""
Bark TTS引擎实现

Bark是一个基于Transformer的文本转语音模型，支持生成高度逼真的语音。
除了语音合成外，还支持非语言声音（如笑声、叹息）和背景音乐生成。
"""

import os
import tempfile
import time
from pathlib import Path
from typing import Any

from farlog import getLogger

from fartts.base import BaseTTS
from fartts.models import (
    AudioSegment,
    SubtitleMaker,
    TTSRequest,
    TTSResponse,
    VoiceInfo,
)

logger = getLogger("fartts")

try:
    import torch
    from bark import SAMPLE_RATE, generate_audio, preload_models

    BARK_AVAILABLE = True
except ImportError:
    BARK_AVAILABLE = False
    SAMPLE_RATE = 24000


class BarkTTS(BaseTTS):
    """Bark TTS引擎实现类"""

    def __init__(self, device: str = "auto", **kwargs):
        """
        初始化Bark TTS引擎

        Args:
            device: 计算设备 ('cpu', 'cuda', 'auto')
            **kwargs: 其他配置参数
        """
        super().__init__(**kwargs)

        self.device = self._setup_device(device)
        self.model = None

        # 配置参数
        self.config = {
            "sample_rate": kwargs.get("sample_rate", 24000),
            "text_temp": kwargs.get("text_temp", 0.7),
            "waveform_temp": kwargs.get("waveform_temp", 0.7),
            "silent": kwargs.get("silent", True),
            "use_small_models": kwargs.get("use_small_models", False),
        }

        logger.info(f"Bark TTS引擎初始化完成，设备: {self.device}")

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
        if self.model is not None:
            return

        if not BARK_AVAILABLE:
            raise RuntimeError("Bark TTS未安装，请运行: pip install bark>=0.1.5")

        try:
            logger.info("正在加载Bark TTS模型...")

            # 设置设备
            if self.device == "cuda" and torch.cuda.is_available():
                os.environ["CUDA_VISIBLE_DEVICES"] = "0"

            # 预加载模型
            preload_models(
                text_use_gpu=(self.device == "cuda"),
                text_use_small=(self.config["use_small_models"]),
                coarse_use_gpu=(self.device == "cuda"),
                coarse_use_small=(self.config["use_small_models"]),
                fine_use_gpu=(self.device == "cuda"),
                fine_use_small=(self.config["use_small_models"]),
                codec_use_gpu=(self.device == "cuda"),
            )

            # 设置随机种子以获得可重现的结果
            self.model = {"status": "loaded", "sample_rate": SAMPLE_RATE}
            self.config["sample_rate"] = SAMPLE_RATE

            logger.success("Bark TTS模型加载成功")

        except Exception as e:
            logger.error(f"Bark TTS模型加载失败: {e}")
            raise RuntimeError(f"无法加载Bark TTS模型: {e}")

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

            logger.info(f"开始Bark TTS语音合成: {request.text[:50]}...")
            start_time = time.time()

            # 准备输出文件路径
            timestamp = int(time.time() * 1000)
            base_name = f"bark_output_{timestamp}"

            if request.output_dir:
                output_dir = Path(request.output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
            else:
                output_dir = Path(tempfile.gettempdir()) / "fartts"
                output_dir.mkdir(parents=True, exist_ok=True)

            audio_file = output_dir / f"{base_name}.wav"

            # 准备合成参数
            synthesis_params = self._prepare_synthesis_params(request)

            # 执行语音合成
            audio_array = self._generate_speech(synthesis_params)

            # 保存音频文件
            self._save_audio(audio_array, audio_file)

            # 获取音频时长
            duration = len(audio_array) / self.config["sample_rate"]

            # 生成字幕
            subtitle_file = None
            frt_subtitle_file = None

            if request.subtitle_format:
                segments = [
                    AudioSegment(
                        text=request.text,
                        start_time=0.0,
                        end_time=duration,
                        voice_name=request.voice_name or "default",
                    )
                ]

                subtitle_maker = SubtitleMaker(segments)

                # 生成标准字幕
                if "srt" in request.subtitle_format.lower():
                    subtitle_file = output_dir / f"{base_name}.srt"
                    subtitle_maker.save_srt(subtitle_file)

                # 生成FRT字幕
                if "frt" in request.subtitle_format.lower():
                    frt_subtitle_file = output_dir / f"{base_name}.frt"
                    subtitle_maker.save_frt(frt_subtitle_file)

            synthesis_time = time.time() - start_time
            logger.success(f"Bark TTS语音合成完成，耗时: {synthesis_time:.2f}秒")

            return TTSResponse(
                success=True,
                audio_file=str(audio_file),
                subtitle_file=str(subtitle_file) if subtitle_file else None,
                frt_subtitle_file=str(frt_subtitle_file) if frt_subtitle_file else None,
                duration=duration,
                voice_used=request.voice_name or "default",
                engine_info={
                    "engine_name": "Bark TTS",
                    "sample_rate": self.config["sample_rate"],
                },
            )

        except Exception as e:
            logger.error(f"Bark TTS语音合成失败: {e}")
            raise RuntimeError(f"Bark TTS语音合成错误: {e}")

    def _prepare_synthesis_params(self, request: TTSRequest) -> dict[str, Any]:
        """准备合成参数"""
        params = {
            "text_prompt": request.text,
            "history_prompt": request.voice_name or "v2/en_speaker_6",
            "text_temp": getattr(request, "text_temp", self.config["text_temp"]),
            "waveform_temp": getattr(
                request, "waveform_temp", self.config["waveform_temp"]
            ),
            "silent": self.config["silent"],
        }

        return params

    def _generate_speech(self, params: dict[str, Any]):
        """
        生成语音数据

        Args:
            params: 合成参数

        Returns:
            numpy.ndarray: 音频数组
        """
        try:
            logger.debug(f"生成语音，参数: {params}")

            # 执行语音生成
            audio_array = generate_audio(
                text_prompt=params["text_prompt"],
                history_prompt=params["history_prompt"],
                text_temp=params["text_temp"],
                waveform_temp=params["waveform_temp"],
                silent=params["silent"],
            )

            return audio_array

        except Exception as e:
            logger.error(f"生成语音数据失败: {e}")
            raise

    def _save_audio(self, audio_array, output_path: Path):
        """保存音频文件"""
        try:
            from scipy.io.wavfile import write as write_wav

            # 保存为WAV文件
            write_wav(str(output_path), self.config["sample_rate"], audio_array)

            logger.debug(f"音频文件已保存: {output_path}")

        except ImportError:
            # 如果没有scipy，使用soundfile
            try:
                import soundfile as sf

                sf.write(str(output_path), audio_array, self.config["sample_rate"])
                logger.debug(f"音频文件已保存: {output_path}")
            except ImportError:
                logger.error("需要安装scipy或soundfile来保存音频文件")
                raise
        except Exception as e:
            logger.error(f"保存音频文件失败: {e}")
            raise

    def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        """
        获取可用语音列表

        Args:
            language: 语言代码过滤，如 'en', 'zh'

        Returns:
            List[VoiceInfo]: 语音信息列表
        """
        try:
            logger.info("获取Bark TTS可用语音列表")

            # Bark预设语音列表
            voices = [
                # 英语语音
                VoiceInfo(
                    name="v2/en_speaker_0",
                    display_name="English Speaker 0 (Male)",
                    language="en",
                    gender="Male",
                    locale="en-US",
                    sample_rate=24000,
                    description="English male voice, clear and professional",
                ),
                VoiceInfo(
                    name="v2/en_speaker_1",
                    display_name="English Speaker 1 (Female)",
                    language="en",
                    gender="Female",
                    locale="en-US",
                    sample_rate=24000,
                    description="English female voice, warm and friendly",
                ),
                VoiceInfo(
                    name="v2/en_speaker_2",
                    display_name="English Speaker 2 (Male)",
                    language="en",
                    gender="Male",
                    locale="en-US",
                    sample_rate=24000,
                    description="English male voice, deep and authoritative",
                ),
                VoiceInfo(
                    name="v2/en_speaker_3",
                    display_name="English Speaker 3 (Female)",
                    language="en",
                    gender="Female",
                    locale="en-US",
                    sample_rate=24000,
                    description="English female voice, young and energetic",
                ),
                VoiceInfo(
                    name="v2/en_speaker_4",
                    display_name="English Speaker 4 (Male)",
                    language="en",
                    gender="Male",
                    locale="en-US",
                    sample_rate=24000,
                    description="English male voice, casual and relaxed",
                ),
                VoiceInfo(
                    name="v2/en_speaker_5",
                    display_name="English Speaker 5 (Female)",
                    language="en",
                    gender="Female",
                    locale="en-US",
                    sample_rate=24000,
                    description="English female voice, mature and sophisticated",
                ),
                VoiceInfo(
                    name="v2/en_speaker_6",
                    display_name="English Speaker 6 (Male)",
                    language="en",
                    gender="Male",
                    locale="en-US",
                    sample_rate=24000,
                    description="English male voice, expressive and dynamic",
                ),
                VoiceInfo(
                    name="v2/en_speaker_7",
                    display_name="English Speaker 7 (Female)",
                    language="en",
                    gender="Female",
                    locale="en-US",
                    sample_rate=24000,
                    description="English female voice, gentle and soothing",
                ),
                VoiceInfo(
                    name="v2/en_speaker_8",
                    display_name="English Speaker 8 (Male)",
                    language="en",
                    gender="Male",
                    locale="en-US",
                    sample_rate=24000,
                    description="English male voice, confident and strong",
                ),
                VoiceInfo(
                    name="v2/en_speaker_9",
                    display_name="English Speaker 9 (Female)",
                    language="en",
                    gender="Female",
                    locale="en-US",
                    sample_rate=24000,
                    description="English female voice, bright and cheerful",
                ),
                # 中文语音
                VoiceInfo(
                    name="v2/zh_speaker_0",
                    display_name="Chinese Speaker 0 (Female)",
                    language="zh",
                    gender="Female",
                    locale="zh-CN",
                    sample_rate=24000,
                    description="Chinese female voice, standard Mandarin",
                ),
                VoiceInfo(
                    name="v2/zh_speaker_1",
                    display_name="Chinese Speaker 1 (Male)",
                    language="zh",
                    gender="Male",
                    locale="zh-CN",
                    sample_rate=24000,
                    description="Chinese male voice, standard Mandarin",
                ),
                # 其他语言语音
                VoiceInfo(
                    name="v2/de_speaker_0",
                    display_name="German Speaker 0",
                    language="de",
                    gender="Unknown",
                    locale="de-DE",
                    sample_rate=24000,
                    description="German voice, natural pronunciation",
                ),
                VoiceInfo(
                    name="v2/es_speaker_0",
                    display_name="Spanish Speaker 0",
                    language="es",
                    gender="Unknown",
                    locale="es-ES",
                    sample_rate=24000,
                    description="Spanish voice, natural pronunciation",
                ),
                VoiceInfo(
                    name="v2/fr_speaker_0",
                    display_name="French Speaker 0",
                    language="fr",
                    gender="Unknown",
                    locale="fr-FR",
                    sample_rate=24000,
                    description="French voice, natural pronunciation",
                ),
            ]

            # 根据语言过滤
            if language:
                voices = [v for v in voices if v.language.startswith(language)]

            logger.success(f"获取到 {len(voices)} 个Bark TTS语音")
            return voices

        except Exception as e:
            logger.error(f"获取Bark TTS语音列表失败: {e}")
            return []

    def generate_with_effects(
        self, text: str, output_path: str, effects: list[str] = None
    ) -> str:
        """
        生成带有特效的语音

        Args:
            text: 要合成的文本（可包含特效标记）
            output_path: 输出文件路径
            effects: 特效列表，如 ['laughter', 'music', 'applause']

        Returns:
            str: 生成的音频文件路径
        """
        try:
            # 延迟加载模型
            self._load_model()

            logger.info(f"开始生成带特效的语音: {text[:50]}...")

            # 在文本中添加特效标记
            enhanced_text = text
            if effects:
                for effect in effects:
                    if effect == "laughter":
                        enhanced_text += " [laughter]"
                    elif effect == "music":
                        enhanced_text = "♪ " + enhanced_text + " ♪"
                    elif effect == "applause":
                        enhanced_text += " [applause]"

            # 执行合成
            from bark import generate_audio

            audio_array = generate_audio(
                text_prompt=enhanced_text,
                history_prompt="v2/en_speaker_6",
                text_temp=self.config["text_temp"],
                waveform_temp=self.config["waveform_temp"],
                silent=self.config["silent"],
            )

            # 保存音频
            self._save_audio(audio_array, Path(output_path))

            logger.success(f"带特效语音生成完成: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"生成带特效语音失败: {e}")
            raise RuntimeError(f"特效语音生成错误: {e}")

    def get_engine_info(self) -> dict[str, Any]:
        """获取引擎信息"""
        return {
            "name": "Bark TTS",
            "version": "1.0.0",
            "description": "基于Transformer的TTS模型，支持非语言声音和音乐生成",
            "supported_formats": ["wav"],
            "supported_languages": [
                "en",
                "zh",
                "de",
                "es",
                "fr",
                "hi",
                "it",
                "ja",
                "ko",
                "pl",
                "pt",
                "ru",
                "tr",
            ],
            "features": [
                "高质量语音合成",
                "非语言声音生成",
                "背景音乐生成",
                "多语言支持",
                "情感表达",
                "特效音效",
            ],
            "device": self.device,
            "sample_rate": self.config["sample_rate"],
            "special_features": [
                "支持 [laughter], [sighs], [music] 等特效标记",
                "可生成背景音乐和环境音",
                "支持情感化语音表达",
            ],
        }
