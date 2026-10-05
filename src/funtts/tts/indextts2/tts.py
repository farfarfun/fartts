"""
IndexTTS2 TTS引擎实现

IndexTTS2是一个工业级可控制的文本转语音模型，支持情感控制和自然语言指令。
具有高质量的语音合成能力和精确的时长控制功能。
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


class IndexTTS2(BaseTTS):
    """IndexTTS2 TTS引擎实现类"""

    def __init__(self, model_path: str | None = None, device: str = "auto", **kwargs):
        """
        初始化IndexTTS2引擎

        Args:
            model_path: 模型路径，如果为None则使用默认路径
            device: 计算设备 ('cpu', 'cuda', 'auto')
            **kwargs: 其他配置参数
        """
        super().__init__(**kwargs)

        self.model_path = model_path
        self.device = self._setup_device(device)
        self.model = None
        self.tokenizer = None

        # 配置参数
        self.config = {
            "sample_rate": kwargs.get("sample_rate", 22050),
            "temperature": kwargs.get("temperature", 1.0),
            "top_k": kwargs.get("top_k", 50),
            "top_p": kwargs.get("top_p", 0.9),
            "emotion_strength": kwargs.get("emotion_strength", 1.0),
            "speed_factor": kwargs.get("speed_factor", 1.0),
        }

        logger.info(f"IndexTTS2引擎初始化完成，设备: {self.device}")

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
        """延迟加载模型

        本引擎目前只有骨架，尚未对接真实的 IndexTTS2 模型，因此这里直接抛错。

        原实现把 `self.model = {"status": "loaded"}` 当作「加载成功」，再由
        `_generate_speech()` 返回一段 `np.zeros(...)` 静音，最终以
        `success=True` 返回一个纯静音 WAV——调用方完全无法察觉合成根本没发生。
        宁可快速失败，也不要静默产出错误结果。
        """
        raise NotImplementedError(
            "IndexTTS2 引擎尚未对接真实模型，当前仅有骨架实现。"
            "请改用 edge / azure / bark / coqui / tortoise / kitten 等引擎。"
        )

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

            logger.info(f"开始IndexTTS2语音合成: {request.text[:50]}...")
            start_time = time.time()

            # 准备输出文件路径
            timestamp = int(time.time() * 1000)
            base_name = f"indextts2_output_{timestamp}"

            if request.output_dir:
                output_dir = Path(request.output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
            else:
                output_dir = Path(tempfile.gettempdir()) / "funtts"
                output_dir.mkdir(parents=True, exist_ok=True)

            audio_file = output_dir / f"{base_name}.wav"

            # 准备合成参数
            synthesis_params = {
                "text": request.text,
                "voice_name": request.voice_name or "default",
                "temperature": getattr(request, "temperature", None)
                or self.config["temperature"],
                "speed": getattr(request, "speed", None) or self.config["speed_factor"],
                "emotion": getattr(request, "emotion", "neutral"),
                "emotion_strength": getattr(
                    request, "emotion_strength", self.config["emotion_strength"]
                ),
            }

            # 执行语音合成
            audio_data = self._generate_speech(synthesis_params)

            # 保存音频文件
            self._save_audio(audio_data, audio_file)

            # 估算音频时长
            duration = self._estimate_duration(
                request.text, synthesis_params.get("speed", 1.0)
            )

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
            logger.success(f"IndexTTS2语音合成完成，耗时: {synthesis_time:.2f}秒")

            return TTSResponse(
                success=True,
                audio_file=str(audio_file),
                subtitle_maker=subtitle_maker,
                duration=duration,
                voice_used=request.voice_name or "default",
                engine_info={
                    "engine_name": "IndexTTS2",
                    "sample_rate": self.config["sample_rate"],
                },
            )

        except NotImplementedError:
            # 引擎未实现的事实不要被包装成普通运行时错误
            raise
        except Exception as e:
            logger.error(f"IndexTTS2语音合成失败: {e}")
            raise RuntimeError(f"IndexTTS2语音合成错误: {e}")

    def _generate_speech(self, params: dict[str, Any]) -> bytes:
        """生成语音数据

        未对接真实模型前不要返回任何占位音频：原实现返回
        `np.zeros(...)` 静音，调用链一路 `success=True`，用户拿到的是一个
        合法但完全无声的 WAV。

        Args:
            params: 合成参数

        Returns:
            bytes: 音频数据
        """
        raise NotImplementedError(
            "IndexTTS2 引擎尚未对接真实模型，无法生成音频。"
            f"待实现的合成参数: {sorted(params)}"
        )

    def _save_audio(self, audio_data: bytes, output_path: Path):
        """保存音频文件"""
        try:
            import wave

            # 保存为WAV文件
            with wave.open(str(output_path), "wb") as wav_file:
                wav_file.setnchannels(1)  # 单声道
                wav_file.setsampwidth(2)  # 16位
                wav_file.setframerate(self.config["sample_rate"])
                wav_file.writeframes(audio_data)

            logger.debug(f"音频文件已保存: {output_path}")

        except Exception as e:
            logger.error(f"保存音频文件失败: {e}")
            raise

    def _estimate_duration(self, text: str, speed: float = 1.0) -> float:
        """估算音频时长"""
        # 基于文本长度和语速估算时长
        # 平均每个字符0.1秒，根据语速调整
        base_duration = len(text) * 0.1
        return base_duration / speed

    def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        """
        获取可用语音列表

        Args:
            language: 语言代码过滤，如 'zh-CN', 'en-US'

        Returns:
            List[VoiceInfo]: 语音信息列表
        """
        try:
            logger.info("获取IndexTTS2可用语音列表")

            # IndexTTS2支持的语音列表（示例）
            voices = [
                VoiceInfo(
                    name="zh-CN-XiaoxiaoNeural",
                    display_name="晓晓 (女声)",
                    language="zh-CN",
                    gender="Female",
                    locale="zh-CN",
                    sample_rate=22050,
                    description="中文女声，自然流畅，支持情感控制",
                ),
                VoiceInfo(
                    name="zh-CN-YunxiNeural",
                    display_name="云希 (男声)",
                    language="zh-CN",
                    gender="Male",
                    locale="zh-CN",
                    sample_rate=22050,
                    description="中文男声，沉稳大气，支持情感控制",
                ),
                VoiceInfo(
                    name="en-US-AriaNeural",
                    display_name="Aria (Female)",
                    language="en-US",
                    gender="Female",
                    locale="en-US",
                    sample_rate=22050,
                    description="English female voice with emotion control",
                ),
                VoiceInfo(
                    name="en-US-GuyNeural",
                    display_name="Guy (Male)",
                    language="en-US",
                    gender="Male",
                    locale="en-US",
                    sample_rate=22050,
                    description="English male voice with emotion control",
                ),
            ]

            # 根据语言过滤
            if language:
                voices = [v for v in voices if v.language.startswith(language)]

            logger.success(f"获取到 {len(voices)} 个IndexTTS2语音")
            return voices

        except Exception as e:
            logger.error(f"获取IndexTTS2语音列表失败: {e}")
            return []

    def get_engine_info(self) -> dict[str, Any]:
        """获取引擎信息"""
        return {
            "name": "IndexTTS2",
            "version": "2.0.0",
            "description": "工业级可控制的文本转语音模型，支持情感控制",
            "supported_formats": ["wav"],
            "supported_languages": ["zh-CN", "en-US", "ja-JP", "ko-KR"],
            "features": [
                "高质量语音合成",
                "情感控制",
                "自然语言指令",
                "精确时长控制",
                "多语言支持",
            ],
            "device": self.device,
            "sample_rate": self.config["sample_rate"],
        }
