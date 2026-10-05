"""
Tortoise TTS引擎实现

Tortoise TTS是一个高质量的语音克隆TTS模型，能够生成极其逼真的语音。
虽然合成速度较慢，但音质接近真人水平，特别适合高质量语音克隆应用。
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


class TortoiseTTS(BaseTTS):
    """Tortoise TTS引擎实现类"""

    def __init__(self, device: str = "auto", **kwargs):
        """
        初始化Tortoise TTS引擎

        Args:
            device: 计算设备 ('cpu', 'cuda', 'auto')
            **kwargs: 其他配置参数
        """
        super().__init__(**kwargs)

        self.device = self._setup_device(device)
        self.api = None

        # 配置参数
        self.config = {
            "sample_rate": kwargs.get("sample_rate", 22050),
            "preset": kwargs.get(
                "preset", "fast"
            ),  # 'ultra_fast', 'fast', 'standard', 'high_quality'
            "voice_fixer": kwargs.get("voice_fixer", False),
            "candidates": kwargs.get("candidates", 1),
        }

        logger.info(f"Tortoise TTS引擎初始化完成，设备: {self.device}")

    def _setup_device(self, device: str) -> str:
        """设置计算设备"""
        if device == "auto":
            try:
                import torch

                if torch.cuda.is_available():
                    return "cuda"
                else:
                    return "cpu"
            except ImportError:
                return "cpu"
        return device

    def _load_model(self):
        """延迟加载模型"""
        if self.api is not None:
            return

        try:
            from tortoise.api import TextToSpeech

            logger.info("正在加载Tortoise TTS模型...")

            # 初始化API
            self.api = TextToSpeech(
                use_deepspeed=(self.device == "cuda"),
                kv_cache=True,
                half=(self.device == "cuda"),
            )

            logger.success("Tortoise TTS模型加载成功")

        except ImportError:
            logger.error("Tortoise TTS未安装，请运行: pip install tortoise-tts")
            raise RuntimeError("Tortoise TTS未安装，请先安装依赖")
        except Exception as e:
            logger.error(f"Tortoise TTS模型加载失败: {e}")
            raise RuntimeError(f"无法加载Tortoise TTS模型: {e}")

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

            logger.info(f"开始Tortoise TTS语音合成: {request.text[:50]}...")
            start_time = time.time()

            # 准备输出文件路径
            timestamp = int(time.time() * 1000)
            base_name = f"tortoise_output_{timestamp}"

            if request.output_dir:
                output_dir = Path(request.output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
            else:
                output_dir = Path(tempfile.gettempdir()) / "funtts"
                output_dir.mkdir(parents=True, exist_ok=True)

            audio_file = output_dir / f"{base_name}.wav"

            # 准备合成参数
            voice_name = request.voice_name or "random"

            # 执行语音合成
            gen = self.api.tts_with_preset(
                text=request.text,
                voice_samples=None,  # 使用预设语音
                conditioning_latents=None,
                preset=self.config["preset"],
                k=self.config["candidates"],
            )

            # 保存音频文件
            import torchaudio

            torchaudio.save(
                str(audio_file), gen.squeeze(0).cpu(), self.config["sample_rate"]
            )

            # 获取音频时长
            duration = gen.shape[-1] / self.config["sample_rate"]

            # 生成字幕
            subtitle_file = None
            frt_subtitle_file = None

            if request.subtitle_format:
                segments = [
                    AudioSegment(
                        text=request.text,
                        start_time=0.0,
                        end_time=duration,
                        voice_name=voice_name,
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
            logger.success(f"Tortoise TTS语音合成完成，耗时: {synthesis_time:.2f}秒")

            return TTSResponse(
                success=True,
                audio_file=str(audio_file),
                subtitle_file=str(subtitle_file) if subtitle_file else None,
                frt_subtitle_file=str(frt_subtitle_file) if frt_subtitle_file else None,
                duration=duration,
                voice_used=voice_name,
                engine_info={
                    "engine_name": "Tortoise TTS",
                    "sample_rate": self.config["sample_rate"],
                },
            )

        except Exception as e:
            logger.error(f"Tortoise TTS语音合成失败: {e}")
            raise RuntimeError(f"Tortoise TTS语音合成错误: {e}")

    def clone_voice(self, text: str, voice_samples: list[str], output_path: str) -> str:
        """
        语音克隆功能

        Args:
            text: 要合成的文本
            voice_samples: 参考语音文件路径列表
            output_path: 输出文件路径

        Returns:
            str: 生成的音频文件路径
        """
        try:
            # 延迟加载模型
            self._load_model()

            logger.info(f"开始Tortoise语音克隆: {text[:50]}...")

            # 加载参考语音
            import torchaudio

            voice_samples_audio = []
            for sample_path in voice_samples:
                audio, sr = torchaudio.load(sample_path)
                if sr != 22050:
                    audio = torchaudio.functional.resample(audio, sr, 22050)
                voice_samples_audio.append(audio)

            # 执行语音克隆
            gen = self.api.tts_with_preset(
                text=text,
                voice_samples=voice_samples_audio,
                conditioning_latents=None,
                preset=self.config["preset"],
                k=self.config["candidates"],
            )

            # 保存音频
            torchaudio.save(
                output_path, gen.squeeze(0).cpu(), self.config["sample_rate"]
            )

            logger.success(f"Tortoise语音克隆完成: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Tortoise语音克隆失败: {e}")
            raise RuntimeError(f"语音克隆错误: {e}")

    def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        """
        获取可用语音列表

        Args:
            language: 语言代码过滤

        Returns:
            List[VoiceInfo]: 语音信息列表
        """
        try:
            logger.info("获取Tortoise TTS可用语音列表")

            # Tortoise内置语音
            voices = [
                VoiceInfo(
                    name="angie",
                    display_name="Angie (Female)",
                    language="en",
                    gender="Female",
                    locale="en-US",
                    sample_rate=22050,
                    description="Clear female voice, professional tone",
                ),
                VoiceInfo(
                    name="deniro",
                    display_name="Deniro (Male)",
                    language="en",
                    gender="Male",
                    locale="en-US",
                    sample_rate=22050,
                    description="Deep male voice, distinctive character",
                ),
                VoiceInfo(
                    name="freeman",
                    display_name="Freeman (Male)",
                    language="en",
                    gender="Male",
                    locale="en-US",
                    sample_rate=22050,
                    description="Authoritative male voice, narrator style",
                ),
                VoiceInfo(
                    name="geralt",
                    display_name="Geralt (Male)",
                    language="en",
                    gender="Male",
                    locale="en-US",
                    sample_rate=22050,
                    description="Gruff male voice, character-like",
                ),
                VoiceInfo(
                    name="jlaw",
                    display_name="JLaw (Female)",
                    language="en",
                    gender="Female",
                    locale="en-US",
                    sample_rate=22050,
                    description="Young female voice, casual tone",
                ),
                VoiceInfo(
                    name="lj",
                    display_name="LJ (Female)",
                    language="en",
                    gender="Female",
                    locale="en-US",
                    sample_rate=22050,
                    description="Classic female voice, clear pronunciation",
                ),
                VoiceInfo(
                    name="mol",
                    display_name="Mol (Female)",
                    language="en",
                    gender="Female",
                    locale="en-US",
                    sample_rate=22050,
                    description="Soft female voice, gentle tone",
                ),
                VoiceInfo(
                    name="pat",
                    display_name="Pat (Male)",
                    language="en",
                    gender="Male",
                    locale="en-US",
                    sample_rate=22050,
                    description="Friendly male voice, conversational",
                ),
                VoiceInfo(
                    name="pat2",
                    display_name="Pat2 (Male)",
                    language="en",
                    gender="Male",
                    locale="en-US",
                    sample_rate=22050,
                    description="Alternative Pat voice, slightly different tone",
                ),
                VoiceInfo(
                    name="tom",
                    display_name="Tom (Male)",
                    language="en",
                    gender="Male",
                    locale="en-US",
                    sample_rate=22050,
                    description="Mature male voice, professional",
                ),
                VoiceInfo(
                    name="train_dreams",
                    display_name="Train Dreams (Narrator)",
                    language="en",
                    gender="Unknown",
                    locale="en-US",
                    sample_rate=22050,
                    description="Narrative voice, storytelling style",
                ),
                VoiceInfo(
                    name="weaver",
                    display_name="Weaver (Female)",
                    language="en",
                    gender="Female",
                    locale="en-US",
                    sample_rate=22050,
                    description="Distinctive female voice, character-like",
                ),
            ]

            # 根据语言过滤
            if language:
                voices = [v for v in voices if v.language.startswith(language)]

            logger.success(f"获取到 {len(voices)} 个Tortoise TTS语音")
            return voices

        except Exception as e:
            logger.error(f"获取Tortoise TTS语音列表失败: {e}")
            return []

    def get_engine_info(self) -> dict[str, Any]:
        """获取引擎信息"""
        return {
            "name": "Tortoise TTS",
            "version": "2.4.2",
            "description": "高质量语音克隆TTS模型，音质接近真人水平",
            "supported_formats": ["wav"],
            "supported_languages": ["en"],
            "features": [
                "极高质量语音合成",
                "优秀的语音克隆能力",
                "多种预设质量级别",
                "内置多种语音角色",
                "支持自定义语音训练",
            ],
            "device": self.device,
            "sample_rate": self.config["sample_rate"],
            "preset": self.config["preset"],
            "note": "合成速度较慢，但音质极佳，适合高质量应用",
        }
