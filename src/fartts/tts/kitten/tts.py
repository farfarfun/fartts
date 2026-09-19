"""
KittenTTS引擎实现

KittenTTS是一个基于深度学习的高质量文本转语音引擎，
支持多种语言和语音风格，提供自然流畅的语音合成效果。

本模块提供了统一的接口来使用KittenTTS进行语音合成。
"""

import os
import tempfile
import time
from typing import Any

try:
    import requests
    import torch

    # 假设KittenTTS的导入方式
    from kitten_tts import KittenTTSConfig, KittenTTSModel
except ImportError:
    requests = None
    torch = None
    KittenTTSModel = None
    KittenTTSConfig = None

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


class KittenTTS(BaseTTS):
    """KittenTTS引擎实现

    基于KittenTTS深度学习模型的高质量TTS引擎，支持多种语言和语音风格。
    """

    def __init__(self, voice_name: str = "default", **kwargs):
        """初始化KittenTTS引擎

        Args:
            voice_name: 语音名称或ID
            **kwargs: 其他配置参数
                - model_path: 模型文件路径
                - config_path: 配置文件路径
                - device: 计算设备 ('cpu', 'cuda', 'auto')
                - sample_rate: 采样率，默认22050
                - speed: 语音速度倍数，默认1.0
                - pitch: 音调调节，默认1.0
        """
        super().__init__(voice_name, **kwargs)

        # 检查依赖
        if KittenTTSModel is None:
            raise ImportError(
                "KittenTTS相关依赖未安装，请运行: pip install kitten-tts torch"
            )

        # 配置参数
        self.model_path = kwargs.get("model_path", None)
        self.config_path = kwargs.get("config_path", None)
        self.device = kwargs.get("device", "auto")
        self.sample_rate = kwargs.get("sample_rate", 22050)
        self.speed = kwargs.get("speed", 1.0)
        self.pitch = kwargs.get("pitch", 1.0)

        # 模型实例
        self.model = None
        self.config = None

        self._init_model()

    def _init_model(self):
        """初始化KittenTTS模型"""
        try:
            # 设备选择
            if self.device == "auto":
                self.device = "cuda" if torch.cuda.is_available() else "cpu"

            logger.info(f"初始化KittenTTS模型，设备: {self.device}")

            # 加载配置
            if self.config_path and os.path.exists(self.config_path):
                self.config = KittenTTSConfig.from_file(self.config_path)
            else:
                self.config = KittenTTSConfig()
                logger.warning("使用默认配置，建议提供配置文件路径")

            # 加载模型
            if self.model_path and os.path.exists(self.model_path):
                self.model = KittenTTSModel.load_model(
                    self.model_path, config=self.config, device=self.device
                )
            else:
                # 尝试加载预训练模型
                self.model = KittenTTSModel.load_pretrained(
                    config=self.config, device=self.device
                )
                logger.info("使用预训练模型")

            logger.info("KittenTTS模型初始化成功")

        except Exception as e:
            logger.error(f"KittenTTS模型初始化失败: {str(e)}")
            raise

    def _synthesize(self, request: TTSRequest) -> TTSResponse:
        """执行语音合成

        Args:
            request: TTS请求对象

        Returns:
            TTS响应对象
        """
        start_time = time.time()

        try:
            if not self.model:
                self._init_model()

            # 验证文本长度
            if len(request.text) > 5000:
                return TTSResponse(
                    success=False,
                    request=request,
                    error_message="文本长度超过限制（最大5000字符）",
                    error_code="TEXT_TOO_LONG",
                    processing_time=time.time() - start_time,
                )

            # 准备输出文件
            output_file = request.output_file
            if not output_file:
                output_file = tempfile.mktemp(suffix=".wav")

            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            # 准备合成参数
            synthesis_params = self._prepare_synthesis_params(request)

            # 执行合成
            logger.info(f"开始KittenTTS合成: {len(request.text)}字符")

            audio_data = self.model.synthesize(
                text=request.text,
                voice_name=request.voice_name or self.voice_name,
                **synthesis_params,
            )

            # 保存音频文件
            self._save_audio(audio_data, output_file)

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
            duration = self._calculate_audio_duration(audio_data)

            # 生成字幕（如果需要）
            subtitle_file = None
            frt_subtitle_file = None
            if request.generate_subtitles:
                subtitle_file, frt_subtitle_file = self._generate_subtitles(
                    request, output_file, duration
                )

            logger.success(f"KittenTTS合成完成: {output_file} ({duration:.2f}s)")

            return TTSResponse(
                success=True,
                request=request,
                audio_file=output_file,
                subtitle_file=subtitle_file,
                frt_subtitle_file=frt_subtitle_file,
                duration=duration,
                voice_used=request.voice_name or self.voice_name,
                processing_time=time.time() - start_time,
                engine_info=self.get_engine_info(),
            )

        except Exception as e:
            logger.error(f"KittenTTS语音合成失败: {str(e)}")
            return TTSResponse(
                success=False,
                request=request,
                error_message=str(e),
                error_code="SYNTHESIS_ERROR",
                processing_time=time.time() - start_time,
            )

    def _prepare_synthesis_params(self, request: TTSRequest) -> dict[str, Any]:
        """准备合成参数

        Args:
            request: TTS请求对象

        Returns:
            合成参数字典
        """
        params = {
            "sample_rate": self.sample_rate,
            "speed": self.speed * request.voice_rate,
            "pitch": self.pitch,
        }

        # 输出格式映射
        format_mapping = {
            "wav": "wav",
            "mp3": "mp3",
            "ogg": "ogg",
        }

        if request.output_format in format_mapping:
            params["output_format"] = format_mapping[request.output_format]

        return params

    def _save_audio(self, audio_data, output_file: str):
        """保存音频数据到文件

        Args:
            audio_data: 音频数据
            output_file: 输出文件路径
        """
        try:
            # 根据音频数据类型保存
            if hasattr(audio_data, "save"):
                # 如果是音频对象，直接保存
                audio_data.save(output_file)
            elif isinstance(audio_data, bytes):
                # 如果是字节数据，写入文件
                with open(output_file, "wb") as f:
                    f.write(audio_data)
            elif hasattr(audio_data, "numpy"):
                # 如果是tensor，转换后保存
                import soundfile as sf

                audio_np = audio_data.numpy()
                sf.write(output_file, audio_np, self.sample_rate)
            else:
                raise ValueError(f"不支持的音频数据类型: {type(audio_data)}")

        except Exception as e:
            logger.error(f"保存音频文件失败: {str(e)}")
            raise

    def _calculate_audio_duration(self, audio_data) -> float:
        """计算音频时长

        Args:
            audio_data: 音频数据

        Returns:
            音频时长（秒）
        """
        try:
            if hasattr(audio_data, "shape"):
                # 如果是numpy数组或tensor
                if len(audio_data.shape) == 1:
                    return len(audio_data) / self.sample_rate
                elif len(audio_data.shape) == 2:
                    return audio_data.shape[1] / self.sample_rate
            elif hasattr(audio_data, "duration"):
                # 如果有duration属性
                return audio_data.duration
            else:
                # 默认估算
                return (
                    len(audio_data) / self.sample_rate
                    if hasattr(audio_data, "__len__")
                    else 0.0
                )

        except Exception:
            return 0.0

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
                voice_name=request.voice_name or self.voice_name,
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
            if not self.model:
                self._init_model()

            # 获取模型支持的语音列表
            voices = (
                self.model.get_available_voices()
                if hasattr(self.model, "get_available_voices")
                else []
            )

            if not voices:
                # 如果模型不提供语音列表，返回默认语音
                logger.warning("模型未提供语音列表，返回默认语音")
                return [
                    VoiceInfo(
                        name="default",
                        display_name="KittenTTS Default",
                        language="zh-CN",
                        gender="female",
                        region="CN",
                        engine="kitten",
                        sample_rate=self.sample_rate,
                        quality="high",
                        metadata={
                            "model_based": True,
                            "neural": True,
                        },
                    )
                ]

            result = []
            for voice in voices:
                # 语言过滤
                voice_lang = getattr(voice, "language", "unknown")
                if language and not voice_lang.lower().startswith(language.lower()):
                    continue

                voice_info = VoiceInfo(
                    name=getattr(voice, "id", getattr(voice, "name", "unknown")),
                    display_name=getattr(
                        voice, "display_name", getattr(voice, "name", "Unknown")
                    ),
                    language=voice_lang,
                    gender=getattr(voice, "gender", "unknown").lower(),
                    region=getattr(voice, "region", "unknown"),
                    engine="kitten",
                    sample_rate=getattr(voice, "sample_rate", self.sample_rate),
                    quality="high",
                    metadata={
                        "model_based": True,
                        "neural": True,
                        "style": getattr(voice, "style", None),
                        "emotion": getattr(voice, "emotion", None),
                    },
                )
                result.append(voice_info)

            logger.info(f"找到 {len(result)} 个KittenTTS语音")
            return result

        except Exception as e:
            logger.error(f"获取KittenTTS语音列表失败: {str(e)}")
            return []

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

    def get_engine_info(self) -> dict:
        """获取引擎信息

        Returns:
            引擎信息字典
        """
        return {
            "engine_name": "KittenTTS",
            "version": "1.0.0",
            "description": "基于深度学习的高质量TTS引擎",
            "supported_formats": ["wav", "mp3", "ogg"],
            "max_text_length": 5000,
            "supports_ssml": False,
            "supports_subtitles": True,
            "neural_based": True,
            "default_voice": self.voice_name,
            "device": self.device,
            "sample_rate": self.sample_rate,
            "model_path": self.model_path,
        }

    def __del__(self):
        """析构函数，清理资源"""
        if hasattr(self, "model") and self.model:
            try:
                # 清理GPU内存
                if hasattr(self.model, "cleanup"):
                    self.model.cleanup()
                del self.model
                if torch and torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass
